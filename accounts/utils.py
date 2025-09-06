from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    if user.is_staff or user.is_superuser:
        # Admin: long refresh
        refresh.set_exp(lifetime=timedelta(days=30))
    else:
        # Client: short refresh
        refresh.set_exp(lifetime=timedelta(hours=6))

    # Short-lived access token
    refresh.access_token.set_exp(timedelta(minutes=10))

    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    }
