"""大模型服务 — 支持 Mock 模式与 DeepSeek API 调用。"""

from __future__ import annotations

import random
import time
from typing import Any

import requests

import config


class LLMService:
    """封装大模型调用逻辑。"""

    def __init__(self) -> None:
        self.mock_mode = config.LLM_MOCK_MODE
        self.api_key = config.DEEPSEEK_API_KEY or config.LLM_API_KEY
        self.api_base = config.LLM_API_BASE
        self.model = config.LLM_MODEL

    def chat(
        self,
        user_message: str,
        knowledge_context: str,
        system_instructions: str = "",
    ) -> dict[str, Any]:
        """
        生成客服回复。

        Returns:
            {"reply": str, "source": "mock"|"api", "latency_ms": int}
        """
        start = time.time()

        if self.mock_mode or not self.api_key:
            reply = self._mock_reply(user_message, knowledge_context, system_instructions)
            source = "mock"
        else:
            reply = self._call_deepseek_api(user_message, knowledge_context, system_instructions)
            source = "api"

        latency_ms = int((time.time() - start) * 1000)
        return {"reply": reply, "source": source, "latency_ms": latency_ms}

    def _build_system_prompt(self, knowledge_context: str, system_instructions: str) -> str:
        instructions = system_instructions or (
            "你是一名专业、友善的 AI 智能客服助手。"
            "请优先基于知识库内容回答；若无匹配条目，可运用通用知识直接作答。"
        )
        return f"{instructions}\n\n【本地参考知识】\n{knowledge_context}"

    def _mock_reply(
        self,
        user_message: str,
        knowledge_context: str,
        system_instructions: str,
    ) -> str:
        """模拟大模型响应，带轻微随机延迟感。"""
        time.sleep(random.uniform(0.3, 0.8))

        if "未加载任何本地知识文件" in knowledge_context or "未匹配到相关知识库条目" in knowledge_context:
            if "创作请求" in system_instructions or "通用知识" in system_instructions:
                return (
                    f"（Mock 模式）关于「{user_message[:30]}」，"
                    "我会直接用通用能力来回答。接入真实 API 后可获得完整回复。"
                )
            return "您好！我是 AI 智能客服，请问有什么可以帮您？"

        if system_instructions and "高风险" in system_instructions:
            return (
                "非常抱歉给您带来了不好的体验，我完全理解您的心情。"
                "我已为您标记优先处理，并通知人工客服专员尽快与您联系。"
                "请留下您的订单号，我们会第一时间跟进。"
            )

        # 从知识库上下文中提取回答
        if "A: " in knowledge_context:
            first_answer = knowledge_context.split("A: ", 1)[1].split("\n")[0].strip()
            prefixes = [
                "您好！根据我们的服务政策，",
                "感谢您的提问！",
                "很高兴为您解答：",
            ]
            suffixes = [
                " 如还有其他问题，欢迎继续咨询。",
                " 如需进一步帮助，请随时告诉我。",
            ]
            return random.choice(prefixes) + first_answer + random.choice(suffixes)

        return "您好！我是 AI 智能客服，请问有什么可以帮您？"

    def _call_deepseek_api(
        self,
        user_message: str,
        knowledge_context: str,
        system_instructions: str,
    ) -> str:
        """调用 DeepSeek Chat Completions API。"""
        try:
            system_prompt = self._build_system_prompt(knowledge_context, system_instructions)
            url = f"{self.api_base.rstrip('/')}/chat/completions"
            response = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 512,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

        except Exception as exc:
            return f"（API 调用失败，已降级为本地应答）抱歉，系统暂时繁忙：{exc}"
