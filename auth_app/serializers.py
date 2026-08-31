from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "fullname", "username", "email", "bio", "user_image",
            "date_joined", "last_login", "is_active", "is_deleted","pending_email",
            "is_email_verified",
        ]

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "fullname", "username", "email", "password"]
        extra_kwargs = {
            "email": {"required": True},
        }

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        return user

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate(self, attrs):
        try:
            uid = urlsafe_base64_decode(attrs['uid']).decode()
            self.user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid UID")

        if not default_token_generator.check_token(self.user, attrs['token']):
            raise serializers.ValidationError("Invalid or expired token")

        return attrs

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def save(self):
        password = self.validated_data['new_password']
        self.user.set_password(password)
        self.user.save()
        return self.user

class UserUpdateSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["username", "fullname", "password", "old_password", "user_image", "bio"]
    

    def validate(self, attrs):
        if "password" in attrs:
            old_password = attrs.get("old_password")
            if not old_password:
                raise serializers.ValidationError({"old_password": "Current password is required to set a new password."})
            
            if not self.instance.check_password(old_password):
                raise serializers.ValidationError({"old_password": "Current password is incorrect."})
        return attrs

    def validate_password(self, value):
        validate_password(value)
        return value

    def update(self, instance, validated_data):
        validated_data.pop("old_password", None)

        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

class ChatUserSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'fullname', 'username', 'user_image', 'is_active', 'is_deleted']

    def get_username(self, obj):
        if obj.is_deleted:
            return None
        return obj.username

class OtherUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "fullname", "username", "bio", "user_image"
        ]