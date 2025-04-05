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

class users_view(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = user.objects.all()
    
User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    print('im inside views.register')
    print('request.data', request.data)
    serializer = UserSerializer(data=request.data)
    print('serializer', serializer)
    if serializer.is_valid():
        serializer.save()
        print('serializer.data', serializer.data)
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
        return Response({"message": "Profile fetched successfully", "user_data": serializer.data}, status=status.HTTP_200_OK) 
    except:
        return Response({"error": "profile failed to load"}, status=status.HTTP_400_BAD_REQUEST)
