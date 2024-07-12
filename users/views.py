from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from users.models import UserProfile
from django.views.decorators.csrf import csrf_exempt


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
