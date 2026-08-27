# main/models.py
from django.db import models
from django.conf import settings  # 确保导入settings
from accounts.models import CustomUser  # 导入自定义用户模型
import uuid
from django.utils import timezone  # 确保导入timezone


class DesignProject(models.Model):
    """
    用户创建的整体设计项目。
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name='项目名称')
    description = models.TextField(blank=True, verbose_name='项目描述')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='design_projects',
                             verbose_name='项目所有者')
    thumbnail_url = models.URLField(max_length=1024, blank=True, null=True, verbose_name='项目缩略图URL')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_public = models.BooleanField(default=False, verbose_name='是否公开')

    class Meta:
        verbose_name = '设计项目'
        verbose_name_plural = '设计项目'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Room(models.Model):
    """
    DesignProject中的一个房间。
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    design_project = models.ForeignKey(DesignProject, on_delete=models.CASCADE, related_name='rooms',
                                       verbose_name='所属设计项目')
    name = models.CharField(max_length=255, verbose_name='房间名称')
    room_type = models.CharField(max_length=100, verbose_name='房间类型', help_text='例如: 客厅, 卧室, 厨房')

    class Meta:
        verbose_name = '房间'
        verbose_name_plural = '房间'
        unique_together = ('design_project', 'name')  # 同一项目下房间名唯一

    def __str__(self):
        return f"{self.design_project.name} - {self.name}"


# +++ 新增 AssetSource 枚举类 +++
class AssetSource(models.TextChoices):
    UPLOADED = 'UPLOADED', '用户上传'
    AI_TEXT_TO_3D = 'AI_TXT_3D', 'AI文本生成3D'
    AI_IMAGE_TO_3D = 'AI_IMG_3D', 'AI单图生成3D'
    AI_MULTI_IMAGE_TO_3D = 'AI_MULTI_IMG_3D', 'AI多图生成3D'
    # 如果有AI生成的纹理，可能需要新的类型或在Material模型中处理
    # AI_TEXT_TO_TEXTURE = 'AI_TXT_TEX', 'AI文本生成纹理'

class SceneSnapshot(models.Model):
    """
    代表一个房间在特定时间点的一个已保存的设计方案版本/快照。
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='snapshots', verbose_name='所属房间')
    name = models.CharField(max_length=255, verbose_name='快照名称')
    snapshot_image_url = models.URLField(max_length=1024, blank=True, null=True, verbose_name='快照图片URL')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='scene_snapshots', verbose_name='快照所有者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '场景快照'
        verbose_name_plural = '场景快照'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.room.name} - {self.name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"



class Asset(models.Model):
    """
    所有3D模型（家具、建筑风格、材质等）的抽象基类或父类。
    """

    class AssetType(models.TextChoices):
        FURNITURE = 'FURNITURE', '家具'
        MATERIAL = 'MATERIAL', '材质'
        LIGHTING = 'LIGHTING', '灯光'
        ARCHITECTURAL_STYLE = 'ARCH_STYLE', '建筑风格'
        IMAGE = 'IMAGE', '图片'
        MODEL_3D = 'MODEL_3D', '3D模型'
        OTHER = 'OTHER', '其他'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name='资产名称')
    description = models.TextField(blank=True, verbose_name='资产描述')
    # --- 修改：URLField 长度建议增加到1024以适应可能较长的签名URL或复杂路径 ---
    file_url = models.URLField(max_length=1024, blank=True, null=True, verbose_name='文件URL')
    thumbnail_url = models.URLField(max_length=1024, blank=True, null=True, verbose_name='缩略图URL')

    asset_type = models.CharField(
        max_length=20,  # 原来是50，根据choices调整
        choices=AssetType.choices,
        default=AssetType.MODEL_3D,  # 修改默认值为更通用的MODEL_3D
        verbose_name="资产类型"
    )
    metadata = models.JSONField(default=dict, blank=True, null=True, verbose_name="元数据")  # 允许metadata为空
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_assets',  # 新增 related_name
        verbose_name="所属用户"  # 修改 verbose_name
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    # --- 新增字段以支持AI生成信息 ---
    source_type = models.CharField(
        max_length=20,  # 确保长度足够容纳choices中的键
        choices=AssetSource.choices,
        default=AssetSource.UPLOADED,
        verbose_name='资产来源'
    )
    # 用于存储触发AI生成的原始输入信息 (例如文本提示，或源图片在您OSS上的URL列表)
    source_reference_input = models.JSONField(default=dict, blank=True, null=True, verbose_name='来源参考输入')
    # 用于存储Meshy AI返回的任务ID
    external_ai_task_id = models.CharField(max_length=255, blank=True, null=True, db_index=True,
                                           verbose_name='外部AI任务ID')
    # (可选) 记录生成该资产时使用的Meshy AI模型版本
    ai_model_used = models.CharField(max_length=50, blank=True, null=True, verbose_name='使用的AI模型')

    # --- 新增字段结束 ---

    # ASSET_TYPE_CHOICES = AssetType.choices # 这行通常不需要在模型中定义为类属性，choices已在字段中指定

    class Meta:
        verbose_name = '资产'
        verbose_name_plural = '资产'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_asset_type_display()})"  # 使用get_..._display()更友好


class DesignLayout(models.Model):
    """
    记录在“场景快照”中摆放的资产实例。
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # --- 这是关键改动：删除 room 字段，添加 scene_snapshot 字段 ---
    # room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='layouts', verbose_name='所属房间') # <--- 删除或注释掉这一行
    scene_snapshot = models.ForeignKey(SceneSnapshot, on_delete=models.CASCADE, related_name='layouts',
                                       verbose_name='所属快照', null=True)

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='layouts', verbose_name='放置资产')
    position = models.JSONField(default=dict, verbose_name='位置 (x,y,z)')
    rotation = models.JSONField(default=dict, verbose_name='旋转 (四元数或欧拉角)')
    scale = models.JSONField(default=dict, verbose_name='缩放 (x,y,z)')


    class Meta:
        verbose_name = '设计布局'
        verbose_name_plural = '设计布局'


    def __str__(self):
        return f"Layout in {self.scene_snapshot.name}: {self.asset.name}"

class Material(models.Model):
    """
    材质模型，供资产覆盖使用。
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name='材质名称')
    # --- 修改：URLField 长度建议增加到1024 ---
    texture_map_url = models.URLField(max_length=1024, blank=True, null=True, verbose_name='漫反射纹理图URL')
    normal_map_url = models.URLField(max_length=1024, blank=True, null=True, verbose_name='法线贴图URL')
    roughness_map_url = models.URLField(max_length=1024, blank=True, null=True, verbose_name='粗糙度贴图URL')
    material_type = models.CharField(max_length=100, verbose_name='材质类型',
                                     choices=[('wood', '木材'), ('metal', '金属'), ('fabric', '织物'),
                                              ('glass', '玻璃'), ('other', '其他')])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '材质'
        verbose_name_plural = '材质'
        ordering = ['name']

    def __str__(self):
        return self.name


class DesignBackpack(models.Model):
    """
    代表用户收藏的自定义和AI生成模型的集合。
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='design_backpack_items',
                             verbose_name='用户')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='in_backpacks', verbose_name='收藏资产')
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')

    class Meta:
        verbose_name = '设计背包'
        verbose_name_plural = '设计背包'
        unique_together = ('user', 'asset')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username}'s backpack: {self.asset.name}"

