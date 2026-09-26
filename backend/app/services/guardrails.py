import logging
import re

import numpy as np
from sentence_transformers import CrossEncoder

from ..config import guardrails as config

logger = logging.getLogger(__name__)

NO_RETRIEVAL_MESSAGE = (
    "I don't have grounded information in my knowledge base to answer that — "
    "I didn't search for anything relevant before answering."
)
LOW_CONFIDENCE_MESSAGE = (
    "I couldn't find anything in my knowledge base relevant enough to answer that confidently, "
    "so I won't guess."
)
NOT_GROUNDED_MESSAGE = (
    "I found something in my knowledge base, but my answer doesn't look fully supported by "
    "it, so I won't stand behind it as-is."
)

_nli_model: CrossEncoder | None = None
_hhem_model: CrossEncoder | None = None
_hhem_broken = False


def check(trace: dict, answer: str, domain: str = "nimbus") -> dict:
    """Dispatches to whichever strategy GUARDRAIL_STRATEGY selects (see
    config/guardrails.py). All strategies return the same verdict shape.

    `domain` ("nimbus" | "resume") only matters for retrieval_threshold, which needs
    a different threshold per content shape — see config/guardrails.py.
    """
    strategy = config.GUARDRAIL_STRATEGY

    if strategy == "nli_entailment":
        return _check_nli_entailment(trace, answer)
    if strategy == "hhem":
        return _check_hhem(trace, answer, domain)
    if strategy != "retrieval_threshold":
        logger.warning("Unknown GUARDRAIL_STRATEGY=%r, falling back to retrieval_threshold", strategy)
    return _check_retrieval_threshold(trace, domain)


# ---- retrieval_threshold: cosine similarity of the search query against retrieved chunks ----


def _check_retrieval_threshold(trace: dict, domain: str = "nimbus") -> dict:
    threshold = config.RETRIEVAL_SIMILARITY_THRESHOLD_BY_DOMAIN.get(
        domain, config.RETRIEVAL_SIMILARITY_THRESHOLD_DEFAULT
    )
    retrieved = trace.get("retrieved", [])
    if not retrieved:
        return {
            "blocked": True,
            "reason": "no_retrieval",
            "message": NO_RETRIEVAL_MESSAGE,
            "threshold": threshold,
            "strategy": "retrieval_threshold",
        }

    best_score = max(r["score"] for r in retrieved)
    if best_score < threshold:
        return {
            "blocked": True,
            "reason": "low_similarity",
            "message": LOW_CONFIDENCE_MESSAGE,
            "best_score": best_score,
            "threshold": threshold,
            "strategy": "retrieval_threshold",
        }

    return {
        "blocked": False,
        "reason": None,
        "message": None,
        "best_score": best_score,
        "threshold": threshold,
        "strategy": "retrieval_threshold",
    }


# ---- nli_entailment: generic SNLI/MultiNLI cross-encoder, per (sentence, chunk) pair ----


def _get_nli_model() -> CrossEncoder:
    global _nli_model
    if _nli_model is None:
        logger.info("Loading NLI groundedness model: %s", config.NLI_MODEL_NAME)
        _nli_model = CrossEncoder(config.NLI_MODEL_NAME)
    return _nli_model


def _softmax(scores: np.ndarray) -> np.ndarray:
    exp = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
    return exp / exp.sum(axis=-1, keepdims=True)


def _split_sentences(text: str) -> list[str]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    return sentences or [text.strip()]


def _check_nli_entailment(trace: dict, answer: str) -> dict:
    """Scored per (answer sentence, retrieved chunk) pair rather than one big blob
    against another: NLI cross-encoders are calibrated on short single-sentence
    pairs, and comparing a whole multi-sentence answer against a whole concatenated
    context collapses almost everything to "neutral" regardless of correctness —
    confirmed empirically (a correct answer scored 0.01 entailment as one big pair).
    For each answer sentence, take the best-supporting chunk (max); the answer's
    overall score is the *weakest*-supported claim (min over sentences).

    Known limitation (see config/guardrails.py / issue #4): generic NLI models
    under-score legitimate paraphrasing, so this strategy can false-refuse correct
    answers that summarize rather than closely quote their source.
    """
    threshold = config.NLI_ENTAILMENT_THRESHOLD
    retrieved = trace.get("retrieved", [])
    if not retrieved:
        return {
            "blocked": True,
            "reason": "no_retrieval",
            "message": NO_RETRIEVAL_MESSAGE,
            "threshold": threshold,
            "strategy": "nli_entailment",
        }

    contexts = [r["text"] for r in retrieved]
    sentences = _split_sentences(answer)

    model = _get_nli_model()
    pairs = [(ctx, sent) for sent in sentences for ctx in contexts]
    raw_scores = np.asarray(model.predict(pairs))
    probs = _softmax(raw_scores).reshape(len(sentences), len(contexts), 3)

    entailment = probs[:, :, 1]
    contradiction = probs[:, :, 0]

    overall_entailment = float(entailment.max(axis=1).min())
    overall_contradiction = float(contradiction.max(axis=1).max())

    logger.debug(
        "nli_entailment check: entailment=%.3f contradiction=%.3f (%d sentence(s) x %d chunk(s))",
        overall_entailment,
        overall_contradiction,
        len(sentences),
        len(contexts),
    )

    if overall_entailment < threshold:
        return {
            "blocked": True,
            "reason": "not_grounded",
            "message": NOT_GROUNDED_MESSAGE,
            "best_score": overall_entailment,
            "contradiction": overall_contradiction,
            "threshold": threshold,
            "strategy": "nli_entailment",
        }

    return {
        "blocked": False,
        "reason": None,
        "message": None,
        "best_score": overall_entailment,
        "contradiction": overall_contradiction,
        "threshold": threshold,
        "strategy": "nli_entailment",
    }


# ---- hhem: Vectara's purpose-built RAG factual-consistency model ----


def _get_hhem_model() -> CrossEncoder | None:
    global _hhem_model, _hhem_broken
    if _hhem_broken:
        return None
    if _hhem_model is None:
        try:
            logger.info("Loading HHEM groundedness model: %s", config.HHEM_MODEL_NAME)
            _hhem_model = CrossEncoder(config.HHEM_MODEL_NAME, trust_remote_code=True)
        except Exception:
            logger.exception(
                "Failed to load HHEM model %s — falling back to retrieval_threshold for this "
                "request. See config/guardrails.py for the known transformers-5.x incompatibility.",
                config.HHEM_MODEL_NAME,
            )
            _hhem_broken = True
            return None
    return _hhem_model


def _check_hhem(trace: dict, answer: str, domain: str = "nimbus") -> dict:
    model = _get_hhem_model()
    if model is None:
        verdict = _check_retrieval_threshold(trace, domain)
        verdict["strategy"] = "hhem_fallback_retrieval_threshold"
        return verdict

    threshold = config.HHEM_CONSISTENCY_THRESHOLD
    retrieved = trace.get("retrieved", [])
    if not retrieved:
        return {
            "blocked": True,
            "reason": "no_retrieval",
            "message": NO_RETRIEVAL_MESSAGE,
            "threshold": threshold,
            "strategy": "hhem",
        }

    contexts = [r["text"] for r in retrieved]
    sentences = _split_sentences(answer)
    pairs = [(ctx, sent) for sent in sentences for ctx in contexts]
    scores = np.asarray(model.predict(pairs)).reshape(len(sentences), len(contexts))
    overall_score = float(scores.max(axis=1).min())

    if overall_score < threshold:
        return {
            "blocked": True,
            "reason": "not_grounded",
            "message": NOT_GROUNDED_MESSAGE,
            "best_score": overall_score,
            "threshold": threshold,
            "strategy": "hhem",
        }

    return {
        "blocked": False,
        "reason": None,
        "message": None,
        "best_score": overall_score,
        "threshold": threshold,
        "strategy": "hhem",
    }
