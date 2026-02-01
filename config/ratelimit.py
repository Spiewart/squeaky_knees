"""Simple rate limiting utilities using Django cache."""

from django.core.cache import cache
from django.http import HttpRequest


def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP address from request.

    Respects X-Forwarded-For header for proxied requests.
    """
    if request.headers.get("x-forwarded-for"):
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def get_identifier_for_user_action(request: HttpRequest, action: str) -> str:
    """Get cache key identifier for a user's action."""
    if hasattr(request, "user") and request.user and request.user.is_authenticated:
        return f"ratelimit:{action}:user:{request.user.id}"
    ip = get_client_ip(request)
    return f"ratelimit:{action}:ip:{ip}"


def is_rate_limited(
    request: HttpRequest,
    action: str,
    max_attempts: int,
    window_seconds: int,
) -> bool:
    """Check if a request exceeds rate limit.

    Args:
        request: HTTP request object
        action: Action identifier (e.g., 'comment_add', 'user_signup')
        max_attempts: Maximum attempts allowed in the window
        window_seconds: Time window in seconds

    Returns:
        True if rate limited, False otherwise
    """
    key = get_identifier_for_user_action(request, action)
    attempt_count = cache.get(key, 0)

    if attempt_count >= max_attempts:
        return True

    # Increment counter and set expiration
    cache.set(key, attempt_count + 1, window_seconds)
    return False


def get_rate_limit_info(request: HttpRequest, action: str, max_attempts: int) -> dict:
    """Get remaining attempts and reset time for display purposes.

    Args:
        request: HTTP request object
        action: Action identifier
        max_attempts: Maximum attempts allowed

    Returns:
        Dict with 'remaining' and 'reset_in_seconds' keys
    """
    key = get_identifier_for_user_action(request, action)
    attempt_count = cache.get(key, 0)
    ttl = cache.ttl(key) if hasattr(cache, "ttl") else None

    return {
        "remaining": max(0, max_attempts - attempt_count),
        "reset_in_seconds": ttl or 0,
    }
