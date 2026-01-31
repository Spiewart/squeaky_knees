"""Security headers middleware."""


class SecurityHeadersMiddleware:
    """Add additional security headers to responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Prevent MIME type sniffing
        response["X-Content-Type-Options"] = "nosniff"

        # Enable XSS filter in older browsers
        response["X-XSS-Protection"] = "1; mode=block"

        # Prevent clickjacking (defense-in-depth; also set in SecurityMiddleware)
        if "X-Frame-Options" not in response:
            response["X-Frame-Options"] = "DENY"

        # Enforce HTTPS in production (set in production settings)
        # response["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
