from rest_framework import serializers

from .models import User
from rest_framework_simplejwt.tokens import RefreshToken

class Userserializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [ 'id' , 'username', 'email' , 'date_joined' , 'last_login' ,'balance' , 'rating']
        

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}) 

    class Meta:
        model = User
        fields = ['username', 'email', 'password' , 'confirm_password']
        extra_kwargs = {'password': {'write_only': True} , 'confirm_password': {'write_only': True}}
        
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        user = User.objects.create_user(**validated_data)
        return user
    

class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.RegexField(
        regex=r'^(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$',
        write_only=True,
        error_messages={'invalid': 'Password must be at least 8 chars with uppercase, number & symbol'}
    )
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data
    

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    
    new_password = serializers.RegexField(
        regex=r'^(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$',
        write_only=True,
        error_messages={'invalid': 'Password must be at least 8 chars with uppercase, number & symbol'}
    )
    
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data