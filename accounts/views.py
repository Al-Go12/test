
from rest_framework.response import Response
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from accounts.models import *
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model 
from django.contrib.auth import authenticate 
from twilio.rest import Client
from django.conf import settings
from .utils import get_tokens_for_user

User = get_user_model()






def normalize_mobile(mobile: str) -> str:
    # Remove spaces, dashes, accidental prefixes
    mobile = str(mobile).strip().replace(" ", "").replace("-", "")

    # Ensure it starts with +91
    if not mobile.startswith("+91"):
        mobile = "+91" + mobile.lstrip("0")  # remove leading 0 if present

    return mobile








class SendOtpView(APIView):
    def post(self, request):
        serializer = SendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mobile = normalize_mobile(serializer.validated_data['mobile'])

        # Invalidate previous OTPs for this number
        OTP.objects.filter(mobile=mobile, is_verified=False).delete()

        # Generate OTP
        otp_code = OTP.generate_otp()
        OTP.objects.create(mobile=mobile, code=otp_code)

        # ---- Twilio send ----
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                from_=settings.TWILIO_FROM,    # or messaging_service_sid=settings.TWILIO_MSG_SERVICE_SID
                to=mobile,                     # must be in E.164 format (e.g., +9198xxxxxxx)
                body=f"Your OTP is {otp_code}. It expires in 5 minutes."
            )
            msg = "OTP sent successfully"
        except Exception as e:
            # fallback: you can still debug via console
            print(f"Twilio send failed: {e}")
            msg = "OTP generated but failed to send SMS (check Twilio config)."
        
        # Debug log (only for dev) 
        # msg="OTP"
        print(f"DEBUG OTP for {mobile}: {otp_code}")

        return Response({"success": True, "message": msg}, status=status.HTTP_200_OK)


class VerifyOtpView(APIView):
    def post(self, request, *args, **kwargs):
        mobile = normalize_mobile(request.data.get("mobile"))
        otp = request.data.get("otp")

        if not mobile or not otp:
            return Response({"message": "Mobile and OTP required"}, status=400)

        otp_entry = OTP.objects.filter(mobile=mobile, is_verified=False).order_by("-created_at").first()
        if not otp_entry:
            return Response({"message": "No OTP found for this number"}, status=400)

        if otp_entry.is_expired():
            return Response({"message": "OTP expired"}, status=400)

        if otp_entry.code != otp:
            return Response({"message": "Invalid OTP"}, status=400)

        otp_entry.is_verified = True
        otp_entry.save()

        # ✅ Idempotent safe creation
        user, created = User.objects.get_or_create(
            phone_number=mobile,
            defaults={"is_phone_verified": True}
        )
        if not created:
            user.is_phone_verified = True
            user.save()

        tokens = get_tokens_for_user(user)

        return Response({
            "success": True,
            "message": "OTP verified successfully",
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "user": {
                "id": user.id,
                "phone_number": str(user.phone_number),
                "is_phone_verified": user.is_phone_verified,
            },
        }, status=200)

class AdminLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        raw_username = request.data.get("username")
        password = request.data.get("password")

        if not raw_username or not password:
            return Response({"detail": "Username and password required"}, status=400)

        # Normalize: ensure +91
        username = raw_username
        if not raw_username.startswith("+91"):
            username = "+91" + raw_username

        user = authenticate(request, username=username, password=password)

        if not user:
            return Response({"detail": "Invalid credentials"}, status=401)

        # 🚨 Strict admin validation
        if not (user.is_staff or user.is_superuser):
            return Response({"detail": "Access denied. Admins only."}, status=403)

        tokens = get_tokens_for_user(user)
        return Response({
            "success": True,
            "message": "Admin login successful",
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "user": {
                "id": user.id,
                "phone_number": str(user.phone_number),
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }
        }, status=200)

