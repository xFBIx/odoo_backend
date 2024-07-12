from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
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


@api_view(["POST"])
def signup(request):
    username = request.data.get("username")
    password = request.data.get("password")
    email = request.data.get("email")
    name = request.data.get("name")

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
    except Exception as e:
        return Response({"status": "error", "message": str(e)})

    return Response({"status": "success"})

@csrf_exempt
@permission_classes((IsAuthenticated,))
def update_profile(request):
    user_profile = UserProfile.objects.get(auth_user=request.user)
    user_profile.name = request.data.get("name")
    user_profile.save()

    return Response({"status": "success", "name": user_profile.name})

class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        content = {"message": "This is a protected view"}
        return Response(content)

@csrf_exempt
def google_auth(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            token = body.get('id_token')

            if not token:
                return JsonResponse({'error': 'ID token is required'}, status=400)

            # Verify the token
            idinfo = googleIdToken.verify_oauth2_token(token, google_requests.Request())

            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                return JsonResponse({'error': 'Invalid token issuer'}, status=400)

            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')

            # Get or create the user
            user, created = User.objects.get_or_create(
                username=email,
                defaults={'first_name': first_name, 'last_name': last_name, 'email': email}
            )

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Prepare response
            response_data = {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                },
                'tokens': {
                    'access': access_token,
                    'refresh': refresh_token,
                }
            }

            return JsonResponse(response_data, status=200)

        except ValueError:
            return JsonResponse({'error': 'Invalid ID token'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid HTTP method'}, status=405)