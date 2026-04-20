from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated , AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from skincare.response import success_response
from .serializers import RegisterSerializer,CustomTokenObtainPairSerializer,ChangePasswordSerializer,SendOTPSerializer,VerifyOTPSerializer,ResetPasswordSerializer,ProfileSerializer,UserUpdateSerializer
from .models import Profile


#jwt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView


#swagger 
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.


class RegisterView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser , FormParser]

    @swagger_auto_schema(
        operation_description="Register a new user and return JWT tokens",
        request_body=RegisterSerializer,
        tags=["Authentication"],
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language code for translation (default is 'EN')",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "access_token": openapi.Schema(type=openapi.TYPE_STRING),
                                "refresh_token": openapi.Schema(type=openapi.TYPE_STRING),
                                "user": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "email": openapi.Schema(type=openapi.TYPE_STRING),
                                        "membership_Id": openapi.Schema(type=openapi.TYPE_STRING),
                                        "role": openapi.Schema(type=openapi.TYPE_STRING),
                                        "full_name": openapi.Schema(type=openapi.TYPE_STRING),
                                        "gender": openapi.Schema(type=openapi.TYPE_STRING),
                                        "date_of_birth": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                                        "contact_number": openapi.Schema(type=openapi.TYPE_STRING),
                                        "skin_type": openapi.Schema(type=openapi.TYPE_STRING),
                                        "image": openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                ),
                            },
                        ),
                    },
                ),
            )
        },

    )

    def post(self , request , *args,**kwargs):
        lean = request.query_params.get('lean', 'EN').upper()
        serializer = RegisterSerializer(data = request.data,context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        profile = user.profile
        refresh = RefreshToken.for_user(user)
        refresh['id'] = user.id
        refresh['email'] = user.email
        refresh['role'] = user.role
        refresh['full_name'] = profile.full_name if profile.full_name else ""
        access_token = str(refresh.access_token)

        data={
                'refresh': str(refresh), 
                'access': access_token,
                'user': {
                    'id' : user.id,
                    'email': user.email,
                    "membership_Id":user.username,
                    'role': user.role,
                    'full_name': profile.full_name if profile.full_name else "",
                    'gender': profile.gender if profile.gender else "",
                    'date_of_birth': profile.date_of_birth if profile.date_of_birth else None,
                    "contact_number":profile.contact_number if profile.contact_number else None,
                    "skin_type":profile.skin_type if profile.skin_type else None,
                    'image': profile.image.url if profile.image else "",
                }
            }
        return success_response(message="User registerd successfully",data=data,status_code=status.HTTP_201_CREATED)
    
    


#Token view

class LoginAPIView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Authenticate a user with email and password, returning JWT access and refresh tokens along with user details.",
        tags=["Authentication"],
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language code for translation (default is 'EN')",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "access_token": openapi.Schema(type=openapi.TYPE_STRING),
                                "refresh_token": openapi.Schema(type=openapi.TYPE_STRING),
                                "user": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "email": openapi.Schema(type=openapi.TYPE_STRING),
                                        "role": openapi.Schema(type=openapi.TYPE_STRING),
                                        "full_name": openapi.Schema(type=openapi.TYPE_STRING),
                                        "gender": openapi.Schema(type=openapi.TYPE_STRING),
                                        "date_of_birth": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                                        "image": openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                ),
                            },
                        ),
                    },
                ),
            )
        },
    )
    def post(self , request , *args, **kwargs):
        lean = request.query_params.get('lean', 'EN').upper()
        response = super().post(request , *args, **kwargs)
        return success_response(message="Login successfully",data=response.data,status_code=status.HTTP_200_OK)



#Refresh Token view

class CustomTokenRefresView(TokenRefreshView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Refresh JWT access token using a valid refresh token.",
        tags=["Authentication"],
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language code for translation (default is 'EN')",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
    )
    
    def post (self , request , *args, **kwargs):
        lean = request.query_params.get('lean', 'EN').upper()
        response = super().post(request , *args, **kwargs)
        return success_response(message="New Token get successfully",data=response.data,status_code=status.HTTP_200_OK)



#change password

class ChangePasswordApiView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser,FormParser]

    @swagger_auto_schema(
        operation_description="Change the current user's password using old and new password.",
        tags=["Authentication"],
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language code for translation (default is 'EN')",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Password updated successfully"
                        ),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, example={}),
                    },
                )
            ),
        },
    )
    
    def post(self , request , *args, **kwargs):
        lean = request.query_params.get('lean', 'EN').upper()
        serializer = ChangePasswordSerializer(data = request.data,context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Password updated successfully",
            data={},
            status_code=status.HTTP_200_OK
        )



#forget password Send OTP

class ForgetPasswordSendOTP(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser , FormParser]

    @swagger_auto_schema(
        operation_description="Send OTP to user email for password reset",
        request_body=SendOTPSerializer,
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language code for translation (default is 'EN')",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
        responses={
            201: openapi.Response(
                description="OTP sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="OTP sent successfully."),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, example={}),
                    },
                ),
            ),
        },
        tags=["Forget Password"],
    )

    def post(self, request, *args, **kwargs):
        lean = request.query_params.get('lean', 'EN').upper()
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="OTP sent successfully.",data={},status_code=status.HTTP_201_CREATED)
    


#verify OTP

class ForgetPasswordVerifyOTP(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser , FormParser]

    @swagger_auto_schema(
        operation_description="Verify the OTP sent to the user's email",
        request_body=VerifyOTPSerializer,
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language code for translation (default is 'EN')",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
        responses={
            200: openapi.Response(
                description="OTP verified successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="OTP verified successfully."),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, example={}),
                    },
                ),
            ),
        },
        tags=["Forget Password"],
    )

    def post(self, request, *args, **kwargs):
        lean = request.query_params.get('lean', 'EN').upper()
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="OTP verified successfully.",data={},status_code=status.HTTP_200_OK)
 


# reset Password

class ForgetPasswordReset(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser , FormParser]

    @swagger_auto_schema(
        operation_description="Reset the user's password after OTP verification",
        request_body=ResetPasswordSerializer,
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language code for translation (default is 'EN')",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
        responses={
            200: openapi.Response(
                description="Password reset successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Password reset successfully."),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, example={}),
                    },
                ),
            ),
        },
        tags=["Forget Password"],
    )
    def post(self, request, *args, **kwargs):
        lean = request.query_params.get('lean', 'EN').upper()
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="Password reset successfully.",data={},status_code=status.HTTP_200_OK)



#User profile update

class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Get logged-in user's profile details.",
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language code for translation (default is 'EN')",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
        tags=["Profile"],
        responses={
            200: ProfileSerializer,
        }
    )

    def get(self, request):
        serializer = ProfileSerializer(request.user.profile,context ={'request': request})
        return success_response(
            message="Profile fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    

    @swagger_auto_schema(
        tags=["Profile"],
        operation_description="Update logged-in user's profile. Supports partial updates.",
        request_body=UserUpdateSerializer,
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language code for translation (default is 'EN')",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
        responses={
            200: ProfileSerializer,
        }
    )
    def patch(self, request):
        lean = request.query_params.get('lean', 'EN').upper()
        profile, _ = Profile.objects.get_or_create(user=request.user)

        serializer = UserUpdateSerializer(
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.update(request.user, serializer.validated_data)

        updated_data = ProfileSerializer(
            request.user.profile,
            context={'request': request}
        ).data

        return success_response(
            message="Profile updated successfully",
            data=updated_data,
            status_code=status.HTTP_200_OK
        )

