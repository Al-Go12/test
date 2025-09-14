
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
from django.contrib.auth.hashers import make_password  
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

import secrets
from django.core.cache import cache 

User = get_user_model()
import requests



def send_otp_fast2sms(phone_number,otp):
    """
    Send OTP SMS via OTP route (DLT-compliant) using Fast2SMS API.
    :param otp: The OTP string or int to send
    :param phone_number: 10-digit mobile number as a string
    :returns: Response from Fast2SMS API (JSON dict)
    """
    url = "https://www.fast2sms.com/dev/bulkV2"
   

    params = {
        "authorization": settings.FAST2SMS_API_KEY,
        "variables_values": str(otp),
        "route": "otp",
        "numbers": phone_number
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()  # Successfully sent
    except Exception as e:
        print(f"Fast2SMS send_otp failed: {e}")
        return None



def normalize_mobile(mobile: str) -> str:
    # Remove spaces, dashes, accidental prefixes
    mobile = str(mobile).strip().replace(" ", "").replace("-", "")

    # Ensure it starts with +91
    if not mobile.startswith("+91"):
        mobile = "+91" + mobile.lstrip("0")  # remove leading 0 if present

    return mobile




class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        # Get refresh token from cookie instead of request body
        request = self.context["request"]
        refresh = request.COOKIES.get("refresh_token")

        if not refresh:
            raise self.fail("no_refresh")

        attrs["refresh"] = refresh
        return super().validate(attrs)


class CookieTokenRefreshView(TokenRefreshView):
    serializer_class = CookieTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail": "Refresh token invalid or expired"}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = serializer.validated_data["access"]

        # Create response and set new access token in HttpOnly cookie
        response = Response({"success": True}, status=status.HTTP_200_OK)
        response.set_cookie(
            "access_token",
            access_token,
            httponly=True,
              secure=False, 
            samesite="Lax",
            max_age=60 * 5,  # match your access token lifetime
        )
        return response








class SendOtpView(APIView): 
    authentication_classes = []   
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = SendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mobile = normalize_mobile(serializer.validated_data['mobile'])

        # Invalidate previous OTPs for this number
        OTP.objects.filter(mobile=mobile, is_verified=False).delete()

        # Generate OTP
        otp_code = OTP.generate_otp()
        OTP.objects.create(mobile=mobile, code=otp_code)

        send_otp_fast2sms(mobile,otp_code)
        
        # Debug log (only for dev) 
        msg="OTP"
        print(f"DEBUG OTP for {mobile}: {otp_code}")

        return Response({"success": True, "message": msg}, status=status.HTTP_200_OK)

class SignupApiView(APIView): 
    authentication_classes = []   
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        mobile = normalize_mobile(request.data.get("phone_number"))    
        print(mobile)
        otp = request.data.get("otp")
        password = request.data.get("password")  # ✅ password from request
        
        if not mobile or not otp or not password:
            return Response({"message": "Mobile, OTP and Password required"}, status=400)

        otp_entry = OTP.objects.filter(
            mobile=mobile, is_verified=False
        ).order_by("-created_at").first() 
        print(otp_entry)
        if not otp_entry:
            return Response({"message": "No OTP found for this number"}, status=400)

        if otp_entry.is_expired():
            return Response({"message": "OTP expired"}, status=400)

        if otp_entry.code != otp:
            return Response({"message": "Invalid OTP"}, status=400)

        otp_entry.is_verified = True
        otp_entry.save()

        # ✅ Create user with provided password
        user, created = User.objects.get_or_create(
            phone_number=mobile,
            defaults={
                "is_phone_verified": True,
                "password": make_password(password),  # hash before saving
            },
        )
        if not created:
            # If user exists, just update phone verification
            user.is_phone_verified = True
            # Optional: allow updating password if passed
            user.set_password(password)
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

class UserDetailView(APIView):
    """
    API endpoint to return authenticated user details.
    Accessible only with a valid authentication token.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        data = {
            "id": user.id,
            "phone_number": str(user.phone_number) if user.phone_number else None,
            "is_phone_verified": getattr(user, "is_phone_verified", False),
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        }
        return Response(data)  



class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]  # anyone can call

    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response



    
class UserLoginView(APIView): 
    authentication_classes = []   
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        phone_number = normalize_mobile(request.data.get("mobile"))
        password = request.data.get("password")

        if not phone_number or not password:
            return Response({"message": "Phone number and password required"}, status=400)

        user = authenticate(request, username=phone_number, password=password)

        if user is None:
            return Response({"message": "Invalid phone number or password"}, status=401)

        if not user.is_active:
            return Response({"message": "User account is inactive"}, status=403)

        # ✅ 1. Get tokens
        tokens = get_tokens_for_user(user)

        # ✅ 2. Create a response object
        response = Response()

        # ✅ 3. Set tokens as HttpOnly cookies
        response.set_cookie(  

            
            key='access_token',
            value=tokens['access'],
           httponly=True,
              secure=False, 
            samesite="Lax",             # Or 'Strict'
        )
        response.set_cookie(
            key='refresh_token',
            value=tokens['refresh'],
            httponly=True,
              secure=False, 
            samesite="Lax",
        )

        # ✅ 4. Set the response data (without tokens)
        response.data = {
            "success": True,
            "message": "User login successful",
            "user": {
                "id": user.id,
                "phone_number": str(user.phone_number),
                "is_phone_verified": user.is_phone_verified,
            }
        }
        response.status_code = status.HTTP_200_OK

        return response


class AdminLoginView(APIView):
    authentication_classes = []  
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        raw_username = request.data.get("username")
        password = request.data.get("password")

        if not raw_username or not password:
            return Response({"detail": "Username and password required"}, status=400)

        username = raw_username
        if not raw_username.startswith("+91"):
            username = "+91" + raw_username

        user = authenticate(request, username=username, password=password)

        if not user or not (user.is_staff or user.is_superuser):
            return Response({"detail": "Invalid credentials or access denied"}, status=401)

        # ✅ 1. Get tokens
        tokens = get_tokens_for_user(user)

        # ✅ 2. Create response and set cookies
        response = Response()
        response.set_cookie(
            key='access_token',
            value=tokens['access'],
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )
        response.set_cookie(
            key='refresh_token',
            value=tokens['refresh'],
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )

        # ✅ 3. Set response data
        response.data = {
            "success": True,
            "message": "Admin login successful",
            "user": {
                "id": user.id,
                "phone_number": str(user.phone_number),
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }
        }
        response.status_code = status.HTTP_200_OK

        return response


 # for temporary storage  


class ForgotPasswordRequestView(APIView): 
    authentication_classes = []  
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        phone_number = normalize_mobile(request.data.get("phone_number"))
        print(phone_number)
        if not phone_number:
            return Response({"message": "Phone number required"}, status=400)

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            # Don't reveal existence of user
            return Response({"message": "If this number is registered, you will receive an OTP"}, status=200)

        # Generate and save OTP
        otp = OTP.generate_otp()
        OTP.objects.create(mobile=phone_number, code=otp)

        send_otp_fast2sms(phone_number,otp)
        print(f"DEBUG: OTP for {phone_number} is {otp}")

        return Response({"message": "If this number is registered, you will receive an OTP"}, status=200)


class ForgotPasswordVerifyOTPView(APIView): 
    authentication_classes = []  
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        phone_number = normalize_mobile(request.data.get("phone_number"))
        otp = request.data.get("otp")
        print(otp)
        if not phone_number or not otp:
            return Response({"message": "Phone number and OTP required"}, status=400)

        otp_entry = OTP.objects.filter(
            mobile=phone_number, is_verified=False
        ).order_by("-created_at").first()

        if not otp_entry or otp_entry.is_expired() or otp_entry.code != otp:
            return Response({"message": "Invalid or expired OTP"}, status=400)

        otp_entry.is_verified = True
        otp_entry.save()

        # ✅ Generate reset token (10 min expiry)
        reset_token = secrets.token_urlsafe(32)
        cache.set(f"reset:{phone_number}", reset_token, timeout=600)  

        return Response({
            "success": True,
            "message": "OTP verified successfully. Use reset token to reset password.",
            "reset_token": reset_token
        }, status=200)


class ForgotPasswordResetView(APIView): 
    authentication_classes = []  
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        phone_number = normalize_mobile(request.data.get("phone_number"))
        reset_token = request.data.get("reset_token")
        new_password = request.data.get("new_password")
        
        print(reset_token)
        if not phone_number or not reset_token or not new_password:
            return Response({"message": "Phone number, reset token and new password required"}, status=400)

        # Validate token
        cached_token = cache.get(f"reset:{phone_number}") 
        print(cached_token)
        if not cached_token or cached_token != reset_token:
            return Response({"message": "Invalid or expired reset token"}, status=400)

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=404)

        user.set_password(new_password)
        user.save()

        # Invalidate token
        cache.delete(f"reset:{phone_number}")

        return Response({"success": True, "message": "Password reset successful"}, status=200)
