from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model, authenticate, login, logout
from .serializers import UserSerializer, TokenSerializer, UserRegistrationSerializer
from datetime import datetime, timedelta
from rest_framework import viewsets
from .serializers import UserSerializer
from .models import user, Token
from .apis.fetch_autofill_data import get_file_from_dropbox_and_return_ocr_data, get_autofill_data

class users_view(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = user.objects.all()
    
User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"success": True, "message": "You are now registered on our website!"},
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
                    "message": "Invalid username or password Credentials!",
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

@api_view(['POST'])
@permission_classes([AllowAny])
def auto_fill(request):
    try:
        url_link = request.data['link']
        user_data = request.data['user_data']
        autofill_data = get_autofill_data(url_link, user_data)
        return Response({"message": "Auto-fill successful", "autofill_data": autofill_data}, status=status.HTTP_200_OK)
    except Exception as err:
        print(err)
        return Response({"error": "Auto-fill failed"}, status=status.HTTP_400_BAD_REQUEST)
    
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
            user_data['aadhaar_card'] = get_file_from_dropbox_and_return_ocr_data(user_data['aadhaar_card'])
            user_data['pan_card'] = get_file_from_dropbox_and_return_ocr_data(user_data['pan_card'])
            print('user_data:', user_data)
            autofill_data = get_autofill_data(html_data, user_data)
            print('autofill_data:', autofill_data)
            return Response({"message": "Auto-fill successful", "autofill_data": autofill_data}, status=status.HTTP_200_OK)
        except user.DoesNotExist:
            print('User does not exist...')
            return Response({"message": "User not found", "autofill_data": {}}, status=status.HTTP_200_OK)
    except Exception as err:
        print('Error:', err)
        return Response({"error": "Auto-fill failed"}, status=status.HTTP_400_BAD_REQUEST)
 