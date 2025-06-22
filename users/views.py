import os
import json
from datetime import datetime, timedelta

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.core.cache import cache
from django.conf import settings

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from google.oauth2 import id_token
from google.auth.transport import requests

from .serializers import (
    UserSerializer,
    TokenSerializer,
    UserRegistrationSerializer,
)
from .models import user, Token
from .apis.ocr_endpoint import get_ocr_data
from .apis.fetch_autofill_data import get_autofill_data
from .dropbox_storage import DropboxStorage  # import your custom storage


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
        try:
            # You'll need to set your Google OAuth client ID in settings
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

            # Extract comprehensive user data from Google
            email = idinfo.get("email")
            name = idinfo.get("name", "")
            given_name = idinfo.get("given_name", "")
            family_name = idinfo.get("family_name", "")
            picture = idinfo.get("picture", "")
            locale = idinfo.get("locale", "")
            
            # Create a full name from given_name and family_name if name is not available
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

            # Check if user already exists
            try:
                existing_user = user.objects.get(email=email)
                
                # Update existing user with Google data if fields are empty
                updated = False
                if not existing_user.fullName and name:
                    existing_user.fullName = name
                    updated = True
                
                # Update Google profile picture if available
                if picture and not existing_user.google_profile_picture:
                    existing_user.google_profile_picture = picture
                    updated = True
                
                if updated:
                    existing_user.save()
                
                # User exists, check if profile is complete
                profile_complete = all(
                    [
                        existing_user.fullName,
                        existing_user.dateofbirth,
                        existing_user.correspondenceAddress,
                        existing_user.phone_number,
                    ]
                )

                if profile_complete:
                    # User has complete profile, return login data with Google info
                    return Response(
                        {
                            "success": True,
                            "user": UserSerializer(existing_user).data,
                            "needsProfileCompletion": False,
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
                else:
                    # User exists but needs to complete profile
                    return Response(
                        {
                            "success": True,
                            "user": UserSerializer(existing_user).data,
                            "email": email,
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

            except user.DoesNotExist:
                # Create new user with Google data
                new_user = user.objects.create(
                    email=email,
                    fullName=name,
                    google_profile_picture=picture,  # Store Google profile picture
                    password="",  # Placeholder password for Google users
                )

                return Response(
                    {
                        "success": True,
                        "user": UserSerializer(new_user).data,
                        "email": email,
                        "needsProfileCompletion": True,
                        "message": "Account created successfully. Please complete your profile.",
                        "googleData": {
                            "name": name,
                            "email": email,
                            "picture": picture,
                            "given_name": given_name,
                            "family_name": family_name,
                            "locale": locale
                        }
                    },
                    status=status.HTTP_201_CREATED,
                )

        except ValueError as e:
            return Response(
                {
                    "success": False,
                    "message": f"Invalid Google token: {str(e)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        return Response(
            {"success": False, "message": f"Google signup failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


######################  API End Points for Website UI ####################


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    print(request.data)
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
        serializer.save()
        return Response(
            {
                "success": True,
                "message": "You are now registered on our website!",
            },
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def update_data(request):
    try:
        userData = request.data.copy()
        print("userData:", userData)
        
        # Map frontend field names to backend model field names
        if 'address' in userData:
            userData['correspondenceAddress'] = userData.pop('address')
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
            print(f"Processing file upload for field: {field_name}")
            
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
                print(f"File saved to Dropbox: {file_url}")

                # Store in documents with the correct field name that frontend expects
                usr.document_urls[field_name] = file_url
                print(f"Stored in document_urls with key: {field_name}")

                # Extract and store OCR text
                try:
                    ocr_text = get_ocr_data(uploaded_file)
                    text_field_name = field_name.replace('_file_url', '_text_data')
                    usr.document_texts[text_field_name] = ocr_text
                    print(f"OCR extracted and stored with key: {text_field_name}")
                except Exception as ocr_error:
                    print(f"OCR extraction failed: {ocr_error}")
                    # Store empty text if OCR fails
                    text_field_name = field_name.replace('_file_url', '_text_data')
                    usr.document_texts[text_field_name] = ""
                
            except Exception as upload_error:
                print(f"File upload failed for {field_name}: {upload_error}")
                return Response(
                    {"success": False, "message": f"File upload failed: {str(upload_error)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            
            # Remove file field from userData to avoid serializer issues
            if field_name in userData:
                userData.pop(field_name)

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
        print("Update error:", err)
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
    print(request.data)
    print(request.data.get("email", ""))
    try:
        userData = request.data.copy()
        usr = user.objects.filter(email=userData.get("email", "")).first()
        field = request.data.get("field")
        print("field:", field)

        if not field:
            return Response(
                {"error": "Field name required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if field in usr.document_urls:
            print("inside if field in usr.document_urls")
            del usr.document_urls[field]
            print("deleted field from document_urls")
            del usr.document_texts[field.replace("_file_url", "_text_data")]
            print("deleted field from document_texts")
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
            return Response(
                {"success": True, "message": "You are now logged in!"},
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
    try:
        usr = user.objects.get(email=request.GET.get("email"))
        serializer = UserSerializer(usr)
        user_data = serializer.data
        print("user_data:", user_data)
        return Response(
            {
                "message": "Profile fetched successfully",
                "user_data": user_data,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as err:
        print(err)
        return Response(
            {"error": "profile failed to load"},
            status=status.HTTP_400_BAD_REQUEST,
        )


####################  API End Points for Extension ####################


@csrf_exempt
@api_view(["POST"])
# @permission_classes([AllowAny])
def extension_login_view(request):
    try:
        print("inside extension_login_view")
        email = request.data.get("user_email")
        password = request.data.get("user_password")
        try:
            usr = user.objects.get(
                email=email
            )  # Make User -> user as per Main Code
            if (usr is None) or (usr.password != password):
                return Response(
                    {
                        "success": False,
                        "message": "Invalid user Credentials!",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            else:
                print("User exists, proceeding with auto-fill")
                print(usr)
                try:
                    usr = user.objects.get(email=email)
                    print("User found:", usr)
                    user_data = UserSerializer(usr).data
                    print("user_data:", user_data)
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
                    print("User does not exist...")
                    return Response(
                        {"message": "User not found", "autofill_data": {}},
                        status=status.HTTP_404_NOT_FOUND,
                    )
        except user.DoesNotExist:
            return Response(
                {"success": False, "message": "User does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
    except Exception as err:
        print("Error:", err)
        return Response(
            {"error": "Login Failed"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def auto_fill_extension(request):
    try:
        html_data = request.data["html_data"]
        user_email = request.data["user_email"]
        try:
            usr = user.objects.get(email=user_email)
            user_data = UserSerializer(usr).data
            print("user_data:", user_data)
            autofill_data = get_autofill_data(html_data, user_data)
            print("autofill_data:", autofill_data)
            return Response(
                {
                    "message": "Auto-fill successful",
                    "autofill_data": autofill_data,
                },
                status=status.HTTP_200_OK,
            )
        except user.DoesNotExist:
            print("User does not exist...")
            return Response(
                {"message": "User not found", "autofill_data": {}},
                status=status.HTTP_404_OK,
            )
    except Exception as err:
        print("Error:", err)
        return Response(
            {"error": "Auto-fill failed"}, status=status.HTTP_400_BAD_REQUEST
        )
