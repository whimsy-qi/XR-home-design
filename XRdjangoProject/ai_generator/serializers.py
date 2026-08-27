# ai_generator/serializers.py

from rest_framework import serializers
from .models import AIGenerationTask, ChatSession, DecorPlan

class ChatSessionSerializer(serializers.ModelSerializer):
    """
    用于获取单个会话详情，包含完整的聊天记录。
    """
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'history', 'updated_at']
        read_only_fields = fields # 详情页通常是只读的

class ChatSessionListSerializer(serializers.ModelSerializer):
    """
    专门用于在侧边栏显示历史列表，不包含庞大的history字段，更高效。
    """
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'updated_at']

class DecorPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecorPlan
        # 返回所有我们需要的字段给前端
        fields = [
            'id', 'user', 'title', 'final_pdf_url',
            'generated_text_content', 'generated_image_urls', 'created_at'
        ]

class AIGenerationTaskSerializer(serializers.ModelSerializer):
    # generated_decor_plan字段是关联到最终方案的ID，任务完成时会有值
    generated_decor_plan = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = AIGenerationTask
        fields = ['id', 'status', 'progress', 'meshy_result_data', 'generated_decor_plan', 'error_message']


class AIGenerationTaskListSerializer(serializers.ModelSerializer):
    # 使用get_..._display()方法来获取人类可读的名称，而不是原始的数据库值
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AIGenerationTask
        fields = [
            'id',  # 任务ID，用于跳转到详情页
            'task_type_display',  # 任务类型（例如：“文本生成图片”）
            'status_display',  # 任务状态（例如：“已完成”）
            'text_prompt',  # 原始的提示词，方便用户回忆
            'created_at'  # 任务创建时间
        ]