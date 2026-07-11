from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Capsule
from .serializers import CapsuleSerializer
from .permissions import IsOwner
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class CapsuleViewSet(viewsets.ModelViewSet):
    serializer_class = CapsuleSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        queryset = Capsule.objects.filter(user=user)
        
        include_locked = self.request.query_params.get('include_locked', 'false').lower() == 'true'
        
        if not include_locked:
            # Filter where unlock_date is in the past
            queryset = queryset.filter(unlock_date__lte=timezone.now())
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .ai.search import smart_search

class SearchAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        query = request.query_params.get('q')
        if not query:
            return Response({"error": "Missing 'q' query parameter."}, status=status.HTTP_400_BAD_REQUEST)
            
        results = smart_search(request.user, query)
        return Response({"results": results})

from .ai.reflect import generate_reflection
from .models import ReflectionQuery

class ReflectAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        question = request.data.get('question')
        if not question:
            return Response({"error": "Missing 'question' in request body."}, status=status.HTTP_400_BAD_REQUEST)
            
        reflection_data = generate_reflection(request.user, question)
        
        # Log the reflection
        ReflectionQuery.objects.create(
            user=request.user,
            question=question,
            response=reflection_data["reflection"]
        )
        
        return Response(reflection_data)
from django.db.models import Count
from django.db.models.functions import TruncMonth

class MoodTrendsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Only unlocked capsules for the requesting user
        qs = Capsule.objects.filter(user=request.user, unlock_date__lte=timezone.now())
        # Truncate created_at to month and count moods
        data = qs.annotate(month=TruncMonth('created_at'))\
            .values('month', 'mood')\
            .annotate(count=Count('id'))
        result = {}
        for entry in data:
            month_key = entry['month'].strftime('%Y-%m')
            mood = entry['mood']
            count = entry['count']
            result.setdefault(month_key, {})[mood] = count
        return Response(result)

from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        user = self.request.user
        qs = Notification.objects.filter(user=user).order_by('-created_at')
        unread_only = self.request.query_params.get('unread_only', 'false').lower() == 'true'
        if unread_only:
            qs = qs.filter(is_read=False)
        return qs
