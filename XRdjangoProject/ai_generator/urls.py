# ai_generator/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('image-to-3d/', views.AIImageTo3DView.as_view(), name='ai_image_to_3d'),
    # 后续为 Text-to-3D, Multi-image-to-3D, Text-to-Texture 添加各自的View和URL
    path('text-to-3d/', views.AITextTo3DView.as_view(), name='ai_text_to_3d'),
    # ...
]
