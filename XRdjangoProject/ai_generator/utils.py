# /ai_generator/utils.py (修正网络代理版)
from typing import Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from dashscope import Generation


class CustomChatTongyi(BaseChatModel):
    model: str = "qwen-plus"
    api_key: Optional[str] = None

    def _generate(self, messages: List[BaseMessage], **kwargs: Any) -> ChatResult:
        converted_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                converted_messages.append({'role': 'system', 'content': msg.content})
            elif isinstance(msg, HumanMessage):
                converted_messages.append({'role': 'user', 'content': msg.content})
            elif isinstance(msg, AIMessage):
                converted_messages.append({'role': 'assistant', 'content': msg.content})

        # 【核心修改】明确不使用代理
        proxies = {"http": None, "https": None}

        response = Generation.call(
            model=self.model,
            messages=converted_messages,
            api_key=self.api_key,
            result_format='message',
            proxies=proxies  # <-- 将代理设置传给SDK
        )

        if response.status_code == 200:
            content = response.output.choices[0].message.content
            message = AIMessage(content=content)
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])
        else:
            raise Exception(f"DashScope API Error: Code {response.code}, Message: {response.message}")

    @property
    def _llm_type(self) -> str:
        return "custom_chat_tongyi"