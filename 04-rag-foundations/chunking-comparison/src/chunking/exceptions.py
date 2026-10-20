"""Typed exception hierarchy for document loading.

Callers catch LoaderError to handle every loading failure with one handler,
or a specific subclass when the response should differ (e.g. skip a web page
that timed out, but abort on a missing PDF).
"""


class LoaderError(Exception):
    """Base class for every failure while loading a document."""


class EmptyDocumentError(LoaderError):
    """The source exists but contains no extractable text."""


class FetchError(LoaderError):
    """A network fetch failed: timeout, connection error, or bad HTTP status."""
