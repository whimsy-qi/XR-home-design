# ai_generator/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings
import uuid
import os

from django_oss_storage.backends import OssMediaStorage
from .tasks import generate_3d_model_from_image_via_meshy_task,generate_text_to_3d_via_meshy_task  # 确保导入了Celery任务
from .models import AIGenerationTask  # 确保导入了模型


class AIImageTo3DView(APIView):  # <--- 确保这个类名和定义存在
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        source_image_file = request.FILES.get('source_image')
        asset_name = request.data.get('name', 'AI Generated Model')
        asset_description = request.data.get('description', 'AI generated 3D model from image.')

        generation_params = {
            "enable_pbr": request.data.get("enable_pbr", "true").lower() == 'true',  # 处理字符串'true'/'false'
            "should_remesh": request.data.get("should_remesh", "true").lower() == 'true',
            "should_texture": request.data.get("should_texture", "true").lower() == 'true',
            "ai_model": request.data.get("ai_model", "meshy-4"),
        }
        generation_params = {k: v for k, v in generation_params.items() if v is not None}

        if not source_image_file:
            return Response({"error": "必须提供源图片 (source_image)。"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            storage = OssMediaStorage()
            file_ext = os.path.splitext(source_image_file.name)[1]
            source_image_oss_path_key = f"ai_source_images/{request.user.id}/{uuid.uuid4()}{file_ext}"
            saved_image_key = storage.save(source_image_oss_path_key, source_image_file)
            clean_source_image_oss_url = storage.url(saved_image_key)
            print(f"Source image for AI generation uploaded to user's OSS: {clean_source_image_oss_url}")
        except Exception as e:
            print(f"Error uploading source image to user's OSS: {e}")
            return Response({"error": f"处理用户上传的源图片失败: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        ai_task_record = AIGenerationTask.objects.create(
            user=request.user,
            task_type=AIGenerationTask.AITaskType.IMAGE_TO_3D,
            source_image_url_for_ai=clean_source_image_oss_url,
            generation_params=generation_params,
            status=AIGenerationTask.AITaskStatus.PENDING
        )
        print(f"Created AIGenerationTask record with ID: {ai_task_record.id}")

        celery_task_instance = generate_3d_model_from_image_via_meshy_task.delay(
            user_id=request.user.id,
            source_image_oss_url=clean_source_image_oss_url,
            generation_params=generation_params,
            ai_generation_record_id=str(ai_task_record.id)
        )

        ai_task_record.celery_task_id = celery_task_instance.id
        ai_task_record.save(update_fields=['celery_task_id'])

        return Response(
            {"message": "AI图像生成3D模型任务已启动。",
             "ai_task_tracker_id": str(ai_task_record.id),
             "celery_task_id": celery_task_instance.id},
            status=status.HTTP_202_ACCEPTED
        )



def get_boolean_param(data, param_name, default_value=True):
    """
    从请求数据中获取布尔参数，能处理字符串 "true"/"false" (不区分大小写) 和实际布尔值。
    """
    value = data.get(param_name)
    if value is None: # 如果前端没有发送这个参数
        return default_value
    if isinstance(value, bool): # 如果前端发送的是JSON布尔值 true/false
        return value
    if isinstance(value, str): # 如果前端发送的是字符串
        return value.lower() == 'true'
    # 对于其他意外类型，可以返回默认值或抛出错误，这里返回默认值
    return default_value


# ai_generator/views.py
# ...
class AITextTo3DView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        prompt = request.data.get('prompt')
        if not prompt:
            return Response({"error": "必须提供文本提示 (prompt)。"}, status=status.HTTP_400_BAD_REQUEST)

        asset_name = request.data.get('name', f"AI Text-3D: {prompt[:30]}")
        asset_description = request.data.get('description', f"AI generated 3D model from text: '{prompt}'.")

        meshy_params = {
            "art_style": request.data.get("art_style", "realistic"),
            "negative_prompt": request.data.get("negative_prompt", "low quality, low poly, ugly, deformed"),
            # 使用新的辅助函数处理布尔参数
            "should_remesh": get_boolean_param(request.data, "should_remesh", True),
            "ai_model": request.data.get("ai_model", "meshy-4"),
            "topology": request.data.get("topology", "triangle"),
            # target_polycount 需要是整数
            "target_polycount": int(request.data.get("target_polycount", 30000) or 30000),
            "symmetry_mode": request.data.get("symmetry_mode", "auto"),
            # 使用新的辅助函数处理布尔参数
            "enable_pbr": get_boolean_param(request.data, "enable_pbr", True),
            "texture_prompt": request.data.get("texture_prompt", prompt)
            # "texture_image_url": request.data.get("texture_image_url") # 如果前端提供
        }
        # 清理掉值为None的参数 (如果get_boolean_param返回None，则不会被包含)
        meshy_params_cleaned = {k: v for k, v in meshy_params.items() if v is not None}

        # 创建AI生成任务记录
        ai_task_record = AIGenerationTask.objects.create(
            user=request.user,
            task_type=AIGenerationTask.AITaskType.TEXT_TO_3D_PREVIEW,
            text_prompt=prompt,
            generation_params=meshy_params_cleaned, # 使用清理后的参数
            status=AIGenerationTask.AITaskStatus.PENDING
        )
        print(f"Created AIGenerationTask record for Text-to-3D with ID: {ai_task_record.id}")

        celery_task_instance = generate_text_to_3d_via_meshy_task.delay(
            user_id=request.user.id,
            prompt=prompt,
            asset_name=asset_name,
            asset_description=asset_description,
            meshy_params=meshy_params_cleaned, # 传递清理后的参数
            ai_generation_record_id=str(ai_task_record.id)
        )

        ai_task_record.celery_task_id = celery_task_instance.id
        ai_task_record.save(update_fields=['celery_task_id'])

        return Response(
            {"message": "AI文本生成3D模型任务已启动（预览阶段）。",
             "ai_task_tracker_id": str(ai_task_record.id),
             "celery_task_id": celery_task_instance.id},
            status=status.HTTP_202_ACCEPTED
        )