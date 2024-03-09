import random
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import (
    UserSerializer,
    ChangePasswordSerializer,
    UserGroupCountSerializer,
)


User = get_user_model()
EMAIL_HOST_USER = 'your_email@example.com'


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['email']



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    if request.method == 'POST':
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data.get('old_password')):
                user.set_password(serializer.data.get('new_password'))
                user.save()
                login(request, user)  # To update session after password change
                return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
            return Response({'error': 'Incorrect old password.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserGroupCountViewSet(viewsets.ViewSet):
    def list(self, request, group_name=None):
        try:
            group = Group.objects.get(name=group_name)
            count = group.user_set.count()
            serializer = UserGroupCountSerializer({"count": count})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND)


class SignupView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        if not (username and password):
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
            return Response({'error': 'Username or email already taken'}, status=status.HTTP_400_BAD_REQUEST)

        num = str(random.randint(1, 899999) + 100000)
        while User.objects.filter(ymp_id=num).exists():
            num = str(random.randint(1, 899999) + 100000)

        user = User.objects.create_user(username=username, email=email, password=password, ymp_id=num)
        user_groups = [group.name for group in user.groups.all()]

        send_mail("Welcome To YMP!", "Your YMP Id is: " + user.ymp_id, EMAIL_HOST_USER, [email], fail_silently=False)

        token, _ = Token.objects.get_or_create(user=user)

        return Response({'User': username, 'Username': user.username, 'Id': user.id, 'Groups': user_groups, 'token': token.key})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not (username and password):
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'User': username, 'Username': user.username, 'Id': user.id, 'Groups': [group.name for group in user.groups.all()], 'token': token.key})
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def logout_view(request):
    logout(request)
    return JsonResponse({'message': 'Logout successful'})



