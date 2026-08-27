# ai_generator/tools.py
from langchain.tools import tool
from typing import Literal

# ==============================================================================
#  【最终优化版】核心工具集定义
# ==============================================================================
#  说明：本文件中的所有工具描述（docstring）都经过了强化，
#  旨在为AI提供更明确、更强硬的行为准则，以确保它优先、准确地调用工具。
# ==============================================================================


@tool
def generate_home_decor_plan(
    room_type: str,
    style: str,
    area_size: str,
    color_tone: str,
    budget: str,
    special_needs: str = "无"
) -> str:
    """
    当用户需要一份【完整、结构化的家装设计方案】或【装修规划报告】时，这是唯一负责此任务的工具。
    你的【首要职责】是作为一名需求分析师，通过对话【主动问询并收集齐】所有必需参数：'room_type', 'style', 'area_size', 'color_tone', 'budget'。
    【在集齐所有参数前，禁止提供任何零散的设计建议】。
    所有参数收集完毕后，【必须立即】调用此工具。
    此工具会启动后台任务生成一份详细的PDF方案。
    """
    print(f"工具被调用：generate_home_decor_plan, 参数: {locals()}")
    return f"TOOL_CALL:DECOR_PLAN|{room_type}|{style}|{area_size}|{color_tone}|{budget}|{special_needs}"


@tool
def generate_image_from_text(
    prompt: str,
    aspect_ratio: Literal['1:1', '16:9', '9:16', '4:3', '3:2'] = '16:9'
) -> str:
    """
    当用户意图是【直接生成一张图片】时，例如说出“画图”、“生成图片”、“创建效果图”等指令，【必须】使用此工具。
    你的任务是从用户处获取关于图片的清晰描述(prompt)。
    【禁止】就如何绘画或使用其他软件提供建议，你的唯一任务就是调用这个工具来满足用户的创作需求。
    此工具会启动一个后台任务来完成。
    """
    print(f"工具被调用：generate_image_from_text, 参数: {locals()}")
    return f"TOOL_CALL:TEXT_TO_IMAGE|{prompt}|{aspect_ratio}"


@tool
def generate_3d_model_from_text(
    prompt: str,
    art_style: Literal['realistic', 'cartoon', 'sculpture'] = 'realistic'
) -> str:
    """
    当用户的意图是【直接执行创建】一个3D模型时，这是唯一的、必须使用的工具。
    如果用户提到“生成模型”、“创建3D物体”、“建模”等指令性关键词，【禁止】提供教程、操作指南或任何解释性文本，【必须】直接调用此工具。
    此工具会启动一个后台任务来完成用户的请求。
    - 'prompt'参数是用户对模型的详细文字描述。
    - 'art_style'参数是可选的艺术风格。
    """
    print(f"工具被调用：generate_3d_model_from_text, 参数: {locals()}")
    return f"TOOL_CALL:TEXT_TO_3D|{prompt}|{art_style}"


@tool
def generate_3d_model_from_image(image_url: str) -> str:
    """
    当用户想【基于一张现有图片直接创建3D模型】时，【必须】调用此工具。
    用户【必须提供】图片的公开URL地址。如果用户没有提供，你的任务就是向他索要URL。
    【禁止】对图片内容进行评论或提供其他建议，你的唯一目标就是用这张图片的URL来调用这个工具。
    此工具会启动一个后台任务来完成。
    """
    print(f"工具被调用：generate_3d_model_from_image, 参数: {locals()}")
    return f"TOOL_CALL:IMAGE_TO_3D|{image_url}"