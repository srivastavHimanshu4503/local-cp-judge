from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class Verdict(str, Enum):
    """Competitive programming test case / overall judge verdicts."""
    AC = "AC"    # Accepted
    WA = "WA"    # Wrong Answer
    TLE = "TLE"  # Time Limit Exceeded
    MLE = "MLE"  # Memory Limit Exceeded
    RE = "RE"    # Runtime Error
    CE = "CE"    # Compilation Error


class SupportedLang(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVA = "java"


class TestSuite(str, Enum):
    """Test suite selection."""
    SAMPLE = "sample"
    SECRET = "secret"
    ALL = "all"


class TestCaseInfo(BaseModel):
    """Metadata for an indexed test case file pair (.in, .ans, .desc)."""
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(description="Test case identifier, e.g. 'sample/1' or 'secret/01-len1-equal'")
    suite: str = Field(description="Suite classification: 'sample' or 'secret'")
    in_path: str = Field(description="Absolute path to .in input file")
    ans_path: str = Field(description="Absolute path to .ans expected output file")
    desc_path: Optional[str] = Field(default=None, description="Absolute path to .desc file if present")
    description: str = Field(default="", description="Human-readable test case summary from .desc")
    input_size_bytes: int = Field(default=0, description="Size of the .in file in bytes")


class ProblemMeta(BaseModel):
    """Complete problem metadata parsed from DOMjudge contest archive."""
    model_config = ConfigDict(populate_by_name=True)

    problem_id: str = Field(description="Problem folder name, e.g. 'A-anagram-check'")
    short_name: str = Field(description="Problem letter/code, e.g. 'A'")
    name: str = Field(description="Problem title, e.g. 'Anagram Check'")
    time_limit_sec: float = Field(default=2.0, description="Time limit in seconds (from domjudge-problem.ini)")
    memory_limit_mb: int = Field(default=1024, description="Memory limit in MB (from problem.yaml)")
    color: str = Field(default="#2c4a7a", description="Problem color code (hex string, e.g. '#2c4a7a')")
    has_pdf: bool = Field(default=False, description="Whether problem.pdf exists for viewing")
    has_statement: bool = Field(default=False, description="Whether problem statement (PDF or HTML) exists")
    statement_type: str = Field(default="pdf", description="Statement format: 'pdf', 'html', or 'none'")
    sample_count: int = Field(default=0, description="Number of sample test cases")
    secret_count: int = Field(default=0, description="Number of secret test cases")
    workspace_dir: str = Field(default="", description="Absolute path to the local problem workspace directory")
    files: dict[str, str] = Field(
        default_factory=dict,
        description="Map of language identifier ('python', 'java') to absolute source file path on disk"
    )
    reference_submissions: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Catalog of reference submissions by category: 'accepted', 'wrong_answer', 'time_limit_exceeded'"
    )
    source_contest_id: Optional[str] = Field(
        default=None,
        description="Original contest slug if this problem belongs to a mockup contest"
    )
    source_contest_title: Optional[str] = Field(
        default=None,
        description="Original contest display title if this problem belongs to a mockup contest"
    )
    source_problem_id: Optional[str] = Field(
        default=None,
        description="Original problem folder ID if this problem belongs to a mockup contest"
    )


class ContestMeta(BaseModel):
    """Metadata for an extracted and indexed contest."""
    model_config = ConfigDict(populate_by_name=True)

    contest_id: str = Field(description="Contest slug, e.g. '15oct-contest'")
    title: str = Field(description="Human-readable contest title")
    created_at: str = Field(description="Extraction timestamp (ISO 8601 string)")
    problems: list[ProblemMeta] = Field(default_factory=list, description="Ordered list of contest problems")


class CodeUpdateRequest(BaseModel):
    """Payload to update local source file on disk."""
    model_config = ConfigDict(populate_by_name=True)

    lang: str = Field(description="Target language: 'python' or 'java'")
    code: str = Field(description="Full source code text to persist to disk")


class CodeResponse(BaseModel):
    """Response containing source code read from disk."""
    model_config = ConfigDict(populate_by_name=True)

    lang: str = Field(description="Language identifier")
    code: str = Field(description="Source code content")
    file_path: str = Field(description="Absolute path to the source file on disk")
    last_modified: float = Field(description="Last modified POSIX timestamp of the file")
    is_reference: bool = Field(default=False, description="True if this is a read-only reference submission")


class ChecklistPayload(BaseModel):
    """Persistent contest and problem completion checklist."""
    model_config = ConfigDict(populate_by_name=True)

    contests: dict[str, Any] = Field(
        default_factory=dict,
        description="Map of contest_id to problem completion states and completed_at timestamp"
    )
    updated_at: Optional[int] = Field(default=None, description="Last client update epoch ms")


class OfficialSolutionItem(BaseModel):
    """Official accepted solution entry for Practice Mode Solutions tab."""
    model_config = ConfigDict(populate_by_name=True)

    lang: str = Field(description="Normalized language: 'python' or 'java'")
    filename: str = Field(description="Solution filename under submissions/accepted/")
    ref_path: str = Field(description="Relative reference path, e.g. 'accepted/Main.java'")
    code: str = Field(description="Full solution source code")
    is_primary: bool = Field(default=False, description="True if selected as default solution for this language")


class ProblemSolutionsResponse(BaseModel):
    """Catalog of official accepted Python and Java solutions for a problem."""
    model_config = ConfigDict(populate_by_name=True)

    contest_id: str = Field(description="Contest identifier")
    problem_id: str = Field(description="Problem identifier")
    python: list[OfficialSolutionItem] = Field(default_factory=list, description="Accepted Python solutions")
    java: list[OfficialSolutionItem] = Field(default_factory=list, description="Accepted Java solutions")


class OpenExternalRequest(BaseModel):
    """Request to launch VS Code or Windows File Explorer."""
    model_config = ConfigDict(populate_by_name=True)

    target: str = Field(description="External target to open: 'vscode' or 'explorer'")
    lang: Optional[str] = Field(default=None, description="Optional active language to focus in editor")


class JudgeRunRequest(BaseModel):
    """Request to run problem judging suite (SSE streaming endpoint)."""
    model_config = ConfigDict(populate_by_name=True)

    contest_id: str = Field(description="Contest identifier")
    problem_id: str = Field(description="Problem identifier")
    lang: str = Field(description="Language to judge: 'python' or 'java'")
    suite: str = Field(default="sample", description="Test suite to run: 'sample' or 'all'")
    ref_submission: Optional[str] = Field(
        default=None,
        description="Optional relative path to reference submission to judge instead of user workspace code"
    )
    fail_fast: bool = Field(default=False, description="Stop immediately on the first failed test case")


class CustomRunRequest(BaseModel):
    """Request to execute user code against custom input."""
    model_config = ConfigDict(populate_by_name=True)

    contest_id: str = Field(description="Contest identifier")
    problem_id: str = Field(description="Problem identifier")
    lang: str = Field(description="Language to run: 'python' or 'java'")
    custom_input: str = Field(default="", description="Arbitrary custom stdin text")
    ref_submission: Optional[str] = Field(
        default=None,
        description="Optional relative path to reference submission to execute"
    )


class CustomTestCaseCreate(BaseModel):
    """Request to persist a user testcase on disk."""
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(description="Custom testcase identifier or label")
    input_text: str = Field(description="Standard input content")
    expected_text: Optional[str] = Field(default="", description="Expected answer content")


class CustomTestCaseItem(BaseModel):
    """Metadata for a saved custom testcase."""
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(description="Testcase name")
    input_text: str = Field(description="Input content preview")
    expected_text: str = Field(default="", description="Expected content preview")


class SampleTestCaseItem(BaseModel):
    """Metadata and editable content for a canonical sample testcase (with optional session override)."""
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(description="Sample testcase stem, e.g. '1' or '01-sample'")
    test_name: str = Field(description="Full test identifier, e.g. 'sample/1'")
    input_text: str = Field(default="", description="Standard input text")
    expected_text: str = Field(default="", description="Expected output text")
    description: str = Field(default="", description="Optional sample description from .desc")
    is_edited: bool = Field(default=False, description="True if overridden in the user's current session")
    is_truncated: bool = Field(default=False, description="True if file exceeds editable size limit")


class SampleTestCaseUpdate(BaseModel):
    """Payload to update an existing sample testcase override for the active session."""
    model_config = ConfigDict(populate_by_name=True)

    input_text: str = Field(default="", description="Updated standard input content")
    expected_text: str = Field(default="", description="Updated expected output content")


class StressTestRequest(BaseModel):
    """Request to run randomized differential testing against a reference brute-force solution."""
    model_config = ConfigDict(populate_by_name=True)

    contest_id: str = Field(description="Contest identifier")
    problem_id: str = Field(description="Problem identifier")
    lang: str = Field(default="python", description="Language of optimal solution to test")
    brute_ref: Optional[str] = Field(default=None, description="Reference brute-force submission path")
    max_iterations: int = Field(default=50, description="Maximum randomized iterations to execute")


class StressTestResult(BaseModel):
    """Outcome of automated differential stress testing."""
    model_config = ConfigDict(populate_by_name=True)

    status: str = Field(description="'mismatch', 'passed', or 'error'")
    iteration: int = Field(default=0, description="Iteration count reached")
    input_text: Optional[str] = Field(default=None, description="Discrepant input content")
    actual_output: Optional[str] = Field(default=None, description="User solution output")
    expected_output: Optional[str] = Field(default=None, description="Brute-force reference output")
    diff_message: Optional[str] = Field(default=None, description="Explanation of discrepancy")
    message: Optional[str] = Field(default=None, description="Human-readable summary status")


class TestCaseResult(BaseModel):
    """Result of running a single test case against user or reference solution."""
    model_config = ConfigDict(populate_by_name=True)

    test_name: str = Field(description="Test case name, e.g. 'sample/1' or 'secret/10-small-all-traps'")
    suite: str = Field(description="Suite classification: 'sample' or 'secret'")
    description: str = Field(default="", description="Description from .desc if available")
    verdict: str = Field(description="Judge verdict: 'AC', 'WA', 'TLE', 'MLE', 'RE', or 'CE'")
    time_ms: float = Field(default=0.0, description="Wall-clock execution time in milliseconds")
    memory_mb: float = Field(default=0.0, description="Peak RSS memory consumption in megabytes")
    input_size_bytes: int = Field(default=0, description="Input file size in bytes")
    input_preview: str = Field(default="", description="Truncated preview of standard input (max 500 chars)")
    expected_preview: str = Field(default="", description="Truncated preview of expected answer (max 500 chars)")
    actual_preview: str = Field(default="", description="Truncated preview of actual stdout (max 500 chars)")
    stderr_preview: str = Field(default="", description="Truncated preview of stderr output if any")
    diff_message: str = Field(default="", description="Detailed comparison summary or mismatch diagnostic")


class CustomRunResult(BaseModel):
    """Result of running code against custom input."""
    model_config = ConfigDict(populate_by_name=True)

    verdict: str = Field(description="Execution verdict: 'AC', 'TLE', 'MLE', 'RE', or 'CE'")
    time_ms: float = Field(default=0.0, description="Wall-clock execution time in milliseconds")
    memory_mb: float = Field(default=0.0, description="Peak RSS memory consumption in megabytes")
    stdout_preview: str = Field(default="", description="Program standard output")
    stderr_preview: str = Field(default="", description="Program standard error output")
    exit_code: int = Field(default=0, description="Process return code")


class CompileResult(BaseModel):
    """Result of compilation / syntax verification step."""
    model_config = ConfigDict(populate_by_name=True)

    success: bool = Field(description="True if compilation succeeded without errors")
    run_cmd: list[str] = Field(default_factory=list, description="Resolved executable command list to run test cases")
    error: str = Field(default="", description="Compiler or syntax checker diagnostic error output")
    binary_path: Optional[str] = Field(default=None, description="Path to generated executable binary or class")
    compile_time_ms: float = Field(default=0.0, description="Time taken to compile in milliseconds")


class JudgeSummary(BaseModel):
    """Final summary emitted at the conclusion of a judging run."""
    model_config = ConfigDict(populate_by_name=True)

    contest_id: str = Field(description="Contest identifier")
    problem_id: str = Field(description="Problem identifier")
    lang: str = Field(description="Tested language")
    suite: str = Field(description="Executed test suite ('sample' or 'all')")
    total: int = Field(description="Total number of test cases executed")
    passed: int = Field(description="Number of test cases with AC verdict")
    overall_verdict: str = Field(description="Overall verdict ('AC' if all passed, else first failing verdict)")
    max_time_ms: float = Field(default=0.0, description="Maximum execution time across all executed tests in ms")
    max_memory_mb: float = Field(default=0.0, description="Maximum peak RSS memory across all executed tests in MB")


class SystemStatus(BaseModel):
    """System toolchain diagnostic information and active workspace root."""
    model_config = ConfigDict(populate_by_name=True)

    compilers: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Toolchain status map for 'python' and 'java' with availability and version details"
    )
    workspace_root: str = Field(default="", description="Absolute path to the active workspaces directory")
    os_name: str = Field(default="nt", description="Operating system identifier ('nt' for Windows)")


class AppConfig(BaseModel):
    """Application configuration schema mapping to config.json."""
    model_config = ConfigDict(populate_by_name=True)

    host: str = Field(default="127.0.0.1", description="Server listen host")
    port: int = Field(default=8080, description="Server listen port")
    python_cmd: str = Field(default="python", description="Python interpreter command")
    javac_cmd: str = Field(default="javac", description="Java compiler binary or command")
    java_cmd: str = Field(default="java", description="Java runtime launcher command")
    max_preview_bytes: int = Field(default=500, description="Maximum bytes for input/output previews")
    default_time_limit_sec: float = Field(default=2.0, description="Fallback time limit if omitted in contest archive")
    default_memory_limit_mb: int = Field(default=1024, description="Fallback memory limit if omitted in archive")
