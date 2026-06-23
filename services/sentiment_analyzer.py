"""客情预警 — 基于关键词的简单情绪/风险检测（Demo）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SentimentResult:
    level: str  # normal | warning | critical
    score: float  # 0.0 ~ 1.0
    triggers: list[str]
    suggestion: str


# 负面/高风险关键词
WARNING_KEYWORDS = [
    "不满意", "失望", "投诉", "差评", "欺骗", "骗人", "垃圾",
    "太慢", "还没收到", "催", "等太久",
]

CRITICAL_KEYWORDS = [
    "起诉", "律师", "12315", "消协", "曝光", "媒体", "举报",
    "欺诈", "诈骗", "退款不到", "骗子", "工商", "报警",
]


class SentimentAnalyzer:
    """简易客情预警分析器。"""

    def analyze(self, text: str) -> SentimentResult:
        triggers: list[str] = []
        score = 0.0

        for kw in CRITICAL_KEYWORDS:
            if kw in text:
                triggers.append(kw)
                score = max(score, 0.85)

        for kw in WARNING_KEYWORDS:
            if kw in text:
                triggers.append(kw)
                score = max(score, 0.55)

        if score >= 0.8:
            level = "critical"
            suggestion = "检测到高风险客情，建议立即转接人工客服并记录工单。"
        elif score >= 0.5:
            level = "warning"
            suggestion = "客户情绪偏负面，建议优先安抚并加快处理进度。"
        else:
            level = "normal"
            suggestion = "客情正常，可继续智能应答。"

        return SentimentResult(
            level=level,
            score=round(score, 2),
            triggers=triggers,
            suggestion=suggestion,
        )
