"""HTTP helpers that validate redirects before urllib follows them."""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urljoin
from urllib.request import HTTPRedirectHandler, OpenerDirector, build_opener


class ValidatingRedirectHandler(HTTPRedirectHandler):
    """Reject redirect targets before a second network request is emitted."""

    def __init__(self, validator: Callable[[str], str]):
        super().__init__()
        self._validator = validator

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = self._validator(urljoin(req.full_url, newurl))
        return super().redirect_request(req, fp, code, msg, headers, target)


def build_validating_opener(validator: Callable[[str], str]) -> OpenerDirector:
    return build_opener(ValidatingRedirectHandler(validator))


__all__ = ["ValidatingRedirectHandler", "build_validating_opener"]
