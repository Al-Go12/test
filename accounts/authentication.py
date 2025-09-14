from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # 1. Look for the access token in cookies
        access_token = request.COOKIES.get("access_token")

        if access_token is None:
            return None  # DRF will continue with other authenticators

        # 2. Validate the token using SimpleJWT’s built-in logic
        validated_token = self.get_validated_token(access_token)

        # 3. Return (user, token)
        return self.get_user(validated_token), validated_token
