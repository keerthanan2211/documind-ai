import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PdfError(ValueError):
    """Raised when a file isn't a readable PDF or has no extractable text."""


def extract_pages(data: bytes, max_pages: int) -> list[str]:
    """Returns the text of each page (index 0 = page 1)."""
    if not data.startswith(b"%PDF"):
        raise PdfError("That file isn't a PDF")
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise PdfError("This PDF is password-protected. Remove the password and upload it again.")
        if len(reader.pages) > max_pages:
            raise PdfError(f"This PDF has {len(reader.pages)} pages; the limit is {max_pages}")
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
    except PdfReadError as exc:
        raise PdfError("This PDF is damaged or unreadable") from exc

    if not any(pages):
        raise PdfError("No text found. Scanned PDFs need OCR before they can be searched.")
    return pages
