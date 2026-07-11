from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CapsuleViewSet, SearchAPIView, ReflectAPIView, MoodTrendsAPIView

router = DefaultRouter()
router.register(r'', CapsuleViewSet, basename='capsule')

urlpatterns = [
    path('search/', SearchAPIView.as_view(), name='capsule-search'),
    path('reflect/', ReflectAPIView.as_view(), name='capsule-reflect'),
    path('mood-trends/', MoodTrendsAPIView.as_view(), name='capsule-mood-trends'),
    path('', include(router.urls)),
]
