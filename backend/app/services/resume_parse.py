import io
import logging

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ..config import resume as resume_config

logger = logging.getLogger(__name__)

DEFAULT_MAX_PAGES = resume_config.MAX_PAGES
DEFAULT_EXTRACTION_MODE = resume_config.PDF_EXTRACTION_MODE
DEFAULT_PAGE_SEPARATOR = resume_config.PAGE_SEPARATOR


class ResumeParseError(Exception):
    """Raised when a PDF can't be opened or yields no usable text."""


def extract_text_from_pdf(
    data: bytes,
    *,
    max_pages: int = DEFAULT_MAX_PAGES,
    extraction_mode: str = DEFAULT_EXTRACTION_MODE,
    page_separator: str = DEFAULT_PAGE_SEPARATOR,
) -> str:
    logger.info("Parsing uploaded PDF (%d bytes, max_pages=%d, mode=%s)", len(data), max_pages, extraction_mode)

    try:
        reader = PdfReader(io.BytesIO(data))
    except PdfReadError:
        logger.exception("Failed to open PDF — file may be corrupted or not a valid PDF")
        raise ResumeParseError("Could not open this file as a PDF.") from None

    total_pages = len(reader.pages)
    logger.info("PDF opened successfully: %d page(s)", total_pages)

    if total_pages > max_pages:
        logger.warning("PDF has %d pages, exceeding max_pages=%d — only the first %d will be read", total_pages, max_pages, max_pages)

    pages_text = []
    empty_pages = 0
    for i, page in enumerate(reader.pages[:max_pages]):
        try:
            text = page.extract_text(extraction_mode=extraction_mode) or ""
        except Exception:
            logger.exception("Failed to extract text from page %d — skipping this page", i)
            text = ""

        if not text.strip():
            empty_pages += 1
            logger.warning("Page %d produced no extractable text (possibly a scanned image without OCR)", i)
        else:
            logger.debug("Page %d: extracted %d characters", i, len(text))

        pages_text.append(text)

    full_text = page_separator.join(pages_text)
    pages_read = min(total_pages, max_pages)
    logger.info(
        "PDF parsing complete: %d/%d page(s) had extractable text, %d total characters",
        pages_read - empty_pages,
        pages_read,
        len(full_text),
    )

    if not full_text.strip():
        logger.error("PDF yielded no extractable text at all (%d pages read)", pages_read)
        raise ResumeParseError(
            "Couldn't extract any text from this PDF — it may be a scanned image with no embedded text. "
            "Try the paste-as-text option instead."
        )

    return full_text
