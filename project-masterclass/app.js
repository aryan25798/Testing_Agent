/* =====================================================================
   AI Testing Agent - Interactive Technical Masterclass
   Application Logic, Search Index, Interactive Engines & State
   ===================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // State variables
  const STATE = {
    currentChapter: 'intro',
    theme: localStorage.getItem('masterclass_theme') || 'dark',
    completedChapters: new Set(JSON.parse(localStorage.getItem('masterclass_completed') || '[]')),
    activeFilter: 'all',
    currentFlashcardIndex: 0,
    quizAnswers: {},
  };

  // DOM Elements
  const htmlRoot = document.documentElement;
  const sidebar = document.getElementById('sidebar');
  const mobileToggleBtn = document.getElementById('mobileToggleBtn');
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const progressText = document.getElementById('progressText');
  const progressBarFill = document.getElementById('progressBarFill');
  const searchModalBackdrop = document.getElementById('searchModalBackdrop');
  const searchTriggerBtn = document.getElementById('searchTriggerBtn');
  const searchInput = document.getElementById('searchInput');
  const searchResultsList = document.getElementById('searchResultsList');

  // Flashcards Dataset
  const FLASHCARDS = [
    {
      category: 'Model Context Protocol (MCP)',
      question: 'What is the Model Context Protocol (MCP) and why is it used instead of direct REST API integration?',
      hint: 'Think about dynamic tool discovery vs hardcoding API endpoints.',
      answer: 'MCP is an open standard that allows AI applications (clients) to connect to external developer tools (servers) via standardized stdio/SSE transports. Instead of hardcoding direct Jira or GitHub REST endpoints and schemas into prompt strings, MCP provides dynamic tool discovery, structured schema negotiation, strict project boundary enforcement, and human-in-the-loop approval queues for mutating operations.'
    },
    {
      category: 'LangGraph Orchestration',
      question: 'What is a StateGraph in LangGraph and how do agents pass data between themselves?',
      hint: 'Think about stateful Python dictionaries and node functions.',
      answer: 'A StateGraph is a state machine whose execution nodes are Python functions and whose edges define control flow. In AI Testing Agent, state is stored in `TestingWorkflowState` (a TypedDict). Each node (Agent 1 to 6) accepts the global state, executes its specialized LLM/tool logic, and returns a dictionary of updated keys (e.g. `approved_requirements`, `test_scenarios`). LangGraph merges this dictionary back into the centralized state graph.'
    },
    {
      category: 'Security Architecture',
      question: 'How are sensitive credentials (API keys, GitHub PATs, Jira tokens) protected at rest and in memory?',
      hint: 'Look at `src/core/security/secrets_manager.py`.',
      answer: 'Credentials are encrypted at rest using hardware-accelerated AES-256-GCM via the `cryptography` library. When saved, a random 96-bit nonce is generated, and ciphertext is written to an atomic file (`.secrets_vault.enc`). At runtime, credentials exist only in memory during subprocess execution. Furthermore, zero-token browser storage guarantees keys are never stored in localStorage, and defensive HTTP headers (CSP, nosniff) prevent client-side leaks.'
    },
    {
      category: 'Test Automation (POM)',
      question: 'What is the Page Object Model (POM) and why does Agent 4 write tests using it?',
      hint: 'Separation of locators and test assertions.',
      answer: 'The Page Object Model (POM) is an industry-standard test design pattern that encapsulates web page locators and interaction methods inside reusable page classes (e.g. `BasePage`). The actual test cases (`test_auth.py`) call high-level methods on the page object rather than executing raw CSS/XPath queries directly. If a button locator changes, only the Page Object requires an update—zero test cases break.'
    },
    {
      category: 'AI Model Engine',
      question: 'How does Independent Per-Agent Model Routing work in this platform?',
      hint: 'Look at `AgentModelRouter` in `src/llm/router/agent_model_router.py`.',
      answer: 'Rather than using a single global model for all tasks, the application maintains a per-agent registry. Fast, cost-efficient models with massive context windows (such as `gemini-2.5-flash`) are routed to Requirement Analysis and Scenario Generation, while reasoning-heavy models (such as `gpt-4o` or `gemini-2.5-pro`) are routed to Test Automation and Execution Triage.'
    },
    {
      category: 'Database Architecture',
      question: 'Why was SQLite chosen for this application, and when would you migrate to PostgreSQL?',
      hint: 'Local single-tenant application vs multi-user concurrent enterprise SaaS.',
      answer: 'SQLite is an embedded, zero-configuration database that resides entirely in a single local file (`testing_platform.db`). Because this personal testing assistant runs locally as a single-tenant workspace, SQLite provides lightning-fast zero-latency relational queries without running a separate database server. Migration to PostgreSQL is recommended if the platform evolves into a multi-tenant, cloud-hosted SaaS requiring hundreds of concurrent writers and horizontal scaling.'
    },
    {
      category: 'Browser Sandbox',
      question: 'How does the test execution sandbox isolate browser scripts and capture failures?',
      hint: 'Look at `src/agents/test_execution/agent.py`.',
      answer: 'Agent 5 executes generated test scripts inside an isolated Python subprocess with a strict execution timeout (120 seconds). It launches headless Chromium via Playwright or Selenium, captures stdout and stderr, collects browser traces, and executes an AI failure triage classifier to categorize failures into ApplicationDefect, EnvironmentIssue, or FlakyTest.'
    }
  ];

  // Quizzes Dataset
  const QUIZZES = [
    {
      id: 'q1',
      question: 'Which component in the repository is responsible for executing mutating MCP operations (like creating Jira issues or committing files) only after human consent?',
      options: [
        'A) StdioServerParameters in connection_manager.py',
        'B) ApprovalManager in approval_manager.py (Human-in-the-Loop Gate)',
        'C) TrustedHostMiddleware in src/main.py',
        'D) ExtractedRequirement in requirement_analysis/agent.py'
      ],
      correctIndex: 1,
      explanation: 'ApprovalManager gates mutating/write operations. When an agent attempts a mutating action (like github_create_issue), an approval request is saved in SQLite and halted until a human user explicitly clicks Approve in the Approval Queue.'
    },
    {
      id: 'q2',
      question: 'How does the Angular frontend communicate with the FastAPI backend in this implementation?',
      options: [
        'A) Bi-directional real-time WebSockets over ws://127.0.0.1:8000',
        'B) Direct SQLite database query bindings over WebAssembly',
        'C) Asynchronous REST HTTP requests via Angular HttpClient and RxJS Observables',
        'D) gRPC Protocol Buffers over HTTP/2'
      ],
      correctIndex: 2,
      explanation: 'The frontend interacts with the FastAPI backend through standard asynchronous REST HTTP calls using Angular\'s built-in HttpClient service, returning RxJS Observables that update component signals and template state.'
    },
    {
      id: 'q3',
      question: 'What is the role of the ProjectIntegrationMapping table in the database?',
      options: [
        'A) It maps CSS selectors to HTML elements on the dashboard',
        'B) It enforces strict project boundaries so agents cannot query or modify repositories outside assigned projects',
        'C) It converts SQLite SQL queries into PostgreSQL syntax',
        'D) It stores temporary browser cookies for Google Chrome'
      ],
      correctIndex: 1,
      explanation: 'ProjectIntegrationMapping establishes project boundary enforcement. When an agent requests a file or Jira issue, the MCP agent client verifies that the requested repository or Jira project key matches the mapped project resources before executing the tool.'
    },
    {
      id: 'q4',
      question: 'What happens when a user clicks "Refresh Discovered Models" in the AI Model Settings page?',
      options: [
        'A) It downloads all open-source Hugging Face weights to the user\'s hard drive',
        'B) It queries live provider endpoints (Google Gemini and OpenAI) via ModelRegistry to discover active available models',
        'C) It re-installs Python and restarts the operating system',
        'D) It resets the SQLite database and deletes all test cases'
      ],
      correctIndex: 1,
      explanation: 'The endpoint /api/v1/models queries the configured provider SDKs dynamically, inspecting available live endpoints and caching their token pricing and context window capabilities without hardcoded model lists.'
    }
  ];

  // Glossary Dataset
  const GLOSSARY = [
    {
      term: 'Model Context Protocol (MCP)',
      simpleDef: 'A universal USB-cable for AI agents that lets them plug into tools like GitHub and Jira.',
      techDef: 'An open JSON-RPC protocol specification standardizing communication between LLM clients and external tool servers over stdio or SSE transports.',
      projectExample: 'Used in `src/integrations/mcp/` to browse GitHub files and retrieve Jira acceptance criteria.'
    },
    {
      term: 'LangGraph StateGraph',
      simpleDef: 'A flowchart where each step is an AI agent that receives work from the previous agent.',
      techDef: 'A graph-based state machine library extending LangChain that manages state transitions, loops, and human-in-the-loop approvals across multi-agent pipelines.',
      projectExample: 'Compiled in `src/workflows/graph.py` to orchestrate all 6 testing agents.'
    },
    {
      term: 'Page Object Model (POM)',
      simpleDef: 'A blueprint of a web page that keeps button selectors in one place so tests don\'t break when UI changes.',
      techDef: 'A test design pattern where web pages are represented by classes with encapsulated element locators and action methods.',
      projectExample: 'Generated by Agent 4 (`test_automation/agent.py`) creating `BasePage` and `LoginPage` classes.'
    },
    {
      term: 'AES-256-GCM',
      simpleDef: 'Bank-grade encryption that locks secret API keys with a digital key and detects any tampering.',
      techDef: 'Advanced Encryption Standard in Galois/Counter Mode providing authenticated symmetric data encryption and integrity assurance.',
      projectExample: 'Implemented in `src/core/security/secrets_manager.py` to encrypt API keys in `.secrets_vault.enc`.'
    },
    {
      term: 'Subprocess Sandbox',
      simpleDef: 'An isolated room where test scripts run so they cannot mess up the main application if they crash.',
      techDef: 'An OS process boundary created via Python\'s `subprocess` module with sanitized environment variables, resource limits, and timeout controls.',
      projectExample: 'Invoked in `src/agents/test_execution/agent.py` to run Playwright Chromium headless browsers.'
    },
    {
      term: 'Project Boundary Guard',
      simpleDef: 'A security fence that stops an AI working on Project A from peeking at Project B\'s private code.',
      techDef: 'An authorization gateway intercepting tool invocations to ensure resource identifiers match the current project\'s mapping whitelist.',
      projectExample: 'Enforced by `mcp_agent_client.py` during `get_github_file` and `get_jira_issues`.'
    }
  ];

  // 1. Initialize Theme
  function applyTheme(theme) {
    STATE.theme = theme;
    htmlRoot.setAttribute('data-theme', theme);
    localStorage.setItem('masterclass_theme', theme);
    if (themeToggleBtn) {
      themeToggleBtn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
      themeToggleBtn.setAttribute('title', theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode');
    }
  }

  applyTheme(STATE.theme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      applyTheme(STATE.theme === 'dark' ? 'light' : 'dark');
    });
  }

  // 2. Mobile Sidebar Toggle
  if (mobileToggleBtn) {
    mobileToggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }

  // 3. Navigation & Chapter Switching
  function navigateToChapter(chapterId) {
    const targetView = document.getElementById(`view-${chapterId}`);
    if (!targetView) return;

    STATE.currentChapter = chapterId;

    // Update active view
    document.querySelectorAll('.chapter-view').forEach(view => view.classList.remove('active'));
    targetView.classList.add('active');

    // Update sidebar navigation
    document.querySelectorAll('.nav-item').forEach(item => {
      if (item.getAttribute('data-chapter') === chapterId) {
        item.classList.add('active');
        item.scrollIntoView({ block: 'nearest' });
      } else {
        item.classList.remove('active');
      }
    });

    // Close mobile drawer on navigation
    if (sidebar.classList.contains('open')) {
      sidebar.classList.remove('open');
    }

    // Update URL hash without jump
    history.replaceState(null, null, `#${chapterId}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      const chapterId = item.getAttribute('data-chapter');
      navigateToChapter(chapterId);
    });
  });

  // Next / Prev Button Clicks
  document.addEventListener('click', (e) => {
    if (e.target.closest('.btn-next-chapter')) {
      const nextId = e.target.closest('.btn-next-chapter').getAttribute('data-next');
      if (nextId) navigateToChapter(nextId);
    }
    if (e.target.closest('.btn-prev-chapter')) {
      const prevId = e.target.closest('.btn-prev-chapter').getAttribute('data-prev');
      if (prevId) navigateToChapter(prevId);
    }
  });

  // 4. Progress Tracking
  function updateProgress() {
    const totalChapters = document.querySelectorAll('.nav-item').length;
    const completedCount = STATE.completedChapters.size;
    const percentage = totalChapters > 0 ? Math.round((completedCount / totalChapters) * 100) : 0;

    if (progressBarFill) progressBarFill.style.width = `${percentage}%`;
    if (progressText) progressText.textContent = `${percentage}% (${completedCount}/${totalChapters} Chapters)`;

    document.querySelectorAll('.nav-item').forEach(item => {
      const chId = item.getAttribute('data-chapter');
      if (STATE.completedChapters.has(chId)) {
        item.classList.add('completed');
        const checkEl = item.querySelector('.chapter-check');
        if (checkEl) checkEl.textContent = '✓';
      } else {
        item.classList.remove('completed');
        const checkEl = item.querySelector('.chapter-check');
        if (checkEl) checkEl.textContent = '○';
      }
    });

    localStorage.setItem('masterclass_completed', JSON.stringify(Array.from(STATE.completedChapters)));
  }

  document.addEventListener('click', (e) => {
    if (e.target.closest('.btn-mark-complete')) {
      const btn = e.target.closest('.btn-mark-complete');
      const chapterId = btn.getAttribute('data-chapter') || STATE.currentChapter;

      if (STATE.completedChapters.has(chapterId)) {
        STATE.completedChapters.delete(chapterId);
        btn.textContent = 'Mark Chapter as Completed';
        btn.classList.remove('btn-complete');
      } else {
        STATE.completedChapters.add(chapterId);
        btn.textContent = '✓ Completed';
        btn.classList.add('btn-complete');
      }
      updateProgress();
    }
  });

  updateProgress();

  // 5. Accordion Interactivity
  document.addEventListener('click', (e) => {
    if (e.target.closest('.accordion-header')) {
      const acc = e.target.closest('.accordion');
      acc.classList.toggle('open');
      const icon = acc.querySelector('.accordion-icon');
      if (icon) icon.textContent = acc.classList.contains('open') ? '▲' : '▼';
    }
    if (e.target.closest('.interview-question-bar')) {
      const item = e.target.closest('.interview-item');
      item.classList.toggle('open');
      const icon = item.querySelector('.interview-toggle-icon');
      if (icon) icon.textContent = item.classList.contains('open') ? '▲' : '▼';
    }
  });

  // 6. Copy Code Button
  document.addEventListener('click', (e) => {
    if (e.target.closest('.copy-btn')) {
      const btn = e.target.closest('.copy-btn');
      const codeBlock = btn.closest('.code-walkthrough').querySelector('pre');
      if (codeBlock) {
        navigator.clipboard.writeText(codeBlock.textContent.trim()).then(() => {
          const origText = btn.textContent;
          btn.textContent = 'Copied!';
          setTimeout(() => { btn.textContent = origText; }, 2000);
        });
      }
    }
  });

  // 7. Flashcards Engine
  const flashcardEl = document.getElementById('flashcard');
  const flashcardCategory = document.getElementById('flashcardCategory');
  const flashcardQuestion = document.getElementById('flashcardQuestion');
  const flashcardAnswer = document.getElementById('flashcardAnswer');
  const flashcardCounter = document.getElementById('flashcardCounter');
  const flashcardPrevBtn = document.getElementById('flashcardPrevBtn');
  const flashcardNextBtn = document.getElementById('flashcardNextBtn');

  function renderFlashcard() {
    if (!flashcardEl || FLASHCARDS.length === 0) return;
    const card = FLASHCARDS[STATE.currentFlashcardIndex];
    flashcardEl.classList.remove('flipped');
    flashcardCategory.textContent = card.category;
    flashcardQuestion.textContent = card.question;
    flashcardAnswer.textContent = card.answer;
    flashcardCounter.textContent = `${STATE.currentFlashcardIndex + 1} / ${FLASHCARDS.length}`;
  }

  if (flashcardEl) {
    flashcardEl.addEventListener('click', () => {
      flashcardEl.classList.toggle('flipped');
    });
  }

  if (flashcardPrevBtn) {
    flashcardPrevBtn.addEventListener('click', () => {
      STATE.currentFlashcardIndex = (STATE.currentFlashcardIndex - 1 + FLASHCARDS.length) % FLASHCARDS.length;
      renderFlashcard();
    });
  }

  if (flashcardNextBtn) {
    flashcardNextBtn.addEventListener('click', () => {
      STATE.currentFlashcardIndex = (STATE.currentFlashcardIndex + 1) % FLASHCARDS.length;
      renderFlashcard();
    });
  }

  renderFlashcard();

  // 8. Quiz Engine
  const quizContainer = document.getElementById('quizContainer');

  function renderQuizzes() {
    if (!quizContainer) return;
    quizContainer.innerHTML = '';

    QUIZZES.forEach((q, qIndex) => {
      const card = document.createElement('div');
      card.className = 'quiz-card';

      const qTitle = document.createElement('div');
      qTitle.className = 'quiz-question';
      qTitle.textContent = `${qIndex + 1}. ${q.question}`;
      card.appendChild(qTitle);

      const optionsWrapper = document.createElement('div');
      optionsWrapper.className = 'quiz-options';

      const explanationBox = document.createElement('div');
      explanationBox.className = 'quiz-explanation';
      explanationBox.textContent = q.explanation;

      q.options.forEach((opt, optIndex) => {
        const optBtn = document.createElement('button');
        optBtn.className = 'quiz-option-btn';
        optBtn.textContent = opt;

        optBtn.addEventListener('click', () => {
          // Disable sibling buttons
          const allButtons = optionsWrapper.querySelectorAll('.quiz-option-btn');
          allButtons.forEach(btn => btn.disabled = true);

          if (optIndex === q.correctIndex) {
            optBtn.classList.add('correct');
            explanationBox.style.display = 'block';
            explanationBox.style.borderColor = 'var(--success)';
            explanationBox.style.backgroundColor = 'var(--success-light)';
            explanationBox.innerHTML = `<strong>Correct!</strong> ${q.explanation}`;
          } else {
            optBtn.classList.add('incorrect');
            allButtons[q.correctIndex].classList.add('correct');
            explanationBox.style.display = 'block';
            explanationBox.style.borderColor = 'var(--danger)';
            explanationBox.style.backgroundColor = 'var(--danger-light)';
            explanationBox.innerHTML = `<strong>Incorrect.</strong> ${q.explanation}`;
          }
        });

        optionsWrapper.appendChild(optBtn);
      });

      card.appendChild(optionsWrapper);
      card.appendChild(explanationBox);
      quizContainer.appendChild(card);
    });
  }

  renderQuizzes();

  // 9. Searchable Glossary Engine
  const glossaryContainer = document.getElementById('glossaryContainer');
  const glossarySearchInput = document.getElementById('glossarySearchInput');

  function renderGlossary(filter = '') {
    if (!glossaryContainer) return;
    glossaryContainer.innerHTML = '';
    const norm = filter.toLowerCase().trim();

    const matches = GLOSSARY.filter(item =>
      item.term.toLowerCase().includes(norm) ||
      item.simpleDef.toLowerCase().includes(norm) ||
      item.techDef.toLowerCase().includes(norm)
    );

    if (matches.length === 0) {
      glossaryContainer.innerHTML = '<div style="color: var(--text-dim); padding: 20px;">No matching glossary terms found.</div>';
      return;
    }

    matches.forEach(item => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <div class="card-title" style="color: var(--primary);">${item.term}</div>
        <p style="margin-bottom: 8px;"><strong>Simple Explanation:</strong> ${item.simpleDef}</p>
        <p style="margin-bottom: 8px; color: var(--text-muted); font-size: 13.5px;"><strong>Technical Definition:</strong> ${item.techDef}</p>
        <div style="background-color: rgba(255, 255, 255, 0.04); padding: 8px 12px; border-radius: 6px; font-size: 12px; border-left: 3px solid var(--purple);">
          <strong>In This Project:</strong> ${item.projectExample}
        </div>
      `;
      glossaryContainer.appendChild(card);
    });
  }

  if (glossarySearchInput) {
    glossarySearchInput.addEventListener('input', (e) => {
      renderGlossary(e.target.value);
    });
  }

  renderGlossary();

  // 10. Global Search Modal (Cmd+K / Ctrl+K)
  const SEARCH_ITEMS = [
    { title: 'Project Overview & Absolute Zero', chapter: 'intro', snippet: 'Problem statement, virtual QA team, manual testing comparison.' },
    { title: 'High-Level Architecture Diagram', chapter: 'architecture', snippet: 'Angular frontend, FastAPI gateway, LangGraph orchestrator, SQLite database.' },
    { title: 'Technology Stack & Comparisons', chapter: 'tech-stack', snippet: 'Why Angular, FastAPI, LiteLLM, Playwright, Selenium, and MCP were chosen.' },
    { title: 'Complete Directory Tree Explorer', chapter: 'directory-tree', snippet: 'Structure of testing-agent-platform, responsibilities of every folder.' },
    { title: 'Frontend Deep Dive: Angular 19', chapter: 'code-frontend', snippet: 'Standalone components, main.ts, ApiService, RxJS, icon.component.ts.' },
    { title: 'Backend Deep Dive: FastAPI Gateway', chapter: 'code-backend', snippet: 'main.py, settings.py, routes, security middleware, trusted hosts.' },
    { title: 'Database Deep Dive: SQLite & Entities', chapter: 'code-database', snippet: 'session.py, entities.py, ER diagram, foreign keys, migrations.' },
    { title: 'AI Engine: Dynamic Model Routing', chapter: 'code-agents', snippet: 'Gemini and OpenAI dynamic discovery, AgentModelRouter, per-agent routing.' },
    { title: 'The 6 Autonomous Testing Agents', chapter: 'agents-6', snippet: 'Requirement Analysis, Scenario Generator, Test Case Designer, Automation, Execution, Reporting.' },
    { title: 'Model Context Protocol (MCP) Deep Dive', chapter: 'code-mcp', snippet: 'stdio transport, GitHub and Atlassian servers, tool discovery, approval queue.' },
    { title: 'Selenium & Playwright Automation Engine', chapter: 'code-automation', snippet: 'Page Object Model code generation, conftest.py, headless browser sandbox.' },
    { title: 'Defensive Security & AES-256 Vault', chapter: 'code-security', snippet: 'secrets_manager.py, zero-token browser storage, prompt injection sanitizer.' },
    { title: 'End-to-End Traced User Journeys', chapter: 'flows', snippet: '5 complete walkthrough flows from requirement to execution report.' },
    { title: 'Practical Code-Reading Exercises', chapter: 'exercises', snippet: 'Hands-on practice finding files, endpoints, and database models.' },
    { title: 'Technical Interview Defense Hub', chapter: 'interview', snippet: 'Levels 1 to 4 interview questions, spoken answers, and common traps.' },
    { title: 'Interactive Flashcards', chapter: 'flashcards', snippet: 'Flip cards covering MCP, LangGraph, AES-256, and Page Object Model.' },
    { title: 'Interactive MCQ Quizzes', chapter: 'quizzes', snippet: 'Multiple-choice questions with instant grading and explanations.' },
    { title: 'Searchable Technical Glossary', chapter: 'glossary', snippet: 'Terms explained in simple English, technical English, and project context.' },
    { title: '17-Lesson Learning Roadmap', chapter: 'roadmap', snippet: 'Structured learning journey and final mock technical interview.' }
  ];

  function openSearch() {
    if (searchModalBackdrop) {
      searchModalBackdrop.classList.add('open');
      searchInput.value = '';
      renderSearchResults('');
      setTimeout(() => searchInput.focus(), 50);
    }
  }

  function closeSearch() {
    if (searchModalBackdrop) searchModalBackdrop.classList.remove('open');
  }

  function renderSearchResults(query) {
    if (!searchResultsList) return;
    searchResultsList.innerHTML = '';
    const norm = query.toLowerCase().trim();

    const matches = SEARCH_ITEMS.filter(item =>
      item.title.toLowerCase().includes(norm) ||
      item.snippet.toLowerCase().includes(norm)
    );

    if (matches.length === 0) {
      searchResultsList.innerHTML = '<div style="padding: 16px; color: var(--text-dim); text-align: center;">No matches found.</div>';
      return;
    }

    matches.forEach(item => {
      const el = document.createElement('div');
      el.className = 'search-result-item';
      el.innerHTML = `
        <div class="search-result-title">${item.title}</div>
        <div class="search-result-snippet">${item.snippet}</div>
      `;
      el.addEventListener('click', () => {
        closeSearch();
        navigateToChapter(item.chapter);
      });
      searchResultsList.appendChild(el);
    });
  }

  if (searchTriggerBtn) searchTriggerBtn.addEventListener('click', openSearch);
  if (searchInput) searchInput.addEventListener('input', (e) => renderSearchResults(e.target.value));

  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      openSearch();
    }
    if (e.key === 'Escape') closeSearch();
  });

  if (searchModalBackdrop) {
    searchModalBackdrop.addEventListener('click', (e) => {
      if (e.target === searchModalBackdrop) closeSearch();
    });
  }

  // 11. Initial Routing from Hash
  const initialHash = window.location.hash.replace('#', '');
  if (initialHash && document.getElementById(`view-${initialHash}`)) {
    navigateToChapter(initialHash);
  } else {
    navigateToChapter('intro');
  }
});
