"""Resume PDF parsing settings."""

import os

MAX_PAGES = int(os.environ.get("RESUME_MAX_PAGES", "20"))
PDF_EXTRACTION_MODE = os.environ.get("RESUME_PDF_EXTRACTION_MODE", "plain")  # "plain" or "layout"
PAGE_SEPARATOR = "\n\n"
