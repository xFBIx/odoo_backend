from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from users.models import UserProfile
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as googleIdToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def get_user_data(user):
    user_profile = UserProfile.objects.get(auth_user=user)
    return {
        'username': user.username,
        'email': user.email,
        'name': user_profile.name,
    }

def validate_signup_data(data):
    errors = {}
    required_fields = ['username', 'password', 'email', 'name']
    
    for field in required_fields:
        if not data.get(field):
            errors[field] = f"{field} is required"
    
    if 'email' in data:
        try:
            validate_email(data['email'])
        except ValidationError:
            errors['email'] = "Invalid email format"
    
    if 'password' in data and len(data['password']) < 8:
        errors['password'] = "Password must be at least 8 characters long"
    
    return errors

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    errors = validate_signup_data(request.data)
    if errors:
        return Response({"status": "error", "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    username = request.data['username']
    password = request.data['password']
    email = request.data['email']
    name = request.data['name']

    try:
        auth_user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
        )
        user_profile = UserProfile.objects.create(
            auth_user=auth_user,
            name=name,
        )
        
        tokens = get_tokens_for_user(auth_user)
        user_data = get_user_data(auth_user)
        
        return Response({
            "status": "success",
            "user": user_data,
            "tokens": tokens
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    try:
        user_profile = UserProfile.objects.get(auth_user=request.user)
    except UserProfile.DoesNotExist:
        return Response({"status": "error", "message": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        user_data = get_user_data(request.user)
        return Response({"status": "success", "user": user_data})
    
    elif request.method == 'POST':
        name = request.data.get("name")
        username = request.data.get("username")
        email = request.data.get("email")

        if not name and not username and not email:
            return Response({"status": "error", "message": "At least one field (name, username, or email) is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if name:
            user_profile.name = name
            user_profile.save()
        
        if username:
            if User.objects.filter(username=username).exclude(id=request.user.id).exists():
                return Response({"status": "error", "message": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
            request.user.username = username
        
        if email:
            try:
                validate_email(email)
            except ValidationError:
                return Response({"status": "error", "message": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)
            
            # if User.objects.filter(email=email).exclude(id=request.user.id).exists():
            #     return Response({"status": "error", "message": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
            request.user.email = email
        
        request.user.save()
        
        user_data = get_user_data(request.user)
        return Response({"status": "success", "user": user_data})


class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        content = {"message": "This is a protected view"}
        return Response(content)

@csrf_exempt
def google_auth(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid HTTP method'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    token = body.get('id_token')
    if not token:
        return JsonResponse({'error': 'ID token is required'}, status=400)

    try:
        idinfo = googleIdToken.verify_oauth2_token(token, google_requests.Request())
    except ValueError:
        return JsonResponse({'error': 'Invalid ID token'}, status=400)

    if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
        return JsonResponse({'error': 'Invalid token issuer'}, status=400)

    email = idinfo['email']
    first_name = idinfo.get('given_name', '')
    last_name = idinfo.get('family_name', '')

    try:
        user, created = User.objects.get_or_create(
            username = email.split('@')[0],
            defaults={'first_name': first_name, 'last_name': last_name, 'email': email}
        )

        if created:
            UserProfile.objects.create(auth_user=user, name=f"{first_name} {last_name}".strip())

        tokens = get_tokens_for_user(user)
        user_data = get_user_data(user)

        response_data = {
            'status': 'success',
            'user': user_data,
            'tokens': tokens
        }

        return JsonResponse(response_data, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = get_user_data(self.user)
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({"status": "error", "message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            "status": "success",
            "user": serializer.validated_data['user'],
            "tokens": {
                "access": serializer.validated_data['access'],
                "refresh": serializer.validated_data['refresh'],
            }
        })