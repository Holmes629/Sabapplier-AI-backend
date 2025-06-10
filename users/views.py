import os
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model, authenticate, login, logout
from .serializers import UserSerializer, TokenSerializer, UserRegistrationSerializer
from datetime import datetime, timedelta
from rest_framework import viewsets
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


######################  API End Points for Website UI ####################


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    print(request.data)
    # Ignore extra fields and only process email and password (and confirmPassword if present)
    allowed_fields = {'email', 'password', 'confirmPassword'}
    data = {k: v for k, v in request.data.items() if k in allowed_fields}
    if 'confirmPassword' in data and data['password'] != data['confirmPassword']:
        return Response({'success': False, 'message': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)
    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"success": True, "message": "You are now registered on our website!"},
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def update_data(request):
    try:
        userData = request.data.copy()
        usr = user.objects.filter(email=userData.get('email', "")).first()
        if not usr:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if 'password' in userData:
            userData.pop('password')
        # Initialize documents and document_texts if not already set
        if usr.document_urls is None:
            usr.document_urls = {}
        if usr.document_texts is None:
            usr.document_texts = {}

        # Handle file uploads
        for field_name, uploaded_file in request.FILES.items():
            # Example: field_name = "aadhaar_card"
            base_folder = f"{usr.email.split('@')[0]}"
            file_name = uploaded_file.name
            file_path = os.path.join(base_folder, file_name)

            # Save to Dropbox
            saved_path = dropbox_storage.save(file_path, uploaded_file)
            file_url = dropbox_storage.url(saved_path)

            # Store in documents
            usr.document_urls[file_name+"_file_url"] = file_url

            # Extract and store OCR text
            ocr_text = get_ocr_data(uploaded_file)
            usr.document_texts[file_name+"_text_data"] = ocr_text
            if field_name in userData:
                userData.pop(field_name)

        # Save user instance with updated documents
        usr.save()
        serializer = UserSerializer(usr, data=userData, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "message": "Profile updated successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as err:
        print("Update error:", err)
        return Response(
            {"success": False, "message": "An error occurred while updating the data."},
            status=status.HTTP_400_BAD_REQUEST
        )
        
        
@api_view(['POST'])
@permission_classes([AllowAny])
def delete_data(request):
    print(request.data)
    print(request.data.get("email", ""))
    try:
        userData = request.data.copy()
        usr = user.objects.filter(email=userData.get('email', "")).first()
        field = request.data.get('field')
        print('field:', field)

        if not field:
            return Response({"error": "Field name required."}, status=status.HTTP_400_BAD_REQUEST)

        if field in usr.document_urls:
            print('inside if field in usr.document_urls')
            del usr.document_urls[field]
            print('deleted field from document_urls')
            del usr.document_texts[field.replace("_file_url", "_text_data")]
            print('deleted field from document_texts')
            usr.save()
            return Response({"success": True, "message": f"{field} deleted."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid field."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')
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

@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    try:
        request.session.flush()
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
    except:
        return Response({"error": "Logout failed"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_profile(request):
    try:
        usr = user.objects.get(email=request.GET.get('email'))
        serializer = UserSerializer(usr)
        user_data = serializer.data 
        print('user_data:', user_data)
        return Response({"message": "Profile fetched successfully", "user_data": user_data}, status=status.HTTP_200_OK) 
    except Exception as err:
        print(err)
        return Response({"error": "profile failed to load"}, status=status.HTTP_400_BAD_REQUEST)




####################  API End Points for Extension ####################



@api_view(['POST'])
@permission_classes([AllowAny])
def extension_login_view(request):
    try:
        email = request.data.get('user_email')
        password = request.data.get('user_password')
        try:
            usr = User.objects.get(email=email) # Make User -> user as per Main Code
            if (usr is None) or (usr.password != password):
                return Response(
                    {
                        "success": False,
                        "message": "Invalid user Credentials!",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            else:
                print('User exists, proceeding with auto-fill')
                print(usr)
                try:
                    usr = User.objects.get(email=email)
                    print('User found:', usr)
                    user_data = UserSerializer(usr).data
                    print('user_data:', user_data)
                    return Response({"message": "Login successful", "success": True, "user_name": usr.fullName, "user_email": usr.email, "user_info": user_data,}, status=status.HTTP_200_OK)
                except User.DoesNotExist:
                    print('User does not exist...')
                    return Response({"message": "User not found", "autofill_data": {}}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response(
                {"success": False, "message": "User does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
    except Exception as err:
        print('Error:', err)
        return Response({"error": "Login Failed"}, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(['POST'])
@permission_classes([AllowAny])
def auto_fill_extension(request):
    try:
        html_data = request.data['html_data']
        user_email = request.data['user_email']
        try:
            usr = user.objects.get(email=user_email)
            user_data = UserSerializer(usr).data
            print('user_data:', user_data)
            autofill_data = get_autofill_data(html_data, user_data)
            print('autofill_data:', autofill_data)
            return Response({"message": "Auto-fill successful", "autofill_data": autofill_data}, status=status.HTTP_200_OK)
        except user.DoesNotExist:
            print('User does not exist...')
            return Response({"message": "User not found", "autofill_data": {}}, status=status.HTTP_404_OK)
    except Exception as err:
        print('Error:', err)
        return Response({"error": "Auto-fill failed"}, status=status.HTTP_400_BAD_REQUEST)
 