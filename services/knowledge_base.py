"""知识库检索模块 — 支持本地文件 + 内置 FAQ。"""

from __future__ import annotations

from dataclasses import dataclass

import config
from services.file_knowledge_loader import FileKnowledgeHit, FileKnowledgeLoader


@dataclass
class KnowledgeItem:
    id: str
    category: str
    question: str
    answer: str
    keywords: list[str]
    source: str = "builtin"


# Demo 内置 FAQ（本地文件未覆盖时的补充）
KNOWLEDGE_ITEMS: list[KnowledgeItem] = [
    KnowledgeItem(
        id="kb-001",
        category="订单",
        question="如何查询订单物流？",
        answer="您可以在「我的订单」中点击对应订单，查看实时物流轨迹。如需人工协助，请提供订单号。",
        keywords=["物流", "快递", "发货", "订单", "配送"],
    ),
    KnowledgeItem(
        id="kb-002",
        category="退换货",
        question="如何申请退货退款？",
        answer="签收后 7 天内，进入订单详情页点击「申请售后」，选择退货退款并填写原因，审核通过后按指引寄回商品。",
        keywords=["退货", "退款", "售后", "换货", "维修"],
    ),
    KnowledgeItem(
        id="kb-003",
        category="账户",
        question="忘记密码怎么办？",
        answer="在登录页点击「忘记密码」，通过绑定手机号或邮箱验证后即可重置密码。",
        keywords=["密码", "登录", "账户", "找回", "注册"],
    ),
    KnowledgeItem(
        id="kb-004",
        category="支付",
        question="支持哪些支付方式？",
        answer="目前支持微信支付、支付宝、银联卡及企业对公转账（需联系商务开通）。",
        keywords=["支付", "付款", "微信", "支付宝", "发票"],
    ),
    KnowledgeItem(
        id="kb-005",
        category="会员",
        question="会员权益有哪些？",
        answer="会员享有专属折扣、优先客服、生日礼券及积分翻倍等权益，详情可在「会员中心」查看。",
        keywords=["会员", "积分", "权益", "VIP", "等级"],
    ),
]


class KnowledgeBase:
    """本地文件知识库 + 简易关键词 FAQ。"""

    def __init__(self, items: list[KnowledgeItem] | None = None) -> None:
        self.items = items or KNOWLEDGE_ITEMS
        self.file_loader = FileKnowledgeLoader(config.KNOWLEDGE_DIR)
        self.file_loader.reload()

    def reload(self) -> None:
        """重新加载 knowledge/ 目录下的文件。"""
        self.file_loader.reload()

    def has_local_files(self) -> bool:
        return self.file_loader.has_documents()

    def loaded_filenames(self) -> list[str]:
        return self.file_loader.filenames()

    def search(self, query: str, top_k: int = 3) -> list[KnowledgeItem]:
        """根据用户问题检索最相关的知识条目（内置 FAQ）。"""
        query_lower = query.lower()
        scored: list[tuple[int, KnowledgeItem]] = []

        for item in self.items:
            score = 0
            for kw in item.keywords:
                if kw in query or kw.lower() in query_lower:
                    score += 2
            if any(word in item.question for word in query if len(word) > 1):
                score += 1
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]

    def search_files(self, query: str, top_k: int = 8) -> list[FileKnowledgeHit]:
        return self.file_loader.search(query, top_k=top_k)

    def build_context(self, query: str) -> tuple[str, bool, bool, list[KnowledgeItem], list[FileKnowledgeHit]]:
        """
        构建大模型参考上下文。

        Returns:
            (context, has_local_files, has_relevant_hits, faq_hits, file_hits)
        """
        self.reload()

        file_hits = self.search_files(query)
        faq_hits = self.search(query)
        has_local_files = self.has_local_files()
        has_relevant_hits = bool(file_hits or faq_hits)

        parts: list[str] = []

        file_context = self.file_loader.build_reference_context(query, file_hits)
        if file_context:
            parts.append(file_context)

        if faq_hits:
            parts.append("=== 内置 FAQ 参考 ===")
            for item in faq_hits:
                parts.append(f"[{item.category}] Q: {item.question}\nA: {item.answer}")

        if not parts:
            return (
                "（未加载任何本地知识文件，也未匹配到内置 FAQ）",
                False,
                False,
                [],
                [],
            )

        return "\n\n".join(parts), has_local_files, has_relevant_hits, faq_hits, file_hits

    def format_context(self, items: list[KnowledgeItem]) -> str:
        if not items:
            return "（未匹配到相关知识库条目）"
        lines = []
        for item in items:
            lines.append(f"[{item.category}] Q: {item.question}\nA: {item.answer}")
        return "\n\n".join(lines)
