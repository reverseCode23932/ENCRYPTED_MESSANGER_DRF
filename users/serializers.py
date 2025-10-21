from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import *


class MessageSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    conversation = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id','conversation', 'username', 'content', 'timestamp']
        read_only_fields = ['id', 'timestamp', 'username']
        
    def get_username(self, obj):
        return obj.sender.username
    
    def get_conversation(self,obj):
        return obj.conversation.name


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'is_active', 'date_joined', 'image', 'bio', 'is_staff']
        read_only_fields = ['id','username', 'date_joined', 'height', 'width', 'is_active', 'is_staff']
        
class ConversationSerializer(serializers.ModelSerializer):
    all_messages = serializers.SerializerMethodField(read_only=True)
    participants = UserProfileSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'name', 'created_at', 'participants', 'all_messages']
        read_only_fields = ['id', 'created_at' , 'all_messages']
        
    def get_all_messages(self, obj):
        messages = Message.objects.filter(conversation=obj).order_by('timestamp')
        return MessageSerializer(messages, many=True).data

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user

        if not user.is_active: #type:ignore
            raise serializers.ValidationError('User account is disabled.')
        
        return data
