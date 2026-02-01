import json
import logging
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request
from urllib.request import urlopen

from django.conf import settings

logger = logging.getLogger(__name__)


def verify_recaptcha_v3(token, action, remote_ip=None):
    """Verify a reCAPTCHA v3 token and return (is_valid, score)."""
    if settings.RECAPTCHA_V3_TESTING:
        return True, 1.0

    if not token:
        return False, 0.0

    if not settings.RECAPTCHA_V3_SECRET_KEY:
        logger.error("RECAPTCHA_V3_SECRET_KEY is not configured.")
        return False, 0.0

    payload = {
        "secret": settings.RECAPTCHA_V3_SECRET_KEY,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        request = Request(
            "https://www.google.com/recaptcha/api/siteverify",
            data=urlencode(payload).encode("utf-8"),
        )
        with urlopen(request, timeout=5) as response:  # noqa: S310
            result = json.loads(response.read().decode("utf-8"))
    except URLError:
        logger.exception("reCAPTCHA verification failed.")
        return False, 0.0

    success = bool(result.get("success"))
    score = float(result.get("score") or 0.0)
    response_action = result.get("action")

    return (
        success
        and response_action == action
        and score >= settings.RECAPTCHA_V3_SCORE_THRESHOLD,
        score,
    )
