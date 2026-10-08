/**
 * HealthAI v0.3 — Dual-Pane Frontend Application Logic with Live Clinical Notepad,
 * MongoDB Persistence, Follow-Up Assessment, User Authentication, and History Drawer
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
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

  // Dual-Pane Elements
  const workspaceDualPane = document.getElementById('workspaceDualPane');
  const mobileViewTabs = document.getElementById('mobileViewTabs');
  const tabViewChat = document.getElementById('tabViewChat');
  const tabViewNotepad = document.getElementById('tabViewNotepad');

  // Clinical Notepad Elements
  const notepadBody = document.getElementById('notepadBody');
  const notepadSyncPill = document.getElementById('notepadSyncPill');
  const notepadSyncStatus = document.getElementById('notepadSyncStatus');
  const copyNoteBtn = document.getElementById('copyNoteBtn');
  const printNoteBtn = document.getElementById('printNoteBtn');
  const notepadEmptyState = document.getElementById('notepadEmptyState');
  const clinicalSheet = document.getElementById('clinicalSheet');
  const sheetSessionId = document.getElementById('sheetSessionId');
  const sheetTimestamp = document.getElementById('sheetTimestamp');
  const sheetRiskBadge = document.getElementById('sheetRiskBadge');
  const sheetChiefComplaint = document.getElementById('sheetChiefComplaint');
  const sheetDuration = document.getElementById('sheetDuration');
  const sheetSeverity = document.getElementById('sheetSeverity');
  const sheetFindingsList = document.getElementById('sheetFindingsList');
  const sheetRedFlagStatus = document.getElementById('sheetRedFlagStatus');
  const sheetDoctorQuestions = document.getElementById('sheetDoctorQuestions');
  const sheetSupportiveCare = document.getElementById('sheetSupportiveCare');

  // Sidebar & Auth Elements
  const appLayout = document.getElementById('appLayout');
  const toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
  const closeSidebarBtn = document.getElementById('closeSidebarBtn');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  const newChatBtn = document.getElementById('newChatBtn');
  const conversationList = document.getElementById('conversationList');
  const historyCount = document.getElementById('historyCount');
  const historyEmpty = document.getElementById('historyEmpty');

  const userLoggedOut = document.getElementById('userLoggedOut');
  const userLoggedIn = document.getElementById('userLoggedIn');
  const openAuthBtn = document.getElementById('openAuthBtn');
  const userHeaderBtn = document.getElementById('userHeaderBtn');
  const userAvatar = document.getElementById('userAvatar');
  const userName = document.getElementById('userName');
  const userEmail = document.getElementById('userEmail');
  const logoutBtn = document.getElementById('logoutBtn');

  // Auth Modal Elements
  const authModal = document.getElementById('authModal');
  const authCloseBtn = document.getElementById('authCloseBtn');
  const tabSignIn = document.getElementById('tabSignIn');
  const tabRegister = document.getElementById('tabRegister');
  const signInForm = document.getElementById('signInForm');
  const registerForm = document.getElementById('registerForm');
  const authAlert = document.getElementById('authAlert');
  const loginEmail = document.getElementById('loginEmail');
  const loginPassword = document.getElementById('loginPassword');
  const regName = document.getElementById('regName');
  const regEmail = document.getElementById('regEmail');
  const regPassword = document.getElementById('regPassword');

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
  let activeConversations = [];
  let currentClinicalNote = null;

  // --- Auth State Management ---
  const getAuthToken = () => localStorage.getItem('healthai_token');
  const setAuthToken = (token) => localStorage.setItem('healthai_token', token);
  const clearAuthToken = () => {
    localStorage.removeItem('healthai_token');
    localStorage.removeItem('healthai_user');
  };

  const getCachedUser = () => {
    try {
      const u = localStorage.getItem('healthai_user');
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  };

  const setCachedUser = (user) => localStorage.setItem('healthai_user', JSON.stringify(user));

  const getAuthHeaders = () => {
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
    const token = getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  };

  const updateAuthUI = (user) => {
    if (user) {
      if (userLoggedOut) userLoggedOut.style.display = 'none';
      if (userLoggedIn) userLoggedIn.style.display = 'flex';
      if (userName) userName.textContent = user.name || 'User';
      if (userEmail) userEmail.textContent = user.email || '';
      if (userAvatar) userAvatar.textContent = (user.name ? user.name.charAt(0).toUpperCase() : 'U');
      if (userHeaderBtn) userHeaderBtn.title = `Signed in as ${user.name}`;
    } else {
      if (userLoggedOut) userLoggedOut.style.display = 'flex';
      if (userLoggedIn) userLoggedIn.style.display = 'none';
      if (userHeaderBtn) userHeaderBtn.title = 'Account / Sign In';
    }
  };

  const verifyAuthSession = async () => {
    const token = getAuthToken();
    if (!token) {
      updateAuthUI(null);
      loadConversations();
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const user = await res.json();
        setCachedUser(user);
        updateAuthUI(user);
      } else {
        clearAuthToken();
        updateAuthUI(null);
      }
    } catch (e) {
      const cached = getCachedUser();
      updateAuthUI(cached);
    }
    loadConversations();
  };

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
          const dbStatus = data.database_connected ? 'DB Connected' : 'DB Offline';
          statusText.textContent = data.gemini_configured ? (data.database_connected ? 'Ready' : 'AI Ready') : 'Key Required';
          serverStatus.title = `Backend online (Model: ${data.model || 'Gemini'}, ${dbStatus})`;
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

  checkBackendStatus();
  setInterval(checkBackendStatus, 15000);

  // --- Utility: Format Time & Dates ---
  const formatCurrentTime = (isoString) => {
    const d = isoString ? new Date(isoString) : new Date();
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDateLabel = (isoString) => {
    if (!isoString) return '';
    const d = new Date(isoString);
    const now = new Date();
    const isToday = d.toDateString() === now.toDateString();
    if (isToday) return 'Today';
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  // --- Utility: Markdown Formatter ---
  const formatMarkdown = (text) => {
    if (!text) return '';

    let escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    escaped = escaped.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    escaped = escaped.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');

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

      if (inList) {
        result.push(listType === 'ul' ? '</ul>' : '</ol>');
        inList = false;
      }

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

  // --- Utility: Escape HTML ---
  const escapeHtml = (str) => {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      chatMain.scrollTop = chatMain.scrollHeight;
    }, 50);
  };

  const showErrorToast = (msg) => {
    if (!errorToast || !toastMessage) return;
    toastMessage.textContent = msg;
    errorToast.style.display = 'flex';
    setTimeout(() => hideErrorToast(), 6000);
  };

  const hideErrorToast = () => {
    if (errorToast) errorToast.style.display = 'none';
  };

  // Alias for prescription feature
  const showToast = (msg) => showErrorToast(msg);

  if (toastClose) {
    toastClose.addEventListener('click', hideErrorToast);
  }

  // --- Clinical Assessment Notepad Renderer ---
  const renderClinicalNotepad = (note, sessionId = null, riskHint = 'unknown', timestamp = null) => {
    if (!notepadBody) return;

    if (!note && !currentClinicalNote) {
      if (notepadEmptyState) notepadEmptyState.style.display = 'flex';
      if (clinicalSheet) clinicalSheet.style.display = 'none';
      if (notepadSyncStatus) notepadSyncStatus.textContent = 'Awaiting Assessment';
      if (notepadSyncPill) notepadSyncPill.className = 'notepad-sync-pill';
      return;
    }

    const activeNote = note || currentClinicalNote;
    if (notepadEmptyState) notepadEmptyState.style.display = 'none';
    if (clinicalSheet) clinicalSheet.style.display = 'flex';

    if (notepadSyncStatus) notepadSyncStatus.textContent = 'Live Synced';
    if (notepadSyncPill) notepadSyncPill.className = 'notepad-sync-pill active';

    // Header metadata
    if (sheetSessionId) sheetSessionId.textContent = sessionId || currentConversationId || 'conv_active';
    if (sheetTimestamp) sheetTimestamp.textContent = timestamp ? `Recorded ${formatDateLabel(timestamp)} at ${formatCurrentTime(timestamp)}` : `Updated ${formatCurrentTime()}`;
    
    // Risk Level Badge
    const risk = (riskHint || activeNote.risk_hint || 'unknown').toLowerCase();
    if (sheetRiskBadge) {
      sheetRiskBadge.textContent = risk;
      sheetRiskBadge.className = `risk-badge-large ${risk}`;
    }

    // Section 1: Chief Complaint & Timeline
    if (sheetChiefComplaint) {
      sheetChiefComplaint.textContent = activeNote.chief_complaint || 'Symptom inquiry under evaluation';
    }
    if (sheetDuration) {
      sheetDuration.textContent = activeNote.duration || 'Not specified';
    }
    if (sheetSeverity) {
      sheetSeverity.textContent = activeNote.severity || 'Under evaluation';
    }

    // Section 2: Clinical Findings List
    if (sheetFindingsList) {
      const findings = activeNote.key_findings || [];
      if (findings.length > 0) {
        sheetFindingsList.innerHTML = findings.map(f => `<li>${f.replace(/</g, '&lt;')}</li>`).join('');
      } else {
        sheetFindingsList.innerHTML = `<li>Evaluating reported symptoms...</li>`;
      }
    }

    // Section 3: Red Flag Safety Screening
    if (sheetRedFlagStatus) {
      const redFlags = activeNote.red_flags || [];
      if (redFlags.length > 0 || risk === 'emergency') {
        const flagItems = redFlags.length > 0 ? redFlags.map(rf => `<li>${rf.replace(/</g, '&lt;')}</li>`).join('') : `<li>Potential emergency medical indicators described.</li>`;
        sheetRedFlagStatus.innerHTML = `
          <div class="danger-indicator">
            <div class="danger-title-row">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              <span>Urgent Safety Warning: Immediate Care Advised</span>
            </div>
            <ul class="danger-items-list">
              ${flagItems}
            </ul>
          </div>
        `;
      } else {
        sheetRedFlagStatus.innerHTML = `
          <div class="safe-indicator">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            <span>No acute red-flag emergencies detected in current description.</span>
          </div>
        `;
      }
    }

    // Section 4: Doctor Discussion Guide
    if (sheetDoctorQuestions) {
      const questions = activeNote.doctor_questions || [];
      if (questions.length > 0) {
        sheetDoctorQuestions.innerHTML = questions.map(q => `<li>${q.replace(/</g, '&lt;')}</li>`).join('');
      } else {
        sheetDoctorQuestions.innerHTML = `<li>Discuss duration, progression, and potential triggers with your healthcare provider.</li>`;
      }
    }

    // Section 5: Supportive Care & Home Measures
    if (sheetSupportiveCare) {
      const careTips = activeNote.supportive_care || [];
      if (careTips.length > 0) {
        sheetSupportiveCare.innerHTML = careTips.map(c => `<li>${c.replace(/</g, '&lt;')}</li>`).join('');
      } else {
        sheetSupportiveCare.innerHTML = `<li>Rest comfortably and stay hydrated while monitoring symptoms.</li>`;
      }
    }
  };

  // --- Copy Clinical Note Handler ---
  if (copyNoteBtn) {
    copyNoteBtn.addEventListener('click', () => {
      if (!currentClinicalNote) {
        showErrorToast('No clinical note has been generated yet.');
        return;
      }

      const note = currentClinicalNote;
      const lines = [
        `# CLINICAL ASSESSMENT NOTE — HEALTHAI`,
        `Session ID: ${currentConversationId || 'Active'}`,
        `Date: ${new Date().toLocaleString()}`,
        `Risk Triage: ${(note.risk_hint || 'Moderate').toUpperCase()}`,
        ``,
        `## 1. Chief Complaint & Timeline`,
        `* Stated Concern: ${note.chief_complaint || 'N/A'}`,
        `* Reported Duration: ${note.duration || 'N/A'}`,
        `* Assessed Severity: ${note.severity || 'N/A'}`,
        ``,
        `## 2. Clinical Dimensions & Findings`,
        ...(note.key_findings || []).map(f => `* ${f}`),
        ``,
        `## 3. Red-Flag Safety Screening`,
        ...(note.red_flags && note.red_flags.length > 0 ? note.red_flags.map(rf => `* ⚠️ ALERT: ${rf}`) : ['* No acute red-flags identified.']),
        ``,
        `## 4. Questions for Your Healthcare Provider`,
        ...(note.doctor_questions || []).map(q => `* ${q}`),
        ``,
        `## 5. Supportive Home Care Recommendations`,
        ...(note.supportive_care || []).map(c => `* ${c}`),
        ``,
        `---`,
        `Disclaimer: This structured report is for educational symptom assessment and patient record keeping. It is not an official medical diagnosis.`
      ];

      navigator.clipboard.writeText(lines.join('\n')).then(() => {
        copyNoteBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> <span>Copied!</span>`;
        setTimeout(() => {
          copyNoteBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> <span>Copy Note</span>`;
        }, 2000);
      }).catch(() => {
        showErrorToast('Failed to copy note to clipboard.');
      });
    });
  }

  // --- Print / Export Note Handler ---
  if (printNoteBtn) {
    printNoteBtn.addEventListener('click', () => {
      if (!currentClinicalNote) {
        showErrorToast('No clinical note has been generated yet.');
        return;
      }
      window.print();
    });
  }

  // --- Mobile Tab View Switcher (Consultation vs Clinical Note) ---
  if (tabViewChat && tabViewNotepad && workspaceDualPane) {
    tabViewChat.addEventListener('click', () => {
      tabViewChat.classList.add('active');
      tabViewNotepad.classList.remove('active');
      workspaceDualPane.classList.remove('view-notepad');
      workspaceDualPane.classList.add('view-chat');
    });

    tabViewNotepad.addEventListener('click', () => {
      tabViewNotepad.classList.add('active');
      tabViewChat.classList.remove('active');
      workspaceDualPane.classList.remove('view-chat');
      workspaceDualPane.classList.add('view-notepad');
    });
  }

  // --- Render Messages in Chat ---
  const appendUserMessage = (text, timeStr = null) => {
    if (welcomeCard) welcomeCard.style.display = 'none';

    const t = timeStr || formatCurrentTime();
    const row = document.createElement('div');
    row.className = 'message-row user-row';
    row.innerHTML = `
      <div class="message-content-wrap">
        <div class="message-meta">
          <span class="sender-name">You</span>
          <span class="message-time">${t}</span>
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

  const appendAiResponse = (data, isHistorical = false, timeStr = null) => {
    if (welcomeCard) welcomeCard.style.display = 'none';

    const t = timeStr || formatCurrentTime();
    const row = document.createElement('div');
    row.className = 'message-row ai-row';
    const messageId = 'ai-msg-' + Math.random().toString(36).substring(2, 9);

    const responseType = data.response_type || 'guidance';
    const rawMessage = data.message || data.content || '';
    const questions = data.questions || [];

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

    let bodyHtml = `<div class="ai-content-message">${formatMarkdown(rawMessage)}</div>`;

    if (responseType === 'follow_up' && questions.length > 0) {
      const mcqId = 'mcq-' + Math.random().toString(36).substring(2, 9);
      const selectedAnswers = new Array(questions.length).fill(null);

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
            ${isHistorical ? 'disabled' : ''}
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
        <div class="followup-mcq-container ${isHistorical ? 'submitted' : ''}" id="${mcqId}">
          <div class="followup-intro">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
            ${isHistorical ? 'Follow-up questions evaluated:' : 'Please select the best answer for each question below:'}
          </div>
          <div class="mcq-questions-list">
            ${questionsHtml}
          </div>
          ${!isHistorical ? `
            <button class="mcq-submit-btn" id="${mcqId}-submit" type="button" disabled>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
              Submit Answers
            </button>
          ` : ''}
        </div>
      `;

      if (!isHistorical) {
        setTimeout(() => {
          const container = document.getElementById(mcqId);
          if (!container) return;
          const submitBtn = document.getElementById(`${mcqId}-submit`);

          const checkAllAnswered = () => selectedAnswers.every(a => a !== null);

          container.querySelectorAll('.mcq-option-btn').forEach(btn => {
            btn.addEventListener('click', () => {
              const qIdx = parseInt(btn.getAttribute('data-q'));
              const optText = btn.getAttribute('data-text');

              container.querySelectorAll(`.mcq-option-btn[data-q="${qIdx}"]`).forEach(b => {
                b.classList.remove('selected');
              });

              btn.classList.add('selected');
              selectedAnswers[qIdx] = optText;

              const card = document.getElementById(`${mcqId}-q${qIdx}`);
              if (card) card.classList.add('answered');

              if (submitBtn) submitBtn.disabled = !checkAllAnswered();
            });
          });

          const doSubmit = () => {
            if (!checkAllAnswered()) return;
            const parts = questions.map((q, i) => {
              const qText = typeof q === 'string' ? q : (q.question || `Question ${i+1}`);
              return `${qText}: ${selectedAnswers[i]}`;
            });
            const replyText = parts.join('; ');

            container.querySelectorAll('.mcq-option-btn').forEach(b => b.disabled = true);
            if (submitBtn) submitBtn.disabled = true;
            container.classList.add('submitted');

            handleSendMessage(replyText);
          };

          if (submitBtn) submitBtn.addEventListener('click', doSubmit);
        }, 0);
      }
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
          <span class="message-time">${t}</span>
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
          copyBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied!`;
          setTimeout(() => {
            copyBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy`;
          }, 2000);
        }).catch(() => {
          showErrorToast('Failed to copy response.');
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
      <div class="message-avatar ai-avatar" title="HealthAI Notice">
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

  // --- Send Message Flow ---
  const handleSendMessage = async (userText) => {
    const text = (userText || messageInput.value || '').trim();
    if (!text || isSubmitting) return;

    messageInput.value = '';
    updateInputHeight();

    isSubmitting = true;
    sendButton.disabled = true;
    hideErrorToast();

    appendUserMessage(text);

    typingIndicator.style.display = 'flex';
    scrollToBottom();

    try {
      const payload = { message: text };
      if (currentConversationId) {
        payload.conversation_id = currentConversationId;
      }

      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        const errorDetail = data.detail || 'Failed to get response from HealthAI server.';
        appendErrorMessage(errorDetail);
        showErrorToast(errorDetail);
      } else {
        if (data.conversation_id) {
          currentConversationId = data.conversation_id;
        }

        // Update Clinical Notepad
        if (data.clinical_note) {
          currentClinicalNote = data.clinical_note;
          renderClinicalNotepad(data.clinical_note, data.conversation_id, data.risk_hint);
        }

        appendAiResponse(data);
        loadConversations();
      }
    } catch (err) {
      const networkError = 'Unable to connect to the backend server. Please verify that the FastAPI backend is running.';
      appendErrorMessage(networkError);
      showErrorToast(networkError);
    } finally {
      typingIndicator.style.display = 'none';
      isSubmitting = false;
      sendButton.disabled = false;
      messageInput.focus();
    }
  };

  // --- Conversation History Management ---
  const loadConversations = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/conversations`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        activeConversations = data.conversations || [];
        renderConversationList(activeConversations);
      }
    } catch (err) {
      console.warn('Could not load conversations from server:', err);
    }
  };

  const renderConversationList = (conversations) => {
    if (!conversationList) return;

    if (historyCount) historyCount.textContent = conversations.length;

    if (!conversations || conversations.length === 0) {
      conversationList.innerHTML = `
        <div class="history-empty">
          <p>No saved assessments yet.</p>
          <span class="subtext">Your consultations will appear here.</span>
        </div>
      `;
      return;
    }

    conversationList.innerHTML = '';

    conversations.forEach(conv => {
      const item = document.createElement('div');
      const isActive = conv.id === currentConversationId;
      item.className = `conversation-item ${isActive ? 'active' : ''}`;
      item.setAttribute('data-id', conv.id);

      const riskHint = conv.last_risk_hint || 'unknown';
      const dateLabel = formatDateLabel(conv.updated_at);

      item.innerHTML = `
        <div class="conv-info">
          <span class="conv-title" title="${conv.title.replace(/"/g, '&quot;')}">${conv.title.replace(/</g, '&lt;')}</span>
          <div class="conv-meta-row">
            <span class="conv-risk-badge ${riskHint}">${riskHint}</span>
            <span>&bull;</span>
            <span>${dateLabel}</span>
            <span>(${conv.message_count} msg)</span>
          </div>
        </div>
        <button class="conv-delete-btn" title="Delete assessment" data-del-id="${conv.id}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </button>
      `;

      item.addEventListener('click', (e) => {
        if (e.target.closest('.conv-delete-btn')) return;
        loadConversationDetail(conv.id);
      });

      const delBtn = item.querySelector('.conv-delete-btn');
      if (delBtn) {
        delBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          deleteConversation(conv.id);
        });
      }

      conversationList.appendChild(item);
    });
  };

  const loadConversationDetail = async (conversationId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}`, {
        headers: getAuthHeaders()
      });

      if (!res.ok) {
        showErrorToast('Failed to load conversation history.');
        return;
      }

      const detail = await res.json();
      currentConversationId = detail.id;

      // Clear current chat container
      const rows = messagesContainer.querySelectorAll('.message-row');
      rows.forEach(r => r.remove());

      if (welcomeCard) welcomeCard.style.display = 'none';

      // Render historical messages
      if (detail.messages && detail.messages.length > 0) {
        detail.messages.forEach(msg => {
          if (msg.role === 'user') {
            appendUserMessage(msg.content, formatCurrentTime(msg.created_at));
          } else {
            appendAiResponse({
              response_type: msg.response_type || 'guidance',
              message: msg.content,
              questions: msg.questions || [],
              risk_hint: msg.risk_hint
            }, true, formatCurrentTime(msg.created_at));
          }
        });
      } else {
        if (welcomeCard) welcomeCard.style.display = 'flex';
      }

      // Restore Clinical Notepad
      if (detail.last_clinical_note) {
        currentClinicalNote = detail.last_clinical_note;
        renderClinicalNotepad(detail.last_clinical_note, detail.id, detail.last_clinical_note.risk_hint, detail.updated_at);
      } else {
        currentClinicalNote = null;
        renderClinicalNotepad(null);
      }

      // Update active highlight in sidebar
      document.querySelectorAll('.conversation-item').forEach(el => {
        el.classList.toggle('active', el.getAttribute('data-id') === conversationId);
      });

      // On mobile, close sidebar after selection
      if (window.innerWidth <= 768 && appLayout) {
        appLayout.classList.remove('sidebar-mobile-open');
      }

      messageInput.focus();
    } catch (err) {
      showErrorToast('Could not load assessment details.');
    }
  };

  const deleteConversation = async (conversationId) => {
    if (!confirm('Are you sure you want to delete this assessment record?')) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });

      if (res.ok) {
        if (currentConversationId === conversationId) {
          startNewAssessment();
        }
        loadConversations();
      } else {
        showErrorToast('Failed to delete conversation.');
      }
    } catch (e) {
      showErrorToast('Error deleting conversation.');
    }
  };

  const startNewAssessment = () => {
    currentConversationId = null;
    currentClinicalNote = null;
    renderClinicalNotepad(null);

    const rows = messagesContainer.querySelectorAll('.message-row');
    rows.forEach(r => r.remove());
    if (welcomeCard) welcomeCard.style.display = 'flex';
    document.querySelectorAll('.conversation-item').forEach(el => el.classList.remove('active'));
    messageInput.value = '';
    updateInputHeight();
    messageInput.focus();

    if (window.innerWidth <= 768 && appLayout) {
      appLayout.classList.remove('sidebar-mobile-open');
    }
  };

  // --- Sidebar Toggle Handlers ---
  if (toggleSidebarBtn && appLayout) {
    toggleSidebarBtn.addEventListener('click', () => {
      if (window.innerWidth <= 768) {
        appLayout.classList.toggle('sidebar-mobile-open');
      } else {
        appLayout.classList.toggle('sidebar-closed');
      }
    });
  }

  if (closeSidebarBtn && appLayout) {
    closeSidebarBtn.addEventListener('click', () => {
      appLayout.classList.remove('sidebar-mobile-open');
    });
  }

  if (sidebarBackdrop && appLayout) {
    sidebarBackdrop.addEventListener('click', () => {
      appLayout.classList.remove('sidebar-mobile-open');
    });
  }

  if (newChatBtn) {
    newChatBtn.addEventListener('click', startNewAssessment);
  }

  // --- Auth Modal & Tab Handlers ---
  const openAuth = (isRegister = false) => {
    if (!authModal) return;
    authModal.style.display = 'flex';
    hideAuthAlert();
    if (isRegister) {
      tabRegister.click();
    } else {
      tabSignIn.click();
    }
  };

  const closeAuth = () => {
    if (authModal) authModal.style.display = 'none';
    hideAuthAlert();
  };

  const showAuthAlert = (msg, type = 'error') => {
    if (!authAlert) return;
    authAlert.textContent = msg;
    authAlert.className = `auth-alert ${type}`;
    authAlert.style.display = 'block';
  };

  const hideAuthAlert = () => {
    if (authAlert) authAlert.style.display = 'none';
  };

  if (openAuthBtn) openAuthBtn.addEventListener('click', () => openAuth(false));
  if (userHeaderBtn) {
    userHeaderBtn.addEventListener('click', () => {
      if (getAuthToken()) {
        if (window.innerWidth <= 768) {
          appLayout.classList.add('sidebar-mobile-open');
        } else {
          appLayout.classList.remove('sidebar-closed');
        }
      } else {
        openAuth(false);
      }
    });
  }
  if (authCloseBtn) authCloseBtn.addEventListener('click', closeAuth);
  if (authModal) {
    authModal.addEventListener('click', (e) => {
      if (e.target === authModal) closeAuth();
    });
  }

  if (tabSignIn && tabRegister) {
    tabSignIn.addEventListener('click', () => {
      tabSignIn.classList.add('active');
      tabRegister.classList.remove('active');
      signInForm.style.display = 'flex';
      registerForm.style.display = 'none';
      hideAuthAlert();
    });

    tabRegister.addEventListener('click', () => {
      tabRegister.classList.add('active');
      tabSignIn.classList.remove('active');
      registerForm.style.display = 'flex';
      signInForm.style.display = 'none';
      hideAuthAlert();
    });
  }

  // Sign In Form Submit
  if (signInForm) {
    signInForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = loginEmail.value.trim();
      const password = loginPassword.value;
      const submitBtn = document.getElementById('loginSubmitBtn');

      if (!email || !password) return;

      submitBtn.disabled = true;
      hideAuthAlert();

      try {
        const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (res.ok) {
          setAuthToken(data.access_token);
          setCachedUser(data.user);
          updateAuthUI(data.user);
          showAuthAlert('Successfully signed in!', 'success');
          setTimeout(() => {
            closeAuth();
            loadConversations();
          }, 800);
        } else {
          showAuthAlert(data.detail || 'Invalid email or password.');
        }
      } catch (err) {
        showAuthAlert('Unable to connect to authentication server.');
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  // Register Form Submit
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = regName.value.trim();
      const email = regEmail.value.trim();
      const password = regPassword.value;
      const submitBtn = document.getElementById('registerSubmitBtn');

      if (!name || !email || !password) return;

      submitBtn.disabled = true;
      hideAuthAlert();

      try {
        const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, password })
        });

        const data = await res.json();

        if (res.ok) {
          setAuthToken(data.access_token);
          setCachedUser(data.user);
          updateAuthUI(data.user);
          showAuthAlert('Account created successfully!', 'success');
          setTimeout(() => {
            closeAuth();
            loadConversations();
          }, 800);
        } else {
          showAuthAlert(data.detail || 'Registration failed. Email might already exist.');
        }
      } catch (err) {
        showAuthAlert('Unable to connect to registration server.');
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  // Logout Handler
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      clearAuthToken();
      updateAuthUI(null);
      startNewAssessment();
      loadConversations();
    });
  }

  // --- Form Events ---
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    handleSendMessage();
  });

  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  suggestionChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      if (prompt) {
        handleSendMessage(prompt);
      }
    });
  });

  if (clearChatButton) {
    clearChatButton.addEventListener('click', startNewAssessment);
  }

  if (infoButton && infoModal) {
    infoButton.addEventListener('click', () => {
      infoModal.style.display = 'flex';
    });
  }

  const closeInfoModal = () => {
    if (infoModal) infoModal.style.display = 'none';
  };

  if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeInfoModal);
  if (modalUnderstandBtn) modalUnderstandBtn.addEventListener('click', closeInfoModal);
  if (infoModal) {
    infoModal.addEventListener('click', (e) => {
      if (e.target === infoModal) closeInfoModal();
    });
  }

  // ==============================================================================
  // 3-PAGE WEBSITE NAVIGATION ROUTER
  // ==============================================================================
  const pageWelcome = document.getElementById('pageWelcome');
  const pageSymptom = document.getElementById('pageSymptom');
  const pagePrescription = document.getElementById('pagePrescription');

  const launchSymptomBtn = document.getElementById('launchSymptomBtn');
  const launchPrescriptionBtn = document.getElementById('launchPrescriptionBtn');
  const backToWelcomeSymptom = document.getElementById('backToWelcomeSymptom');
  const backToWelcomePrescription = document.getElementById('backToWelcomePrescription');
  const homeBrandLogo = document.getElementById('homeBrandLogo');
  const homeBrandTitle = document.getElementById('homeBrandTitle');
  const welcomeOpenAuthBtn = document.getElementById('welcomeOpenAuthBtn');
  const clearChatButtonSymptom = document.getElementById('clearChatButtonSymptom');

  const showPage = (pageName) => {
    // Hide all pages
    if (pageWelcome) pageWelcome.style.display = 'none';
    if (pageSymptom) pageSymptom.style.display = 'none';
    if (pagePrescription) pagePrescription.style.display = 'none';

    // Show target page
    if (pageName === 'symptom') {
      if (pageSymptom) pageSymptom.style.display = 'flex';
      window.location.hash = '#symptom-assessment';
    } else if (pageName === 'prescription') {
      if (pagePrescription) pagePrescription.style.display = 'flex';
      window.location.hash = '#prescription-explainer';
    } else {
      if (pageWelcome) pageWelcome.style.display = 'flex';
      window.location.hash = '#welcome';
    }

    window.scrollTo(0, 0);
  };

  // Launch buttons on Welcome Page
  if (launchSymptomBtn) {
    launchSymptomBtn.addEventListener('click', () => showPage('symptom'));
  }
  if (launchPrescriptionBtn) {
    launchPrescriptionBtn.addEventListener('click', () => showPage('prescription'));
  }

  // Back to Welcome Page buttons
  if (backToWelcomeSymptom) {
    backToWelcomeSymptom.addEventListener('click', () => showPage('welcome'));
  }
  if (backToWelcomePrescription) {
    backToWelcomePrescription.addEventListener('click', () => showPage('welcome'));
  }
  if (homeBrandLogo) {
    homeBrandLogo.addEventListener('click', () => showPage('welcome'));
  }
  if (homeBrandTitle) {
    homeBrandTitle.addEventListener('click', () => showPage('welcome'));
  }
  if (welcomeOpenAuthBtn) {
    welcomeOpenAuthBtn.addEventListener('click', () => openAuth(false));
  }
  if (clearChatButtonSymptom) {
    clearChatButtonSymptom.addEventListener('click', startNewAssessment);
  }

  // Hash change router listener
  const handleHashChange = () => {
    const hash = window.location.hash;
    if (hash === '#symptom-assessment') {
      showPage('symptom');
    } else if (hash === '#prescription-explainer') {
      showPage('prescription');
    } else {
      showPage('welcome');
    }
  };

  window.addEventListener('hashchange', handleHashChange);

  // ==============================================================================
  // PRESCRIPTION EXPLAINER FEATURE LOGIC
  // ==============================================================================
  const rxTrySampleBtn = document.getElementById('rxTrySampleBtn');
  const rxUploadCard = document.getElementById('rxUploadCard');
  const rxDropzone = document.getElementById('rxDropzone');
  const rxFileInput = document.getElementById('rxFileInput');
  const rxDropzoneContent = document.getElementById('rxDropzoneContent');
  const rxBrowseBtn = document.getElementById('rxBrowseBtn');
  const rxFilePreview = document.getElementById('rxFilePreview');
  const rxPreviewThumb = document.getElementById('rxPreviewThumb');
  const rxFileName = document.getElementById('rxFileName');
  const rxFileSize = document.getElementById('rxFileSize');
  const rxRemoveFileBtn = document.getElementById('rxRemoveFileBtn');
  const rxNotesInput = document.getElementById('rxNotesInput');
  const rxAnalyzeBtn = document.getElementById('rxAnalyzeBtn');
  const rxLoadingState = document.getElementById('rxLoadingState');
  const rxResultsDashboard = document.getElementById('rxResultsDashboard');

  const rxAnalysisTime = document.getElementById('rxAnalysisTime');
  const rxCopyBtn = document.getElementById('rxCopyBtn');
  const rxPrintBtn = document.getElementById('rxPrintBtn');
  const rxNewAnalysisBtn = document.getElementById('rxNewAnalysisBtn');

  const sumProblem = document.getElementById('sumProblem');
  const sumTests = document.getElementById('sumTests');
  const sumMedicines = document.getElementById('sumMedicines');
  const sumInstructions = document.getElementById('sumInstructions');

  const rxDiagBadge = document.getElementById('rxDiagBadge');
  const rxDiagProblem = document.getElementById('rxDiagProblem');
  const rxDiagExplanation = document.getElementById('rxDiagExplanation');
  const rxDiagNote = document.getElementById('rxDiagNote');

  const rxTestsCount = document.getElementById('rxTestsCount');
  const rxTestsGrid = document.getElementById('rxTestsGrid');

  const rxMedsCount = document.getElementById('rxMedsCount');
  const rxMedicinesGrid = document.getElementById('rxMedicinesGrid');

  const rxInstructionsList = document.getElementById('rxInstructionsList');

  const rxUnclearCard = document.getElementById('rxUnclearCard');
  const rxUnclearCount = document.getElementById('rxUnclearCount');
  const rxUnclearList = document.getElementById('rxUnclearList');

  const rxDisclaimerText = document.getElementById('rxDisclaimerText');

  let selectedPrescriptionFile = null;
  let currentPrescriptionExplanation = null;


  // File Upload Handlers
  const handleFileSelect = (file) => {
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      showToast('File size exceeds maximum limit of 10MB.');
      return;
    }

    selectedPrescriptionFile = file;
    if (rxFileName) rxFileName.textContent = file.name;
    if (rxFileSize) rxFileSize.textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';

    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      if (rxPreviewThumb) rxPreviewThumb.innerHTML = `<img src="${url}" alt="Prescription preview">`;
    } else {
      if (rxPreviewThumb) {
        rxPreviewThumb.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>`;
      }
    }

    if (rxDropzoneContent) rxDropzoneContent.style.display = 'none';
    if (rxFilePreview) rxFilePreview.style.display = 'flex';
    if (rxAnalyzeBtn) rxAnalyzeBtn.disabled = false;
  };

  const resetFileUpload = () => {
    selectedPrescriptionFile = null;
    if (rxFileInput) rxFileInput.value = '';
    if (rxDropzoneContent) rxDropzoneContent.style.display = 'block';
    if (rxFilePreview) rxFilePreview.style.display = 'none';
    if (rxAnalyzeBtn) rxAnalyzeBtn.disabled = true;
    if (rxNotesInput) rxNotesInput.value = '';
  };

  if (rxBrowseBtn) {
    rxBrowseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (rxFileInput) rxFileInput.click();
    });
  }

  if (rxDropzone) {
    rxDropzone.addEventListener('click', () => {
      if (!selectedPrescriptionFile && rxFileInput) rxFileInput.click();
    });

    rxDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      rxDropzone.classList.add('drag-over');
    });

    rxDropzone.addEventListener('dragleave', () => {
      rxDropzone.classList.remove('drag-over');
    });

    rxDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      rxDropzone.classList.remove('drag-over');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileSelect(e.dataTransfer.files[0]);
      }
    });
  }

  if (rxFileInput) {
    rxFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileSelect(e.target.files[0]);
      }
    });
  }

  if (rxRemoveFileBtn) {
    rxRemoveFileBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      resetFileUpload();
    });
  }

  // Render Prescription Analysis Results
  const renderPrescriptionResults = (data) => {
    currentPrescriptionExplanation = data;

    if (rxAnalysisTime) {
      rxAnalysisTime.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // 6. Simple Summary Card
    if (data.summary) {
      if (sumProblem) sumProblem.textContent = data.summary.problem_summary || 'N/A';
      if (sumTests) sumTests.textContent = data.summary.tests_summary || 'None prescribed.';
      if (sumMedicines) sumMedicines.textContent = data.summary.medicines_summary || 'N/A';
      if (sumInstructions) sumInstructions.textContent = data.summary.instructions_summary || 'N/A';
    }

    // 1. Diagnosis Card
    if (data.diagnosis) {
      if (rxDiagProblem) rxDiagProblem.textContent = data.diagnosis.problem || 'No Medical Diagnosis Stated';
      if (rxDiagExplanation) rxDiagExplanation.textContent = data.diagnosis.explanation || 'No diagnosis was written on this prescription.';
      if (rxDiagNote) rxDiagNote.textContent = data.diagnosis.note || 'Diagnoses are only displayed when explicitly written on the prescription sheet.';

      if (rxDiagBadge) {
        if (data.diagnosis.is_present) {
          rxDiagBadge.textContent = 'Stated on Prescription';
          rxDiagBadge.className = 'presence-badge present';
        } else {
          rxDiagBadge.textContent = 'Not Written on Prescription';
          rxDiagBadge.className = 'presence-badge absent';
        }
      }
    }

    // 2. Tests Card
    const tests = data.tests || [];
    if (rxTestsCount) rxTestsCount.textContent = `${tests.length} Test${tests.length === 1 ? '' : 's'}`;
    if (rxTestsGrid) {
      if (tests.length === 0) {
        rxTestsGrid.innerHTML = '<div class="test-item-card"><p class="test-detail">No diagnostic or laboratory tests mentioned on this prescription.</p></div>';
      } else {
        rxTestsGrid.innerHTML = tests.map(t => `
          <div class="test-item-card">
            <h4>${escapeHtml(t.test_name)}</h4>
            <p class="test-detail"><strong>What it is:</strong> ${escapeHtml(t.what_it_is)}</p>
            <p class="test-detail"><strong>What it checks:</strong> ${escapeHtml(t.what_it_checks)}</p>
            <p class="test-detail"><strong>Why recommended:</strong> ${escapeHtml(t.why_recommended)}</p>
          </div>
        `).join('');
      }
    }

    // 3. Medicines Card
    const meds = data.medicines || [];
    if (rxMedsCount) rxMedsCount.textContent = `${meds.length} Medicine${meds.length === 1 ? '' : 's'}`;
    if (rxMedicinesGrid) {
      if (meds.length === 0) {
        rxMedicinesGrid.innerHTML = '<div class="medicine-item-card"><p>No medications listed on prescription.</p></div>';
      } else {
        rxMedicinesGrid.innerHTML = meds.map((m, idx) => `
          <div class="medicine-item-card">
            <div class="med-header">
              <div class="med-title-group">
                <span class="med-name">${idx + 1}. ${escapeHtml(m.medicine_name)}</span>
              </div>
              <span class="meta-pill ${m.is_clear ? 'abbrev-pill' : 'timing-pill'}">${m.is_clear ? '✓ Legible' : '⚠️ Handwriting Unclear'}</span>
            </div>
            
            <div class="use-box">
              <strong>General Use:</strong> ${escapeHtml(m.general_use)}
            </div>

            <div class="med-meta-pills">
              <span class="meta-pill"><strong>Dose:</strong> ${escapeHtml(m.strength_dosage)}</span>
              <span class="meta-pill abbrev-pill" title="Frequency & Abbreviation Breakdown">
                <strong>Schedule (${escapeHtml(m.frequency)}):</strong> ${escapeHtml(m.abbreviation_explained)}
              </span>
              <span class="meta-pill timing-pill"><strong>Food Timing:</strong> ${escapeHtml(m.timing_food)}</span>
              <span class="meta-pill"><strong>Duration:</strong> ${escapeHtml(m.duration)}</span>
            </div>

            ${m.other_instructions ? `<p class="test-detail"><strong>Doctor Notes:</strong> ${escapeHtml(m.other_instructions)}</p>` : ''}
          </div>
        `).join('');
      }
    }

    // 4. Doctor Instructions Card
    const instructions = data.doctors_instructions || [];
    if (rxInstructionsList) {
      if (instructions.length === 0) {
        rxInstructionsList.innerHTML = '<li>No additional special instructions written on prescription.</li>';
      } else {
        rxInstructionsList.innerHTML = instructions.map(inst => `
          <li><span>${escapeHtml(inst)}</span></li>
        `).join('');
      }
    }

    // 5. Unclear Information & Verification Alerts
    const unclear = data.unclear_items || [];
    if (rxUnclearCount) rxUnclearCount.textContent = `${unclear.length} Alert${unclear.length === 1 ? '' : 's'}`;
    if (rxUnclearCard && rxUnclearList) {
      if (unclear.length === 0) {
        rxUnclearList.innerHTML = '<div class="unclear-item-box" style="border-left-color: var(--emerald-500);"><span class="unclear-cat" style="color: var(--emerald-600);">✓ Legibility Check Passed</span><p class="unclear-reason">All medicine names, dosages, and instructions written on this prescription appear legible.</p></div>';
      } else {
        rxUnclearList.innerHTML = unclear.map(u => `
          <div class="unclear-item-box">
            <span class="unclear-cat">⚠️ Unclear Detail: ${escapeHtml(u.category)}</span>
            <div class="unclear-text">${escapeHtml(u.item_text)}</div>
            <p class="unclear-reason"><strong>Reason:</strong> ${escapeHtml(u.reason)}</p>
            <p class="unclear-advice">👉 ${escapeHtml(u.action_advice)}</p>
          </div>
        `).join('');
      }
    }

    // Safety Disclaimer
    if (rxDisclaimerText && data.safety_disclaimer) {
      rxDisclaimerText.textContent = data.safety_disclaimer;
    }

    // Show Results Dashboard
    if (rxLoadingState) rxLoadingState.style.display = 'none';
    if (rxUploadCard) rxUploadCard.style.display = 'none';
    if (rxResultsDashboard) rxResultsDashboard.style.display = 'flex';
  };

  // Submit Prescription Upload Action
  if (rxAnalyzeBtn) {
    rxAnalyzeBtn.addEventListener('click', async () => {
      if (!selectedPrescriptionFile) return;

      const formData = new FormData();
      formData.append('file', selectedPrescriptionFile);
      if (rxNotesInput && rxNotesInput.value.trim()) {
        formData.append('notes', rxNotesInput.value.trim());
      }

      if (rxUploadCard) rxUploadCard.style.display = 'none';
      if (rxResultsDashboard) rxResultsDashboard.style.display = 'none';
      if (rxLoadingState) rxLoadingState.style.display = 'flex';

      try {
        const response = await fetch(`${API_BASE_URL}/api/prescription/explain`, {
          method: 'POST',
          headers: {
            'Authorization': getAuthToken() ? `Bearer ${getAuthToken()}` : ''
          },
          body: formData
        });

        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Failed to process prescription document.');
        }

        const data = await response.json();
        renderPrescriptionResults(data);

      } catch (err) {
        showToast(err.message || 'Error analyzing prescription.');
        if (rxLoadingState) rxLoadingState.style.display = 'none';
        if (rxUploadCard) rxUploadCard.style.display = 'flex';
      }
    });
  }

  // Try Sample Prescription Button
  if (rxTrySampleBtn) {
    rxTrySampleBtn.addEventListener('click', async () => {
      showPage('prescription');

      if (rxUploadCard) rxUploadCard.style.display = 'none';
      if (rxResultsDashboard) rxResultsDashboard.style.display = 'none';
      if (rxLoadingState) rxLoadingState.style.display = 'flex';

      try {
        const response = await fetch(`${API_BASE_URL}/api/prescription/sample`);
        if (!response.ok) throw new Error('Could not load sample prescription.');
        const data = await response.json();
        setTimeout(() => {
          renderPrescriptionResults(data);
        }, 500);
      } catch (err) {
        showToast('Unable to load sample prescription.');
        if (rxLoadingState) rxLoadingState.style.display = 'none';
        if (rxUploadCard) rxUploadCard.style.display = 'flex';
      }
    });
  }

  // Action Bar Handlers: Copy, Print, New Analysis
  if (rxNewAnalysisBtn) {
    rxNewAnalysisBtn.addEventListener('click', () => {
      resetFileUpload();
      if (rxResultsDashboard) rxResultsDashboard.style.display = 'none';
      if (rxUploadCard) rxUploadCard.style.display = 'flex';
    });
  }

  if (rxCopyBtn) {
    rxCopyBtn.addEventListener('click', () => {
      if (!currentPrescriptionExplanation) return;
      const d = currentPrescriptionExplanation;
      let text = `=== PRESCRIPTION EXPLANATION SUMMARY ===\n\n`;
      text += `Problem/Diagnosis: ${d.diagnosis.problem || 'Not Written'}\n${d.diagnosis.explanation}\n\n`;
      text += `SUMMARY:\n- Problem: ${d.summary.problem_summary}\n- Tests: ${d.summary.tests_summary}\n- Medicines: ${d.summary.medicines_summary}\n- Instructions: ${d.summary.instructions_summary}\n\n`;
      text += `MEDICINES:\n`;
      (d.medicines || []).forEach((m, i) => {
        text += `${i+1}. ${m.medicine_name} (${m.strength_dosage}) - ${m.frequency} [${m.abbreviation_explained}]\n   General Use: ${m.general_use}\n   Timing: ${m.timing_food} | Duration: ${m.duration}\n`;
      });
      if (d.unclear_items && d.unclear_items.length > 0) {
        text += `\n⚠️ UNCLEAR ITEMS (CONFIRM WITH DOCTOR/PHARMACIST):\n`;
        d.unclear_items.forEach(u => {
          text += `- ${u.category}: "${u.item_text}" -> ${u.action_advice}\n`;
        });
      }
      text += `\n${d.safety_disclaimer}`;

      navigator.clipboard.writeText(text).then(() => {
        showToast('Prescription explanation copied to clipboard!');
      }).catch(() => {
        showToast('Failed to copy to clipboard.');
      });
    });
  }

  if (rxPrintBtn) {
    rxPrintBtn.addEventListener('click', () => {
      window.print();
    });
  }

  // Initialize Auth, History & Empty Notepad
  renderClinicalNotepad(null);
  verifyAuthSession();
});

