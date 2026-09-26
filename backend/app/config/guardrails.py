"""Central switchboard for the guardrail strategy — nothing gets deleted when we try
a new approach, it just becomes another selectable option here. Swap strategies via
GUARDRAIL_STRATEGY without touching code.

Strategies:
  retrieval_threshold  Original approach. Cosine similarity of the *search query* against
                       retrieved chunks. Cheap, reliable, but only checks that something
                       relevant was found — never looks at whether the generated answer
                       is actually supported by it. Needs a per-domain threshold: Nimbus's
                       prose docs and the Resume Agent's short fragments score very
                       differently against the same embedding model (fragments as low as
                       ~0.15-0.25 even when clearly on-topic — confirmed empirically).
  nli_entailment       Generic SNLI/MultiNLI cross-encoder, scored per (answer sentence,
                       retrieved chunk) pair, weakest-supported-claim aggregation. Checks
                       the *answer* itself, but generic NLI models are calibrated for
                       strict logical entailment and under-score legitimate paraphrasing
                       — confirmed empirically (see issue #4), expect some false refusals
                       on answers that summarize rather than closely quote their source.
  hhem                 Vectara's Hughes Hallucination Evaluation Model — same CrossEncoder
                       interface, but fine-tuned specifically on summarization/factual-
                       consistency data (FEVER, VitaminC, PAWS) after NLI pretraining,
                       which is exactly the paraphrase-tolerance nli_entailment lacks.
                       Currently BROKEN in this environment: its custom HF remote code
                       (written against transformers 4.x) crashes on transformers 5.17
                       with `AttributeError: 'HHEMv2ForSequenceClassification' object has
                       no attribute 'all_tied_weights_keys'`. Selecting this strategy logs
                       the failure and falls back to retrieval_threshold rather than
                       crashing the app. Revisit by pinning an older transformers version
                       (risks breaking sentence-transformers/langgraph's own requirements)
                       or waiting for an updated checkpoint.
"""

import os

GUARDRAIL_STRATEGY = os.environ.get("GUARDRAIL_STRATEGY", "retrieval_threshold")

# retrieval_threshold — per-domain, see the docstring above for why they differ
RETRIEVAL_SIMILARITY_THRESHOLD_BY_DOMAIN = {
    "nimbus": float(os.environ.get("GUARDRAIL_SIMILARITY_THRESHOLD_NIMBUS", "0.3")),
    "resume": float(os.environ.get("GUARDRAIL_SIMILARITY_THRESHOLD_RESUME", "0.15")),
}
RETRIEVAL_SIMILARITY_THRESHOLD_DEFAULT = float(os.environ.get("GUARDRAIL_SIMILARITY_THRESHOLD", "0.3"))

# nli_entailment
NLI_MODEL_NAME = os.environ.get("GUARDRAIL_NLI_MODEL", "cross-encoder/nli-deberta-v3-xsmall")
NLI_ENTAILMENT_THRESHOLD = float(os.environ.get("GUARDRAIL_ENTAILMENT_THRESHOLD", "0.3"))

# hhem
HHEM_MODEL_NAME = os.environ.get("GUARDRAIL_HHEM_MODEL", "vectara/hallucination_evaluation_model")
HHEM_CONSISTENCY_THRESHOLD = float(os.environ.get("GUARDRAIL_HHEM_THRESHOLD", "0.5"))
