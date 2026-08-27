from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DesignProjectViewSet, RoomViewSet, AssetViewSet, DesignLayoutViewSet,
    MaterialViewSet, DesignBackpackViewSet,
    AssetUploadRequestView, AssetUploadConfirmView,SaveDesignLayoutView,SceneSnapshotCreateView
)

router = DefaultRouter()
router.register(r'design-projects', DesignProjectViewSet)
router.register(r'rooms', RoomViewSet)
router.register(r'assets', AssetViewSet)
router.register(r'layouts', DesignLayoutViewSet)
router.register(r'materials', MaterialViewSet)
router.register(r'design-backpack', DesignBackpackViewSet)

urlpatterns = [
    # ！！！之前 request-upload-url 的临时测试URL，可以保留或也用新的！！！
    path('THIS-IS-A-UNIQUE-TEST-URL-FOR-UPLOAD/', AssetUploadRequestView.as_view(), name='test_debug_upload_url_unique'),

    # ！！！为 confirm-upload 创建一个新的、唯一的URL！！！
    path('assets/finalize-asset-upload-operation/', AssetUploadConfirmView.as_view(), name='asset-finalize-upload-operation'), # <--- 新的唯一URL

    # 这是旧的覆盖式保存API，您可以暂时保留，或最终用下面的新API替代它
    path('layouts/save-scene/', SaveDesignLayoutView.as_view(), name='save-design-layout'),

    # --- 这是新的、用于版本化保存的API ---
    path('scene-snapshots/create/', SceneSnapshotCreateView.as_view(), name='scene-snapshot-create'),

    path('', include(router.urls)),

]
