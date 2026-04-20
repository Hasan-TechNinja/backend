from rest_framework.response import Response
from rest_framework import status

def success_response(message, data=None, status_code=status.HTTP_200_OK):
    return Response({
        "success": True,
        "message": message,
        "data": data if data is not None else {}
    }, status=status_code)