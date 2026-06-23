"""
AI 智能客服知识库与客情预警系统 — Flask 后端入口
"""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request

import config
from services.knowledge_base import KnowledgeBase
from services.llm_service import LLMService
from services.sentiment_analyzer import SentimentAnalyzer

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY

kb = KnowledgeBase()
llm = LLMService()
sentiment_analyzer = SentimentAnalyzer()

# 启动时预加载 knowledge/ 目录下的文件
kb.reload()


def build_llm_system_instructions(
    has_local_files: bool,
    has_relevant_hits: bool,
    sentiment_hint: str = "",
) -> str:
    """根据本地文件加载与检索结果，生成不同的系统提示词。"""
    lines = ["你是一名专业、友善的 AI 智能客服助手。"]

    if has_local_files:
        lines.extend([
            "下方【本地参考知识】中包含公司报价表等文件内容，这是你回答业务问题的首要依据。",
            "当用户询问价格、规格、套餐、服务内容等信息时，必须优先从本地文件中查找并准确引用，不得编造。",
            "若本地文件中确实没有相关信息，再运用你的通用知识作答，并说明该信息未在报价表中找到。",
            "回答简洁清晰，使用中文。",
        ])
        if has_relevant_hits:
            lines.append("已为你标注检索到的相关片段，请优先参考这些片段作答。")
    elif has_relevant_hits:
        lines.extend([
            "请优先基于下方【本地参考知识】中的内置 FAQ 内容回答，确保与官方政策一致。",
            "回答简洁清晰，使用中文，不超过 200 字。",
        ])
    else:
        lines.extend([
            "当前未加载本地报价表文件，也未匹配到相关知识条目。",
            "请直接运用你的通用知识与能力作答，不要以「没有资料」为由拒绝或敷衍用户。",
            "你可以回答日常提问、常识问题，也可以完成创作请求（如写诗、写文案、讲笑话等）。",
            "仅当用户需要处理具体订单、退款、账户密码等业务操作时，再礼貌建议联系人工客服或提供订单号。",
            "回答简洁清晰，使用中文。",
        ])

    if sentiment_hint:
        lines.append(f"\n【客情提示】{sentiment_hint}")

    return "\n".join(lines)


@app.route("/")
def index():
    """渲染用户对话页面。"""
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    核心对话接口。

    请求体: {"message": "用户问题", "session_id": "可选"}
    响应体: {
        "reply": "AI 回复",
        "knowledge_hits": [...],
        "sentiment": {...},
        "meta": {"source": "mock|api", "latency_ms": 123}
    }
    """
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400

    # 1. 客情预警分析
    sentiment = sentiment_analyzer.analyze(user_message)
    sentiment_hint = ""
    if sentiment.level == "critical":
        sentiment_hint = "高风险客情，客户情绪激动，请优先安抚并建议转人工。"
    elif sentiment.level == "warning":
        sentiment_hint = "客户情绪偏负面，请注意语气温和、积极解决问题。"

    # 2. 知识库检索（每次提问重新读取 knowledge/ 目录）
    knowledge_context, has_local_files, has_relevant_hits, faq_hits, file_hits = kb.build_context(
        user_message
    )
    system_instructions = build_llm_system_instructions(
        has_local_files,
        has_relevant_hits,
        sentiment_hint,
    )

    # 3. 调用大模型（或 Mock）
    llm_result = llm.chat(
        user_message,
        knowledge_context,
        system_instructions=system_instructions,
    )

    return jsonify({
        "reply": llm_result["reply"],
        "knowledge_hits": [
            {
                "id": item.id,
                "category": item.category,
                "question": item.question,
                "answer": item.answer,
                "source": item.source,
            }
            for item in faq_hits
        ],
        "file_hits": [
            {
                "filename": hit.filename,
                "excerpt": hit.excerpt,
                "score": hit.score,
            }
            for hit in file_hits
        ],
        "sentiment": {
            "level": sentiment.level,
            "score": sentiment.score,
            "triggers": sentiment.triggers,
            "suggestion": sentiment.suggestion,
        },
        "meta": {
            "source": llm_result["source"],
            "latency_ms": llm_result["latency_ms"],
            "local_files": kb.loaded_filenames(),
            "has_local_files": has_local_files,
        },
    })


@app.route("/api/health", methods=["GET"])
def health():
    """健康检查。"""
    return jsonify({
        "status": "ok",
        "mock_mode": config.LLM_MOCK_MODE,
        "llm_provider": "deepseek" if config.DEEPSEEK_API_KEY else "none",
        "llm_model": config.LLM_MODEL,
        "llm_configured": bool(config.DEEPSEEK_API_KEY),
        "knowledge_dir": str(config.KNOWLEDGE_DIR),
        "local_files": kb.loaded_filenames(),
        "knowledge_count": len(kb.items),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
