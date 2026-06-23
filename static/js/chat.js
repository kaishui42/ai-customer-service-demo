/**
 * AI 智能客服 — 前端对话交互逻辑
 */

(function () {
  "use strict";

  const chatMessages = document.getElementById("chatMessages");
  const messageInput = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const sentimentBadge = document.getElementById("sentimentBadge");
  const sentimentDetail = document.getElementById("sentimentDetail");
  const sentimentTriggers = document.getElementById("sentimentTriggers");
  const knowledgeHits = document.getElementById("knowledgeHits");

  const SENTIMENT_LABELS = {
    normal: "客情正常",
    warning: "客情预警",
    critical: "高风险客情",
  };

  /** 初始化快捷问题按钮 */
  document.querySelectorAll(".quick-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      messageInput.value = btn.dataset.question;
      messageInput.focus();
      sendMessage();
    });
  });

  /** 发送按钮 & Enter 快捷键 */
  sendBtn.addEventListener("click", sendMessage);
  messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  /** 自动调整输入框高度 */
  messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
  });

  async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    appendMessage("user", text);
    messageInput.value = "";
    messageInput.style.height = "auto";
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      const data = await res.json();

      if (!res.ok) {
        appendMessage("bot", data.error || "请求失败，请稍后重试。");
        return;
      }

      const meta = data.meta
        ? ` · ${data.meta.source === "mock" ? "模拟" : "API"} · ${data.meta.latency_ms}ms`
        : "";
      appendMessage("bot", data.reply, meta);
      updateSentiment(data.sentiment);
      updateKnowledgeHits(data.knowledge_hits);
    } catch (err) {
      appendMessage("bot", "网络异常，请检查后端服务是否已启动。");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function appendMessage(role, content, meta) {
    const welcome = chatMessages.querySelector(".welcome-card");
    if (welcome) welcome.remove();

    const div = document.createElement("div");
    div.className = `message ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "user" ? "我" : "AI";

    const body = document.createElement("div");
    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = content;
    body.appendChild(bubble);

    if (meta) {
      const metaEl = document.createElement("div");
      metaEl.className = "message-meta";
      metaEl.textContent = meta;
      body.appendChild(metaEl);
    }

    div.appendChild(avatar);
    div.appendChild(body);
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function setLoading(loading) {
    sendBtn.disabled = loading;
    messageInput.disabled = loading;

    const existing = document.getElementById("typingIndicator");
    if (loading) {
      if (!existing) {
        const div = document.createElement("div");
        div.id = "typingIndicator";
        div.className = "message bot";
        div.innerHTML = `
          <div class="message-avatar">AI</div>
          <div class="message-bubble">
            <div class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>`;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }
    } else if (existing) {
      existing.remove();
    }
  }

  function updateSentiment(sentiment) {
    if (!sentiment) return;

    const level = sentiment.level || "normal";
    sentimentBadge.className = `sentiment-badge ${level}`;
    sentimentBadge.textContent = SENTIMENT_LABELS[level] || level;
    sentimentDetail.textContent = sentiment.suggestion || "";

    sentimentTriggers.innerHTML = "";
    (sentiment.triggers || []).forEach((t) => {
      const tag = document.createElement("span");
      tag.className = "trigger-tag";
      tag.textContent = t;
      sentimentTriggers.appendChild(tag);
    });
  }

  function updateKnowledgeHits(hits) {
    knowledgeHits.innerHTML = "";

    if (!hits || hits.length === 0) {
      knowledgeHits.innerHTML =
        '<p class="empty-hint">暂无匹配的知识库条目</p>';
      return;
    }

    hits.forEach((item) => {
      const div = document.createElement("div");
      div.className = "kb-item";
      div.innerHTML = `
        <div class="kb-category">${escapeHtml(item.category)}</div>
        <div class="kb-question">${escapeHtml(item.question)}</div>
        <div class="kb-answer">${escapeHtml(item.answer)}</div>`;
      knowledgeHits.appendChild(div);
    });
  }

  function escapeHtml(str) {
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" };
    return String(str).replace(/[&<>"']/g, (c) => map[c]);
  }
})();
