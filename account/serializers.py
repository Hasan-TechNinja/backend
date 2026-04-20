from rest_framework import serializers
from account.models import User,Profile,PasswordReserOTP
from datetime import date
from django.contrib.auth.models import update_last_login
from django.contrib.auth import password_validation
from .tasks import send_otp_email,send_welcome_email


#jwt 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer




#Register serializer

class RegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(max_length=200,required=False,allow_blank=True,allow_null=True)
    gender = serializers.CharField(max_length=50,required=False,allow_blank=True,allow_null=True)
    contact_number = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    skin_type = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    date_of_birth = serializers.DateField(required=False,allow_null=True)
    image = serializers.ImageField(required=False,allow_null=True)

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True,write_only=True)

    class Meta:
        model = User
        fields = ['email' , 'password' , 'full_name' , 'gender' ,"contact_number", 'date_of_birth',"skin_type",'image']
        extra_kwargs = {'password':{'write_only':True}}
    

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        full_name = attrs.get("full_name")
        gender = attrs.get("gender")
        date_of_birth = attrs.get("date_of_birth")
        contact_number = attrs.get("contact_number")
        skin_type = attrs.get("skin_type")
        image = attrs.get("image")


        if User.objects.filter(email = email).exists():
            raise serializers.ValidationError({"email" : "Email already exists."})
        
        
        if password and len(password) < 6:
            raise serializers.ValidationError({"password": "Password must be at least 6 characters long."})
        
        if full_name and len(full_name) < 2:
            raise serializers.ValidationError({"full_name": "Full name must be at least 2 characters."})
        
        if gender:
            allowed_genders = ["male", "female", "other"]
            if gender.lower() not in allowed_genders:
                raise serializers.ValidationError({
                    "gender": "Gender must be male, female, or other."
                })
            
        if date_of_birth:
            if date_of_birth >= date.today():
                raise serializers.ValidationError({
                    "date_of_birth": "Date of birth must be in the past."
                })
            
        if contact_number:
            phone = contact_number.strip()
            if not phone.startswith("+"):
                raise serializers.ValidationError({"contact_number": "Phone number must start with a country code (e.g., +1, +44, +880)."})
            
            digits = phone[1:]
            if not digits.isdigit():
                raise serializers.ValidationError({"contact_number": "Phone number must contain digits only after the country code."})

            country_code = digits[:3]
            if len(country_code) < 1:
                raise serializers.ValidationError({"contact_number": "Invalid country code."})

            number_part = digits[len(country_code):]
            if len(number_part) < 6:
                raise serializers.ValidationError({"contact_number": "Phone number must contain a valid number after the country code (minimum 6 digits)."})

            if not (8 <= len(digits) <= 20):
                raise serializers.ValidationError({"contact_number": "Phone number must be 8–20 digits (excluding +)."})
            
        if skin_type:
            if not isinstance(skin_type, str):
                raise serializers.ValidationError({
                    "skin_type": "Skin type must be a string."
                })
            
        return attrs
    

    def create(self, validated_data):
        request = self.context.get("request")
        full_name = validated_data.pop("full_name", None)
        gender = validated_data.pop("gender", None)
        contact_number = validated_data.pop("contact_number", None)
        skin_type = validated_data.pop("skin_type", None)
        date_of_birth = validated_data.pop("date_of_birth", None)
        image = validated_data.pop("image", None)
        lean = request.query_params.get('lean', 'EN').upper() if request else "EN"


        email = validated_data.pop('email',None)
        password = validated_data.pop('password',None)

        user = User.objects.create_user(
            email = email,
            username=User().generate_unique_username(),
            password = password
        )

        profile = Profile.objects.create(
            user=user,
            full_name=full_name,
            gender=gender,
            contact_number=contact_number,
            skin_type=skin_type,
            date_of_birth=date_of_birth,
            image=image
        )

        send_welcome_email.delay(user.id, lean)

        return user



#login Serializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ['email' , 'password']

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")


        try:
            user = User.objects.get(email = email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email address."})
        
        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Invalid Password"})

        data = super().validate({'email': user.email, 'password': password})

        update_last_login(None, user)
        
        profile = Profile.objects.get(user =user)

        data['user'] = {
            'id': user.id,
            'email': user.email,
            'membership_Id': user.username,
            'role': user.role,
            'full_name': profile.full_name if profile.full_name else None,
            'gender': profile.gender if profile.gender else None,
            'date_of_birth': profile.date_of_birth if profile.date_of_birth else None,
            "contact_number":profile.contact_number if profile.contact_number else None,
            "skin_type": profile.skin_type if profile.skin_type else None,
            'image': profile.image.url if profile.image else None,
        }

        return data
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['id'] = user.id
        token['email'] = user.email
        token['role'] = user.role
        token['full_name'] = user.profile.full_name if user.profile.full_name else ""
        return token



#change password

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only = True)
    new_password = serializers.CharField(write_only = True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value
    
    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value
    
    def save(self, **kwargs):
        user = self.context['request'].user
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save()
        return user




#Send OTP

class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value
    
    def save(self):
        email = self.validated_data["email"]
        user = User.objects.get(email=email)
        otp_obj = PasswordReserOTP.objects.create(user=user)   
        send_otp_email.delay(user.id, otp_obj.otp)    
        return otp_obj



#Verify OTP

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found."})

        try:
            otp_obj = PasswordReserOTP.objects.get(
                user=user,
                otp=otp,
                is_verified=False
            )
        except PasswordReserOTP.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid OTP."})

        if otp_obj.is_expired():
            raise serializers.ValidationError({"otp": "OTP expired."})

        attrs["user"] = user
        attrs["otp_obj"] = otp_obj
        return attrs
    
    def save(self):
        otp_obj = self.validated_data["otp_obj"]
        otp_obj.is_verified = True
        otp_obj.save()
        return otp_obj



#Reset Password

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value
    
    def validate(self, attrs):
        email = attrs.get("email")
        new_password = attrs.get("new_password")

        if not new_password or len(new_password) < 6:
            raise serializers.ValidationError({"new_password": "Password must be at least 6 characters long."})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found."})
        
        otp_obj = PasswordReserOTP.objects.filter(
            user=user,
            is_verified=True
        ).first()
        
        if not otp_obj:
            raise serializers.ValidationError({"otp": "Invalid or unverified OTP."})

        attrs["user"] = user
        attrs["otp_obj"] = otp_obj
        return attrs
    
    def save(self):
        user = self.validated_data["user"]
        otp_obj = self.validated_data["otp_obj"]
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save()
        otp_obj.delete()
        return user




#Profile 

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email',read_only = True)
    role = serializers.CharField(source ='user.role', read_only = True)

    class Meta:
        model = Profile
        fields = ['full_name', 'email', 'role','image','gender','date_of_birth']
        read_only_fields = ['email', 'role']


#User Update Serializer

class UserUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    full_name = serializers.CharField(max_length=200,required=False,allow_blank=True,allow_null=True)
    gender = serializers.CharField(max_length=50,required=False,allow_blank=True,allow_null=True)
    date_of_birth = serializers.DateField(required=False,allow_null=True)
    image = serializers.ImageField(required=False,allow_null=True)

    def validate(self, attrs):

        user = self.context['request'].user
        email = attrs.get("email", None)
        full_name = attrs.get('full_name')
        gender = attrs.get('gender')
        date_of_birth = attrs.get('date_of_birth')

        if email:
            if not User.objects.filter(id=user.id).exists():
                raise serializers.ValidationError({"email": "User not found."})
            if User.objects.exclude(id=user.id).filter(email=email).exists():
                raise serializers.ValidationError({"email": "Email is already in use."})
            
        if full_name and len(full_name) < 2:
            raise serializers.ValidationError({"full_name": "Full name must be at least 2 characters."})
        

        if gender:
            allowed_genders = ["male", "female", "other"]
            if gender.lower() not in allowed_genders:
                raise serializers.ValidationError({
                    "gender": "Gender must be male, female, or other."
                })
            
        if date_of_birth:
            if date_of_birth >= date.today():
                raise serializers.ValidationError({
                    "date_of_birth": "Date of birth must be in the past."
                })
            
        return attrs
    
    def update(self, instance, validated_data):
        
        if 'email' in validated_data:
            instance.email = validated_data.get('email', instance.email)
            instance.save()

        
        profile = instance.profile
        profile.full_name = validated_data.get('full_name', profile.full_name)
        profile.gender = validated_data.get('gender', profile.gender)
        profile.date_of_birth = validated_data.get('date_of_birth', profile.date_of_birth)

        if 'image' in validated_data:
            profile.image = validated_data['image']

        profile.save()
        return instance


