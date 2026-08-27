import os
import uuid
from urllib.parse import urlparse
import mimetypes  # 这一行目前代码未直接使用，但可为未来潜在的文件类型检查保留

from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_oss_storage.backends import OssMediaStorage
from django.conf import settings  # 如果需要直接访问OSS配置项
from django.db.models import Q  # 用于AssetViewSet中的复杂查询
from django.db import transaction # 用于数据库事务，确保数据一致性
# 确保正确导入了您的模型和序列化器
# 如果您的模型结构不同，请调整导入路径，但 'from .models import ...' 是标准做法
from .models import (
    DesignProject, Room, Asset, DesignLayout, Material, DesignBackpack,SceneSnapshot
)
from .serializers import (
    DesignProjectSerializer, RoomSerializer, AssetSerializer,
    DesignLayoutSerializer, MaterialSerializer, DesignBackpackSerializer,SceneSnapshotSerializer
)
# 确保为 AssetUploadConfirmView 导入任务
from .tasks import generate_thumbnail_task


# --- 标准的 ModelViewSets ---
class DesignProjectViewSet(viewsets.ModelViewSet):
    queryset = DesignProject.objects.all()
    serializer_class = DesignProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 用户只能管理自己的设计项目
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        # 创建项目时自动设置所有者
        serializer.save(user=self.request.user)

    # +++ 新增的自定义action +++
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser])
    def upload_thumbnail(self, request, pk=None):
        """
        为指定的设计项目上传一个缩略图。
        客户端应发送一个包含 'thumbnail' 文件字段的 multipart/form-data 请求。
        URL: POST /api/design-projects/{project_id}/upload_thumbnail/
        """
        try:
            project = self.get_object() # 获取当前项目实例，DRF会自动处理权限和404
        except DesignProject.DoesNotExist:
            return Response({"error": "项目未找到。"}, status=status.HTTP_404_NOT_FOUND)

        thumbnail_file = request.FILES.get('thumbnail')
        if not thumbnail_file:
            return Response({"error": "必须在 'thumbnail' 字段中提供图片文件。"}, status=status.HTTP_400_BAD_REQUEST)

        # 使用 django-oss-storage 上传文件
        try:
            storage = OssMediaStorage()
            file_ext = os.path.splitext(thumbnail_file.name)[1]
            if not file_ext: file_ext = '.png' # 如果没有扩展名，给一个默认

            # 为缩略图创建一个唯一的OSS路径
            thumbnail_oss_path = f"project_thumbnails/{project.id}/{uuid.uuid4()}{file_ext}"

            saved_thumbnail_key = storage.save(thumbnail_oss_path, thumbnail_file)
            thumbnail_full_url = storage.url(saved_thumbnail_key)

            # 更新并保存项目模型的thumbnail_url字段
            project.thumbnail_url = thumbnail_full_url
            project.save(update_fields=['thumbnail_url'])

            print(f"项目 {project.id} 的缩略图已更新为: {thumbnail_full_url}")

            return Response({
                "message": "缩略图上传成功。",
                "thumbnail_url": thumbnail_full_url
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"上传项目缩略图时出错: {e}")
            return Response({"error": f"上传缩略图时发生内部错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 根据当前认证用户拥有的项目来过滤房间
        return self.queryset.filter(design_project__user=self.request.user)


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if self.action in ['list', 'retrieve']:
            # 允许用户查看自己的资产和公共资产（假设公共资产的user字段为NULL）
            # 如果您的公共资产逻辑不同，请调整 Q(user__isnull=True)
            return self.queryset.filter(Q(user=user) | Q(user__isnull=True))
        # 对于其他操作（创建、更新、删除），仅允许用户自己的资产
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        # 对于带文件上传的资产，这通常由 AssetUploadConfirmView 处理
        # 如果您允许通过此ViewSet直接创建不带上传流程的Asset，请确保设置用户
        serializer.save(user=self.request.user)


class DesignLayoutViewSet(viewsets.ModelViewSet):
    queryset = DesignLayout.objects.all()
    serializer_class = DesignLayoutSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 根据用户拥有的项目中的房间来过滤布局
        return self.queryset.filter(room__design_project__user=self.request.user)


class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]
    # 如果需要特定的基于用户的逻辑，请添加 get_queryset 或 perform_create


class DesignBackpackViewSet(viewsets.ModelViewSet):
    queryset = DesignBackpack.objects.all()
    serializer_class = DesignBackpackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# --- 资产上传视图 (已修正) ---
class AssetUploadRequestView(APIView):
    permission_classes = [IsAuthenticated]

    http_method_names = ['post', 'options', 'head','get'] # 原始计划中仅POST

    def dispatch(self, request, *args, **kwargs):
        print(f"--- AssetUploadRequestView DISPATCH ---")
        print(f"请求进入的原始方法: {request.method}")
        print(f"视图定义的 http_method_names: {self.http_method_names}")
        # DRF 会根据 http_method_names 和定义的 get(), post() 等方法计算出 allowed_methods
        print(f"视图计算出的 allowed_methods (DRF 计算的): {self.allowed_methods}")
        print(f"视图是否有 post 方法处理器: {hasattr(self, 'post')}")
        print(f"视图是否有 get 方法处理器: {hasattr(self, 'get')}")
        response = super().dispatch(request, *args, **kwargs)
        print(f"Dispatch 之后的响应状态码: {response.status_code}")
        return response

    def post(self, request, *args, **kwargs):
        print("--- AssetUploadRequestView POST method CALLED ---")  # 如果POST被允许且分发，应该能看到这个
        file_name = request.data.get('file_name')
        file_name = request.data.get('file_name')
        file_type = request.data.get('file_type')  # 例如: 'image/png', 'model/gltf-binary'

        if not file_name or not file_type:
            return Response(
                {"error": "必须提供 file_name 和 file_type。"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 基本的文件类型验证 (可以扩展)
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'model/gltf-binary', 'model/gltf+json', 'model/obj', 'model/fbx',
            'application/octet-stream'  # 通用二进制类型
        ]
        if file_type not in allowed_types:
            return Response(
                {"error": f"不支持的文件类型: {file_type}。允许的类型包括: {', '.join(allowed_types)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 为OSS生成唯一的路径/文件名
        # 示例: asset_uploads/user_id/uuid_filename.ext
        file_extension = os.path.splitext(file_name)[1]  # 获取扩展名，如 .png
        unique_filename_stem = uuid.uuid4()
        oss_filename = f"{unique_filename_stem}{file_extension}"
        oss_path = f"asset_uploads/{request.user.id}/{oss_filename}"  # OSS中的存储路径

        storage = OssMediaStorage()  # OssMediaStorage 实例
        try:
            # 使用 oss2.Bucket 对象的 sign_url 方法生成预签名URL
            presigned_url = storage.bucket.sign_url(
                method='PUT',  # 指定HTTP方法为PUT，用于上传
                key=oss_path,  # 文件在Bucket中的完整路径
                expires=3600,  # URL有效期，单位秒（这里是1小时）
                headers={'Content-Type': file_type}  # 对于PUT操作，Content-Type头通常是必要的
                # params={} # 如果需要其他参数，可以在这里添加
            )
        except Exception as e:
            # 实际生产中，应该记录更详细的错误日志
            print(f"生成预签名URL时出错: {str(e)}")
            # 返回具体的错误信息给前端，或者一个通用的错误提示
            return Response(
                {"error": f"无法生成预签名URL: {str(e)}"},  # 可以考虑不在生产中暴露详细的 e
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        # 这是文件成功上传后，在OSS上的最终访问URL
        # storage.url(oss_path) 会根据您的OSS配置（如自定义域名）生成正确的URL
        # 从已初始化的 storage 对象获取 bucket_name 和 end_point (它已经是规范化的，带 https://)
        bucket_name_from_storage = storage.bucket_name
        # 从 storage.end_point ('https://oss-cn-beijing.aliyuncs.com') 中提取域名部分 ('oss-cn-beijing.aliyuncs.com')
        endpoint_domain_part = storage.end_point.split('//', 1)[-1]

        # 确保 oss_path 在拼接时不带开头的 '/' (如果它有的话，虽然我们定义时通常不带)
        clean_oss_path = oss_path.lstrip('/')

        final_file_url = f"https://{bucket_name_from_storage}.{endpoint_domain_part}/{clean_oss_path}"

        # 有时OSS路径中的斜杠可能被URL编码为%2F，如果直接拼接，需要确保它们是字面上的斜杠
        # (通常requests或oss2库在处理时会自动处理编码，但这里是手动构造URL，以防万一)
        # final_file_url = final_file_url.replace('%2F', '/') # 这一步通常不是必须的，因为oss_path本身应该是纯路径

        print(f"调试: [AssetUploadRequestView] OSS Path: {oss_path}")
        print(f"调试: [AssetUploadRequestView] Bucket Name from Storage: {bucket_name_from_storage}")
        print(f"调试: [AssetUploadRequestView] Endpoint Domain Part: {endpoint_domain_part}")
        print(f"调试: [AssetUploadRequestView] 最终生成的 file_url: {final_file_url}")

        return Response({
            "presigned_url": presigned_url,
            "file_url": final_file_url,  # <--- 使用我们新构造的干净URL
            "oss_path": oss_path
        }, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        print("--- AssetUploadRequestView GET method CALLED ---")
        # 注意：如果 IsAuthenticated 生效，直接在浏览器未登录状态访问会看到认证错误页面
        # 您可能需要在浏览器中先登录Django Admin或通过其他方式获取会话/认证
        return Response({"message": "GET request received by AssetUploadRequestView (for browser testing)"},
                        status=status.HTTP_200_OK)

class AssetUploadConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        file_url = request.data.get('file_url')  # 客户端上传到OSS后得到的最终文件URL
        asset_name = request.data.get('name')
        asset_description = request.data.get('description', '')
        # asset_type 在 Asset 模型中是一个 choices 字段
        asset_type_key = request.data.get('asset_type')  # 例如: 'FURNITURE', 'MATERIAL'
        metadata = request.data.get('metadata', {})

        if not file_url or not asset_name or not asset_type_key:
            return Response(
                {"error": "必须提供 file_url, name, 和 asset_type。"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 验证 file_url (可选, 但推荐)
        storage = OssMediaStorage()
        # 这是一个简单的检查，可以做得更完善
        # 假设您的OSS Endpoint是标准格式
        expected_base_url_part = f"{storage.bucket_name}.{storage.end_point.replace('https://', '')}"
        if expected_base_url_part not in file_url:
            # 如果您为OSS配置了自定义域名，这里的判断逻辑需要相应调整，
            # 例如： if not file_url.startswith(settings.MEDIA_URL):
            print(f"警告: 提供的 file_url ('{file_url}') 可能与预期的OSS Bucket URL结构不符。")
            # 可以选择在这里返回错误，或者继续处理

        # 检查 asset_type_key 是否是 Asset.asset_type 的有效选项
        # 这取决于您在 models.py 中如何定义 Asset.ASSET_TYPE_CHOICES
        # 例如: ASSET_TYPE_CHOICES = [('FURNITURE', '家具'), ('MATERIAL', '材质')]
        # Asset.ASSET_TYPE_CHOICES 是一个元组列表，我们需要取出其中的key
        # 定义资产类型选项。
        # 每个元组包含一个机器可读的键（例如 'FURNITURE'）
        # 和一个人类可读的标签（例如 '家具'）。
        ASSET_TYPE_CHOICES = [
            ('FURNITURE', '家具'),
            ('MATERIAL', '材质'),
        ]
        # 从 ASSET_TYPE_CHOICES 中只提取键（每个元组的第一个元素）。
        # 这会创建一个像 ['FURNITURE', 'MATERIAL'] 这样的列表。
        valid_asset_types = [choice[0] for choice in ASSET_TYPE_CHOICES]
        if asset_type_key not in valid_asset_types:
            return Response(
                {"error": f"无效的 asset_type: '{asset_type_key}'。有效类型包括: {', '.join(valid_asset_types)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            asset = Asset.objects.create(
                name=asset_name,
                description=asset_description,
                file_url=file_url,
                asset_type=asset_type_key,  # 存储选项的键 (key)
                metadata=metadata,
                user=request.user
            )
        except Exception as e:
            print(f"保存资产到数据库时出错: {str(e)}")
            return Response(
                {"error": f"无法保存资产到数据库: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 根据文件扩展名决定是否需要生成缩略图
        # 已修正的行:
        file_extension = os.path.splitext(urlparse(file_url).path)[1].lower()

        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        model_extensions = ['.glb', '.gltf', '.obj', '.fbx','.blend']

        response_data = AssetSerializer(asset).data  # 先序列化资产数据

        if file_extension in image_extensions or file_extension in model_extensions:
            # 调用异步任务生成缩略图
            generate_thumbnail_task.delay(str(asset.id), file_url, asset.asset_type)
            response_data['thumbnail_status'] = 'generating'  # 告知客户端正在生成
            print(f"资产 {asset.id} 已创建, 缩略图任务已调用。")
        else:
            response_data['thumbnail_status'] = 'not_applicable'  # 对于不支持的文件类型
            print(f"资产 {asset.id} 已创建, 对于文件类型 {file_extension} 无需调用缩略图任务。")

        return Response(response_data, status=status.HTTP_201_CREATED)

"""624VR家具布置方案的保存"""
class SaveDesignLayoutView(APIView):
    """
    接收一个房间的完整设计布局并保存。
    此视图期望接收一个POST请求，其中包含room_id和layout_data（一个对象列表）。
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        room_id = request.data.get('room_id')
        layout_data = request.data.get('layout_data') # 期望是一个字典列表

        if not room_id or not isinstance(layout_data, list):
            return Response(
                {"error": "必须提供room_id和一个layout_data列表。"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 1. 验证用户是否拥有他们尝试保存的房间
            room = Room.objects.get(id=room_id, design_project__user=request.user)
        except Room.DoesNotExist:
            return Response({"error": "房间未找到或您没有权限。"}, status=status.HTTP_404_NOT_FOUND)

        try:
            # 使用数据库事务，确保所有操作要么全部成功，要么全部失败
            with transaction.atomic():
                # 2. 为保证数据同步，先删除此房间所有现有的布局条目
                DesignLayout.objects.filter(room=room).delete()

                # 3. 根据提供的数据创建新的布局条目
                new_layouts = []
                # 为了高效查询，一次性获取所有需要的Asset对象
                asset_ids = [item.get('asset_id') for item in layout_data if item.get('asset_id')]
                assets_in_db = Asset.objects.in_bulk([uuid.UUID(asset_id) for asset_id in asset_ids])

                for item in layout_data:
                    asset_id_str = item.get('asset_id')
                    if not asset_id_str: continue

                    asset_id_uuid = uuid.UUID(asset_id_str)
                    asset = assets_in_db.get(asset_id_uuid)

                    if not asset:
                        print(f"警告: Asset ID {asset_id_str} 未找到，跳过此项。")
                        continue

                    new_layouts.append(
                        DesignLayout(
                            room=room,
                            asset=asset,
                            position=item.get('position', {}),
                            rotation=item.get('rotation', {}),
                            scale=item.get('scale', {})
                        )
                    )

                # 4. 使用bulk_create批量创建所有新的布局对象，以提高数据库性能
                DesignLayout.objects.bulk_create(new_layouts)

        except Exception as e:
            print(f"保存布局时发生错误: {e}")
            return Response({"error": f"保存布局时发生内部错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        return Response({"message": "设计方案已成功保存！"}, status=status.HTTP_201_CREATED)


class SceneSnapshotCreateView(APIView):
    """
    创建一个新的场景快照及其包含的所有设计布局。
    这是一个“创建”操作，而不是“覆盖”。
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # 从请求数据中获取信息
        room_id = request.data.get('room_id')
        snapshot_name = request.data.get('snapshot_name')
        snapshot_image_url = request.data.get('snapshot_image_url')
        layout_data = request.data.get('layout_data')  # 依然是那个包含所有家具信息的列表

        # --- 1. 数据验证 ---
        if not all([room_id, snapshot_name, layout_data]):
            return Response({"error": "必须提供 room_id, snapshot_name, 和 layout_data。"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # 验证用户是否拥有这个房间
            room = Room.objects.get(id=room_id, design_project__user=request.user)
        except Room.DoesNotExist:
            return Response({"error": "房间未找到或您没有权限。"}, status=status.HTTP_404_NOT_FOUND)

        # --- 2. 使用数据库事务来保证数据一致性 ---
        try:
            with transaction.atomic():
                # --- 3. 创建并保存 SceneSnapshot 对象 ---
                snapshot = SceneSnapshot.objects.create(
                    room=room,
                    name=snapshot_name,
                    snapshot_image_url=snapshot_image_url,
                    user=request.user
                )

                # --- 4. 准备批量创建 DesignLayout 对象 ---
                new_layouts = []
                # 一次性获取所有需要的Asset对象，提高效率
                asset_ids = [item.get('asset_id') for item in layout_data if item.get('asset_id')]
                assets_in_db = Asset.objects.in_bulk([uuid.UUID(asset_id) for asset_id in asset_ids])

                for item in layout_data:
                    asset_id_uuid = uuid.UUID(item.get('asset_id'))
                    asset = assets_in_db.get(asset_id_uuid)
                    if not asset:
                        # 在事务中，如果一个asset找不到，整个操作会回滚，这是安全的。
                        raise ValueError(f"提供的 Asset ID {asset_id_uuid} 无效。")

                    new_layouts.append(
                        DesignLayout(
                            scene_snapshot=snapshot,  # <-- 关键：关联到新创建的快照
                            asset=asset,
                            position=item.get('position', {}),
                            rotation=item.get('rotation', {}),
                            scale=item.get('scale', {})
                        )
                    )

                # --- 5. 批量创建所有 DesignLayout 对象 ---
                if new_layouts:
                    DesignLayout.objects.bulk_create(new_layouts)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # 捕获其他可能的错误
            return Response({"error": f"保存快照时发生内部错误: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- 6. 成功后返回新创建的快照信息 ---
        serializer = SceneSnapshotSerializer(snapshot)
        return Response(serializer.data, status=status.HTTP_201_CREATED)