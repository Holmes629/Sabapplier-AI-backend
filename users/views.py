import os
import json
from datetime import datetime, timedelta

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.core.cache import cache
from django.conf import settings
from django.http import JsonResponse

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from google.oauth2 import id_token
from google.auth.transport import requests

from .serializers import (
    UserSerializer,
    TokenSerializer,
    UserRegistrationSerializer,
    DataShareSerializer,
    ShareNotificationSerializer,
)
from .models import user, Token, DataShare, ShareNotification, ContactUsRequest
from .apis.ocr_endpoint import get_ocr_data
from .apis.fetch_autofill_data import get_autofill_data
from .apis.learning_api import process_learned_data_for_display, process_with_gemini
from .dropbox_storage import DropboxStorage  # import your custom storage
import uuid
import jwt


class users_view(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = user.objects.all()


# Define drop box storage
dropbox_storage = DropboxStorage()

User = get_user_model()


######################  NEW: EMAIL OTP ENDPOINTS ####################


@api_view(["POST"])
@permission_classes([AllowAny])
def send_otp(request):
    print('Inside send_otp function')
    email = request.data.get("email", "").strip().lower()  # normalize

    if not email:
        return Response(
            {"detail": "Email is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if user.objects.filter(email=email).exists():
        return Response(
            {"detail": "Email is already registered."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    otp = get_random_string(length=6, allowed_chars="0123456789")
    cache.set(f"otp_{email}", otp, timeout=300)

    send_mail(
        subject="Your OTP Code",
        message=f"Your OTP code for Sabapplier AI is {otp}",
        from_email="noreply@sabapplier.com",
        recipient_list=[email],
        fail_silently=False,
    )
    return Response({"detail": "OTP sent."}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    print('Inside verify_otp function')
    email = request.data.get("email")
    otp = request.data.get("otp")
    if not (email and otp):
        return Response(
            {"detail": "Email and OTP are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    real_otp = cache.get(f"otp_{email}")
    if real_otp == otp:
        cache.delete(f"otp_{email}")
        return Response(
            {"detail": "Email verified."}, status=status.HTTP_200_OK
        )

    return Response(
        {"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST
    )


# Forgot Password: Send OTP to registered email for password reset
@api_view(["POST"])
@permission_classes([AllowAny])
def send_forgot_password_otp(request):
    print('Inside send_forgot_password_otp function')
    email = request.data.get("email", "").strip().lower()

    if not email:
        return Response(
            {"detail": "Email is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if user exists
    if not user.objects.filter(email=email).exists():
        return Response(
            {"detail": "No account found with this email address."},
            status=status.HTTP_404_NOT_FOUND,
        )

    otp = get_random_string(length=6, allowed_chars="0123456789")
    cache.set(f"reset_otp_{email}", otp, timeout=300)  # 5 minutes

    send_mail(
        subject="Password Reset OTP - Sabapplier AI",
        message=f"Your password reset OTP for Sabapplier AI is {otp}. This OTP is valid for 5 minutes.",
        from_email="noreply@sabapplier.com",
        recipient_list=[email],
        fail_silently=False,
    )
    return Response(
        {"detail": "Password reset OTP sent to your email."},
        status=status.HTTP_200_OK,
    )


# Forgot Password: Verify OTP and reset password
@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    print('Inside reset_password function')
    email = request.data.get("email", "").strip().lower()
    otp = request.data.get("otp")
    new_password = request.data.get("password")

    if not all([email, otp, new_password]):
        return Response(
            {"detail": "Email, OTP, and new password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Verify OTP
    real_otp = cache.get(f"reset_otp_{email}")
    if real_otp != otp:
        return Response(
            {"detail": "Invalid or expired OTP."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Update password
    try:
        usr = user.objects.get(email=email)
        usr.password = new_password
        usr.save()

        # Delete the OTP after successful password reset
        cache.delete(f"reset_otp_{email}")

        return Response(
            {"success": True, "message": "Password reset successfully."},
            status=status.HTTP_200_OK,
        )
    except user.DoesNotExist:
        return Response(
            {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
        )


# Google OAuth signup
@api_view(["POST"])
@permission_classes([AllowAny])
def google_signup(request):
    print('Inside google_signup function')
    try:
        credential = request.data.get("credential")
        if not credential:
            return Response(
                {
                    "success": False,
                    "message": "Google credential is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Verify the Google credential
        GOOGLE_CLIENT_ID = getattr(settings, "GOOGLE_CLIENT_ID", None)
        if not GOOGLE_CLIENT_ID:
            return Response(
                {
                    "success": False,
                    "message": "Google OAuth not configured.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        idinfo = id_token.verify_oauth2_token(
            credential, requests.Request(), GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")
        name = idinfo.get("name", "")
        given_name = idinfo.get("given_name", "")
        family_name = idinfo.get("family_name", "")
        picture = idinfo.get("picture", "")
        locale = idinfo.get("locale", "")
        if not name and (given_name or family_name):
            name = f"{given_name} {family_name}".strip()
        if not email:
            return Response(
                {
                    "success": False,
                    "message": "Unable to get email from Google account.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            existing_user = user.objects.get(email=email)
            updated = False
            if not existing_user.fullName and name:
                existing_user.fullName = name
                updated = True
            if picture and not existing_user.google_profile_picture:
                existing_user.google_profile_picture = picture
                updated = True
            if updated:
                existing_user.save()
            # For existing users, only require fullName to be present
            # Other fields (dateofbirth, correspondenceAddress, phone_number) are optional
            # This allows existing users to access the app without forcing profile completion
            profile_complete = bool(existing_user.fullName)
            # --- JWT Token Generation ---
            from datetime import datetime, timedelta
            import jwt
            payload = {
                'user_id': existing_user.id,
                'email': existing_user.email,
                'exp': (datetime.utcnow() + timedelta(days=7)).timestamp(),
                'iat': datetime.utcnow().timestamp(),
            }
            secret = getattr(settings, 'SECRET_KEY', 'sabapplier-secret')
            token = jwt.encode(payload, secret, algorithm='HS256')
            user_data = UserSerializer(existing_user).data
            user_data['name'] = user_data.get('fullName', existing_user.fullName or existing_user.email)
            user_data['fullName'] = user_data.get('fullName', existing_user.fullName or existing_user.email)
            return Response(
                {
                    "success": True,
                    "user": user_data,
                    "token": token,
                    "needsProfileCompletion": not profile_complete,
                    "message": "Login successful",
                    "googleData": {
                        "name": name,
                        "email": email,
                        "picture": picture,
                        "given_name": given_name,
                        "family_name": family_name,
                        "locale": locale
                    }
                },
                status=status.HTTP_200_OK,
            )
        except user.DoesNotExist:
            import uuid
            referral_code = str(uuid.uuid4())[:8]
            while user.objects.filter(referral_code=referral_code).exists():
                referral_code = str(uuid.uuid4())[:8]
            referred_by = request.data.get('referred_by')
            usr = user.objects.create(
                email=email,
                fullName=name,
                google_profile_picture=picture,
                password="",
                referral_code=referral_code,
                referred_by=referred_by,
            )
            # Always enable website access for all users (waitlist disabled)
            # usr.has_website_access = True; # COMMENTED OUT: Waitlist logic is disabled as per request
            # usr.save(update_fields=["has_website_access"]); # COMMENTED OUT: Waitlist logic is disabled as per request
            try:
                from .models import WebsiteAccess
                website_access, created = WebsiteAccess.objects.get_or_create(
                    user=usr,
                    defaults={
                        'is_enabled': True,  # Always enabled
                        'notes': "User registered via Google OAuth (waitlist bypassed)"
                    }
                )
            except Exception as e:
                print('WebsiteAccess creation error:', e)
            # --- JWT Token Generation for new user ---
            from datetime import datetime, timedelta
            import jwt
            payload = {
                'user_id': usr.id,
                'email': usr.email,
                'exp': (datetime.utcnow() + timedelta(days=7)).timestamp(),
                'iat': datetime.utcnow().timestamp(),
            }
            secret = getattr(settings, 'SECRET_KEY', 'sabapplier-secret')
            token = jwt.encode(payload, secret, algorithm='HS256')
            user_data = UserSerializer(usr).data
            user_data['name'] = user_data.get('fullName', usr.fullName or usr.email)
            user_data['fullName'] = user_data.get('fullName', usr.fullName or usr.email)
            return Response(
                {
                    "success": True,
                    "user": user_data,
                    "token": token,
                    "needsProfileCompletion": True,
                    "message": "Please complete your profile",
                    "googleData": {
                        "name": name,
                        "email": email,
                        "picture": picture,
                        "given_name": given_name,
                        "family_name": family_name,
                        "locale": locale
                    }
                },
                status=status.HTTP_200_OK,
            )
    except Exception as e:
        return Response({"success": False, "message": f"Google signup failed: {str(e)}"}, status=400)


######################  API End Points for Website UI ####################


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    print('Inside register function')
    # Ignore extra fields and only process email and password (and confirmPassword if present)
    allowed_fields = {"email", "password", "confirmPassword"}
    data = {k: v for k, v in request.data.items() if k in allowed_fields}
    if (
        "confirmPassword" in data
        and data["password"] != data["confirmPassword"]
    ):
        return Response(
            {"success": False, "message": "Passwords do not match."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        user_instance = serializer.save()
        
        # Count total users and enable access for first 500 only
        # user_count = user.objects.count();
        # is_enabled = user_count <= 500;
        # user_instance.has_website_access = is_enabled;
        # user_instance.save(update_fields=["has_website_access"]);
        # Always enable website access for all users (waitlist disabled)
        user_instance.has_website_access = True;
        user_instance.save(update_fields=["has_website_access"]);

        try:
            # Create WebsiteAccess entry for the new user (disabled by default)
            from .models import WebsiteAccess
            website_access, created = WebsiteAccess.objects.get_or_create(
                user=user_instance,
                # defaults={
                #     'is_enabled': is_enabled,  # Default disabled - admin needs to enable
                #     'notes': "User registered and added to waitlist"
                # }
                defaults={
                    'is_enabled': True,  # Always enabled
                    'notes': "User registered (waitlist bypassed)"
                }
            )
            print(f"WebsiteAccess {'created' if created else 'already exists'} for {user_instance.email}")
        except Exception as e:
            print(f"Error creating WebsiteAccess for {user_instance.email}: {e}")
            # Continue anyway - we can create it later via management command
        
        return Response(
            {
                "success": True,
                "message": "You are now registered and have access! (waitlist bypassed)",
            },
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def update_data(request):
    print('Inside update_data function')
    try:
        userData = request.data.copy()
        
        # In update_data, map 'first_name', 'middle_name', 'last_name' from frontend to backend
        if 'first_name' in userData:
            userData['first_name'] = userData.pop('first_name')
        if 'middle_name' in userData:
            userData['middle_name'] = userData.pop('middle_name')
        if 'last_name' in userData:
            userData['last_name'] = userData.pop('last_name')
        if 'fullname' in userData:
            userData['fullName'] = userData.pop('fullname')
            
        usr = user.objects.filter(email=userData.get("email", "")).first()
        if not usr:
            return Response(
                {"success": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if "password" in userData:
            userData.pop("password")
        # Initialize documents and document_texts if not already set
        if usr.document_urls is None:
            usr.document_urls = {}
        if usr.document_texts is None:
            usr.document_texts = {}

        # Handle file uploads
        for field_name, uploaded_file in request.FILES.items():
            
            # Ensure field_name ends with _file_url for consistency
            if not field_name.endswith('_file_url'):
                field_name = field_name + '_file_url'
            
            ext = uploaded_file.name.split('.')[-1]
            base_folder = f"{usr.email.split('@')[0]}"
            # Create clean file name for Dropbox storage
            clean_field_name = field_name.replace('_file_url', '')
            file_name = f"{base_folder}_{clean_field_name}"
            file_path = os.path.join(base_folder, file_name + "."+ ext)

            try:
                # Save to Dropbox
                saved_path = dropbox_storage.save(file_path, uploaded_file)
                file_url = dropbox_storage.url(saved_path)

                # Store in documents with the correct field name that frontend expects
                usr.document_urls[field_name] = file_url

                # Extract and store OCR text
                try:
                    ocr_text = get_ocr_data(uploaded_file)
                    text_field_name = field_name.replace('_file_url', '_text_data')
                    usr.document_texts[text_field_name] = ocr_text
                except Exception as ocr_error:
                    # Store empty text if OCR fails
                    text_field_name = field_name.replace('_file_url', '_text_data')
                    usr.document_texts[text_field_name] = ""
                
            except Exception as upload_error:
                return Response(
                    {"success": False, "message": f"File upload failed: {str(upload_error)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            
            # Remove file field from userData to avoid serializer issues
            if field_name in userData:
                userData.pop(field_name)

        # Set referred_by and credit inviter if provided and not already set
        referred_by = userData.get('referred_by')
        if referred_by and not usr.referred_by:
            usr.referred_by = referred_by
            inviter = user.objects.filter(referral_code=referred_by).first()
            if inviter:
                inviter.successful_referrals += 1
                inviter.save()

        # Save user instance with updated documents
        usr.save()
        serializer = UserSerializer(usr, data=userData, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Return updated user data
            updated_user_data = UserSerializer(usr).data
            return Response(
                {
                    "success": True, 
                    "message": "Profile updated successfully.",
                    "user_data": updated_user_data
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as err:
        return Response(
            {
                "success": False,
                "message": "An error occurred while updating the data.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def delete_data(request):
    print('Inside delete_data function')
    try:
        userData = request.data.copy()
        usr = user.objects.filter(email=userData.get("email", "")).first()
        field = request.data.get("field")

        if not field:
            return Response(
                {"error": "Field name required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if field in usr.document_urls:
            del usr.document_urls[field]
            del usr.document_texts[field.replace("_file_url", "_text_data")]
            usr.save()
            return Response(
                {"success": True, "message": f"{field} deleted."},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Invalid field."}, status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response(
            {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    print('Inside login_view function')
    is_google_login = request.data.get("isGoogleLogin", False)
    if is_google_login:
        credential = request.data.get("credential")
        if not credential:
            return Response({"success": False, "message": "Google credential is required."}, status=400)
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests
            import uuid
            GOOGLE_CLIENT_ID = getattr(settings, "GOOGLE_CLIENT_ID", None)
            idinfo = id_token.verify_oauth2_token(credential, requests.Request(), GOOGLE_CLIENT_ID)
            email = idinfo.get("email")
            name = idinfo.get("name", "")
            picture = idinfo.get("picture", "")
            if not email:
                return Response({"success": False, "message": "Unable to get email from Google account."}, status=400)
            try:
                usr = user.objects.get(email=email)
                # Update Google profile picture if available
                updated = False
                if picture and not usr.google_profile_picture:
                    usr.google_profile_picture = picture
                    updated = True
                if not usr.fullName and name:
                    usr.fullName = name
                    updated = True
                if updated:
                    usr.save()
            except user.DoesNotExist:
                # Create new user with Google info and referral code
                referral_code = str(uuid.uuid4())[:8]
                while user.objects.filter(referral_code=referral_code).exists():
                    referral_code = str(uuid.uuid4())[:8]
                usr = user.objects.create(
                    email=email,
                    fullName=name,
                    google_profile_picture=picture,
                    password="",
                    referral_code=referral_code,
                )
            # Check if profile is complete
            profile_complete = all([
                usr.fullName,
                usr.dateofbirth,
                usr.correspondenceAddress,
                usr.phone_number,
            ])
            return Response({
                "success": True,
                "message": "You are now logged in!",
                "user": UserSerializer(usr).data,
                "needsProfileCompletion": not profile_complete,
                "email": usr.email
            }, status=200)
        except Exception as e:
            return Response({"success": False, "message": f"Google login failed: {str(e)}"}, status=400)
    email = request.data.get("email")
    password = request.data.get("password")
    try:
        usr = user.objects.get(email=email)
        if (usr is None) or (usr.password != password):
            return Response(
                {
                    "success": False,
                    "message": "Invalid user Credentials!",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        else:
            # Check if profile is complete
            profile_complete = all(
                [
                    usr.fullName,
                    usr.dateofbirth,
                    usr.correspondenceAddress,
                    usr.phone_number,
                ]
            )
            # --- JWT Token Generation ---
            payload = {
                'user_id': usr.id,
                'email': usr.email,
                'exp': (datetime.utcnow() + timedelta(days=7)).timestamp(),
                'iat': datetime.utcnow().timestamp(),
            }
            secret = getattr(settings, 'SECRET_KEY', 'sabapplier-secret')
            token = jwt.encode(payload, secret, algorithm='HS256')
            # Normalize user data for extension compatibility
            user_data = UserSerializer(usr).data
            user_data['name'] = user_data.get('fullName', usr.fullName or usr.email)
            user_data['fullName'] = user_data.get('fullName', usr.fullName or usr.email)
            # Return user data and token for frontend authentication state
            return Response(
                {
                    "success": True, 
                    "message": "You are now logged in!",
                    "user": user_data,
                    "needsProfileCompletion": not profile_complete,
                    "email": usr.email,
                    "token": token,
                },
                status=status.HTTP_200_OK,
            )
    except user.DoesNotExist:
        return Response(
            {"success": False, "message": "User does not exist"},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    print('Inside logout_view function')
    try:
        request.session.flush()
        return Response(
            {"message": "Logout successful"}, status=status.HTTP_200_OK
        )
    except:
        return Response(
            {"error": "Logout failed"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_profile(request):
    print('Inside get_profile function')
    try:
        email = request.GET.get("email")
        if email:
            usr = user.objects.get(email=email)
        else:
            # If no email param, use authenticated user if available
            if request.user.is_authenticated:
                usr = request.user
            else:
                return Response({"error": "No email provided and not authenticated."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer(usr)
        user_data = serializer.data
        # Ensure successful_referrals is always present at the top level
        user_data['successful_referrals'] = getattr(usr, 'successful_referrals', 0)
        return Response(
            {
                "message": "Profile fetched successfully",
                "user_data": user_data,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as err:
        return Response(
            {"error": "profile failed to load"},
            status=status.HTTP_400_BAD_REQUEST,
        )


####################  API End Points for Extension ####################

@csrf_exempt
@api_view(["POST"])

@permission_classes([AllowAny])  # Allow anyone to access this endpoint

def extension_login_view(request):
    print('Inside extension_login_view function')
    try:
        print("=== EXTENSION LOGIN DEBUG ===")
        print("Request method:", request.method)
        print("Request headers:", dict(request.headers))
        print("Request origin:", request.headers.get('Origin', 'No origin header'))
        print("Request user-agent:", request.headers.get('User-Agent', 'No user-agent header'))
        print("Request content-type:", request.headers.get('Content-Type', 'No content-type header'))
        print("Request body type:", type(request.body))
        print("Request body length:", len(request.body) if request.body else 0)
        print("Request data:", getattr(request, 'data', 'No request.data'))
        print("Request POST:", getattr(request, 'POST', 'No request.POST'))
        print("Raw body preview:", request.body[:200] if request.body else 'Empty body')
        
        # Handle both JSON and form data
        if hasattr(request, 'data') and request.data:
            email = request.data.get("user_email")
            password = request.data.get("user_password")
            print("Data source: request.data")
        else:
            # Fallback to raw body parsing
            import json
            try:
                body_data = json.loads(request.body.decode('utf-8'))
                email = body_data.get("user_email")
                password = body_data.get("user_password")
                print("Data source: raw body JSON parsing")
            except Exception as parse_error:
                print("JSON parsing error:", parse_error)
                return Response(
                    {"success": False, "message": "Invalid request data format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        print(f"Extracted email: {email}")
        print(f"Extracted password: {'*' * len(password) if password else 'None'}")
        
        if not email or not password:
            print("Missing email or password")
            return Response(
                {"success": False, "message": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            usr = user.objects.get(email=email)
            
            if usr.password != password:  # Note: In production, use proper password hashing
                return Response(
                    {
                        "success": False,
                        "message": "Invalid credentials!",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            user_data = UserSerializer(usr).data
            
            return Response(
                {
                    "message": "Login successful",
                    "success": True,
                    "user_name": usr.fullName,
                    "user_email": usr.email,
                    "user_info": user_data,
                },
                status=status.HTTP_200_OK,
            )
            
        except user.DoesNotExist:
            return Response(
                {"success": False, "message": "User does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
            
    except Exception as err:
        return Response(
            {"error": f"Login Failed: {str(err)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def auto_fill_extension(request):

    print("Inside auto_fill_extension function")
    try:
        html_data = request.data["html_data"]
        user_email = request.data["user_email"]
        
        # Check if this is a request to use shared account data
        shared_account_email = request.data.get("shared_account_email")
        share_id = request.data.get("share_id")
        
        # Determine which user's data to use for autofill
        target_email = shared_account_email if shared_account_email else user_email
        
        print(f"Auto-fill request - User: {user_email}, Target data: {target_email}")
        
        try:
            # If using shared account data, verify the sharing is valid
            if shared_account_email:
                print(f"Using shared account data from {shared_account_email}")
                
                # Verify that the sharing exists and is active
                try:
                    data_share = DataShare.objects.get(
                        sender_email=shared_account_email,
                        receiver_email=user_email,
                        status='accepted',
                        is_active=True
                    )
                    print(f"Valid data sharing found: {data_share.id}")
                except DataShare.DoesNotExist:
                    return Response(
                        {"message": "No valid data sharing found", "autofill_data": {}},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            
            # Get the target user's data
            usr = user.objects.get(email=target_email)
            user_data = UserSerializer(usr).data

            print("user_data:", user_data)
            
            autofill_data = get_autofill_data(html_data, user_data)
            print("autofill_data:", autofill_data)

            return Response(
                {
                    "message": "Auto-fill successful",
                    "autofill_data": autofill_data,
                    "data_source": "shared" if shared_account_email else "own",
                    "source_email": target_email
                },
                status=status.HTTP_200_OK,
            )
        except user.DoesNotExist:

            print(f"User does not exist: {target_email}")


            return Response(
                {"message": "User not found", "autofill_data": {}},
                status=status.HTTP_404_NOT_FOUND,
            )
    except Exception as err:
        return Response(
            {"error": "Auto-fill failed"}, status=status.HTTP_400_BAD_REQUEST
        )
######################  Narendra Singh Code Merge ####################

@api_view(['POST'])
@permission_classes([AllowAny])
def save_learned_form_data(request):
    """
    Save learned form data from user interactions
    """
    try:
        print(f"Received save_learned_form_data request: {request.data}")
        user_email = request.data.get('user_email')
        form_data = request.data.get('form_data')  # Raw input data from page
        current_url = request.data.get('current_url') or request.data.get('url')
        
        if not user_email or not form_data:
            return Response({
                "success": False, 
                "message": "Missing required data"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle both object and array formats from frontend
        if isinstance(form_data, list):
            # Convert array format back to object format for consistency
            form_data_obj = {}
            for item in form_data:
                if isinstance(item, dict):
                    for key, value in item.items():
                        if key != 'type':
                            form_data_obj[key] = value
            form_data = form_data_obj
        
        usr = user.objects.get(email=user_email)
        
        # Initialize extra_details if not exists
        if usr.extra_details is None:
            usr.extra_details = []
        
        # Add new learned data
        learned_entry = {
            "url": current_url,
            "form_data": form_data,
            "timestamp": datetime.now().isoformat(),
            "processed": False  # Flag to indicate if Gemini has processed this
        }
        
        usr.extra_details.append(learned_entry)
        usr.save()
        
        return Response({
            "success": True, 
            "message": "Form data saved for learning"
        }, status=status.HTTP_200_OK)
        
    except user.DoesNotExist:
        return Response({
            "success": False, 
            "message": "User not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as err:
        print(f"Error saving learned data: {err}")
        return Response({
            "success": False, 
            "message": str(err)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def process_learned_data(request):
    """
    Process learned data with Gemini AI to convert to structured format
    """
    try:
        user_email = request.data.get('user_email')
        
        if not user_email:
            return Response({
                "success": False, 
                "message": "User email required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        usr = user.objects.get(email=user_email)
        
        if not usr.extra_details:
            return Response({
                "success": False, 
                "message": "No learned data to process"
            }, status=status.HTTP_404_NOT_FOUND)
        
        processed_count = 0
        
        # Process unprocessed entries
        for entry in usr.extra_details:
            if not entry.get('processed', False):
                # Send to Gemini for better formatting
                processed_data = process_with_gemini(entry['form_data'])
                if processed_data:
                    entry['processed_data'] = processed_data
                    entry['processed'] = True
                    processed_count += 1
        
        usr.save()
        
        return Response({
            "success": True, 
            "message": f"Processed {processed_count} learned data entries",
            "processed_count": processed_count
        }, status=status.HTTP_200_OK)
        
    except user.DoesNotExist:
        return Response({
            "success": False, 
            "message": "User not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as err:
        print(f"Error processing learned data: {err}")
        return Response({
            "success": False, 
            "message": str(err)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_learned_data(request):
    """
    Get user's learned form data with enhanced processing
    """
    try:
        user_email = request.GET.get('user_email')
        
        if not user_email:
            return Response({
                "success": False, 
                "message": "User email required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        usr = user.objects.get(email=user_email)
        
        if not usr.extra_details:
            return Response({
                "success": True, 
                "learned_data": [],
                "processed_data": [],
                "count": 0
            }, status=status.HTTP_200_OK)
        
        # Use the new processing function from learning_api
        processed_entries = process_learned_data_for_display(usr.extra_details)
        
        return Response({
            "success": True, 
            "learned_data": usr.extra_details,  # Original data
            "processed_data": processed_entries,  # Processed for frontend
            "count": len(processed_entries)
        }, status=status.HTTP_200_OK)
        
    except user.DoesNotExist:
        return Response({
            "success": False, 
            "message": "User not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as err:
        print(f"Error getting learned data: {err}")
        return Response({
            "success": False, 
            "message": str(err)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def delete_learned_data(request):
    try:
        user_email = request.data.get('user_email')
        index = request.data.get('index')
        
        if not user_email:
            return Response({'success': False, 'error': 'User email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        usr = user.objects.filter(email=user_email).first()
        if not usr:
            return Response({'success': False, 'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if usr.extra_details is None:
            usr.extra_details = []
        
        if index is not None and 0 <= index < len(usr.extra_details):
            usr.extra_details.pop(index)
            usr.save()
            return Response({'success': True, 'message': 'Data entry deleted successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'error': 'Invalid index'}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        print(f"Error deleting learned data: {e}")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# New view functions for popup mode and smart comparison

@api_view(['POST'])
@permission_classes([AllowAny])
def toggle_popup_mode(request):
    try:
        user_email = request.data.get('user_email')
        enabled = request.data.get('enabled', False)
        
        if not user_email:
            return Response({'success': False, 'error': 'User email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        usr = user.objects.filter(email=user_email).first()
        if not usr:
            return Response({'success': False, 'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Store popup mode preference in user's extra_details
        if usr.extra_details is None:
            usr.extra_details = []
        
        # Find existing popup mode setting or create new one
        popup_setting = None
        for i, detail in enumerate(usr.extra_details):
            if isinstance(detail, dict) and detail.get('type') == 'popup_mode':
                popup_setting = i
                break
        
        if popup_setting is not None:
            usr.extra_details[popup_setting]['enabled'] = enabled
            usr.extra_details[popup_setting]['last_updated'] = datetime.now().isoformat()
        else:
            usr.extra_details.append({
                'type': 'popup_mode',
                'enabled': enabled,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            })
        
        usr.save()
        
        # Log the action for debugging
        print(f"Popup mode {'enabled' if enabled else 'disabled'} for user: {user_email}")
        
        return Response({
            'success': True, 
            'enabled': enabled,
            'message': f'Popup mode {"enabled" if enabled else "disabled"} successfully',
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error toggling popup mode: {e}")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_popup_mode(request):
    try:
        user_email = request.GET.get('user_email')
        
        if not user_email:
            return Response({'success': False, 'error': 'User email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        usr = user.objects.filter(email=user_email).first()
        if not usr:
            return Response({'success': False, 'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Default to disabled if no setting found
        enabled = False
        last_updated = None
        
        if usr.extra_details:
            for detail in usr.extra_details:
                if isinstance(detail, dict) and detail.get('type') == 'popup_mode':
                    enabled = detail.get('enabled', False)
                    last_updated = detail.get('last_updated')
                    break
        
        return Response({
            'success': True,
            'enabled': enabled,
            'last_updated': last_updated,
            'user_email': user_email
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error getting popup mode: {e}")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_autofill_data(request):
    try:
        user_email = request.GET.get('user_email')
        
        if not user_email:
            return Response({'success': False, 'error': 'User email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        usr = user.objects.filter(email=user_email).first()
        if not usr:
            return Response({'success': False, 'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get user's autofill data
        user_data = UserSerializer(usr).data
        # For this endpoint, we'll return the user's structured data instead of calling autofill function
        # since autofill_data function is meant for form filling, not data retrieval
        autofill_data = user_data
        
        # Add metadata for better tracking
        response_data = {
            'success': True,
            'autofill_data': autofill_data,
            'user_email': user_email,
            'data_count': len(autofill_data) if autofill_data else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"Retrieved {len(autofill_data) if autofill_data else 0} autofill data points for user: {user_email}")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error getting user autofill data: {e}")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def compare_form_data(request):
    try:
        user_email = request.data.get('user_email')
        form_data = request.data.get('form_data', [])
        current_url = request.data.get('url', '')
        
        if not user_email:
            return Response({'success': False, 'error': 'User email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        usr = user.objects.filter(email=user_email).first()
        if not usr:
            return Response({'success': False, 'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get user's existing autofill data
        user_data = UserSerializer(usr).data
        existing_autofill_data = user_data
        
        # Create a mapping of field names to values from existing autofill data
        existing_field_values = {}
        for field_data in existing_autofill_data:
            for field_name, field_value in field_data.items():
                if field_name != 'type' and field_value:
                    # Normalize field name for comparison (remove brackets, quotes, etc.)
                    normalized_name = field_name.replace('[', '').replace(']', '').replace("'", '').replace('"', '').replace('name=', '').replace('#', '').replace('.', '')
                    existing_field_values[normalized_name] = field_value
        
        # Find form data that differs from existing autofill data
        different_data = []
        new_fields = []
        updated_fields = []
        
        for field_data in form_data:
            for field_name, field_value in field_data.items():
                if field_name != 'type' and field_value and field_value.strip():
                    # Normalize field name for comparison
                    normalized_name = field_name.replace('[', '').replace(']', '').replace("'", '').replace('"', '').replace('name=', '').replace('#', '').replace('.', '')
                    
                    # Check if this field exists in existing data
                    if normalized_name in existing_field_values:
                        existing_value = existing_field_values[normalized_name]
                        # If values are different, include this field
                        if existing_value != field_value:
                            different_data.append(field_data)
                            updated_fields.append({
                                'field': normalized_name,
                                'old_value': existing_value,
                                'new_value': field_value
                            })
                            break
                    else:
                        # This is a new field that doesn't exist in autofill data
                        different_data.append(field_data)
                        new_fields.append(normalized_name)
                        break
        
        # Enhanced response with more detailed information
        response_data = {
            'success': True,
            'different_data': different_data,
            'total_form_fields': len(form_data),
            'different_fields': len(different_data),
            'existing_fields_count': len(existing_field_values),
            'new_fields_count': len(new_fields),
            'updated_fields_count': len(updated_fields),
            'new_fields': new_fields,
            'updated_fields': updated_fields,
            'user_email': user_email,
            'current_url': current_url,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"Form comparison for {user_email}: {len(different_data)} different fields out of {len(form_data)} total fields")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error comparing form data: {e}")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_stats(request):
    try:
        user_email = request.GET.get('user_email')
        
        if not user_email:
            return Response({'success': False, 'error': 'User email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        usr = user.objects.filter(email=user_email).first()
        if not usr:
            return Response({'success': False, 'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get user's autofill data
        user_data = UserSerializer(usr).data
        autofill_data = user_data
        
        # Get popup mode status
        popup_enabled = False
        if usr.extra_details:
            for detail in usr.extra_details:
                if isinstance(detail, dict) and detail.get('type') == 'popup_mode':
                    popup_enabled = detail.get('enabled', False)
                    break
        
        # Calculate statistics
        # For stats, we should use the learned data from extra_details, not user profile data
        learned_data = usr.extra_details if usr.extra_details else []
        total_data_points = len(learned_data)
        
        # Group data by website/domain
        website_stats = {}
        if learned_data:
            for entry in learned_data:
                if isinstance(entry, dict) and entry.get('url'):
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(entry['url']).netloc.replace('www.', '')
                    except:
                        domain = 'Unknown'
                        
                    form_data = entry.get('form_data', {})
                    field_count = len(form_data) if isinstance(form_data, dict) else 0
                    
                    if domain not in website_stats:
                        website_stats[domain] = 0
                    website_stats[domain] += field_count
        
        # Get user profile completion stats
        profile_fields = ['fullname', 'email', 'phone', 'address', 'city', 'state', 'pincode']
        completed_fields = sum(1 for field in profile_fields if getattr(usr, field, None))
        profile_completion = (completed_fields / len(profile_fields)) * 100 if profile_fields else 0
        
        stats = {
            'success': True,
            'user_email': user_email,
            'total_data_points': total_data_points,
            'popup_mode_enabled': popup_enabled,
            'profile_completion_percentage': round(profile_completion, 2),
            'websites_count': len(website_stats),
            'website_stats': website_stats,
            'last_activity': usr.updated_at.isoformat() if hasattr(usr, 'updated_at') else None,
            'account_created': usr.created_at.isoformat() if hasattr(usr, 'created_at') else None,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"Generated stats for user {user_email}: {total_data_points} data points across {len(website_stats)} websites")
        
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





######################  DATA SHARING ENDPOINTS ####################

@api_view(["POST"])
@permission_classes([AllowAny])
def share_data_with_friend(request):
    """
    Share user data with a friend by email
    """
    try:
        sender_email = request.data.get("sender_email", "").strip().lower()
        receiver_email = request.data.get("receiver_email", "").strip().lower()
        selected_documents = request.data.get("selected_documents", [])
        sharing_type = request.data.get("sharing_type", "documents_only")
        
        if not sender_email or not receiver_email:
            return Response(
                {"error": "Both sender and receiver email are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Allow sharing without selecting documents (will share only personal info and addresses)
        # if not selected_documents:
        #     return Response(
        #         {"error": "Please select at least one document to share"},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        
        if sender_email == receiver_email:
            return Response(
                {"error": "You cannot share data with yourself"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get sender's user data
        try:
            sender_user = user.objects.get(email=sender_email)
        except user.DoesNotExist:
            return Response(
                {"error": "Sender email is not registered on the platform"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if receiver exists in the system
        if not user.objects.filter(email=receiver_email).exists():
            return Response(
                {"error": "Receiver email is not registered on the platform"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if sharing already exists
        existing_share = DataShare.objects.filter(
            sender_email=sender_email, 
            receiver_email=receiver_email
        ).first()
        
        if existing_share:
            if existing_share.status == 'pending':
                return Response(
                    {"error": "A sharing request is already pending with this user"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif existing_share.status == 'accepted' and existing_share.is_active:
                return Response(
                    {"error": "You are already sharing data with this user"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Reactivate sharing if it was stopped or declined
                existing_share.status = 'pending'
                existing_share.is_active = True
                existing_share.shared_at = datetime.now()
                existing_share.responded_at = None
                existing_share.stopped_at = None
                existing_share.selected_documents = selected_documents
                # Save updated shared data snapshot
                existing_share.save_shared_data(sender_user, sharing_type)
                data_share = existing_share
        else:
            # Create new sharing request
            data_share = DataShare.objects.create(
                sender_email=sender_email,
                receiver_email=receiver_email,
                status='pending',
                is_active=True,
                selected_documents=selected_documents
            )
            # Save shared data snapshot
            data_share.save_shared_data(sender_user, sharing_type)
        
        # Create notification for receiver
        ShareNotification.objects.create(
            data_share=data_share,
            recipient_email=receiver_email,
            notification_type='share_request',
            message=f"{sender_email} wants to share their profile data with you."
        )
        
        # Send email notification
        try:
            send_mail(
                subject='SabApplier - Data Sharing Request',
                message=f"""
                Hello,
                
                {sender_email} has requested to share their profile data with you on SabApplier.
                
                Please log in to your dashboard to accept or decline this request.
                
                Best regards,
                SabApplier Team
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[receiver_email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
        
        return Response({
            "message": "Data sharing request sent successfully",
            "share_id": data_share.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"Share data error: {e}")
        return Response(
            {"error": "Failed to send sharing request"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["POST"])
@permission_classes([AllowAny])
def respond_to_share_request(request):
    """
    Accept or decline a data sharing request
    """
    try:
        share_id = request.data.get("share_id")
        response_action = request.data.get("action")  # 'accept' or 'decline'
        receiver_email = request.data.get("receiver_email", "").strip().lower()
        
        if not all([share_id, response_action, receiver_email]):
            return Response(
                {"error": "Share ID, action, and receiver email are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if response_action not in ['accept', 'decline']:
            return Response(
                {"error": "Action must be 'accept' or 'decline'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the sharing request
        try:
            data_share = DataShare.objects.get(
                id=share_id,
                receiver_email=receiver_email,
                status='pending'
            )
        except DataShare.DoesNotExist:
            return Response(
                {"error": "Sharing request not found or already responded"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update the sharing status
        data_share.status = 'accepted' if response_action == 'accept' else 'declined'
        data_share.responded_at = datetime.now()
        data_share.save()
        
        # Create notification for sender
        notification_type = 'share_accepted' if response_action == 'accept' else 'share_declined'
        message = f"{receiver_email} has {response_action}ed your data sharing request."
        
        ShareNotification.objects.create(
            data_share=data_share,
            recipient_email=data_share.sender_email,
            notification_type=notification_type,
            message=message
        )
        
        # Send email notification to sender
        try:
            send_mail(
                subject=f'SabApplier - Data Sharing Request {response_action.title()}ed',
                message=f"""
                Hello,
                
                {receiver_email} has {response_action}ed your data sharing request on SabApplier.
                
                Best regards,
                SabApplier Team
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[data_share.sender_email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
        
        return Response({
            "message": f"Sharing request {response_action}ed successfully"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Respond to share error: {e}")
        return Response(
            {"error": "Failed to respond to sharing request"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["POST"])
@permission_classes([AllowAny])
def stop_data_sharing(request):
    """
    Stop sharing data with a friend
    """
    try:
        sender_email = request.data.get("sender_email", "").strip().lower()
        receiver_email = request.data.get("receiver_email", "").strip().lower()
        
        if not sender_email or not receiver_email:
            return Response(
                {"error": "Both sender and receiver email are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find active sharing
        try:
            data_share = DataShare.objects.get(
                sender_email=sender_email,
                receiver_email=receiver_email,
                is_active=True
            )
        except DataShare.DoesNotExist:
            return Response(
                {"error": "No active data sharing found with this user"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Stop the sharing
        data_share.status = 'stopped'
        data_share.is_active = False
        data_share.stopped_at = datetime.now()
        data_share.save()
        
        # Create notification for receiver
        ShareNotification.objects.create(
            data_share=data_share,
            recipient_email=receiver_email,
            notification_type='share_stopped',
            message=f"{sender_email} has stopped sharing their data with you."
        )
        
        # Send email notification
        try:
            send_mail(
                subject='SabApplier - Data Sharing Stopped',
                message=f"""
                Hello,
                
                {sender_email} has stopped sharing their profile data with you on SabApplier.
                
                Best regards,
                SabApplier Team
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[receiver_email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
        
        return Response({
            "message": "Data sharing stopped successfully"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Stop sharing error: {e}")
        return Response(
            {"error": "Failed to stop data sharing"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["GET"])
@permission_classes([AllowAny])
def get_shared_data(request):
    """
    Get shared data from a friend
    """
    try:
        receiver_email = request.GET.get("receiver_email", "").strip().lower()
        sender_email = request.GET.get("sender_email", "").strip().lower()
        
        if not receiver_email or not sender_email:
            return Response(
                {"error": "Both receiver and sender email are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if sharing is active and accepted
        try:
            data_share = DataShare.objects.get(
                sender_email=sender_email,
                receiver_email=receiver_email,
                status='accepted',
                is_active=True
            )
        except DataShare.DoesNotExist:
            return Response(
                {"error": "No active data sharing found or not accepted"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Return the stored shared data snapshot
        if data_share.shared_data:
            return Response({
                "shared_data": data_share.shared_data,
                "share_info": DataShareSerializer(data_share).data
            }, status=status.HTTP_200_OK)
        else:
            # Fallback to current data if no snapshot exists (for backward compatibility)
            try:
                sender_user = user.objects.get(email=sender_email)
                # Save the current data snapshot for future use
                data_share.save_shared_data(sender_user)
                return Response({
                    "shared_data": data_share.shared_data,
                    "share_info": DataShareSerializer(data_share).data
                }, status=status.HTTP_200_OK)
            except user.DoesNotExist:
                return Response(
                    {"error": "Sender user not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        
    except Exception as e:
        print(f"Get shared data error: {e}")
        return Response(
            {"error": "Failed to get shared data"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["GET"])
@permission_classes([AllowAny])
def get_user_notifications(request):
    """
    Get notifications for a user
    """
    try:
        user_email = request.GET.get("email", "").strip().lower()
        
        if not user_email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notifications = ShareNotification.objects.filter(
            recipient_email=user_email
        ).order_by('-created_at')
        
        serializer = ShareNotificationSerializer(notifications, many=True)
        return Response({
            "notifications": serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Get notifications error: {e}")
        return Response(
            {"error": "Failed to get notifications"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["GET"])
@permission_classes([AllowAny])
def get_user_shares(request):
    """
    Get all sharing relationships for a user (both sent and received)
    """
    try:
        user_email = request.GET.get("email", "").strip().lower()
        
        if not user_email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get shares sent by user
        sent_shares = DataShare.objects.filter(sender_email=user_email)
        
        # Get shares received by user
        received_shares = DataShare.objects.filter(receiver_email=user_email)
        
        return Response({
            "sent_shares": DataShareSerializer(sent_shares, many=True).data,
            "received_shares": DataShareSerializer(received_shares, many=True).data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Get user shares error: {e}")
        return Response(
            {"error": "Failed to get user shares"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_shared_data(request):
    """
    Refresh/update the shared data snapshot with current user data
    """
    try:
        sender_email = request.data.get("sender_email", "").strip().lower()
        receiver_email = request.data.get("receiver_email", "").strip().lower()
        
        if not sender_email or not receiver_email:
            return Response(
                {"error": "Both sender and receiver email are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if sharing exists and is accepted
        try:
            data_share = DataShare.objects.get(
                sender_email=sender_email,
                receiver_email=receiver_email,
                status='accepted',
                is_active=True
            )
        except DataShare.DoesNotExist:
            return Response(
                {"error": "No active accepted data sharing found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get sender's current data
        try:
            sender_user = user.objects.get(email=sender_email)
            # Update the shared data snapshot
            data_share.save_shared_data(sender_user)
            
            return Response({
                "message": "Shared data updated successfully",
                "updated_at": data_share.shared_data.get('timestamp')
            }, status=status.HTTP_200_OK)
            
        except user.DoesNotExist:
            return Response(
                {"error": "Sender user not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
    except Exception as e:
        print(f"Refresh shared data error: {e}")
        return Response(
            {"error": "Failed to refresh shared data"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_shared_accounts(request):
    """
    Get accounts that have shared data with the current user
    Returns both the user's own account and accounts that have shared data with them
    """
    try:
        user_email = request.GET.get("email", "").strip().lower()
        
        if not user_email:
            return Response(
                {"error": "Email parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        accounts = []
        
        # Add the user's own account
        try:
            current_user = user.objects.get(email=user_email)
            accounts.append({
                "email": current_user.email,
                "name": current_user.fullName or current_user.email.split('@')[0],
                "type": "self",
                "shared_at": None,
                "share_id": None
            })
        except user.DoesNotExist:
            pass
        
        # Get accepted shares from other users to current user
        accepted_shares = DataShare.objects.filter(
            receiver_email=user_email,
            status='accepted',
            is_active=True
        )
        
        # Add each shared account
        for share in accepted_shares:
            try:
                sender_user = user.objects.get(email=share.sender_email)
                # Build shared_documents with URLs
                shared_documents = []
                doc_types = share.selected_documents if hasattr(share, 'selected_documents') else []
                doc_urls = share.shared_data.get('documents', {}).get('document_urls', {}) if hasattr(share, 'shared_data') and share.shared_data else {}
                for doc_type in doc_types:
                    url = doc_urls.get(doc_type, None)
                    if url and 'dropbox.com' in url:
                        url = url.replace('www.dropbox.com', 'dl.dropboxusercontent.com').replace('&dl=0', '&dl=1').replace('?dl=0', '?dl=1')
                    shared_documents.append({
                        "type": doc_type,
                        "name": doc_type.replace('_file_url', '').replace('_', ' ').title(),
                        "url": url
                    })
                accounts.append({
                    "email": share.sender_email,
                    "name": sender_user.fullName or share.sender_email.split('@')[0],
                    "type": "shared",
                    "shared_at": share.shared_at.isoformat() if share.shared_at else None,
                    "share_id": str(share.id),
                    "shared_documents": shared_documents
                })
            except user.DoesNotExist:
                shared_documents = []
                doc_types = share.selected_documents if hasattr(share, 'selected_documents') else []
                doc_urls = share.shared_data.get('documents', {}).get('document_urls', {}) if hasattr(share, 'shared_data') and share.shared_data else {}
                for doc_type in doc_types:
                    url = doc_urls.get(doc_type, None)
                    if url and 'dropbox.com' in url:
                        url = url.replace('www.dropbox.com', 'dl.dropboxusercontent.com').replace('&dl=0', '&dl=1').replace('?dl=0', '?dl=1')
                    shared_documents.append({
                        "type": doc_type,
                        "name": doc_type.replace('_file_url', '').replace('_', ' ').title(),
                        "url": url
                    })
                accounts.append({
                    "email": share.sender_email,
                    "name": share.sender_email.split('@')[0],
                    "type": "shared",
                    "shared_at": share.shared_at.isoformat() if share.shared_at else None,
                    "share_id": str(share.id),
                    "shared_documents": shared_documents
                })
        
        return Response({
            "accounts": accounts,
            "total_count": len(accounts)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Get shared accounts error: {e}")
        return Response(
            {"error": "Failed to get shared accounts"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["POST"])
@permission_classes([AllowAny])
def check_access_status(request):
    """
    Check if a user has access to the main application.
    Returns access status and user information.
    """
    email = request.data.get("email")
    if not email:
        return Response(
            {"success": False, "message": "Email parameter is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    try:
        usr = user.objects.get(email=email)
        
        # Use the new user model fields
        is_enabled = usr.has_website_access
        
        print(f"Access check for {email}: enabled={is_enabled}")
        
        return Response(
            {
                "success": True,
                "is_enabled": is_enabled,
                "user_email": usr.email,
                "user_name": usr.fullName,
                "message": "Access granted" if is_enabled else "User is on waitlist"
            },
            status=status.HTTP_200_OK,
        )
        
    except user.DoesNotExist:
        return Response(
            {"success": False, "message": "User does not exist"},
            status=status.HTTP_404_NOT_FOUND,
        )

@api_view(["POST"])
@permission_classes([AllowAny])
def mark_notification_as_read(request):
    """
    Mark a notification as read by its ID
    """
    try:
        notification_id = request.data.get("notification_id")
        if not notification_id:
            return Response({"error": "Notification ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        from .models import ShareNotification
        try:
            notification = ShareNotification.objects.get(id=notification_id)
            print(f"[DEBUG] Before: Notification ID {notification.id}, is_read={notification.is_read}")
            notification.is_read = True
            notification.save()
            print(f"[DEBUG] After: Notification ID {notification.id}, is_read={notification.is_read}")
            return Response({"message": "Notification marked as read"}, status=status.HTTP_200_OK)
        except ShareNotification.DoesNotExist:
            print(f"[DEBUG] Notification ID {notification_id} not found.")
            return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Mark notification as read error: {e}")
        return Response({"error": "Failed to mark notification as read"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@permission_classes([AllowAny])
def contact_us(request):
    print("Contact Us endpoint HIT")
    name = request.data.get("name", "").strip()
    email = request.data.get("email", "").strip()
    subject = request.data.get("subject", "").strip()
    message = request.data.get("message", "").strip()

    if not all([name, email, subject, message]):
        return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        # Save to DB
        ContactUsRequest.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        send_mail(
            subject=f"[ContactUs] {subject}",
            message=f"From: {name} <{email}>\n\n{message}",
            from_email="noreply@sabapplier.com",
            recipient_list=["sabapplierai100m@gmail.com"],
            fail_silently=False,
        )
        return Response({"success": "Message sent successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@permission_classes([AllowAny])
def delete_account(request):
    print('Inside delete_account function')
    try:
        email = request.data.get("email")
        if not email:
            return Response(
                {"success": False, "message": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Find the user
        try:
            usr = user.objects.get(email=email)
        except user.DoesNotExist:
            return Response(
                {"success": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Delete related data first
        try:
            # Delete data shares where user is sender or receiver
            DataShare.objects.filter(sender_email=email).delete()
            DataShare.objects.filter(receiver_email=email).delete()
            
            # Delete share notifications
            ShareNotification.objects.filter(recipient_email=email).delete()
            
            # Delete access controllers
            from .models import AccessController
            AccessController.objects.filter(email=usr).delete()
            
            # Delete tokens
            Token.objects.filter(user_id=usr.id).delete()
            
            print(f"Deleted related data for user {email}")
        except Exception as e:
            print(f"Error deleting related data: {e}")
            # Continue with user deletion even if related data deletion fails
        
        # Delete the user
        usr.delete()
        
        return Response(
            {
                "success": True,
                "message": "Account deleted successfully. We're sorry to see you go!",
            },
            status=status.HTTP_200_OK,
        )
        
    except Exception as e:
        print(f"Error deleting account: {e}")
        return Response(
            {
                "success": False,
                "message": "An error occurred while deleting your account. Please try again.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
