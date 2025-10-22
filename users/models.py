from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import EmailValidator
from django.contrib.auth.base_user import BaseUserManager
from cryptography.fernet import Fernet

DEFAULT_IMAGE_PATH = 'static/profile.png'

def upload_to(instance, filename) -> str:
    return f'user_profile_images/{instance.id or "temp"}/{filename}'


class Message(models.Model):
    conversation = models.ForeignKey('Conversation', related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey('UserProfile', related_name='messages', on_delete=models.CASCADE)
    content = models.TextField(max_length=700)
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        encryption_key = self.conversation.encryption_key 
        
        if encryption_key and not self.content.startswith('gAAAAA'):
            fernet = Fernet(encryption_key)
            self.content = fernet.encrypt(self.content.encode()).decode()
            
        super().save(*args, **kwargs)

    def decrypt_content(self) -> str:
        encryption_key = self.conversation.encryption_key
        fernet = Fernet(encryption_key)
        return fernet.decrypt(self.content.encode()).decode()

    def __str__(self):
        return f"{self.id}" #type:ignore

class Conversation(models.Model):   
    encryption_key = models.BinaryField(null=True, editable=False)
    name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    participants = models.ManyToManyField('UserProfile', related_name='conversations')
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk and not self.encryption_key:
            self.encryption_key = Fernet.generate_key()
            
        super().save(*args, **kwargs)
        
        if self.participants.count() <= 2:
            self.name = ''.join([user.username for user in self.participants.all()])
        else:
            self.add_to_name = "Group"
            super().save(update_fields=['name'])

    def __str__(self) -> str:
        return self.name

class UserProfileManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        if not email:
            raise ValueError('Email is required')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.encryption_key = Fernet.generate_key()
        
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields) 

class UserProfile(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        validators=[UnicodeUsernameValidator()],
        error_messages={'unique': "A user with that username already exists."},
    )
    email = models.EmailField(unique=True, validators=[EmailValidator(message="Enter a valid email address.")])
    date_joined = models.DateTimeField(auto_now_add=True)
    height = models.IntegerField(default=50, editable=False, null=True, blank=True)
    width = models.IntegerField(default=50, editable=False, null=True, blank=True)
    image = models.ImageField(upload_to=upload_to, null=True, blank=True, default=DEFAULT_IMAGE_PATH)
    bio = models.TextField(null=False, blank=True, default="", help_text="(optional)")
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserProfileManager()

    class Meta:
        default_permissions = ()
        permissions = (
            ('can_list', 'Can view'),
            ('can_create', 'Can create'),
            ('can_update', 'Can update'),
            ('can_part_update', 'Can partial update'),
            ('can_retrieve', 'Can retrieve'),
            ('can_delete', 'Can delete'),
        )
        ordering = ['username']

    def __str__(self):
        return self.username
