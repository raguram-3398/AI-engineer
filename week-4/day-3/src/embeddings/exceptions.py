"""Typed exception hierarchy for Day 24.

Data and I/O problems raise these. Programmer errors (wrong shapes, empty
model name, too few texts) raise ValueError instead.
"""


class EmbeddingError(Exception):
    """Base class: catch this in main to report any expected failure."""


class ModelLoadError(EmbeddingError):
    """The model could not be loaded: download timeout, offline, bad id, bad weights."""


class DataFileError(EmbeddingError):
    """A data file is missing, is not valid JSON, or has the wrong shape."""
