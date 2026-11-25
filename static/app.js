/**
 * Local CP Judge — Frontend Application State & Controller
 * Strict Anti-"Vibe-Coded" Design: Zero Emojis, Lucide Icons, Shadcn Zinc Dark Tokens
 */

"use strict";

const state = {
  contests: [],
  activeContestId: null,
  contestMeta: null,
  activeProblemId: null,
  activeProblem: null,
  activeLang: "cpp",
  activeRefPath: null,
  isReferenceMode: false,
  isDirty: false,
  lastModified: 0,
  autoSync: true,
  monacoEditor: null,
  isMonacoReady: false,
  testResults: [],
  activeFilter: "all",
  activeEventSource: null,
  isJudging: false,
  judgeTotalTests: 0,
};

// =====================================================================
// DOM Elements Cache
// =====================================================================
const elements = {
  contestSelect: document.getElementById("contest-select"),
  btnUpload: document.getElementById("btn-upload"),
  uploadInput: document.getElementById("upload-input"),
  problemTabs: document.getElementById("problem-tabs"),
  btnToolchainStatus: document.getElementById("btn-toolchain-status"),
  toolchainSummaryText: document.getElementById("toolchain-summary-text"),

  // Left Pane
  panePdf: document.getElementById("pane-pdf"),
  pdfViewer: document.getElementById("pdf-viewer"),
  pdfFallback: document.getElementById("pdf-fallback"),
  btnOpenPdfExt: document.getElementById("btn-open-pdf-ext"),
  resizerLeft: document.getElementById("resizer-left"),

  // Center Pane
  paneEditor: document.getElementById("pane-editor"),
  langTabs: document.getElementById("lang-tabs"),
  refSubmissionSelect: document.getElementById("ref-submission-select"),
  chkAutoSync: document.getElementById("chk-auto-sync"),
  refBanner: document.getElementById("ref-banner"),
  btnCopyToWorkspace: document.getElementById("btn-copy-to-workspace"),
  btnReturnWorkspace: document.getElementById("btn-return-workspace"),
  filePathDisplay: document.getElementById("file-path-display"),
  saveIndicator: document.getElementById("save-indicator"),
  btnCopyPath: document.getElementById("btn-copy-path"),
  btnOpenVscode: document.getElementById("btn-open-vscode"),
  btnOpenExplorer: document.getElementById("btn-open-explorer"),
  btnSaveCode: document.getElementById("btn-save-code"),
  editorContainer: document.getElementById("editor-container"),
  editorFallback: document.getElementById("editor-fallback"),
  resizerRight: document.getElementById("resizer-right"),

  // Right Pane
  paneJudge: document.getElementById("pane-judge"),
  btnRunSamples: document.getElementById("btn-run-samples"),
  btnJudgeAll: document.getElementById("btn-judge-all"),
  btnStopJudge: document.getElementById("btn-stop-judge"),
  viewTabs: document.querySelectorAll(".view-tab"),
  viewVerdicts: document.getElementById("view-verdicts"),
  viewCustom: document.getElementById("view-custom"),

  // Judge Verdicts View
  progressBar: document.getElementById("judge-progress-bar"),
  progressStageText: document.getElementById("progress-stage-text"),
  progressCountText: document.getElementById("progress-count-text"),
  progressFill: document.getElementById("progress-fill"),
  summaryBanner: document.getElementById("judge-summary-banner"),
  summaryVerdictBadge: document.getElementById("summary-verdict-badge"),
  metricPassed: document.getElementById("metric-passed"),
  metricTime: document.getElementById("metric-time"),
  metricMemory: document.getElementById("metric-memory"),
  filterTabs: document.querySelectorAll(".filter-tab"),
  filterAllCount: document.getElementById("filter-all-count"),
  filterFailedCount: document.getElementById("filter-failed-count"),
  filterSampleCount: document.getElementById("filter-sample-count"),
  filterSecretCount: document.getElementById("filter-secret-count"),
  testCardsList: document.getElementById("test-cards-list"),

  // Custom Input View
  customStdinInput: document.getElementById("custom-stdin-input"),
  btnRunCustom: document.getElementById("btn-run-custom"),
  customOutputSection: document.getElementById("custom-output-section"),
  customVerdictBadge: document.getElementById("custom-verdict-badge"),
  customTimeVal: document.getElementById("custom-time-val"),
  customMemVal: document.getElementById("custom-mem-val"),
  customStdoutPre: document.getElementById("custom-stdout-pre"),
  customStderrBox: document.getElementById("custom-stderr-box"),
  customStderrPre: document.getElementById("custom-stderr-pre"),

  // Toolchain Modal
  toolchainModal: document.getElementById("toolchain-modal"),
  toolchainModalBody: document.getElementById("toolchain-modal-body"),
  btnCloseModal: document.getElementById("btn-close-modal"),
  btnRefreshToolchains: document.getElementById("btn-refresh-toolchains"),
};

// =====================================================================
// Helper Utilities
// =====================================================================

function refreshIcons() {
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    window.lucide.createIcons();
  }
}

function getEditorCode() {
  if (state.monacoEditor) {
    return state.monacoEditor.getValue();
  }
  return elements.editorFallback.value;
}

function setEditorCode(code, lang = state.activeLang) {
  if (state.monacoEditor) {
    state.monacoEditor.setValue(code || "");
    const monacoLang = lang === "cpp" ? "cpp" : lang === "python" ? "python" : "java";
    const model = state.monacoEditor.getModel();
    if (model && window.monaco) {
      window.monaco.editor.setModelLanguage(model, monacoLang);
    }
  } else {
    elements.editorFallback.value = code || "";
  }
  setDirty(false);
}

function setDirty(isDirty) {
  state.isDirty = isDirty;
  if (isDirty) {
    elements.saveIndicator.textContent = "Unsaved";
    elements.saveIndicator.classList.add("dirty");
  } else {
    elements.saveIndicator.textContent = "Saved";
    elements.saveIndicator.classList.remove("dirty");
  }
}

function getVerdictClass(verdict) {
  const v = (verdict || "").toUpperCase();
  if (v === "AC") return "verdict-ac";
  if (v === "WA") return "verdict-wa";
  if (v === "TLE") return "verdict-tle";
  if (v === "MLE") return "verdict-mle";
  if (v === "RE") return "verdict-re";
  if (v === "CE") return "verdict-ce";
  return "verdict-empty";
}

// =====================================================================
// Monaco Editor Loader & Fallback
// =====================================================================

function initMonacoEditor() {
  if (window.require) {
    window.require.config({
      paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs" },
    });
    window.require(["vs/editor/editor.main"], function () {
      state.monacoEditor = window.monaco.editor.create(elements.editorContainer, {
        value: "",
        language: "cpp",
        theme: "vs-dark",
        automaticLayout: true,
        fontFamily: "'JetBrains Mono', 'Cascadia Code', Consolas, monospace",
        fontSize: 13.5,
        lineNumbersMinChars: 3,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        tabSize: 4,
        insertSpaces: true,
      });

      state.monacoEditor.onDidChangeModelContent(() => {
        if (!state.isReferenceMode) {
          setDirty(true);
        }
      });

      state.isMonacoReady = true;
      elements.editorFallback.style.display = "none";
      elements.editorContainer.style.display = "block";

      // Load initial code if already fetched
      if (state.activeProblem) {
        loadActiveCode();
      }
    });

    // Fallback timer if CDN takes too long
    setTimeout(() => {
      if (!state.isMonacoReady) {
        enableFallbackEditor();
      }
    }, 4000);
  } else {
    enableFallbackEditor();
  }
}

function enableFallbackEditor() {
  elements.editorContainer.style.display = "none";
  elements.editorFallback.style.display = "block";

  elements.editorFallback.addEventListener("input", () => {
    if (!state.isReferenceMode) {
      setDirty(true);
    }
  });

  // Tab key inserts 4 spaces
  elements.editorFallback.addEventListener("keydown", (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const start = elements.editorFallback.selectionStart;
      const end = elements.editorFallback.selectionEnd;
      elements.editorFallback.value =
        elements.editorFallback.value.substring(0, start) +
        "    " +
        elements.editorFallback.value.substring(end);
      elements.editorFallback.selectionStart = elements.editorFallback.selectionEnd = start + 4;
      setDirty(true);
    }
  });
}

// =====================================================================
// 3-Pane Resizer Dragging
// =====================================================================

function initResizers() {
  let isDraggingLeft = false;
  let isDraggingRight = false;

  elements.resizerLeft.addEventListener("mousedown", (e) => {
    isDraggingLeft = true;
    elements.resizerLeft.classList.add("resizing");
    elements.pdfViewer.style.pointerEvents = "none";
    document.body.style.cursor = "col-resize";
  });

  elements.resizerRight.addEventListener("mousedown", (e) => {
    isDraggingRight = true;
    elements.resizerRight.classList.add("resizing");
    elements.pdfViewer.style.pointerEvents = "none";
    document.body.style.cursor = "col-resize";
  });

  document.addEventListener("mousemove", (e) => {
    if (!isDraggingLeft && !isDraggingRight) return;
    const totalWidth = window.innerWidth;

    if (isDraggingLeft) {
      const newWidth = Math.max(200, Math.min(e.clientX, totalWidth * 0.65));
      elements.panePdf.style.flex = `0 0 ${newWidth}px`;
    } else if (isDraggingRight) {
      const newWidth = Math.max(280, Math.min(totalWidth - e.clientX, totalWidth * 0.55));
      elements.paneJudge.style.flex = `0 0 ${newWidth}px`;
    }
  });

  document.addEventListener("mouseup", () => {
    if (isDraggingLeft || isDraggingRight) {
      isDraggingLeft = false;
      isDraggingRight = false;
      elements.resizerLeft.classList.remove("resizing");
      elements.resizerRight.classList.remove("resizing");
      elements.pdfViewer.style.pointerEvents = "auto";
      document.body.style.cursor = "default";
      if (state.monacoEditor) {
        state.monacoEditor.layout();
      }
    }
  });
}

// =====================================================================
// API Communication
// =====================================================================

async function fetchToolchainStatus() {
  try {
    const res = await fetch("/api/system/status");
    if (!res.ok) throw new Error("Failed to query toolchains");
    const data = await res.json();
    renderToolchainsModal(data);

    // Update topbar summary
    const cppOk = data.compilers.cpp && data.compilers.cpp.available;
    const pyOk = data.compilers.python && data.compilers.python.available;
    const javaOk = data.compilers.java && data.compilers.java.available;
    const parts = [];
    if (cppOk) parts.push("C++");
    if (pyOk) parts.push("Python");
    if (javaOk) parts.push("Java");
    elements.toolchainSummaryText.textContent = parts.length > 0 ? `${parts.join("/")} Ready` : "Toolchains Missing";
  } catch (err) {
    elements.toolchainSummaryText.textContent = "Toolchains Error";
  }
}

function renderToolchainsModal(data) {
  const container = elements.toolchainModalBody;
  container.innerHTML = "";

  const items = [
    { label: "C++ Compiler (g++)", key: "cpp" },
    { label: "Python Interpreter", key: "python" },
    { label: "Java Compiler (javac)", key: "java" },
    { label: "Java Runtime (java)", key: "java_runtime" },
  ];

  items.forEach((item) => {
    const info = data.compilers[item.key] || { available: false, version: "Not found", path: "" };
    const row = document.createElement("div");
    row.className = "toolchain-item";
    row.innerHTML = `
      <div class="toolchain-left">
        <span class="toolchain-name">${item.label}</span>
        <span class="toolchain-version">${info.version || info.path || "Binary not in PATH"}</span>
      </div>
      <span class="toolchain-badge ${info.available ? "badge-ready" : "badge-missing"}">
        ${info.available ? "READY" : "MISSING"}
      </span>
    `;
    container.appendChild(row);
  });
}

async function loadContestsList() {
  try {
    const res = await fetch("/api/contests");
    if (!res.ok) throw new Error("Failed to load contests list");
    const contests = await res.json();
    state.contests = contests;

    elements.contestSelect.innerHTML = "";
    if (contests.length === 0) {
      elements.contestSelect.innerHTML = "<option value=''>No contests found</option>";
      return;
    }

    contests.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c.contest_id;
      opt.textContent = `${c.title} (${c.problems.length} problems)`;
      elements.contestSelect.appendChild(opt);
    });

    const targetContestId = state.activeContestId || contests[0].contest_id;
    await selectContest(targetContestId);
  } catch (err) {
    elements.contestSelect.innerHTML = "<option value=''>Error loading contests</option>";
  }
}

async function selectContest(contestId) {
  try {
    const res = await fetch(`/api/contests/${contestId}`);
    if (!res.ok) throw new Error("Contest not found");
    const contestMeta = await res.json();

    state.activeContestId = contestId;
    state.contestMeta = contestMeta;
    elements.contestSelect.value = contestId;

    renderProblemTabs(contestMeta.problems);

    if (contestMeta.problems.length > 0) {
      await selectProblem(contestMeta.problems[0].problem_id);
    }
  } catch (err) {
    console.error("Failed to select contest:", err);
  }
}

function renderProblemTabs(problems) {
  elements.problemTabs.innerHTML = "";

  problems.forEach((prob) => {
    const tab = document.createElement("button");
    tab.className = `problem-tab ${prob.problem_id === state.activeProblemId ? "active" : ""}`;
    tab.dataset.problemId = prob.problem_id;

    const dot = document.createElement("span");
    dot.className = "color-dot";
    dot.style.backgroundColor = prob.color || "#2c4a7a";

    const label = document.createElement("span");
    label.textContent = `${prob.short_name}: ${prob.name}`;

    const limitPill = document.createElement("span");
    limitPill.className = "tab-limit-pill";
    limitPill.textContent = `${prob.time_limit_sec}s`;

    tab.appendChild(dot);
    tab.appendChild(label);
    tab.appendChild(limitPill);

    tab.addEventListener("click", () => selectProblem(prob.problem_id));
    elements.problemTabs.appendChild(tab);
  });
}

async function selectProblem(problemId) {
  if (!state.contestMeta) return;

  const problem = state.contestMeta.problems.find((p) => p.problem_id === problemId);
  if (!problem) return;

  state.activeProblemId = problemId;
  state.activeProblem = problem;
  state.activeRefPath = null;
  state.isReferenceMode = false;

  // Update active tab style
  document.querySelectorAll(".problem-tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.problemId === problemId);
  });

  // Render PDF
  if (problem.has_pdf) {
    elements.pdfViewer.src = `/api/problems/${state.activeContestId}/${problemId}/pdf`;
    elements.pdfViewer.style.display = "block";
    elements.pdfFallback.style.display = "none";
  } else {
    elements.pdfViewer.src = "about:blank";
    elements.pdfViewer.style.display = "none";
    elements.pdfFallback.style.display = "flex";
  }

  // Populate reference submissions selector
  populateReferenceSelector(problem.reference_submissions);

  // Reset judge cards and results
  clearJudgeView();

  // Load code from disk
  await loadActiveCode();
}

function populateReferenceSelector(refSubs) {
  elements.refSubmissionSelect.innerHTML = '<option value="">My Workspace</option>';

  if (!refSubs || Object.keys(refSubs).length === 0) return;

  const categories = [
    { key: "accepted", label: "Accepted" },
    { key: "wrong_answer", label: "Wrong Answer" },
    { key: "time_limit_exceeded", label: "Time Limit Exceeded" },
  ];

  categories.forEach((cat) => {
    const files = refSubs[cat.key];
    if (files && files.length > 0) {
      const optGroup = document.createElement("optgroup");
      optGroup.label = cat.label;
      files.forEach((filename) => {
        const opt = document.createElement("option");
        opt.value = `${cat.key}/${filename}`;
        opt.textContent = `${cat.label} / ${filename}`;
        optGroup.appendChild(opt);
      });
      elements.refSubmissionSelect.appendChild(optGroup);
    }
  });
}

async function loadActiveCode(force = false) {
  if (!state.activeContestId || !state.activeProblemId) return;

  if (state.isDirty && !force) {
    // Do not overwrite user unsaved work unless forced
    return;
  }

  try {
    let url = `/api/problems/${state.activeContestId}/${state.activeProblemId}/code?lang=${state.activeLang}`;
    if (state.activeRefPath) {
      url += `&ref_path=${encodeURIComponent(state.activeRefPath)}`;
    }

    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to load code");
    const data = await res.json();

    setEditorCode(data.code, data.lang);
    state.lastModified = data.last_modified;
    state.isReferenceMode = data.is_reference;

    elements.filePathDisplay.textContent = data.file_path;
    elements.filePathDisplay.title = data.file_path;

    // Toggle reference banner
    if (data.is_reference) {
      elements.refBanner.style.display = "flex";
      if (state.monacoEditor) {
        state.monacoEditor.updateOptions({ readOnly: true });
      } else {
        elements.editorFallback.readOnly = true;
      }
    } else {
      elements.refBanner.style.display = "none";
      if (state.monacoEditor) {
        state.monacoEditor.updateOptions({ readOnly: false });
      } else {
        elements.editorFallback.readOnly = false;
      }
    }

    refreshIcons();
  } catch (err) {
    console.error("Failed to load active code:", err);
  }
}

async function saveCodeToDisk() {
  if (!state.activeContestId || !state.activeProblemId) return;
  if (state.isReferenceMode) return;

  const currentCode = getEditorCode();
  try {
    const res = await fetch(`/api/problems/${state.activeContestId}/${state.activeProblemId}/code`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lang: state.activeLang, code: currentCode }),
    });

    if (!res.ok) throw new Error("Failed to save code");
    const data = await res.json();
    state.lastModified = data.last_modified;
    setDirty(false);
  } catch (err) {
    alert(`Failed to save code: ${err.message}`);
  }
}

// =====================================================================
// Real-Time SSE Judging
// =====================================================================

async function startJudging(suite) {
  if (state.isJudging) return;
  if (!state.activeContestId || !state.activeProblemId) return;

  // Auto-save code first if in workspace mode
  if (!state.isReferenceMode && state.isDirty) {
    await saveCodeToDisk();
  }

  state.isJudging = true;
  state.testResults = [];
  clearJudgeView();

  elements.btnRunSamples.style.display = "none";
  elements.btnJudgeAll.style.display = "none";
  elements.btnStopJudge.style.display = "inline-flex";

  elements.progressBar.style.display = "block";
  elements.progressStageText.textContent = "Compiling solution...";
  elements.progressCountText.textContent = "0 / 0";
  elements.progressFill.style.width = "0%";

  let url = `/api/judge/run-stream?contest_id=${state.activeContestId}&problem_id=${state.activeProblemId}&lang=${state.activeLang}&suite=${suite}`;
  if (state.activeRefPath) {
    url += `&ref_submission=${encodeURIComponent(state.activeRefPath)}`;
  }

  const es = new EventSource(url);
  state.activeEventSource = es;

  es.addEventListener("status", (e) => {
    const data = JSON.parse(e.data);
    elements.progressStageText.textContent = data.message || "Compiling...";
  });

  es.addEventListener("compile_error", (e) => {
    const data = JSON.parse(e.data);
    elements.progressStageText.textContent = "Compilation Error";
    renderCompileErrorCard(data.error);
    renderSummaryBanner({
      overall_verdict: "CE",
      total: 0,
      passed: 0,
      max_time_ms: data.compile_time_ms || 0,
      max_memory_mb: 0,
    });
    stopJudging();
  });

  es.addEventListener("compile_success", (e) => {
    const data = JSON.parse(e.data);
    state.judgeTotalTests = data.total_tests;
    elements.progressStageText.textContent = `Running tests (0 / ${data.total_tests})...`;
    elements.progressCountText.textContent = `0 / ${data.total_tests}`;
  });

  es.addEventListener("test_start", (e) => {
    const data = JSON.parse(e.data);
    elements.progressStageText.textContent = `Running test ${data.index} of ${data.total}: ${data.test_name}`;
    elements.progressCountText.textContent = `${data.index} / ${data.total}`;
    if (data.total > 0) {
      elements.progressFill.style.width = `${Math.round(((data.index - 1) / data.total) * 100)}%`;
    }
  });

  es.addEventListener("test_result", (e) => {
    const tcResult = JSON.parse(e.data);
    state.testResults.push(tcResult);
    appendTestCard(tcResult);
    updateFilterCounts();

    const currentCount = state.testResults.length;
    if (state.judgeTotalTests > 0) {
      elements.progressCountText.textContent = `${currentCount} / ${state.judgeTotalTests}`;
      elements.progressFill.style.width = `${Math.round((currentCount / state.judgeTotalTests) * 100)}%`;
    }
  });

  es.addEventListener("summary", (e) => {
    const summary = JSON.parse(e.data);
    elements.progressFill.style.width = "100%";
    elements.progressStageText.textContent = `Completed — ${summary.passed} of ${summary.total} Passed`;
    renderSummaryBanner(summary);
    stopJudging();
  });

  es.onerror = (err) => {
    console.error("SSE connection error:", err);
    stopJudging();
  };
}

function stopJudging() {
  if (state.activeEventSource) {
    state.activeEventSource.close();
    state.activeEventSource = null;
  }
  state.isJudging = false;
  elements.btnRunSamples.style.display = "inline-flex";
  elements.btnJudgeAll.style.display = "inline-flex";
  elements.btnStopJudge.style.display = "none";
  refreshIcons();
}

function clearJudgeView() {
  elements.testCardsList.innerHTML = "";
  elements.summaryBanner.style.display = "none";
  elements.progressBar.style.display = "none";
  updateFilterCounts();
}

function renderSummaryBanner(summary) {
  elements.summaryBanner.style.display = "flex";
  const badge = elements.summaryVerdictBadge;
  badge.textContent = summary.overall_verdict;
  badge.className = `verdict-badge ${getVerdictClass(summary.overall_verdict)}`;

  elements.metricPassed.textContent = `${summary.passed} / ${summary.total}`;
  elements.metricTime.textContent = `${Number(summary.max_time_ms || 0).toFixed(1)} ms`;
  elements.metricMemory.textContent = `${Number(summary.max_memory_mb || 0).toFixed(1)} MB`;
}

function appendTestCard(tc) {
  // Clear placeholder if present
  const placeholder = elements.testCardsList.querySelector(".empty-state");
  if (placeholder) placeholder.remove();

  const card = document.createElement("div");
  const isFailed = tc.verdict !== "AC";
  const isSample = tc.suite === "sample";

  card.className = `test-card ${isFailed ? "expanded" : ""}`;
  card.dataset.suite = tc.suite;
  card.dataset.verdict = tc.verdict;

  const header = document.createElement("div");
  header.className = "test-card-header";
  header.innerHTML = `
    <div class="test-card-header-left">
      <i data-lucide="chevron-right" class="test-chevron"></i>
      <span class="test-name">${tc.test_name}</span>
      ${tc.description ? `<span class="test-desc" title="${escapeHtml(tc.description)}">${escapeHtml(tc.description)}</span>` : ""}
    </div>
    <div class="test-card-header-right">
      <span class="test-timing">${tc.time_ms.toFixed(1)} ms</span>
      <span class="test-memory">${tc.memory_mb.toFixed(1)} MB</span>
      <span class="verdict-badge ${getVerdictClass(tc.verdict)}">${tc.verdict}</span>
    </div>
  `;

  const body = document.createElement("div");
  body.className = "test-card-body";
  body.style.display = isFailed ? "flex" : "none";

  body.innerHTML = `
    <div class="io-diff-group">
      <div class="io-diff-box">
        <div class="io-diff-title">Standard Input (stdin)</div>
        <pre class="code-preview">${escapeHtml(tc.input_preview || "(empty)")}</pre>
      </div>
      <div class="io-diff-box">
        <div class="io-diff-title">Expected Output</div>
        <pre class="code-preview">${escapeHtml(tc.expected_preview || "(empty)")}</pre>
      </div>
    </div>
    <div class="io-diff-group">
      <div class="io-diff-box">
        <div class="io-diff-title">Actual Output (stdout)</div>
        <pre class="code-preview">${escapeHtml(tc.actual_preview || "(empty)")}</pre>
      </div>
      ${
        tc.stderr_preview
          ? `<div class="io-diff-box">
              <div class="io-diff-title error-title">Standard Error (stderr)</div>
              <pre class="code-preview error-text">${escapeHtml(tc.stderr_preview)}</pre>
            </div>`
          : `<div class="io-diff-box">
              <div class="io-diff-title">Diagnostic Summary</div>
              <div class="diff-message-box ${isFailed ? "mismatch" : ""}">${escapeHtml(tc.diff_message || "Matched")}</div>
            </div>`
      }
    </div>
  `;

  header.addEventListener("click", () => {
    card.classList.toggle("expanded");
    body.style.display = card.classList.contains("expanded") ? "flex" : "none";
  });

  card.appendChild(header);
  card.appendChild(body);
  elements.testCardsList.appendChild(card);

  applyTestCardFilter(card);
  refreshIcons();
}

function renderCompileErrorCard(errorText) {
  const card = document.createElement("div");
  card.className = "test-card expanded";
  card.innerHTML = `
    <div class="test-card-header">
      <div class="test-card-header-left">
        <i data-lucide="x-circle" style="color: var(--verdict-ce);"></i>
        <span class="test-name">Compilation Failure</span>
      </div>
      <div class="test-card-header-right">
        <span class="verdict-badge verdict-ce">CE</span>
      </div>
    </div>
    <div class="test-card-body" style="display: flex;">
      <div class="io-diff-box">
        <div class="io-diff-title error-title">Compiler Diagnostics</div>
        <pre class="code-preview error-text">${escapeHtml(errorText)}</pre>
      </div>
    </div>
  `;
  elements.testCardsList.appendChild(card);
  refreshIcons();
}

function updateFilterCounts() {
  const all = state.testResults.length;
  const failed = state.testResults.filter((t) => t.verdict !== "AC").length;
  const samples = state.testResults.filter((t) => t.suite === "sample").length;
  const secrets = state.testResults.filter((t) => t.suite === "secret").length;

  elements.filterAllCount.textContent = all;
  elements.filterFailedCount.textContent = failed;
  elements.filterSampleCount.textContent = samples;
  elements.filterSecretCount.textContent = secrets;

  // Re-apply filter to all existing cards
  document.querySelectorAll(".test-card").forEach(applyTestCardFilter);
}

function applyTestCardFilter(card) {
  const suite = card.dataset.suite;
  const verdict = card.dataset.verdict;
  const filter = state.activeFilter;

  let visible = true;
  if (filter === "failed") {
    visible = verdict !== "AC";
  } else if (filter === "sample") {
    visible = suite === "sample";
  } else if (filter === "secret") {
    visible = suite === "secret";
  }

  card.style.display = visible ? "block" : "none";
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// =====================================================================
// Custom Input Runner
// =====================================================================

async function runCustomInput() {
  if (!state.activeContestId || !state.activeProblemId) return;

  if (!state.isReferenceMode && state.isDirty) {
    await saveCodeToDisk();
  }

  const customInputText = elements.customStdinInput.value;
  elements.btnRunCustom.disabled = true;
  elements.customOutputSection.style.display = "none";

  try {
    const payload = {
      contest_id: state.activeContestId,
      problem_id: state.activeProblemId,
      lang: state.activeLang,
      custom_input: customInputText,
      ref_submission: state.activeRefPath,
    };

    const res = await fetch("/api/judge/custom", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error("Custom run request failed");
    const data = await res.json();

    elements.customOutputSection.style.display = "flex";
    elements.customVerdictBadge.textContent = data.verdict;
    elements.customVerdictBadge.className = `verdict-badge ${getVerdictClass(data.verdict)}`;
    elements.customTimeVal.textContent = `${Number(data.time_ms || 0).toFixed(1)} ms`;
    elements.customMemVal.textContent = `${Number(data.memory_mb || 0).toFixed(1)} MB`;

    elements.customStdoutPre.textContent = data.stdout_preview || "(empty stdout)";

    if (data.stderr_preview) {
      elements.customStderrBox.style.display = "flex";
      elements.customStderrPre.textContent = data.stderr_preview;
    } else {
      elements.customStderrBox.style.display = "none";
    }
  } catch (err) {
    alert(`Error running custom input: ${err.message}`);
  } finally {
    elements.btnRunCustom.disabled = false;
  }
}

// =====================================================================
// Event Listeners & Initialization
// =====================================================================

function initEventListeners() {
  // Contest select
  elements.contestSelect.addEventListener("change", (e) => {
    if (e.target.value) {
      selectContest(e.target.value);
    }
  });

  // Archive Upload
  elements.btnUpload.addEventListener("click", () => {
    elements.uploadInput.click();
  });

  elements.uploadInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    elements.btnUpload.disabled = true;
    elements.btnUpload.innerHTML = "<i data-lucide='refresh-cw' class='icon-sync'></i> Uploading...";
    refreshIcons();

    try {
      const res = await fetch("/api/contests/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }

      const contestMeta = await res.json();
      await loadContestsList();
      await selectContest(contestMeta.contest_id);
    } catch (err) {
      alert(`Archive upload error: ${err.message}`);
    } finally {
      elements.btnUpload.disabled = false;
      elements.btnUpload.innerHTML = "<i data-lucide='upload'></i> <span>Upload Archive</span>";
      elements.uploadInput.value = "";
      refreshIcons();
    }
  });

  // Open PDF external
  elements.btnOpenPdfExt.addEventListener("click", () => {
    if (state.activeContestId && state.activeProblemId) {
      window.open(`/api/problems/${state.activeContestId}/${state.activeProblemId}/pdf`, "_blank");
    }
  });

  // Language Tabs
  elements.langTabs.querySelectorAll(".lang-tab").forEach((tab) => {
    tab.addEventListener("click", async () => {
      elements.langTabs.querySelectorAll(".lang-tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      state.activeLang = tab.dataset.lang;
      state.activeRefPath = null;
      elements.refSubmissionSelect.value = "";
      await loadActiveCode(true);
    });
  });

  // Reference Submissions Select
  elements.refSubmissionSelect.addEventListener("change", async (e) => {
    const val = e.target.value;
    state.activeRefPath = val || null;
    await loadActiveCode(true);
  });

  // Return to workspace from reference mode
  elements.btnReturnWorkspace.addEventListener("click", async () => {
    state.activeRefPath = null;
    elements.refSubmissionSelect.value = "";
    await loadActiveCode(true);
  });

  // Copy reference code into user workspace
  elements.btnCopyToWorkspace.addEventListener("click", async () => {
    if (!confirm("Copy this reference code into your workspace file? This will overwrite your current file.")) {
      return;
    }
    const refCode = getEditorCode();
    state.activeRefPath = null;
    elements.refSubmissionSelect.value = "";
    await loadActiveCode(true);
    setEditorCode(refCode);
    await saveCodeToDisk();
  });

  // Copy file path
  elements.btnCopyPath.addEventListener("click", () => {
    const pathText = elements.filePathDisplay.textContent;
    if (pathText) {
      navigator.clipboard.writeText(pathText);
      elements.saveIndicator.textContent = "Path Copied!";
      setTimeout(() => setDirty(state.isDirty), 1500);
    }
  });

  // Open in VS Code
  elements.btnOpenVscode.addEventListener("click", async () => {
    if (!state.activeContestId || !state.activeProblemId) return;
    try {
      await fetch(`/api/problems/${state.activeContestId}/${state.activeProblemId}/open-external`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: "vscode", lang: state.activeLang }),
      });
    } catch (err) {
      console.error(err);
    }
  });

  // Open in Explorer
  elements.btnOpenExplorer.addEventListener("click", async () => {
    if (!state.activeContestId || !state.activeProblemId) return;
    try {
      await fetch(`/api/problems/${state.activeContestId}/${state.activeProblemId}/open-external`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: "explorer", lang: state.activeLang }),
      });
    } catch (err) {
      console.error(err);
    }
  });

  // Save button
  elements.btnSaveCode.addEventListener("click", saveCodeToDisk);

  // Auto-sync toggle
  elements.chkAutoSync.addEventListener("change", (e) => {
    state.autoSync = e.target.checked;
  });

  // Judge Actions
  elements.btnRunSamples.addEventListener("click", () => startJudging("sample"));
  elements.btnJudgeAll.addEventListener("click", () => startJudging("all"));
  elements.btnStopJudge.addEventListener("click", stopJudging);

  // View tabs (Test Verdicts vs Custom Input)
  elements.viewTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      elements.viewTabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const targetView = tab.dataset.view;
      if (targetView === "verdicts") {
        elements.viewVerdicts.classList.add("active");
        elements.viewCustom.classList.remove("active");
      } else {
        elements.viewVerdicts.classList.remove("active");
        elements.viewCustom.classList.add("active");
      }
    });
  });

  // Filter tabs
  elements.filterTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      elements.filterTabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      state.activeFilter = tab.dataset.filter;
      updateFilterCounts();
    });
  });

  // Custom Input Run
  elements.btnRunCustom.addEventListener("click", runCustomInput);

  // Toolchain modal open & close
  elements.btnToolchainStatus.addEventListener("click", () => {
    elements.toolchainModal.style.display = "flex";
    fetchToolchainStatus();
    refreshIcons();
  });

  elements.btnCloseModal.addEventListener("click", () => {
    elements.toolchainModal.style.display = "none";
  });

  elements.btnRefreshToolchains.addEventListener("click", fetchToolchainStatus);

  // Close modal when clicking backdrop
  elements.toolchainModal.addEventListener("click", (e) => {
    if (e.target === elements.toolchainModal) {
      elements.toolchainModal.style.display = "none";
    }
  });

  // Global Keyboard Shortcuts
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault();
      saveCodeToDisk();
    }
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      startJudging("sample");
    }
  });

  // Auto-sync polling every 2 seconds
  setInterval(async () => {
    if (!state.autoSync || state.isDirty || state.isReferenceMode || !state.activeProblemId) {
      return;
    }
    try {
      const url = `/api/problems/${state.activeContestId}/${state.activeProblemId}/code?lang=${state.activeLang}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (data.last_modified > state.lastModified) {
          setEditorCode(data.code, data.lang);
          state.lastModified = data.last_modified;
        }
      }
    } catch (e) {
      // Ignore background sync errors
    }
  }, 2000);
}

// =====================================================================
// App Entrypoint
// =====================================================================

document.addEventListener("DOMContentLoaded", async () => {
  initResizers();
  initEventListeners();
  initMonacoEditor();
  await fetchToolchainStatus();
  await loadContestsList();
  refreshIcons();
});
