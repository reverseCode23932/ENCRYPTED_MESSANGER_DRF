from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from rest_framework.decorators import action
from .serializers import *


class MessagePagination(PageNumberPagination):
    page_size = 5
    page_query_param = 'page'

class MessageViewSet(viewsets.ViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'partial_update','delete', 'options']
    
    def list(self, request):
        messages = Message.objects.filter(sender=request.user).order_by('timestamp')
        paginator = MessagePagination()
        page = paginator.paginate_queryset(messages, request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response({
            "message": "List of messages",
            "total": messages.count(),
            "data": serializer.data
        })
    
    def retrieve(self, request, pk=None):
        message = Message.objects.filter(id=pk,sender=request.user)
        if not message.exists():
            return Response({"error": "Message not found"},status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(message.first())
        return Response({
            "message": f"Message details ({pk})",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    def create(self, request):
        conversation_id = request.data.get('conversation')
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        if conversation.participants.exists() and request.user not in conversation.participants.all():
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(sender=request.user, conversation=conversation)
        return Response({
            "message": "Created message",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def partial_update(self, request, pk=None):
        message = Message.objects.filter(id=pk,sender=request.user)
        if not message.exists():
            return Response({"error": "Message not found"},status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(message.first(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "message": f"Updated message ({pk})",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        
    def destroy(self, request, name=None):
        try:
            conversation = Conversation.objects.get(name=name, participants=request.user)
            conversation.delete()
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "message": f"Deleted conversation ({name})"
        }, status=status.HTTP_204_NO_CONTENT)
    
class ConversationPagination(PageNumberPagination):
    page_size = 5
    page_query_param = 'page'

class ConversationViewSet(viewsets.ViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'options']
    lookup_field = 'name'
    
    def list(self, request):
        queryset = Conversation.objects.filter(participants=request.user).order_by('-created_at')
        paginator = ConversationPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response({
            "message": "List of conversations",
            "total": queryset.count(),
            "data": serializer.data
        })

    def retrieve(self, request, name=None):
        try:
            conversations = Conversation.objects.filter(name=name, participants=request.user)

            if not conversations.exists():
                raise PermissionDenied("You are not a participant of any conversation with this name.")
            
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(conversations, many=True)
        return Response({
            "message": f"Conversation details ({name})",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        if request.user not in conversation.participants.all(): #type:ignore
            conversation.participants.add(request.user) #type:ignore
        serializer = self.serializer_class(conversation)
        return Response({
            "message": "Created conversation",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, name=None):
        try:
            conversation = Conversation.objects.get(name=name, participants=request.user)
            conversation.delete()
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "message": f"Deleted conversation ({name})"
        }, status=status.HTTP_204_NO_CONTENT)

class UserPagination(PageNumberPagination):
    page_size = 5
    page_query_param = 'page'
    
class UserViewSet(viewsets.ViewSet):
    serialization_class = UserProfileSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'options']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update', 'partial_update']:
            return [IsAuthenticated()]
        elif self.action == 'destroy':
            return [IsAdminUser()]
        else:
            return [AllowAny()]
    
    @action(detail=False, methods=['POST'], url_path='logout', permission_classes=[IsAuthenticated])
    def logout(self, request):
        refresh_token = request.data["refresh"]
        try:
            token = RefreshToken(refresh_token)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        token.blacklist()
        logout(request)
        return Response({
            "message":"Logged out successful"
        },status=status.HTTP_200_OK)
        
    def list(self,request):
        queryset = UserProfile.objects.filter(is_active=True)
        paginator = UserPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = UserProfileSerializer(page, many=True)
        return Response({
            "message": "List of users",
            "total": queryset.count(),
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def create(self,request, *args, **kwargs):
        serializer = self.serialization_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({"message":"Create user"}, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        queryset = UserProfile.objects.filter(pk=pk, is_active=True)
        serializer = UserProfileSerializer(queryset)
        if not queryset.exists():
            return Response({"error":"User not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "message": f"User details ({pk})",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    def update(self, request,pk=None):
        queryset = UserProfile.objects.get(pk=pk,is_active=True)
        serializer = self.serialization_class(instance=queryset,data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({
            "message": f"User updated details ({pk})",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        
    def partial_update(self, request, pk=None):
        queryset = UserProfile.objects.get(pk=pk,is_active=True)
        serializer = self.serialization_class(instance=queryset,data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({
            "message": f"User partially updated details ({pk})",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, pk=None):
        queryset = UserProfile.objects.get(pk=pk, is_active=True)
        if request.user.is_superuser or request.user.is_staff:
            queryset.is_active = False
            queryset.save()
        return Response({
            "message": f"User has been banned ({pk})"
        }, status=status.HTTP_204_NO_CONTENT)