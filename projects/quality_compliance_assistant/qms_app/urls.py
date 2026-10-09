from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'recalls', views.RecallViewSet)
router.register(r'capas', views.CapaViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('agent/chat/', views.agent_chat, name='agent-chat'),
    path('agent/complaint-analyze/', views.complaint_analyze, name='complaint-analyze'),
]
