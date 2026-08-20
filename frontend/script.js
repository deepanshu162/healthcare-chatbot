/**
 * HealthAI v0.2 — Frontend Application Logic with Intelligent Follow-Up Assessment
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const chatForm = document.getElementById('chatForm');
  const messageInput = document.getElementById('messageInput');
  const sendButton = document.getElementById('sendButton');
  const messagesContainer = document.getElementById('messagesContainer');
  const chatMain = document.getElementById('chatMain');
  const welcomeCard = document.getElementById('welcomeCard');
  const typingIndicator = document.getElementById('typingIndicator');
  const serverStatus = document.getElementById('serverStatus');
  const statusText = document.getElementById('statusText');
  const statusDot = serverStatus ? serverStatus.querySelector('.status-dot') : null;
  const charCounter = document.getElementById('charCounter');
  const errorToast = document.getElementById('errorToast');
  const toastMessage = document.getElementById('toastMessage');
  const toastClose = document.getElementById('toastClose');
  const clearChatButton = document.getElementById('clearChatButton');
  const infoButton = document.getElementById('infoButton');
  const infoModal = document.getElementById('infoModal');
  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const modalUnderstandBtn = document.getElementById('modalUnderstandBtn');
  const suggestionChips = document.querySelectorAll('.chip');

  // Determine API base URL
  const getApiBaseUrl = () => {
    if (window.location.protocol === 'file:' || !window.location.host) {
      return 'http://127.0.0.1:8000';
    }
    return '';
  };

  const API_BASE_URL = getApiBaseUrl();
  let isSubmitting = false;
  let currentConversationId = null;

  // --- Backend Health Check ---
  const checkBackendStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });
      if (response.ok) {
        const data = await response.json();
        if (statusDot && statusText) {
          statusDot.className = 'status-dot online';
          statusText.textContent = data.gemini_configured ? 'AI Ready' : 'Key Required';
          serverStatus.title = `Backend online (Model: ${data.model || 'Gemini'})`;
        }
      } else {
        throw new Error('Backend responded with non-200');
      }
    } catch (err) {
      if (statusDot && statusText) {
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'Offline';
        serverStatus.title = 'Cannot connect to backend. Please ensure FastAPI/Uvicorn server is running.';
      }
    }
  };

  // Run initial status check
  checkBackendStatus();
  setInterval(checkBackendStatus, 15000);

  // --- Utility: Format Time ---
  const formatCurrentTime = () => {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // --- Utility: Simple Markdown Formatter for Healthcare AI Responses ---
  const formatMarkdown = (text) => {
    if (!text) return '';

    let escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Headings (### Heading)
    escaped = escaped.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    escaped = escaped.replace(/^## (.*$)/gim, '<h2>$1</h2>');

    // Bold (**text**)
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic (*text*)
    escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Process lists and paragraphs
    const lines = escaped.split('\n');
    let inList = false;
    let listType = '';
    let result = [];

    for (let i = 0; i < lines.length; i++) {
      let line = lines[i].trim();

      if (!line) {
        if (inList) {
          result.push(listType === 'ul' ? '</ul>' : '</ol>');
          inList = false;
        }
        continue;
      }

      // Unordered list item (* or -)
      if (line.match(/^[\*\-]\s+(.*)/)) {
        if (!inList || listType !== 'ul') {
          if (inList) result.push(listType === 'ul' ? '</ul>' : '</ol>');
          result.push('<ul>');
          inList = true;
          listType = 'ul';
        }
        const itemContent = line.replace(/^[\*\-]\s+/, '');
        result.push(`<li>${itemContent}</li>`);
        continue;
      }

      // Ordered list item (1. )
      if (line.match(/^\d+\.\s+(.*)/)) {
        if (!inList || listType !== 'ol') {
          if (inList) result.push(listType === 'ul' ? '</ul>' : '</ol>');
          result.push('<ol>');
          inList = true;
          listType = 'ol';
        }
        const itemContent = line.replace(/^\d+\.\s+/, '');
        result.push(`<li>${itemContent}</li>`);
        continue;
      }

      // Normal line / paragraph
      if (inList) {
        result.push(listType === 'ul' ? '</ul>' : '</ol>');
        inList = false;
      }

      // Highlight disclaimer if detected
      if (line.toLowerCase().includes('disclaimer:') || line.toLowerCase().includes('please note: this is for informational')) {
        result.push(`<div class="disclaimer-tag">${line}</div>`);
      } else if (line.startsWith('<h3>') || line.startsWith('<h2>')) {
        result.push(line);
      } else {
        result.push(`<p>${line}</p>`);
      }
    }

    if (inList) {
      result.push(listType === 'ul' ? '</ul>' : '</ol>');
    }

    return result.join('\n');
  };

  // --- Scroll to bottom ---
  const scrollToBottom = () => {
    setTimeout(() => {
      chatMain.scrollTop = chatMain.scrollHeight;
    }, 50);
  };

  // --- Show Error Toast ---
  const showErrorToast = (msg) => {
    if (!errorToast || !toastMessage) return;
    toastMessage.textContent = msg;
    errorToast.style.display = 'flex';

    setTimeout(() => {
      hideErrorToast();
    }, 6000);
  };

  const hideErrorToast = () => {
    if (errorToast) errorToast.style.display = 'none';
  };

  if (toastClose) {
    toastClose.addEventListener('click', hideErrorToast);
  }

  // --- Append Messages ---
  const appendUserMessage = (text) => {
    if (welcomeCard) {
      welcomeCard.style.display = 'none';
    }

    const timeStr = formatCurrentTime();
    const row = document.createElement('div');
    row.className = 'message-row user-row';
    row.innerHTML = `
      <div class="message-content-wrap">
        <div class="message-meta">
          <span class="sender-name">You</span>
          <span class="message-time">${timeStr}</span>
        </div>
        <div class="message-bubble">
          ${text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}
        </div>
      </div>
      <div class="message-avatar user-avatar" title="You">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
      </div>
    `;

    messagesContainer.appendChild(row);
    scrollToBottom();
  };

  const appendAiResponse = (data) => {
    const timeStr = formatCurrentTime();
    const row = document.createElement('div');
    row.className = 'message-row ai-row';
    const messageId = 'ai-msg-' + Date.now();

    const responseType = data.response_type || 'guidance';
    const rawMessage = data.message || '';
    const questions = data.questions || [];

    // Header badge
    let badgeHtml = '';
    if (responseType === 'follow_up') {
      badgeHtml = `
        <span class="assessment-badge badge-follow-up">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
          Follow-Up Assessment
        </span>
      `;
    } else if (responseType === 'emergency') {
      badgeHtml = `
        <span class="assessment-badge badge-emergency">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/></svg>
          🚨 Urgent Emergency Advice
        </span>
      `;
    } else {
      badgeHtml = `
        <span class="assessment-badge badge-guidance">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
          General Guidance
        </span>
      `;
    }

    // Message body HTML
    let bodyHtml = `<div class="ai-content-message">${formatMarkdown(rawMessage)}</div>`;

    // Follow-up questions section — MCQ cards
    if (responseType === 'follow_up' && questions.length > 0) {
      const mcqId = 'mcq-' + Date.now();
      const selectedAnswers = new Array(questions.length).fill(null);

      // Build MCQ HTML
      const questionsHtml = questions.map((q, qIdx) => {
        const qText = typeof q === 'string' ? q : (q.question || '');
        const opts = (typeof q === 'object' && Array.isArray(q.options)) ? q.options : [];
        const optionsHtml = opts.map((opt, oIdx) => `
          <button
            class="mcq-option-btn"
            data-q="${qIdx}"
            data-o="${oIdx}"
            data-text="${opt.replace(/"/g, '&quot;')}"
            id="${mcqId}-q${qIdx}-o${oIdx}"
            type="button"
          >
            <span class="mcq-option-letter">${String.fromCharCode(65 + oIdx)}</span>
            <span class="mcq-option-text">${opt.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</span>
          </button>
        `).join('');
        return `
          <div class="mcq-question-card" id="${mcqId}-q${qIdx}">
            <div class="mcq-question-label">
              <span class="mcq-q-num">Q${qIdx + 1}</span>
              <span class="mcq-q-text">${qText.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</span>
            </div>
            <div class="mcq-options-grid">
              ${optionsHtml}
            </div>
          </div>
        `;
      }).join('');

      bodyHtml += `
        <div class="followup-mcq-container" id="${mcqId}">
          <div class="followup-intro">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
            Please select the best answer for each question below:
          </div>
          <div class="mcq-questions-list">
            ${questionsHtml}
          </div>
          <button class="mcq-submit-btn" id="${mcqId}-submit" type="button" disabled>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            Submit Answers
          </button>
        </div>
      `;

      // Attach MCQ interaction after DOM insertion (deferred)
      setTimeout(() => {
        const container = document.getElementById(mcqId);
        if (!container) return;
        const submitBtn = document.getElementById(`${mcqId}-submit`);

        const checkAllAnswered = () => selectedAnswers.every(a => a !== null);

        container.querySelectorAll('.mcq-option-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const qIdx = parseInt(btn.getAttribute('data-q'));
            const optText = btn.getAttribute('data-text');

            // Deselect siblings
            container.querySelectorAll(`.mcq-option-btn[data-q="${qIdx}"]`).forEach(b => {
              b.classList.remove('selected');
            });

            // Select this one
            btn.classList.add('selected');
            selectedAnswers[qIdx] = optText;

            // Mark question card as answered
            const card = document.getElementById(`${mcqId}-q${qIdx}`);
            if (card) card.classList.add('answered');

            // Enable submit if all answered
            if (submitBtn) submitBtn.disabled = !checkAllAnswered();
          });
        });

        const doSubmit = () => {
          if (!checkAllAnswered()) return;
          // Build a natural language reply from all selected answers
          const parts = questions.map((q, i) => {
            const qText = typeof q === 'string' ? q : (q.question || `Question ${i+1}`);
            return `${qText}: ${selectedAnswers[i]}`;
          });
          const replyText = parts.join('; ');

          // Disable MCQ after submission
          container.querySelectorAll('.mcq-option-btn').forEach(b => b.disabled = true);
          if (submitBtn) submitBtn.disabled = true;
          container.classList.add('submitted');

          handleSendMessage(replyText);
        };

        if (submitBtn) submitBtn.addEventListener('click', doSubmit);
      }, 0);
    } else if (responseType === 'emergency') {
      bodyHtml += `
        <div class="emergency-response-card">
          <h4>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/></svg>
            Immediate Action Required
          </h4>
          <p>Please contact your local emergency services or go to the nearest emergency medical facility without delay.</p>
        </div>
      `;
    }

    row.innerHTML = `
      <div class="message-avatar ai-avatar" title="HealthAI">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
          <path d="M12 5v14"/>
          <path d="M5 12h14"/>
        </svg>
      </div>
      <div class="message-content-wrap">
        <div class="message-meta">
          <span class="sender-name">HealthAI Guidance</span>
          <span class="message-time">${timeStr}</span>
        </div>
        <div class="message-bubble">
          <div class="assessment-header">
            ${badgeHtml}
          </div>
          <div class="ai-content" id="${messageId}">
            ${bodyHtml}
          </div>
          <div class="ai-actions">
            <button class="action-btn copy-btn" title="Copy response">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              Copy
            </button>
          </div>
        </div>
      </div>
    `;

    messagesContainer.appendChild(row);

    // Full copy text constructor
    let copyableText = rawMessage;
    if (questions.length > 0) {
      copyableText += '\n\n' + questions.map((q, i) => {
        const qText = typeof q === 'string' ? q : (q.question || '');
        return `${i + 1}. ${qText}`;
      }).join('\n');
    }

    const copyBtn = row.querySelector('.copy-btn');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(copyableText).then(() => {
          copyBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied!
          `;
          setTimeout(() => {
            copyBtn.innerHTML = `
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg> Copy
            `;
          }, 2000);
        }).catch(() => {
          showErrorToast('Failed to copy response to clipboard.');
        });
      });
    }

    scrollToBottom();
  };

  const appendErrorMessage = (errorText) => {
    const timeStr = formatCurrentTime();
    const row = document.createElement('div');
    row.className = 'message-row ai-row';
    row.innerHTML = `
      <div class="message-avatar ai-avatar" title="HealthAI Error">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <div class="message-content-wrap">
        <div class="message-meta">
          <span class="sender-name">HealthAI Notice</span>
          <span class="message-time">${timeStr}</span>
        </div>
        <div class="message-bubble" style="border-color: #fecaca; background-color: #fffafb;">
          <p style="color: var(--rose-600); font-weight: 500;">⚠️ ${errorText}</p>
        </div>
      </div>
    `;
    messagesContainer.appendChild(row);
    scrollToBottom();
  };

  // --- Auto-resize Textarea & Character Count ---
  const updateInputHeight = () => {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 140) + 'px';
    if (charCounter) {
      charCounter.textContent = `${messageInput.value.length}/3000`;
    }
  };

  messageInput.addEventListener('input', updateInputHeight);

  // --- Submit Handler ---
  const handleSendMessage = async (userText) => {
    const text = (userText || messageInput.value || '').trim();
    if (!text || isSubmitting) return;

    // Reset input
    messageInput.value = '';
    updateInputHeight();

    // UI state
    isSubmitting = true;
    sendButton.disabled = true;
    hideErrorToast();

    // Display user message
    appendUserMessage(text);

    // Show typing indicator
    typingIndicator.style.display = 'flex';
    scrollToBottom();

    try {
      const payload = { message: text };
      if (currentConversationId) {
        payload.conversation_id = currentConversationId;
      }

      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        const errorDetail = data.detail || 'Failed to get response from HealthAI server.';
        appendErrorMessage(errorDetail);
        showErrorToast(errorDetail);
      } else {
        // Save conversation ID
        if (data.conversation_id) {
          currentConversationId = data.conversation_id;
        }
        appendAiResponse(data);
      }
    } catch (err) {
      const networkError = 'Unable to connect to the backend server. Please verify that the FastAPI backend is running on http://127.0.0.1:8000.';
      appendErrorMessage(networkError);
      showErrorToast(networkError);
    } finally {
      typingIndicator.style.display = 'none';
      isSubmitting = false;
      sendButton.disabled = false;
      messageInput.focus();
    }
  };

  // --- Form Events ---
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    handleSendMessage();
  });

  // Enter to send (Shift+Enter for newline)
  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  // --- Suggestion Chips ---
  suggestionChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      if (prompt) {
        handleSendMessage(prompt);
      }
    });
  });

  // --- Clear Chat Button ---
  if (clearChatButton) {
    clearChatButton.addEventListener('click', () => {
      const rows = messagesContainer.querySelectorAll('.message-row');
      rows.forEach(r => r.remove());
      if (welcomeCard) {
        welcomeCard.style.display = 'flex';
      }
      currentConversationId = null;
      messageInput.value = '';
      updateInputHeight();
      messageInput.focus();
    });
  }

  // --- Info Modal ---
  if (infoButton && infoModal) {
    infoButton.addEventListener('click', () => {
      infoModal.style.display = 'flex';
    });
  }

  const closeModal = () => {
    if (infoModal) infoModal.style.display = 'none';
  };

  if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeModal);
  if (modalUnderstandBtn) modalUnderstandBtn.addEventListener('click', closeModal);
  if (infoModal) {
    infoModal.addEventListener('click', (e) => {
      if (e.target === infoModal) closeModal();
    });
  }
});
