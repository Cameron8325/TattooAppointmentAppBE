from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings

class JWTAuthFromCookies(JWTAuthentication):
    def authenticate(self, request):
        # Try reading token from Authorization header (default behavior)
        header_auth = super().authenticate(request)
        if header_auth:
            return header_auth

        # If no Authorization header, check cookies
        access_token = request.COOKIES.get(settings.SIMPLE_JWT.get("AUTH_COOKIE"))
        if access_token:
            validated_token = self.get_validated_token(access_token)
            return (self.get_user(validated_token), validated_token)

        return None  # No valid authentication found
