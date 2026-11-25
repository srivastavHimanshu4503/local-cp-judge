/**
 * Local CP Judge — Frontend Application State & Controller
 * Strict Anti-"Vibe-Coded" Design: Zero Emojis, Lucide Icons, Shadcn Zinc Dark Tokens
 */

"use strict";

function getOrCreateSessionId() {
  const KEY = "localcp_session_id";
  let sid = localStorage.getItem(KEY);
  if (!sid || !/^[a-zA-Z0-9_\-]{8,64}$/.test(sid)) {
    const rand = (window.crypto && window.crypto.randomUUID)
      ? window.crypto.randomUUID().replace(/-/g, "")
      : (Math.random().toString(36).slice(2) + Date.now().toString(36));
    sid = `u_${rand}`.slice(0, 32);
    localStorage.setItem(KEY, sid);
  }
  return sid;
}

const SESSION_ID = getOrCreateSessionId();

// Attach X-Session-Id to all same-origin /api/ requests so every browser has an isolated workspace
const _origFetch = window.fetch.bind(window);
window.fetch = function (input, init = {}) {
  const urlStr = typeof input === "string" ? input : (input && input.url ? input.url : "");
  if (urlStr.startsWith("/api/")) {
    const headers = new Headers(init.headers || (input instanceof Request ? input.headers : undefined));
    if (!headers.has("X-Session-Id")) {
      headers.set("X-Session-Id", SESSION_ID);
    }
    init = { ...init, headers };
  }
  return _origFetch(input, init);
};

const state = {
  contests: [],
  activeContestId: null,
  contestMeta: null,
  activeProblemId: null,
  activeProblem: null,
  activeLang: "python", // Python is default
  activeRefPath: null,
  isReferenceMode: false,
  isDirty: false,
  lastModified: 0,
  autoSync: true,
  monacoEditor: null,
  monacoDiffEditor: null,
  diffViewMode: "text", // "text" or "diff"
  activeTestcase: null,
  customTests: [],
  problemStatuses: {},
  editorFontSize: parseFloat(localStorage.getItem("obsidian_editor_font_size")) || 14,
  isWordWrap: localStorage.getItem("local_cp_word_wrap") === "true",
  isMonacoReady: false,
  testResults: [],
  activeFilter: "all",
  activeEventSource: null,
  isJudging: false,
  judgeTotalTests: 0,
  isConsoleOpen: true,
  consoleHeight: 240,
  isSidebarOpen: true,
  timer: {
    mode: "practice", // "practice" or "contest"
    isRunning: false,
    elapsedSec: 0,
    intervalId: null,
  },
};

// =====================================================================
// DOM Elements Cache
// =====================================================================
const elements = {
  contestSelect: document.getElementById("contest-select"),
  mobileProblemSelect: document.getElementById("mobile-problem-select"),
  mobilePaneSwitcher: document.getElementById("mobile-pane-switcher"),
  btnUpload: document.getElementById("btn-upload"),
  uploadInput: document.getElementById("upload-input"),
  problemTabs: document.getElementById("problem-tabs"),
  btnToolchainStatus: document.getElementById("btn-toolchain-status"),
  toolchainSummaryText: document.getElementById("toolchain-summary-text"),

  // Sidebar Controls
  btnToggleSidebar: document.getElementById("btn-toggle-sidebar"),
  btnCollapseSidebar: document.getElementById("btn-collapse-sidebar"),

  // Contest Timer
  contestTimer: document.getElementById("contest-timer"),
  timerDisplay: document.getElementById("timer-display"),
  btnTimerToggle: document.getElementById("btn-timer-toggle"),
  timerToggleIcon: document.getElementById("timer-toggle-icon"),
  btnTimerReset: document.getElementById("btn-timer-reset"),
  btnTimerMode: document.getElementById("btn-timer-mode"),
  timerModeBadge: document.getElementById("timer-mode-badge"),

  // Left Column (Statement)
  panePdf: document.getElementById("pane-pdf"),
  pdfViewer: document.getElementById("pdf-viewer"),
  pdfFallback: document.getElementById("pdf-fallback"),
  btnOpenPdfExt: document.getElementById("btn-open-pdf-ext"),
  resizerCols: document.getElementById("resizer-cols"),

  // Right Column (Workspace)
  workspaceRight: document.getElementById("workspace-right"),
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

  // Zoom Controls
  btnZoomIn: document.getElementById("btn-zoom-in"),
  btnZoomOut: document.getElementById("btn-zoom-out"),
  btnZoomReset: document.getElementById("btn-zoom-reset"),
  zoomLevelText: document.getElementById("zoom-level-text"),
  btnToggleWrap: document.getElementById("btn-toggle-wrap"),
  editorBody: document.getElementById("editor-body"),

  editorContainer: document.getElementById("editor-container"),
  editorFallback: document.getElementById("editor-fallback"),
  editorDropzone: document.getElementById("editor-dropzone"),
  resizerConsole: document.getElementById("resizer-console"),

  // Lower Section (Testing Console)
  paneConsole: document.getElementById("pane-console"),
  btnToggleConsole: document.getElementById("btn-toggle-console"),
  btnMinimizeConsole: document.getElementById("btn-minimize-console"),
  consoleChevronIcon: document.getElementById("console-chevron-icon"),
  btnRunSamples: document.getElementById("btn-run-samples"),
  btnJudgeAll: document.getElementById("btn-judge-all"),
  btnStopJudge: document.getElementById("btn-stop-judge"),
  chkFailFast: document.getElementById("chk-fail-fast"),
  viewTabs: document.querySelectorAll(".view-tab"),
  viewVerdicts: document.getElementById("view-verdicts"),
  viewCustom: document.getElementById("view-custom"),

  // Judge Verdicts View
  progressBar: document.getElementById("judge-progress-bar"),
  progressStageText: document.getElementById("progress-stage-text"),
  progressCountText: document.getElementById("progress-count-text"),
  progressFill: document.getElementById("progress-fill"),
  judgeEmptyState: document.getElementById("judge-empty-state"),

  // LeetCode Result View
  leetcodeResultView: document.getElementById("leetcode-result-view"),
  lcVerdictBannerCard: document.getElementById("lc-verdict-banner-card"),
  lcBannerIcon: document.getElementById("lc-banner-icon"),
  lcBannerTitle: document.getElementById("lc-banner-title"),
  lcBannerSubtitle: document.getElementById("lc-banner-subtitle"),
  problemStatusPill: document.getElementById("problem-status-pill"),
  lcVerdictTitle: document.getElementById("lc-verdict-title"),
  lcPassedCounter: document.getElementById("lc-passed-counter"),
  lcMetricsRow: document.getElementById("lc-metrics-row"),
  lcRuntimeVal: document.getElementById("lc-runtime-val"),
  lcMemoryVal: document.getElementById("lc-memory-val"),
  lcCompileErrorBox: document.getElementById("lc-compile-error-box"),
  lcCompileErrorText: document.getElementById("lc-compile-error-text"),
  lcTestcaseInspector: document.getElementById("lc-testcase-inspector"),
  lcTabsLabel: document.getElementById("lc-tabs-label"),
  lcCasePills: document.getElementById("lc-case-pills"),
  lcInputContent: document.getElementById("lc-input-content"),
  lcActualLabel: document.getElementById("lc-actual-label"),
  lcActualContent: document.getElementById("lc-actual-content"),
  lcExpectedGroup: document.getElementById("lc-expected-group"),
  lcExpectedContent: document.getElementById("lc-expected-content"),
  lcDiagGroup: document.getElementById("lc-diag-group"),
  lcDiagLabel: document.getElementById("lc-diag-label"),
  lcDiagContent: document.getElementById("lc-diag-content"),
  btnCopyLcInput: document.getElementById("btn-copy-lc-input"),
  btnCopyLcOutput: document.getElementById("btn-copy-lc-output"),
  btnCopyLcExpected: document.getElementById("btn-copy-lc-expected"),
  btnToggleAllTests: document.getElementById("btn-toggle-all-tests"),
  lcAllTestsChevron: document.getElementById("lc-all-tests-chevron"),
  lcAllTestsLabel: document.getElementById("lc-all-tests-label"),
  lcAllTestsTable: document.getElementById("lc-all-tests-table"),

  // Backward compatibility fallback elements
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
  btnSaveCustomTest: document.getElementById("btn-save-custom-test"),
  customOutputSection: document.getElementById("custom-output-section"),
  customVerdictBadge: document.getElementById("custom-verdict-badge"),
  customTimeVal: document.getElementById("custom-time-val"),
  customMemVal: document.getElementById("custom-mem-val"),
  customStdoutPre: document.getElementById("custom-stdout-pre"),
  customStderrBox: document.getElementById("custom-stderr-box"),
  customStderrPre: document.getElementById("custom-stderr-pre"),
  customTestsList: document.getElementById("custom-tests-list"),
  customTestsCount: document.getElementById("custom-tests-count"),
  btnRunCustomTests: document.getElementById("btn-run-custom-tests"),

  // Diff View Elements
  btnModeText: document.getElementById("btn-mode-text"),
  btnModeDiff: document.getElementById("btn-mode-diff"),
  lcWhitespaceBadges: document.getElementById("lc-whitespace-badges"),
  lcDiffEditorWrapper: document.getElementById("lc-diff-editor-wrapper"),
  lcMonacoDiffContainer: document.getElementById("lc-monaco-diff-container"),
  lcActualGroup: document.getElementById("lc-actual-group"),
  btnPinActiveTest: document.getElementById("btn-pin-active-test"),

  // Stress Tester Elements
  viewStress: document.getElementById("view-stress"),
  stressRefSelect: document.getElementById("stress-ref-select"),
  stressIterations: document.getElementById("stress-iterations"),
  btnRunStress: document.getElementById("btn-run-stress"),
  stressResultsBox: document.getElementById("stress-results-box"),
  stressStatusBadge: document.getElementById("stress-status-badge"),
  stressStatusText: document.getElementById("stress-status-text"),
  stressCounterexampleDetails: document.getElementById("stress-counterexample-details"),
  stressInputContent: document.getElementById("stress-input-content"),
  stressActualContent: document.getElementById("stress-actual-content"),
  stressExpectedContent: document.getElementById("stress-expected-content"),
  stressDiffGroup: document.getElementById("stress-diff-group"),
  stressDiffContent: document.getElementById("stress-diff-content"),
  btnPinStressInput: document.getElementById("btn-pin-stress-input"),
  btnCopyStressInput: document.getElementById("btn-copy-stress-input"),
  btnCopyStressActual: document.getElementById("btn-copy-stress-actual"),
  btnCopyStressExpected: document.getElementById("btn-copy-stress-expected"),

  // Toolchain Modal
  toolchainModal: document.getElementById("toolchain-modal"),
  toolchainModalBody: document.getElementById("toolchain-modal-body"),
  btnCloseModal: document.getElementById("btn-close-modal"),
  btnRefreshToolchains: document.getElementById("btn-refresh-toolchains"),
};

// Aliases for backward compatibility
elements.paneJudge = elements.paneConsole;
elements.resizerLeft = elements.resizerCols;
elements.resizerRight = elements.resizerConsole;

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
// Workspace Zoom Controller & Font Sizing
// =====================================================================

const BASE_FONT_SIZE = 14;
const MIN_FONT_SIZE = 9;
const MAX_FONT_SIZE = 36;

function updateZoomUI(fontSize) {
  if (elements.zoomLevelText) {
    const pct = Math.round((fontSize / BASE_FONT_SIZE) * 100);
    elements.zoomLevelText.textContent = `${pct}%`;
  }
  localStorage.setItem("obsidian_editor_font_size", fontSize);

  if (elements.editorFallback) {
    elements.editorFallback.style.fontSize = `${fontSize}px`;
  }
  if (state.monacoDiffEditor) {
    try {
      state.monacoDiffEditor.updateOptions({
        fontSize: Math.max(9, fontSize - 1.5),
      });
    } catch (e) {}
  }
}

function setEditorFontSize(newSize) {
  const clamped = Math.max(MIN_FONT_SIZE, Math.min(MAX_FONT_SIZE, newSize));
  state.editorFontSize = clamped;
  if (state.monacoEditor) {
    state.monacoEditor.updateOptions({ fontSize: clamped });
  }
  updateZoomUI(clamped);
}

function zoomIn() {
  setEditorFontSize((state.editorFontSize || BASE_FONT_SIZE) + 1);
}

function zoomOut() {
  setEditorFontSize((state.editorFontSize || BASE_FONT_SIZE) - 1);
}

function zoomReset() {
  setEditorFontSize(BASE_FONT_SIZE);
}

// =====================================================================
// Word Wrap Controller
// =====================================================================

function applyWordWrap(enable) {
  state.isWordWrap = enable;
  localStorage.setItem("local_cp_word_wrap", enable ? "true" : "false");

  if (elements.btnToggleWrap) {
    elements.btnToggleWrap.classList.toggle("active", enable);
    elements.btnToggleWrap.title = enable ? "Disable Word Wrap (Alt + Z)" : "Enable Word Wrap (Alt + Z)";
  }

  const wrapOption = enable ? "on" : "off";
  if (state.monacoEditor) {
    state.monacoEditor.updateOptions({ wordWrap: wrapOption });
  }
  if (state.monacoDiffEditor) {
    try {
      state.monacoDiffEditor.updateOptions({ wordWrap: wrapOption });
    } catch (e) {}
  }
  if (elements.editorFallback) {
    elements.editorFallback.style.whiteSpace = enable ? "pre-wrap" : "pre";
    elements.editorFallback.wrap = enable ? "soft" : "off";
  }
}

function toggleWordWrap() {
  applyWordWrap(!state.isWordWrap);
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
      window.monaco.editor.defineTheme("obsidian-dark", {
        base: "vs-dark",
        inherit: true,
        rules: [
          { token: "comment", foreground: "6B7280", fontStyle: "italic" },
          { token: "keyword", foreground: "A78BFA" },
          { token: "string", foreground: "34D399" },
          { token: "number", foreground: "FBBF24" },
          { token: "type", foreground: "60A5FA" },
        ],
        colors: {
          "editor.background": "#0D0D11",
          "editor.foreground": "#FAFAFA",
          "editorLineNumber.foreground": "#52525B",
          "editorLineNumber.activeForeground": "#A1A1AA",
          "editorGutter.background": "#0D0D11",
          "editor.lineHighlightBackground": "#141419",
          "editorCursor.foreground": "#FAFAFA",
          "editor.selectionBackground": "#27272A",
          "scrollbarSlider.background": "#27272A80",
          "scrollbarSlider.hoverBackground": "#3F3F46B0",
          "scrollbarSlider.activeBackground": "#52525BB0",
        },
      });

      state.monacoEditor = window.monaco.editor.create(elements.editorContainer, {
        value: "",
        language: "python",
        theme: "obsidian-dark",
        automaticLayout: true,
        fontFamily: "'JetBrains Mono', 'Cascadia Code', Consolas, monospace",
        fontSize: state.editorFontSize || 14,
        lineHeight: 22,
        mouseWheelZoom: true,
        wordWrap: state.isWordWrap ? "on" : "off",
        lineNumbersMinChars: 3,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        padding: { top: 10, bottom: 10 },
        renderLineHighlight: "line",
        tabSize: 4,
        insertSpaces: true,
      });

      state.monacoEditor.onDidChangeModelContent(() => {
        if (!state.isReferenceMode) {
          setDirty(true);
        }
      });

      // Synchronize Zoom UI when editor font size changes (e.g. via Ctrl+MouseWheel)
      state.monacoEditor.onDidChangeConfiguration((e) => {
        if (e.hasChanged(window.monaco.editor.EditorOption.fontSize)) {
          const currentSize = state.monacoEditor.getOption(window.monaco.editor.EditorOption.fontSize);
          state.editorFontSize = currentSize;
          updateZoomUI(currentSize);
        }
      });

      // Initialize Side-by-Side Monaco Diff Editor
      if (elements.lcMonacoDiffContainer) {
        state.monacoDiffEditor = window.monaco.editor.createDiffEditor(elements.lcMonacoDiffContainer, {
          theme: "obsidian-dark",
          automaticLayout: true,
          fontFamily: "'JetBrains Mono', 'Cascadia Code', Consolas, monospace",
          fontSize: Math.max(9, (state.editorFontSize || 14) - 1.5),
          readOnly: true,
          renderSideBySide: true,
          wordWrap: state.isWordWrap ? "on" : "off",
          scrollBeyondLastLine: false,
          minimap: { enabled: false },
          lineNumbersMinChars: 2,
        });
      }

      // Register Monaco Editor Keyboard Shortcuts
      // Ctrl + ' (or Cmd + ') to Run Samples
      state.monacoEditor.addCommand(window.monaco.KeyMod.CtrlCmd | window.monaco.KeyCode.Quote, () => {
        startJudging("sample");
      });
      // Ctrl + Enter (or Cmd + Enter) to Judge All
      state.monacoEditor.addCommand(window.monaco.KeyMod.CtrlCmd | window.monaco.KeyCode.Enter, () => {
        startJudging("all");
      });
      // Ctrl + S (or Cmd + S) to Save Code
      state.monacoEditor.addCommand(window.monaco.KeyMod.CtrlCmd | window.monaco.KeyCode.KeyS, () => {
        saveCodeToDisk();
      });
      // Alt + Z to Toggle Word Wrap
      state.monacoEditor.addCommand(window.monaco.KeyMod.Alt | window.monaco.KeyCode.KeyZ, () => {
        toggleWordWrap();
      });

      state.isMonacoReady = true;
      elements.editorFallback.style.display = "none";
      elements.editorContainer.style.display = "block";
      updateZoomUI(state.editorFontSize || 14);
      applyWordWrap(state.isWordWrap);

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

  // Tab key inserts 4 spaces & handle keyboard shortcuts in fallback textarea
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
    // Ctrl + ' to Run Samples
    if ((e.ctrlKey || e.metaKey) && (e.key === "'" || e.code === "Quote")) {
      e.preventDefault();
      startJudging("sample");
    }
    // Ctrl + Enter to Judge All
    if ((e.ctrlKey || e.metaKey) && (e.key === "Enter" || e.code === "Enter")) {
      e.preventDefault();
      startJudging("all");
    }
    // Ctrl + S to Save
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault();
      saveCodeToDisk();
    }
  });
}

// Problem Status (Solved vs Failed Attempt) Helpers
function loadProblemStatuses() {
  if (!state.activeContestId) return;
  try {
    const raw = localStorage.getItem(`localcp_problem_statuses_${state.activeContestId}`);
    state.problemStatuses = raw ? JSON.parse(raw) : {};
  } catch (e) {
    state.problemStatuses = {};
  }
}

function saveProblemStatuses() {
  if (!state.activeContestId) return;
  try {
    localStorage.setItem(`localcp_problem_statuses_${state.activeContestId}`, JSON.stringify(state.problemStatuses));
  } catch (e) {}
}

function updateProblemStatusPill() {
  if (!elements.problemStatusPill) return;
  if (!state.activeProblemId) {
    elements.problemStatusPill.style.display = "none";
    return;
  }
  elements.problemStatusPill.style.display = "inline-flex";
  const stat = state.problemStatuses[state.activeProblemId];
  if (stat && stat.verdict === "AC") {
    elements.problemStatusPill.className = "problem-status-pill status-solved";
    elements.problemStatusPill.textContent = "Solved (AC) ✓";
  } else if (stat && stat.verdict) {
    elements.problemStatusPill.className = "problem-status-pill status-failed";
    elements.problemStatusPill.textContent = `Wrong Attempt (${stat.verdict}) ✕`;
  } else {
    elements.problemStatusPill.className = "problem-status-pill status-unsolved";
    elements.problemStatusPill.textContent = "Not Attempted";
  }
}

// =====================================================================
// VS Code-Style Left Sidebar Toggle
// =====================================================================

function toggleSidebar(forceOpen = null) {
  const isCurrentlyCollapsed = elements.panePdf.classList.contains("collapsed");
  const shouldOpen = forceOpen !== null ? forceOpen : isCurrentlyCollapsed;

  if (shouldOpen) {
    elements.panePdf.classList.remove("collapsed");
    if (elements.resizerCols) elements.resizerCols.classList.remove("hidden");
    if (elements.btnToggleSidebar) elements.btnToggleSidebar.classList.add("active");
    state.isSidebarOpen = true;
  } else {
    elements.panePdf.classList.add("collapsed");
    if (elements.resizerCols) elements.resizerCols.classList.add("hidden");
    if (elements.btnToggleSidebar) elements.btnToggleSidebar.classList.remove("active");
    state.isSidebarOpen = false;
  }
  refreshIcons();
  if (state.monacoEditor) {
    setTimeout(() => state.monacoEditor.layout(), 60);
  }
}

// =====================================================================
// LeetCode-Style Console Toggle & Dual Resizers
// =====================================================================

function toggleConsole(forceOpen = null) {
  const isCurrentlyCollapsed = elements.paneConsole.classList.contains("collapsed");
  const shouldOpen = forceOpen !== null ? forceOpen : isCurrentlyCollapsed;

  if (shouldOpen) {
    elements.paneConsole.classList.remove("collapsed");
    const h = state.consoleHeight || 240;
    elements.paneConsole.style.flex = `0 0 ${h}px`;
    if (elements.resizerConsole) elements.resizerConsole.classList.remove("hidden");
    if (elements.consoleChevronIcon) {
      elements.consoleChevronIcon.innerHTML = '<i data-lucide="chevron-down"></i>';
    }
    state.isConsoleOpen = true;
  } else {
    elements.paneConsole.classList.add("collapsed");
    elements.paneConsole.style.flex = "0 0 44px";
    if (elements.resizerConsole) elements.resizerConsole.classList.add("hidden");
    if (elements.consoleChevronIcon) {
      elements.consoleChevronIcon.innerHTML = '<i data-lucide="chevron-up"></i>';
    }
    state.isConsoleOpen = false;
  }
  refreshIcons();
  if (state.monacoEditor) {
    setTimeout(() => state.monacoEditor.layout(), 60);
  }
}

function initResizers() {
  let isDraggingCols = false;
  let isDraggingConsole = false;

  if (elements.resizerCols) {
    elements.resizerCols.addEventListener("mousedown", (e) => {
      isDraggingCols = true;
      elements.resizerCols.classList.add("resizing");
      elements.pdfViewer.style.pointerEvents = "none";
      document.body.style.cursor = "col-resize";
    });
  }

  if (elements.resizerConsole) {
    elements.resizerConsole.addEventListener("mousedown", (e) => {
      isDraggingConsole = true;
      elements.resizerConsole.classList.add("resizing");
      elements.pdfViewer.style.pointerEvents = "none";
      document.body.style.cursor = "row-resize";
    });
  }

  document.addEventListener("mousemove", (e) => {
    if (!isDraggingCols && !isDraggingConsole) return;
    const totalWidth = window.innerWidth;

    if (isDraggingCols) {
      const newWidth = Math.max(260, Math.min(e.clientX, totalWidth * 0.75));
      elements.panePdf.style.flex = `0 0 ${newWidth}px`;
    } else if (isDraggingConsole && elements.workspaceRight) {
      const rect = elements.workspaceRight.getBoundingClientRect();
      const newHeight = Math.max(120, Math.min(rect.bottom - e.clientY, rect.height * 0.85));
      elements.paneConsole.style.flex = `0 0 ${newHeight}px`;
      state.consoleHeight = newHeight;
    }
  });

  document.addEventListener("mouseup", () => {
    if (isDraggingCols || isDraggingConsole) {
      isDraggingCols = false;
      isDraggingConsole = false;
      if (elements.resizerCols) elements.resizerCols.classList.remove("resizing");
      if (elements.resizerConsole) elements.resizerConsole.classList.remove("resizing");
      elements.pdfViewer.style.pointerEvents = "auto";
      document.body.style.cursor = "default";
      if (state.monacoEditor) {
        state.monacoEditor.layout();
      }
    }
  });
}

// =====================================================================
// Contest & Practice Stopwatch / Timer
// =====================================================================

function initTimer() {
  updateTimerDisplay();

  if (elements.btnTimerToggle) {
    elements.btnTimerToggle.addEventListener("click", toggleTimer);
  }
  if (elements.btnTimerReset) {
    elements.btnTimerReset.addEventListener("click", resetTimer);
  }
  if (elements.btnTimerMode) {
    elements.btnTimerMode.addEventListener("click", switchTimerMode);
  }
}

function toggleTimer() {
  if (state.timer.isRunning) {
    pauseTimer();
  } else {
    startTimer();
  }
}

function startTimer() {
  if (state.timer.isRunning) return;
  state.timer.isRunning = true;
  if (elements.contestTimer) elements.contestTimer.classList.add("running");
  if (elements.timerToggleIcon) elements.timerToggleIcon.setAttribute("data-lucide", "pause");
  refreshIcons();

  state.timer.intervalId = setInterval(() => {
    if (state.timer.mode === "practice") {
      state.timer.elapsedSec++;
    } else {
      if (state.timer.elapsedSec > 0) {
        state.timer.elapsedSec--;
      } else {
        pauseTimer();
        alert("Contest time is up!");
      }
    }
    updateTimerDisplay();
  }, 1000);
}

function pauseTimer() {
  state.timer.isRunning = false;
  if (state.timer.intervalId) clearInterval(state.timer.intervalId);
  state.timer.intervalId = null;
  if (elements.contestTimer) elements.contestTimer.classList.remove("running");
  if (elements.timerToggleIcon) elements.timerToggleIcon.setAttribute("data-lucide", "play");
  refreshIcons();
}

function resetTimer() {
  pauseTimer();
  if (state.timer.mode === "practice") {
    state.timer.elapsedSec = 0;
  } else {
    state.timer.elapsedSec = 7200; // 2 hours
  }
  updateTimerDisplay();
}

function switchTimerMode() {
  pauseTimer();
  if (state.timer.mode === "practice") {
    state.timer.mode = "contest";
    state.timer.elapsedSec = 7200; // 2 hours
    if (elements.timerModeBadge) elements.timerModeBadge.textContent = "2h Contest";
  } else {
    state.timer.mode = "practice";
    state.timer.elapsedSec = 0;
    if (elements.timerModeBadge) elements.timerModeBadge.textContent = "Practice";
  }
  updateTimerDisplay();
}

function updateTimerDisplay() {
  if (!elements.timerDisplay) return;
  const totalSec = state.timer.elapsedSec;
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  const formatted = `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  elements.timerDisplay.textContent = formatted;

  if (elements.contestTimer) {
    if (state.timer.mode === "contest") {
      if (totalSec < 300) {
        elements.contestTimer.classList.add("danger");
        elements.contestTimer.classList.remove("warning");
      } else if (totalSec < 900) {
        elements.contestTimer.classList.add("warning");
        elements.contestTimer.classList.remove("danger");
      } else {
        elements.contestTimer.classList.remove("warning", "danger");
      }
    } else {
      elements.contestTimer.classList.remove("warning", "danger");
    }
  }
}
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
      opt.textContent = c.title;
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

    loadProblemStatuses();
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
  if (elements.mobileProblemSelect) {
    elements.mobileProblemSelect.innerHTML = "";
  }

  problems.forEach((prob) => {
    const tab = document.createElement("button");
    const isActive = prob.problem_id === state.activeProblemId;
    const statusData = state.problemStatuses[prob.problem_id];
    let extraClass = "";
    if (statusData && statusData.verdict === "AC") {
      extraClass = "problem-solved";
    } else if (statusData && statusData.verdict) {
      extraClass = "problem-attempted";
    }
    tab.className = `problem-tab ${isActive ? "active" : ""} ${extraClass}`.trim();
    tab.dataset.problemId = prob.problem_id;
    tab.title = `${prob.short_name} · ${prob.name} (${prob.time_limit_sec}s)`;

    const dot = document.createElement("span");
    dot.className = "problem-status-dot";
    tab.appendChild(dot);

    const label = document.createElement("span");
    label.className = "problem-tab-label";
    // Active pill shows full name ("A · Rabbit / Frog 1"); inactive pills stay compact ("B", "C", "D")
    label.textContent = isActive ? `${prob.short_name} · ${prob.name}` : prob.short_name;
    tab.appendChild(label);

    if (statusData && statusData.verdict && statusData.verdict !== "AC" && isActive) {
      const tag = document.createElement("span");
      tag.className = "tab-verdict-tag tag-wa";
      tag.textContent = statusData.verdict;
      tab.appendChild(tag);
    }

    tab.addEventListener("click", () => selectProblem(prob.problem_id));
    elements.problemTabs.appendChild(tab);

    if (elements.mobileProblemSelect) {
      const opt = document.createElement("option");
      opt.value = prob.problem_id;
      const suffix = statusData && statusData.verdict ? ` [${statusData.verdict}]` : "";
      opt.textContent = `${prob.short_name} · ${prob.name}${suffix}`;
      elements.mobileProblemSelect.appendChild(opt);
    }
  });

  if (elements.mobileProblemSelect && state.activeProblemId) {
    elements.mobileProblemSelect.value = state.activeProblemId;
  }
}

async function selectProblem(problemId) {
  if (!state.contestMeta) return;

  const problem = state.contestMeta.problems.find((p) => p.problem_id === problemId);
  if (!problem) return;

  state.activeProblemId = problemId;
  state.activeProblem = problem;
  state.activeRefPath = null;
  state.isReferenceMode = false;

  // Update active tab style & status pill
  renderProblemTabs(state.contestMeta.problems);
  updateProblemStatusPill();

  // Render Statement (PDF or HTML)
  if (problem.has_statement || problem.has_pdf) {
    elements.pdfViewer.src = `/api/problems/${state.activeContestId}/${problemId}/statement`;
    elements.pdfViewer.style.display = "block";
    elements.pdfFallback.style.display = "none";
  } else {
    elements.pdfViewer.src = "about:blank";
    elements.pdfViewer.style.display = "none";
    elements.pdfFallback.style.display = "flex";
  }

  // Populate reference submissions selector
  populateReferenceSelector(problem.reference_submissions);
  populateStressRefSelector(problem.reference_submissions);

  // Load custom tests for this problem
  loadCustomTestsList();

  // Reset judge cards and results
  clearJudgeView();

  // Load code from disk
  await loadActiveCode();
}

function populateStressRefSelector(refSubs) {
  if (!elements.stressRefSelect) return;
  elements.stressRefSelect.innerHTML = "";

  // 1. Auto-detect option
  const autoOpt = document.createElement("option");
  autoOpt.value = "";
  autoOpt.textContent = "Auto-detect Reference (Recommended)";
  elements.stressRefSelect.appendChild(autoOpt);

  // 2. Custom workspace solvers group
  const wsGroup = document.createElement("optgroup");
  wsGroup.label = "Custom Workspace Solvers";
  const brutePy = document.createElement("option");
  brutePy.value = "brute.py";
  brutePy.textContent = "workspace/brute.py";
  wsGroup.appendChild(brutePy);
  const bruteCpp = document.createElement("option");
  bruteCpp.value = "brute.cpp";
  bruteCpp.textContent = "workspace/brute.cpp";
  wsGroup.appendChild(bruteCpp);
  elements.stressRefSelect.appendChild(wsGroup);

  // 3. Official submissions from contest
  if (refSubs) {
    const categories = [
      { key: "accepted", label: "Accepted (Reference)" },
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
          opt.value = `submissions/${cat.key}/${filename}`;
          opt.textContent = `${cat.label} / ${filename}`;
          optGroup.appendChild(opt);
        });
        elements.stressRefSelect.appendChild(optGroup);
      }
    });
  }
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

function formatBreadcrumbPath(fullPath) {
  if (!fullPath) return ".../workspace/solution.py";
  const norm = fullPath.replace(/\\/g, "/");
  const parts = norm.split("/").filter(Boolean);
  if (parts.length <= 2) return norm;
  return `.../${parts.slice(-2).join("/")}`;
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
    if (elements.langTabs) {
      elements.langTabs.querySelectorAll(".lang-tab").forEach((t) => {
        t.classList.toggle("active", t.dataset.lang === data.lang);
      });
    }
    state.lastModified = data.last_modified;
    state.isReferenceMode = data.is_reference;

    elements.filePathDisplay.textContent = formatBreadcrumbPath(data.file_path);
    elements.filePathDisplay.dataset.fullPath = data.file_path;
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

  // Auto-expand console when starting judge
  toggleConsole(true);

  // Switch to Test Verdicts view
  elements.viewTabs.forEach((t) => t.classList.toggle("active", t.dataset.view === "verdicts"));
  elements.viewVerdicts.classList.add("active");
  elements.viewCustom.classList.remove("active");

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

  const failFast = elements.chkFailFast ? elements.chkFailFast.checked : false;
  let url = `/api/judge/run-stream?contest_id=${state.activeContestId}&problem_id=${state.activeProblemId}&lang=${state.activeLang}&suite=${suite}&fail_fast=${failFast}&session_id=${encodeURIComponent(SESSION_ID)}`;
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
    renderCompileErrorResult(data.error);
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
    renderLeetCodeResult(summary);
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
  if (elements.judgeEmptyState) elements.judgeEmptyState.style.display = "flex";
  if (elements.leetcodeResultView) elements.leetcodeResultView.style.display = "none";
  if (elements.lcVerdictBannerCard) elements.lcVerdictBannerCard.style.display = "none";
  if (elements.lcCompileErrorBox) elements.lcCompileErrorBox.style.display = "none";
  if (elements.progressBar) elements.progressBar.style.display = "none";
  if (elements.summaryBanner) elements.summaryBanner.style.display = "none";
  if (elements.testCardsList) elements.testCardsList.innerHTML = "";
  state.testResults = [];
  state.isAllTestsOpen = false;
  if (elements.lcAllTestsTable) elements.lcAllTestsTable.style.display = "none";
  if (elements.lcAllTestsChevron) elements.lcAllTestsChevron.style.transform = "rotate(0deg)";
}

function renderCompileErrorResult(errorText) {
  if (elements.judgeEmptyState) elements.judgeEmptyState.style.display = "none";
  if (elements.leetcodeResultView) elements.leetcodeResultView.style.display = "flex";
  if (elements.lcVerdictTitle) {
    elements.lcVerdictTitle.textContent = "Compile Error";
    elements.lcVerdictTitle.className = "lc-verdict-title verdict-ce";
  }
  if (elements.lcPassedCounter) elements.lcPassedCounter.textContent = "Build failed";
  if (elements.lcMetricsRow) elements.lcMetricsRow.style.display = "none";

  if (elements.lcCompileErrorBox) elements.lcCompileErrorBox.style.display = "flex";
  if (elements.lcCompileErrorText) elements.lcCompileErrorText.textContent = errorText;
  if (elements.lcTestcaseInspector) elements.lcTestcaseInspector.style.display = "none";

  // Mark wrong attempt in problem status
  if (state.activeProblemId) {
    const existing = state.problemStatuses[state.activeProblemId];
    if (!existing || existing.verdict !== "AC") {
      state.problemStatuses[state.activeProblemId] = { verdict: "CE", timestamp: Date.now() };
    }
    saveProblemStatuses();
    if (state.contestMeta && state.contestMeta.problems) {
      renderProblemTabs(state.contestMeta.problems);
    }
    updateProblemStatusPill();
  }

  // Visual verdict banner
  if (elements.lcVerdictBannerCard) {
    elements.lcVerdictBannerCard.style.display = "flex";
    elements.lcVerdictBannerCard.className = "lc-verdict-banner-card banner-failed";
    if (elements.lcBannerIcon) elements.lcBannerIcon.setAttribute("data-lucide", "alert-triangle");
    if (elements.lcBannerTitle) elements.lcBannerTitle.textContent = "Compile Error (Wrong Attempt)";
    if (elements.lcBannerSubtitle) {
      elements.lcBannerSubtitle.textContent = "Build failed. Inspect compiler diagnostics below.";
    }
  }

  refreshIcons();
}

function renderLeetCodeResult(summary) {
  if (elements.judgeEmptyState) elements.judgeEmptyState.style.display = "none";
  if (elements.leetcodeResultView) elements.leetcodeResultView.style.display = "flex";
  if (elements.lcCompileErrorBox) elements.lcCompileErrorBox.style.display = "none";
  if (elements.lcTestcaseInspector) elements.lcTestcaseInspector.style.display = "flex";
  if (elements.lcMetricsRow) elements.lcMetricsRow.style.display = "flex";

  const failedTests = state.testResults.filter((t) => t.verdict !== "AC");
  const failedCount = failedTests.length;

  let verdictTitle = "Accepted";
  if (summary.overall_verdict === "WA") verdictTitle = "Wrong Answer";
  else if (summary.overall_verdict === "TLE") verdictTitle = "Time Limit Exceeded";
  else if (summary.overall_verdict === "MLE") verdictTitle = "Memory Limit Exceeded";
  else if (summary.overall_verdict === "RE") verdictTitle = "Runtime Error";
  else if (summary.overall_verdict === "CE") verdictTitle = "Compile Error";

  if (elements.lcVerdictTitle) {
    elements.lcVerdictTitle.textContent = verdictTitle;
    elements.lcVerdictTitle.className = `lc-verdict-title ${getVerdictClass(summary.overall_verdict)}`;
  }
  if (elements.lcPassedCounter) {
    elements.lcPassedCounter.textContent = `${summary.passed} / ${summary.total} testcases passed`;
  }
  if (elements.lcRuntimeVal) {
    elements.lcRuntimeVal.textContent = `${Number(summary.max_time_ms || 0).toFixed(1)} ms`;
  }
  if (elements.lcMemoryVal) {
    elements.lcMemoryVal.textContent = `${Number(summary.max_memory_mb || 0).toFixed(1)} MB`;
  }

  // Update problem solved / wrong attempt status
  if (state.activeProblemId) {
    if (summary.overall_verdict === "AC") {
      state.problemStatuses[state.activeProblemId] = { verdict: "AC", timestamp: Date.now() };
    } else {
      const existing = state.problemStatuses[state.activeProblemId];
      if (!existing || existing.verdict !== "AC") {
        state.problemStatuses[state.activeProblemId] = { verdict: summary.overall_verdict, timestamp: Date.now() };
      }
    }
    saveProblemStatuses();
    if (state.contestMeta && state.contestMeta.problems) {
      renderProblemTabs(state.contestMeta.problems);
    }
    updateProblemStatusPill();
  }

  // Prominent visual banner card
  if (elements.lcVerdictBannerCard) {
    elements.lcVerdictBannerCard.style.display = "flex";
    if (summary.overall_verdict === "AC") {
      elements.lcVerdictBannerCard.className = "lc-verdict-banner-card banner-solved";
      if (elements.lcBannerIcon) elements.lcBannerIcon.setAttribute("data-lucide", "check-circle-2");
      if (elements.lcBannerTitle) elements.lcBannerTitle.textContent = "Problem Solved! (Accepted)";
      if (elements.lcBannerSubtitle) {
        elements.lcBannerSubtitle.textContent = `All ${summary.total} testcase(s) passed successfully in ${Number(summary.max_time_ms || 0).toFixed(1)} ms.`;
      }
    } else {
      elements.lcVerdictBannerCard.className = "lc-verdict-banner-card banner-failed";
      if (elements.lcBannerIcon) elements.lcBannerIcon.setAttribute("data-lucide", "alert-circle");
      if (elements.lcBannerTitle) elements.lcBannerTitle.textContent = `${verdictTitle} (Wrong Attempt)`;
      if (elements.lcBannerSubtitle) {
        elements.lcBannerSubtitle.textContent = `${failedCount} of ${summary.total} testcase(s) failed. Inspect the mismatched output below.`;
      }
    }
  }

  // Display only wrong/failed cases on failure, or sample cases on success
  let displayCases = [];
  if (failedCount > 0) {
    if (elements.lcTabsLabel) {
      elements.lcTabsLabel.textContent = failedCount === 1 ? "Failed Testcase:" : "Failed Testcases:";
    }
    displayCases = failedTests;
  } else {
    if (elements.lcTabsLabel) {
      elements.lcTabsLabel.textContent = "Sample Testcases:";
    }
    displayCases = state.testResults.filter((t) => t.suite === "sample");
    if (displayCases.length === 0) displayCases = state.testResults.slice(0, 3);
  }

  if (elements.lcCasePills) {
    elements.lcCasePills.innerHTML = "";
    displayCases.forEach((tc, idx) => {
      const pill = document.createElement("button");
      const isFail = tc.verdict !== "AC";
      pill.className = `lc-case-pill ${isFail ? "failed" : "passed"} ${idx === 0 ? "active" : ""}`;
      pill.innerHTML = `<span>${tc.test_name}</span>${isFail ? `<span>(${tc.verdict})</span>` : ""}`;
      pill.addEventListener("click", () => {
        elements.lcCasePills.querySelectorAll(".lc-case-pill").forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        selectTestcaseDetail(tc);
      });
      elements.lcCasePills.appendChild(pill);
    });
  }

  // Select the first case (which is the first failed case on failure!)
  if (displayCases.length > 0) {
    selectTestcaseDetail(displayCases[0]);
  }

  // Populate secondary table with all tests (hidden by default)
  renderAllTestsTable();
  refreshIcons();
}

function selectTestcaseDetail(tc) {
  if (!tc) return;
  state.activeTestcase = tc;

  if (elements.lcInputContent) {
    elements.lcInputContent.textContent = tc.input_preview || "(empty stdin)";
  }

  const isFailed = tc.verdict !== "AC";
  if (elements.lcActualLabel) {
    elements.lcActualLabel.textContent = isFailed ? `Output (${tc.verdict})` : "Output";
  }
  if (elements.lcActualContent) {
    elements.lcActualContent.textContent = tc.actual_preview || "(empty stdout)";
  }

  if (elements.lcExpectedGroup && elements.lcExpectedContent) {
    if (tc.expected_preview !== undefined && tc.expected_preview !== null) {
      elements.lcExpectedGroup.style.display = "flex";
      elements.lcExpectedContent.textContent = tc.expected_preview || "(empty expected)";
    } else {
      elements.lcExpectedGroup.style.display = "none";
    }
  }

  if (elements.lcDiagGroup && elements.lcDiagContent) {
    if (tc.stderr_preview || (isFailed && tc.diff_message)) {
      elements.lcDiagGroup.style.display = "flex";
      if (tc.stderr_preview) {
        if (elements.lcDiagLabel) elements.lcDiagLabel.textContent = "Standard Error (stderr)";
        elements.lcDiagContent.textContent = tc.stderr_preview;
        elements.lcDiagContent.className = "lc-diff-banner error-text";
      } else {
        if (elements.lcDiagLabel) elements.lcDiagLabel.textContent = "Difference Diagnostics";
        elements.lcDiagContent.textContent = tc.diff_message;
        elements.lcDiagContent.className = "lc-diff-banner";
      }
    } else {
      elements.lcDiagGroup.style.display = "none";
    }
  }

  // Update Visual Side-by-Side Diff and Whitespace Inspector
  updateDiffViewer(tc.expected_preview || "", tc.actual_preview || "");
  detectWhitespaceDifferences(tc.actual_preview || "", tc.expected_preview || "");

  refreshIcons();
}

// =====================================================================
// Visual Diff Inspector & Whitespace Detector
// =====================================================================

function setDiffViewMode(mode) {
  state.diffViewMode = mode;
  const isDiff = mode === "diff";

  if (elements.btnModeDiff) elements.btnModeDiff.classList.toggle("active", isDiff);
  if (elements.btnModeText) elements.btnModeText.classList.toggle("active", !isDiff);

  if (elements.lcDiffEditorWrapper) {
    elements.lcDiffEditorWrapper.style.display = isDiff ? "flex" : "none";
  }
  if (elements.lcActualGroup) {
    elements.lcActualGroup.style.display = isDiff ? "none" : "flex";
  }
  if (elements.lcExpectedGroup) {
    elements.lcExpectedGroup.style.display = isDiff ? "none" : "flex";
  }

  if (isDiff && state.monacoDiffEditor) {
    setTimeout(() => {
      state.monacoDiffEditor.layout();
    }, 50);
  }
}

function updateDiffViewer(expected, actual) {
  if (!state.monacoDiffEditor || !window.monaco) return;
  try {
    const originalModel = window.monaco.editor.createModel(expected || "", "text/plain");
    const modifiedModel = window.monaco.editor.createModel(actual || "", "text/plain");
    state.monacoDiffEditor.setModel({
      original: originalModel,
      modified: modifiedModel,
    });
  } catch (err) {
    console.warn("Failed to update Monaco diff model:", err);
  }
}

function detectWhitespaceDifferences(actual, expected) {
  if (!elements.lcWhitespaceBadges) return;
  elements.lcWhitespaceBadges.innerHTML = "";
  if (!actual || !expected) return;

  const badges = [];
  const actHasCrlf = actual.includes("\r\n");
  const expHasCrlf = expected.includes("\r\n");
  if (actHasCrlf !== expHasCrlf) {
    badges.push(`<span class="badge-ws badge-crlf">Line Endings: ${actHasCrlf ? "CRLF" : "LF"} vs ${expHasCrlf ? "CRLF" : "LF"}</span>`);
  }

  const hasActTrailing = /[ \t]+$/m.test(actual);
  const hasExpTrailing = /[ \t]+$/m.test(expected);
  if (hasActTrailing && !hasExpTrailing) {
    badges.push(`<span class="badge-ws badge-trailing">Trailing Whitespace Detected</span>`);
  }

  const actEofNewline = actual.endsWith("\n") || actual.endsWith("\r\n");
  const expEofNewline = expected.endsWith("\n") || expected.endsWith("\r\n");
  if (actEofNewline !== expEofNewline) {
    badges.push(`<span class="badge-ws badge-newline">EOF Trailing Newline Mismatch</span>`);
  }

  elements.lcWhitespaceBadges.innerHTML = badges.join("");
}

// =====================================================================
// Custom Persistent Test Cases Management
// =====================================================================

async function loadCustomTestsList() {
  if (!state.activeContestId || !state.activeProblemId || !elements.customTestsList) return;
  try {
    const res = await fetch(`/api/problems/${state.activeContestId}/${state.activeProblemId}/custom-tests`);
    if (!res.ok) return;
    const tests = await res.json();
    state.customTests = tests;

    if (elements.customTestsCount) {
      elements.customTestsCount.textContent = `${tests.length} saved`;
    }

    elements.customTestsList.innerHTML = "";
    if (tests.length === 0) {
      elements.customTestsList.innerHTML = '<div class="custom-tests-empty">No saved custom testcases yet. Click "Save to My Tests" to add one.</div>';
      return;
    }

    tests.forEach((tc) => {
      const item = document.createElement("div");
      item.className = "custom-test-item";
      item.innerHTML = `
        <div class="custom-test-info">
          <span class="custom-test-name">${escapeHtml(tc.name)}</span>
          <span class="custom-test-preview">${escapeHtml(tc.input_text.replace(/\\r?\\n/g, " ").slice(0, 60))}</span>
        </div>
        <div class="custom-test-actions">
          <button class="btn btn-xs btn-outline btn-load-tc" title="Load into custom stdin input">Load</button>
          <button class="btn btn-xs btn-outline btn-del-tc" title="Delete custom testcase">Delete</button>
        </div>
      `;

      item.querySelector(".btn-load-tc").addEventListener("click", () => {
        elements.customStdinInput.value = tc.input_text;
        // Switch tab to Custom Input view
        elements.viewTabs.forEach((t) => t.classList.toggle("active", t.dataset.view === "custom"));
        elements.viewVerdicts.classList.remove("active");
        elements.viewCustom.classList.add("active");
        if (elements.viewStress) elements.viewStress.classList.remove("active");
      });

      item.querySelector(".btn-del-tc").addEventListener("click", async () => {
        await deleteCustomTest(tc.name);
      });

      elements.customTestsList.appendChild(item);
    });
  } catch (err) {
    console.error("Failed to load custom tests:", err);
  }
}

async function saveCustomTest(name, inputText, expectedText = "") {
  if (!state.activeContestId || !state.activeProblemId) return;
  try {
    const res = await fetch(`/api/problems/${state.activeContestId}/${state.activeProblemId}/custom-tests`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name,
        input_text: inputText,
        expected_text: expectedText,
      }),
    });
    if (!res.ok) throw new Error("Failed to save custom testcase");
    await loadCustomTestsList();
  } catch (err) {
    alert(`Could not save custom test: ${err.message}`);
  }
}

async function deleteCustomTest(name) {
  if (!state.activeContestId || !state.activeProblemId) return;
  try {
    const res = await fetch(`/api/problems/${state.activeContestId}/${state.activeProblemId}/custom-tests/${encodeURIComponent(name)}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete custom testcase");
    await loadCustomTestsList();
  } catch (err) {
    alert(`Could not delete testcase: ${err.message}`);
  }
}

// =====================================================================
// Automated Differential Stress Testing
// =====================================================================

async function runStressTest() {
  if (!state.activeContestId || !state.activeProblemId) return;

  const btn = elements.btnRunStress;
  const prevHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<span>Running...</span>';

  // Auto-save latest code from editor to disk before compiling
  try {
    await saveCodeToDisk();
  } catch (saveErr) {
    console.warn("Could not auto-save before stress testing:", saveErr);
  }

  elements.stressResultsBox.style.display = "flex";
  elements.stressStatusBadge.className = "verdict-badge verdict-empty";
  elements.stressStatusBadge.textContent = "Running";
  elements.stressStatusText.textContent = "Fuzzing testcases against brute-force reference...";
  elements.stressCounterexampleDetails.style.display = "none";

  const refVal = elements.stressRefSelect ? elements.stressRefSelect.value : "";
  const iters = parseInt(elements.stressIterations ? elements.stressIterations.value : 50) || 50;

  try {
    const res = await fetch(`/api/problems/${state.activeContestId}/${state.activeProblemId}/stress-test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contest_id: state.activeContestId,
        problem_id: state.activeProblemId,
        lang: state.activeLang,
        brute_ref: refVal || null,
        max_iterations: iters,
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Stress test request failed");

    if (data.status === "passed") {
      elements.stressStatusBadge.className = "verdict-badge verdict-ac";
      elements.stressStatusBadge.textContent = "Accepted";
      elements.stressStatusText.textContent = data.message;
      elements.stressCounterexampleDetails.style.display = "none";
    } else if (data.status === "mismatch") {
      elements.stressStatusBadge.className = "verdict-badge verdict-wa";
      elements.stressStatusBadge.textContent = "Mismatch";
      elements.stressStatusText.textContent = data.message || `Discrepancy found at iteration ${data.iteration}!`;
      elements.stressCounterexampleDetails.style.display = "flex";

      if (elements.stressInputContent) elements.stressInputContent.textContent = data.input_text || "(empty)";
      if (elements.stressActualContent) elements.stressActualContent.textContent = data.actual_output || "(empty)";
      if (elements.stressExpectedContent) elements.stressExpectedContent.textContent = data.expected_output || "(empty)";
      if (elements.stressDiffGroup && elements.stressDiffContent) {
        if (data.diff_message) {
          elements.stressDiffGroup.style.display = "flex";
          elements.stressDiffContent.textContent = data.diff_message;
        } else {
          elements.stressDiffGroup.style.display = "none";
        }
      }
    } else {
      elements.stressStatusBadge.className = "verdict-badge verdict-ce";
      elements.stressStatusBadge.textContent = "Error";
      elements.stressStatusText.textContent = data.message || "An error occurred during stress testing.";
      elements.stressCounterexampleDetails.style.display = "none";
    }
  } catch (err) {
    elements.stressStatusBadge.className = "verdict-badge verdict-re";
    elements.stressStatusBadge.textContent = "Error";
    elements.stressStatusText.textContent = err.message;
    elements.stressCounterexampleDetails.style.display = "none";
  } finally {
    btn.disabled = false;
    btn.innerHTML = prevHtml;
    refreshIcons();
  }
}

function renderAllTestsTable() {
  if (!elements.lcAllTestsTable) return;
  const container = elements.lcAllTestsTable;
  container.innerHTML = "";
  if (elements.lcAllTestsLabel) {
    elements.lcAllTestsLabel.textContent = `View all ${state.testResults.length} test results`;
  }

  state.testResults.forEach((tc) => {
    const row = document.createElement("div");
    row.className = "lc-test-row";
    row.innerHTML = `
      <div class="lc-test-row-left">
        <span class="verdict-badge ${getVerdictClass(tc.verdict)}">${tc.verdict}</span>
        <span>${tc.test_name}</span>
        ${tc.suite === "sample" ? `<span class="badge-tag">Sample</span>` : ""}
      </div>
      <div class="lc-test-row-right">
        <span class="tabular-nums">${tc.time_ms.toFixed(1)} ms</span>
        <span class="tabular-nums">${tc.memory_mb.toFixed(1)} MB</span>
      </div>
    `;
    row.addEventListener("click", () => {
      selectTestcaseDetail(tc);
      container.querySelectorAll(".lc-test-row").forEach((r) => r.classList.remove("active"));
      row.classList.add("active");
    });
    container.appendChild(row);
  });
}

function updateFilterCounts() {
  const all = state.testResults.length;
  const failed = state.testResults.filter((t) => t.verdict !== "AC").length;
  const samples = state.testResults.filter((t) => t.suite === "sample").length;
  const secrets = state.testResults.filter((t) => t.suite === "secret").length;

  if (elements.filterAllCount) elements.filterAllCount.textContent = all;
  if (elements.filterFailedCount) elements.filterFailedCount.textContent = failed;
  if (elements.filterSampleCount) elements.filterSampleCount.textContent = samples;
  if (elements.filterSecretCount) elements.filterSecretCount.textContent = secrets;
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

  // Auto-expand console when running custom input
  toggleConsole(true);

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

async function uploadZipFile(file) {
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
    if (file) {
      await uploadZipFile(file);
    }
  });

  // Open Statement external
  elements.btnOpenPdfExt.addEventListener("click", () => {
    if (state.activeContestId && state.activeProblemId) {
      window.open(`/api/problems/${state.activeContestId}/${state.activeProblemId}/statement`, "_blank");
    }
  });

  // Drag and drop code file onto editor pane
  const editorDropzone = document.getElementById("editor-dropzone");
  if (elements.paneEditor) {
    elements.paneEditor.addEventListener("dragover", (e) => {
      e.preventDefault();
      if (editorDropzone) editorDropzone.classList.add("active");
    });
    elements.paneEditor.addEventListener("dragleave", (e) => {
      if (e.relatedTarget && elements.paneEditor.contains(e.relatedTarget)) return;
      if (editorDropzone) editorDropzone.classList.remove("active");
    });
    elements.paneEditor.addEventListener("drop", async (e) => {
      e.preventDefault();
      if (editorDropzone) editorDropzone.classList.remove("active");
      const files = e.dataTransfer.files;
      if (!files || files.length === 0) return;
      const file = files[0];

      if (file.name.endsWith(".zip")) {
        await uploadZipFile(file);
        return;
      }

      const ext = "." + file.name.split(".").pop().toLowerCase();
      let lang = state.activeLang;
      if ([".py"].includes(ext)) lang = "python";
      else if ([".cpp", ".cc", ".cxx", ".c"].includes(ext)) lang = "cpp";
      else if ([".java"].includes(ext)) lang = "java";

      const reader = new FileReader();
      reader.onload = async (evt) => {
        const code = evt.target.result;
        if (lang !== state.activeLang) {
          elements.langTabs.querySelectorAll(".lang-tab").forEach((t) => {
            t.classList.toggle("active", t.dataset.lang === lang);
          });
          state.activeLang = lang;
        }
        setEditorCode(code, lang);
        await saveCodeToDisk();
        elements.saveIndicator.textContent = `Loaded ${file.name}!`;
        setTimeout(() => setDirty(false), 2500);
      };
      reader.readAsText(file);
    });
  }

  // Drag and drop custom input file (.in) onto custom input textarea
  if (elements.customStdinInput) {
    elements.customStdinInput.addEventListener("dragover", (e) => e.preventDefault());
    elements.customStdinInput.addEventListener("drop", (e) => {
      e.preventDefault();
      const files = e.dataTransfer.files;
      if (!files || files.length === 0) return;
      const file = files[0];
      const reader = new FileReader();
      reader.onload = (evt) => {
        elements.customStdinInput.value = evt.target.result;
      };
      reader.readAsText(file);
    });
  }

  // Global drag and drop for contest zip archives
  const globalDropzone = document.getElementById("global-dropzone");
  window.addEventListener("dragenter", (e) => {
    if (e.dataTransfer && e.dataTransfer.types.includes("Files")) {
      const items = e.dataTransfer.items;
      let hasZip = false;
      if (items) {
        for (let i = 0; i < items.length; i++) {
          if (items[i].kind === "file") {
            hasZip = true;
            break;
          }
        }
      }
      if (hasZip && globalDropzone && !elements.paneEditor.contains(e.target)) {
        globalDropzone.classList.add("active");
      }
    }
  });
  window.addEventListener("dragover", (e) => {
    e.preventDefault();
  });
  window.addEventListener("dragleave", (e) => {
    if (e.clientX <= 0 || e.clientY <= 0 || e.clientX >= window.innerWidth || e.clientY >= window.innerHeight) {
      if (globalDropzone) globalDropzone.classList.remove("active");
    }
  });
  window.addEventListener("drop", async (e) => {
    if (globalDropzone) globalDropzone.classList.remove("active");
    if (elements.paneEditor.contains(e.target)) return;
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files && files.length > 0 && files[0].name.endsWith(".zip")) {
      await uploadZipFile(files[0]);
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

  // Copy file path (copies full OS path from dataset, shows truncated breadcrumb in UI)
  elements.btnCopyPath.addEventListener("click", () => {
    const pathText = elements.filePathDisplay.dataset.fullPath || elements.filePathDisplay.textContent;
    if (pathText) {
      navigator.clipboard.writeText(pathText);
      elements.saveIndicator.textContent = "Path Copied!";
      setTimeout(() => setDirty(state.isDirty), 1500);
    }
  });

  // Responsive problem selector dropdown (< 1024px)
  if (elements.mobileProblemSelect) {
    elements.mobileProblemSelect.addEventListener("change", (e) => {
      if (e.target.value) {
        selectProblem(e.target.value);
      }
    });
  }

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

  // Console toggle & collapse
  if (elements.btnToggleConsole) {
    elements.btnToggleConsole.addEventListener("click", () => toggleConsole());
  }
  if (elements.btnMinimizeConsole) {
    elements.btnMinimizeConsole.addEventListener("click", () => toggleConsole(false));
  }

  // Sidebar Toggle (VS Code Style)
  if (elements.btnToggleSidebar) {
    elements.btnToggleSidebar.addEventListener("click", () => toggleSidebar());
  }
  if (elements.btnCollapseSidebar) {
    elements.btnCollapseSidebar.addEventListener("click", () => toggleSidebar(false));
  }

  // View tabs (Test Verdicts vs Custom Input vs Stress Tester)
  elements.viewTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      elements.viewTabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const targetView = tab.dataset.view;
      if (elements.viewVerdicts) elements.viewVerdicts.classList.toggle("active", targetView === "verdicts");
      if (elements.viewCustom) elements.viewCustom.classList.toggle("active", targetView === "custom");
      if (elements.viewStress) elements.viewStress.classList.toggle("active", targetView === "stress");
    });
  });

  // Diff Mode Switcher
  if (elements.btnModeText) {
    elements.btnModeText.addEventListener("click", () => setDiffViewMode("text"));
  }
  if (elements.btnModeDiff) {
    elements.btnModeDiff.addEventListener("click", () => setDiffViewMode("diff"));
  }

  // Pin Active Testcase to My Tests
  if (elements.btnPinActiveTest) {
    elements.btnPinActiveTest.addEventListener("click", async () => {
      if (!state.activeTestcase) return;
      const baseName = `pinned-${(state.activeTestcase.test_name || "test").replace(/[\/\\:]/g, "-")}`;
      const name = prompt("Enter a name for this custom testcase:", baseName);
      if (!name) return;
      await saveCustomTest(
        name,
        state.activeTestcase.input_preview || "",
        state.activeTestcase.expected_preview || ""
      );
    });
  }

  // Custom Input Actions
  if (elements.btnRunCustom) {
    elements.btnRunCustom.addEventListener("click", runCustomInput);
  }
  if (elements.btnSaveCustomTest) {
    elements.btnSaveCustomTest.addEventListener("click", async () => {
      const stdin = elements.customStdinInput ? elements.customStdinInput.value : "";
      if (!stdin.trim()) {
        alert("Please enter some input text before saving.");
        return;
      }
      const defaultName = `custom-${state.customTests.length + 1}`;
      const name = prompt("Enter a name for this custom testcase:", defaultName);
      if (!name) return;
      const expected = elements.customStdoutPre ? elements.customStdoutPre.textContent : "";
      await saveCustomTest(name, stdin, expected);
    });
  }
  if (elements.btnRunCustomTests) {
    elements.btnRunCustomTests.addEventListener("click", () => startJudging("custom"));
  }

  // Stress Testing Actions
  if (elements.btnRunStress) {
    elements.btnRunStress.addEventListener("click", runStressTest);
  }
  if (elements.btnPinStressInput) {
    elements.btnPinStressInput.addEventListener("click", async () => {
      const stdin = elements.stressInputContent ? elements.stressInputContent.textContent : "";
      const expected = elements.stressExpectedContent ? elements.stressExpectedContent.textContent : "";
      if (!stdin.trim()) return;
      const name = prompt("Enter a name for this counterexample testcase:", `stress-fail-${Date.now() % 10000}`);
      if (!name) return;
      await saveCustomTest(name, stdin, expected);
    });
  }
  if (elements.btnCopyStressInput) {
    elements.btnCopyStressInput.addEventListener("click", () => {
      const text = elements.stressInputContent ? elements.stressInputContent.textContent : "";
      navigator.clipboard.writeText(text);
    });
  }
  if (elements.btnCopyStressActual) {
    elements.btnCopyStressActual.addEventListener("click", () => {
      const text = elements.stressActualContent ? elements.stressActualContent.textContent : "";
      navigator.clipboard.writeText(text);
    });
  }
  if (elements.btnCopyStressExpected) {
    elements.btnCopyStressExpected.addEventListener("click", () => {
      const text = elements.stressExpectedContent ? elements.stressExpectedContent.textContent : "";
      navigator.clipboard.writeText(text);
    });
  }

  // Copy IO Buttons for LeetCode Inspector
  if (elements.btnCopyLcInput) {
    elements.btnCopyLcInput.addEventListener("click", () => {
      const text = elements.lcInputContent ? elements.lcInputContent.textContent : "";
      navigator.clipboard.writeText(text);
    });
  }
  if (elements.btnCopyLcOutput) {
    elements.btnCopyLcOutput.addEventListener("click", () => {
      const text = elements.lcActualContent ? elements.lcActualContent.textContent : "";
      navigator.clipboard.writeText(text);
    });
  }
  if (elements.btnCopyLcExpected) {
    elements.btnCopyLcExpected.addEventListener("click", () => {
      const text = elements.lcExpectedContent ? elements.lcExpectedContent.textContent : "";
      navigator.clipboard.writeText(text);
    });
  }
  if (elements.btnToggleAllTests) {
    elements.btnToggleAllTests.addEventListener("click", () => {
      state.isAllTestsOpen = !state.isAllTestsOpen;
      if (elements.lcAllTestsTable) {
        elements.lcAllTestsTable.style.display = state.isAllTestsOpen ? "flex" : "none";
      }
      if (elements.lcAllTestsChevron) {
        elements.lcAllTestsChevron.style.transform = state.isAllTestsOpen ? "rotate(90deg)" : "rotate(0deg)";
      }
    });
  }

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

  // Zoom In / Zoom Out Controls
  if (elements.btnZoomIn) {
    elements.btnZoomIn.addEventListener("click", zoomIn);
  }
  if (elements.btnZoomOut) {
    elements.btnZoomOut.addEventListener("click", zoomOut);
  }
  if (elements.btnZoomReset) {
    elements.btnZoomReset.addEventListener("click", zoomReset);
  }

  // Word Wrap Toggle Control
  if (elements.btnToggleWrap) {
    elements.btnToggleWrap.addEventListener("click", toggleWordWrap);
  }

  // Ctrl + Mouse Wheel Zoom inside workspace editor body
  if (elements.editorBody) {
    elements.editorBody.addEventListener("wheel", (e) => {
      if (e.ctrlKey) {
        e.preventDefault();
        if (e.deltaY < 0) {
          zoomIn();
        } else if (e.deltaY > 0) {
          zoomOut();
        }
      }
    }, { passive: false });
  }

  // Global Keyboard Shortcuts
  document.addEventListener("keydown", (e) => {
    // Alt + Z: Toggle Word Wrap (VS Code standard)
    if (e.altKey && e.key.toLowerCase() === "z") {
      e.preventDefault();
      toggleWordWrap();
    }
    if ((e.ctrlKey || e.metaKey) && (e.key === "=" || e.key === "+")) {
      e.preventDefault();
      zoomIn();
    }
    if ((e.ctrlKey || e.metaKey) && (e.key === "-" || e.key === "_")) {
      e.preventDefault();
      zoomOut();
    }
    if ((e.ctrlKey || e.metaKey) && e.key === "0") {
      e.preventDefault();
      zoomReset();
    }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "b") {
      e.preventDefault();
      toggleSidebar();
    }
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault();
      saveCodeToDisk();
    }
    // Ctrl + ' (or Cmd + ') to Run Samples
    if ((e.ctrlKey || e.metaKey) && (e.key === "'" || e.code === "Quote")) {
      e.preventDefault();
      startJudging("sample");
    }
    // Ctrl + Enter (or Cmd + Enter) to Judge All
    if ((e.ctrlKey || e.metaKey) && (e.key === "Enter" || e.code === "Enter")) {
      e.preventDefault();
      startJudging("all");
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
// Responsive Mobile Pane Switcher (< 1024px)
// =====================================================================

function setMobilePane(paneName) {
  const target = paneName === "workspace" ? "workspace" : "statement";
  document.body.dataset.mobilePane = target;
  if (elements.mobilePaneSwitcher) {
    elements.mobilePaneSwitcher.querySelectorAll(".mobile-pane-tab").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.pane === target);
    });
  }
  if (target === "workspace" && state.monacoEditor) {
    setTimeout(() => state.monacoEditor.layout(), 40);
  }
}

function initMobileSwitcher() {
  setMobilePane("statement");
  if (!elements.mobilePaneSwitcher) return;
  elements.mobilePaneSwitcher.querySelectorAll(".mobile-pane-tab").forEach((btn) => {
    btn.addEventListener("click", () => setMobilePane(btn.dataset.pane));
  });
}

// =====================================================================
// App Entrypoint
// =====================================================================

document.addEventListener("DOMContentLoaded", async () => {
  initResizers();
  initTimer();
  initMobileSwitcher();
  initEventListeners();
  initMonacoEditor();
  await fetchToolchainStatus();
  await loadContestsList();
  refreshIcons();
});
