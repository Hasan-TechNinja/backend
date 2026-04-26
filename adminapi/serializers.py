from rest_framework import serializers
from account.models import User, Profile

class UserListSerializer(serializers.ModelSerializer):
    membership_id = serializers.SerializerMethodField()
    name = serializers.CharField(source='profile.full_name', read_only=True)
    contact_number = serializers.CharField(source='profile.contact_number', read_only=True)
    skin_type = serializers.CharField(source='profile.skin_type', read_only=True)
    birth_date = serializers.DateField(source='profile.date_of_birth', read_only=True, format="%d/%m/%Y")

    class Meta:
        model = User
        fields = ['membership_id', 'name', 'email', 'contact_number', 'skin_type', 'birth_date']

    def get_membership_id(self, obj):
        return f"G{obj.id:04d}"
