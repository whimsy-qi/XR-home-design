from rest_framework import serializers
from .models import DesignProject, Room, Asset, DesignLayout, Material, DesignBackpack,SceneSnapshot

class SceneSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = SceneSnapshot
        fields = '__all__'
        read_only_fields = ('user', 'created_at') # 用户和创建时间由后端自动设置

class DesignProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignProject
        # 将 'thumbnail_url' 添加到字段列表中
        fields = ('id', 'name', 'description', 'user', 'thumbnail_url', 'created_at', 'updated_at', 'is_public')
        read_only_fields = ('user', 'created_at', 'updated_at', 'thumbnail_url') # thumbnail_url通过专门的接口上传，设为只读
# ...
class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = '__all__'
        read_only_fields = ('user', 'file_url', 'thumbnail_url', 'created_at', 'updated_at')

class DesignLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignLayout
        # 将原来的 'room' 字段替换为 'scene_snapshot'
        fields = ('id', 'scene_snapshot', 'asset', 'position', 'rotation', 'scale')

class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = '__all__'

class DesignBackpackSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignBackpack
        fields = '__all__'
        read_only_fields = ('user',)