# main/admin.py

from django.contrib import admin
from .models import DesignProject, Room, Asset, DesignLayout, Material, DesignBackpack,SceneSnapshot

@admin.register(DesignProject)
class DesignProjectAdmin(admin.ModelAdmin):
    """
    设计项目的后台管理配置
    """
    list_display = ('id', 'name', 'user', 'is_public', 'created_at')
    search_fields = ('id', 'name', 'description', 'user__username')
    list_filter = ('is_public', 'created_at')
    # 使用 autocomplete_fields 替代 raw_id_fields，用户体验更好
    autocomplete_fields = ('user',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """
    房间的后台管理配置
    """
    list_display = ('name', 'design_project', 'room_type')
    search_fields = ('name', 'design_project__name')
    list_filter = ('room_type',)
    # 使用 autocomplete_fields 替代 raw_id_fields
    autocomplete_fields = ('design_project',)
    # 根据之前的需求，在表单中隐藏不需要填写的 'dimensions' 字段
    exclude = ('dimensions',)

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """
    资产的后台管理配置
    """
    list_display = ('id', 'name', 'asset_type', 'user', 'source_type', 'created_at')
    search_fields = ('id', 'name', 'description', 'user__username')
    list_filter = ('asset_type', 'source_type', 'user', 'created_at')
    # 使用 autocomplete_fields 替代 raw_id_fields
    autocomplete_fields = ('user',)
    # 在编辑页将自动生成的字段设为只读
    readonly_fields = ('id', 'created_at', 'updated_at', 'file_url', 'thumbnail_url')


@admin.register(DesignLayout)
class DesignLayoutAdmin(admin.ModelAdmin):
    # 在 list_display 的最后加上我们自定义的 'get_project_user'
    # 1. 将 'room' 替换为 'scene_snapshot'
    list_display = ('id', 'scene_snapshot', 'asset', 'position', 'scale')
    # 2. 更新搜索字段，以通过新的关系链进行搜索
    search_fields = ('scene_snapshot__name', 'scene_snapshot__room__name', 'asset__name')
    # 3. 将 'room' 替换为 'scene_snapshot'
    autocomplete_fields = ('scene_snapshot', 'asset')

    # 我们自定义的方法
    @admin.display(description='所属用户')  # 设置列的显示名称
    def get_project_user(self, obj):
        # 通过 obj.room.design_project.user 访问到最终的用户
        if obj.room and obj.room.design_project and obj.room.design_project.user:
            return obj.room.design_project.user.username
        return "N/A"  # 处理无用户的情况

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    """
    材质的后台管理配置
    """
    list_display = ('name', 'material_type', 'texture_map_url')
    search_fields = ('name',)
    list_filter = ('material_type',)

@admin.register(DesignBackpack)
class DesignBackpackAdmin(admin.ModelAdmin):
    """
    设计背包的后台管理配置
    """
    list_display = ('user', 'asset', 'added_at')
    search_fields = ('user__username', 'asset__name')
    # 使用 autocomplete_fields 替代 raw_id_fields
    autocomplete_fields = ('user', 'asset')

@admin.register(SceneSnapshot)
class SceneSnapshotAdmin(admin.ModelAdmin):
    """
    场景快照的后台管理配置
    """
    list_display = ('id', 'name', 'room', 'user', 'created_at', 'snapshot_image_url')
    search_fields = ('id', 'name', 'room__name', 'user__username')
    list_filter = ('created_at', 'user', 'room')
    # 为了方便在后台直接创建或编辑快照，也给它的外键加上搜索框
    autocomplete_fields = ('room', 'user')