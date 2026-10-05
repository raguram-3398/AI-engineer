"""Load PDF, text, and web sources into LangChain Documents.

Side effects live here (disk, network). Every Document leaves this module with
the same metadata keys — source, page, doc_type — so downstream code never
has to know where a chunk came from to cite it.
"""

import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from chunking.exceptions import EmptyDocumentError, FetchError, LoaderError
from chunking.models import (
    DEFAULT_TIMEOUT,
    DOC_TYPE_PDF,
    DOC_TYPE_TEXT,
    DOC_TYPE_WEB,
    USER_AGENT,
    EvalQuery,
)

NON_CONTENT_TAGS: tuple[str, ...] = (
    "script",
    "style",
    "nav",
    "header",
    "footer",
    "noscript",
)


def _require_file(path: Path) -> None:
    """Raise LoaderError if path is not an existing file."""
    if not path.is_file():
        raise LoaderError(f"File not found: {path}")


def load_pdf(path: Path) -> list[Document]:
    """Load a PDF as one Document per page that has extractable text.

    Pages are 1-based in metadata because this number is shown to users in
    citations ("page 4"), and users count from 1. Pages with no text (blank,
    or image-only) are dropped; if every page is empty the PDF is probably
    scanned and needs OCR (Week 5), so EmptyDocumentError is raised.
    """
    _require_file(path)
    try:
        reader = PdfReader(path)
        page_texts = [page.extract_text() or "" for page in reader.pages]
    except PdfReadError as e:
        raise LoaderError(f"Could not parse PDF {path}: {e}") from e

    pages = [
        Document(
            page_content=text,
            metadata={
                "source": str(path),
                "page": page_number,
                "doc_type": DOC_TYPE_PDF,
            },
        )
        for page_number, text in enumerate(page_texts, start=1)
        if text.strip()
    ]
    if not pages:
        raise EmptyDocumentError(
            f"No extractable text in {path} (scanned PDF? needs OCR)"
        )
    return pages


def load_text(path: Path) -> list[Document]:
    """Load a UTF-8 text file as a single Document with page 1."""
    _require_file(path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise LoaderError(f"{path} is not valid UTF-8: {e}") from e
    if not text.strip():
        raise EmptyDocumentError(f"Text file is empty: {path}")
    return [
        Document(
            page_content=text,
            metadata={"source": str(path), "page": 1, "doc_type": DOC_TYPE_TEXT},
        )
    ]


def extract_visible_text(html: str) -> str:
    """Strip scripts, styles, and page chrome from HTML; return non-blank lines."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(NON_CONTENT_TAGS):
        tag.decompose()
    lines = (line.strip() for line in soup.get_text(separator="\n").splitlines())
    return "\n".join(line for line in lines if line)


def load_web(url: str, timeout: float = DEFAULT_TIMEOUT) -> list[Document]:
    """Fetch a web page and return its visible text as a single Document.

    Timeout is caught before the broader RequestException on purpose: a timeout
    is retryable, a 404 is not, and callers may want to treat them differently.
    """
    try:
        response = requests.get(
            url, timeout=timeout, headers={"User-Agent": USER_AGENT}
        )
        response.raise_for_status()
    except requests.Timeout as e:
        raise FetchError(f"Timed out after {timeout}s: {url}") from e
    except requests.RequestException as e:
        raise FetchError(f"Request failed for {url}: {e}") from e

    text = extract_visible_text(response.text)
    if not text:
        raise EmptyDocumentError(f"No visible text at {url}")
    return [
        Document(
            page_content=text,
            metadata={"source": url, "page": 1, "doc_type": DOC_TYPE_WEB},
        )
    ]


def load_eval_queries(path: Path) -> list[EvalQuery]:
    """Load hand-written eval queries.

    Expected JSON: [{"question": ..., "expected_substring": ...}, ...]
    """
    _require_file(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        queries = [
            EvalQuery(item["question"], item["expected_substring"]) for item in raw
        ]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise LoaderError(f"Malformed eval queries file {path}: {e}") from e
    if not queries:
        raise EmptyDocumentError(f"No eval queries in {path}")
    return queries
