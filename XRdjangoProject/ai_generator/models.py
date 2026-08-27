# ai_generator/models.py
from django.db import models
from django.conf import settings  # 用于获取AUTH_USER_MODEL
import uuid


class AIGenerationTask(models.Model):
    # +++ 确保 AITaskType 枚举类在这里定义 +++
    class AITaskType(models.TextChoices):
        IMAGE_TO_3D = 'IMG_TO_3D', '图像生成3D'
        TEXT_TO_3D_PREVIEW = 'TXT_TO_3D_PRE', '文本生成3D预览'
        TEXT_TO_3D_REFINE = 'TXT_TO_3D_REF', '文本生成3D精细化'
        MULTI_IMAGE_TO_3D = 'MULTI_IMG_3D', 'AI多图生成3D'  # 新增
        TEXT_TO_TEXTURE = 'TXT_TO_TEX', 'AI文本生成纹理'  # 新增

    class AITaskStatus(models.TextChoices):
        PENDING = 'PENDING', '等待处理'  # Django端任务创建，等待Celery接收
        CELERY_RECEIVED = 'CELERY_RECEIVED', 'Celery任务已接收'  # Celery任务开始处理此记录
        AI_API_PENDING = 'AI_API_PENDING', 'AI API处理中'  # 调用AI API后，等待AI结果 (通用)
        AI_API_PREVIEW_SUCCEEDED = 'AI_API_PREVIEW_SUCCEEDED', 'AI API预览成功'  # 特指Text-to-3D的预览阶段
        AI_API_REFINING = 'AI_API_REFINING', 'AI API精细化中'  # 特指Text-to-3D的精细化阶段
        AI_API_SUCCEEDED = 'AI_API_SUCCEEDED', 'AI API处理成功'  # AI最终结果成功
        DOWNLOADING_ASSET = 'DOWNLOADING_ASSET', '下载AI生成资产中'
        UPLOADING_TO_OSS = 'UPLOADING_TO_OSS', '上传至OSS中'
        CREATING_ASSET_RECORD = 'CREATING_ASSET_RECORD', '创建资产记录中'
        TRIGGERING_THUMBNAIL = 'TRIGGERING_THUMBNAIL', '触发缩略图生成中'
        COMPLETED = 'COMPLETED', '完成'  # 整个流程成功
        FAILED = 'FAILED', '失败'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_generation_tasks',  # 修改 related_name 以区分于 Asset 中的 user
        verbose_name='用户'
    )
    # +++ 确保 task_type 字段使用了上面定义的 AITaskType +++
    task_type = models.CharField(
        max_length=20,
        choices=AITaskType.choices,
        verbose_name='AI任务类型',
        default=AITaskType.IMAGE_TO_3D
    )

    # 输入参数
    source_image_url_for_ai = models.URLField(max_length=1024, blank=True, null=True,
                                              verbose_name='提交给AI的单张源图片URL')
    source_image_urls_for_ai = models.JSONField(default=list, blank=True,
                                                verbose_name='提交给AI的多张源图片URL列表')  # 用于多图生成3D
    text_prompt = models.TextField(blank=True, null=True, verbose_name='文本提示 (用于文生3D或文生纹理)')

    # 存储传递给Meshy API的具体生成参数
    generation_params = models.JSONField(default=dict, blank=True, verbose_name='AI生成参数')

    # 外部AI服务信息
    external_ai_service_name = models.CharField(max_length=50, default="MeshyAI", verbose_name='外部AI服务名称')
    external_ai_task_id = models.CharField(max_length=255, blank=True, null=True, db_index=True,
                                           verbose_name='外部AI任务ID (例如Meshy的任务ID)')
    external_ai_preview_task_id = models.CharField(max_length=255, blank=True, null=True, db_index=True,
                                                   verbose_name='外部AI预览任务ID (用于文生3D两阶段)')

    # 我方系统信息
    celery_task_id = models.CharField(max_length=255, blank=True, null=True, unique=True, db_index=True,
                                      verbose_name='Celery任务ID')
    status = models.CharField(
        max_length=30,  # 稍微加长以容纳更长的状态键
        choices=AITaskStatus.choices,
        default=AITaskStatus.PENDING,
        verbose_name='任务状态'
    )
    progress = models.IntegerField(default=0, verbose_name='进度 (%)')  # 0-100

    # 结果信息
    meshy_result_data = models.JSONField(default=dict, blank=True, null=True, verbose_name='Meshy API原始结果')

    # 如果任务是生成新的3D模型资产
    generated_asset = models.ForeignKey(
        'main.Asset',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ai_source_task',
        verbose_name='生成的资产 (如果是模型)'
    )
    # 如果任务是生成纹理并应用于现有资产
    target_asset_for_texture = models.ForeignKey(
        'main.Asset',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ai_texture_generation_tasks',
        verbose_name='纹理目标资产 (如果是生成纹理)'
    )
    # 如果是生成独立的纹理资产（较少见，通常纹理是依附于模型的）
    # generated_texture_asset = models.ForeignKey('main.Material', on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_source_task')

    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = 'AI生成任务记录'
        verbose_name_plural = 'AI生成任务记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"AI Task {self.get_task_type_display()} ({self.id}) by {self.user.username} - {self.get_status_display()}"