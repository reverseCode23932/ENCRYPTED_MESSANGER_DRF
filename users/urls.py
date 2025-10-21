from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

class DefaultCustomRouter(DefaultRouter):
    root_view_name = 'root'
    
router = DefaultCustomRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'conversation', ConversationViewSet, basename='conversations')
router.register(r'messages', MessageViewSet, basename='messages')

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
    path('', include(router.urls)),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]