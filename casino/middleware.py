"""
Content Security Policy middleware for Le Casino.

This middleware adds CSP headers to all responses to improve security by
restricting the sources from which scripts, styles, and other resources
can be loaded.
"""


class CSPMiddleware:
    """
    Middleware that adds Content-Security-Policy headers to responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Build CSP directives
        csp_directives = [
            # Default to self for anything not explicitly specified
            "default-src 'self'",
            # Scripts: only self (no inline scripts needed)
            "script-src 'self'",
            # Styles: self + Google Fonts
            "style-src 'self' https://fonts.googleapis.com",
            # Fonts: self + Google Fonts CDN
            "font-src 'self' https://fonts.gstatic.com",
            # Images: self + data URIs (for inline images/base64)
            "img-src 'self' data:",
            # WebSocket connections for roulette
            "connect-src 'self' ws: wss:",
            # Frames: none (no iframes allowed)
            "frame-ancestors 'none'",
            # Form submissions only to self
            "form-action 'self'",
            # Base URI restricted to self
            "base-uri 'self'",
        ]

        csp_header = "; ".join(csp_directives)
        response["Content-Security-Policy"] = csp_header

        return response
