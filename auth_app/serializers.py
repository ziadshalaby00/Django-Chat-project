from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "fullname", "username", "email",
            "date_joined", "is_active", "last_login",
        ]

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "fullname", "username", "email", "password"]
        extra_kwargs = {
            "email": {"required": True},
        }

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)



class SendPasswordResetLinkSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


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
        fields = ["username", "fullname", "email", "password", "old_password"]

    def validate(self, attrs):
        # لو المستخدم عايز يغير الباسوورد
        if "password" in attrs:
            old_password = attrs.get("old_password")
            if not old_password:
                raise serializers.ValidationError({"old_password": "Current password is required to set a new password."})
            
            # تأكد من صحة الباسوورد القديم
            if not self.instance.check_password(old_password):
                raise serializers.ValidationError({"old_password": "Current password is incorrect."})
        return attrs

    def update(self, instance, validated_data):
        # شيل old_password من validated_data
        validated_data.pop("old_password", None)

        # تحديث الباسوورد لو موجود
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)

        # تحديث باقي البيانات
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance