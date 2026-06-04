#!/usr/bin/env python3
"""
verify_all.py — Chạy verify tất cả các step trong PLAN.md
Usage: python verify_all.py [--step N] [--skip-network]
"""

import argparse
import importlib
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Callable

# ─── Colors ────────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
DIM    = "\033[2m"

SKIP_NETWORK = False  # set via --skip-network flag

# ─── Result tracker ────────────────────────────────────────────────────────────
results: list[dict] = []


def passed(step: int, name: str, detail: str = ""):
    results.append({"step": step, "status": "PASS", "name": name, "detail": detail})
    mark = f"{GREEN}✓ PASS{RESET}"
    print(f"  {mark}  {name}" + (f"  {DIM}{detail}{RESET}" if detail else ""))


def failed(step: int, name: str, reason: str):
    results.append({"step": step, "status": "FAIL", "name": name, "detail": reason})
    mark = f"{RED}✗ FAIL{RESET}"
    print(f"  {mark}  {name}  {DIM}{reason}{RESET}")


def skipped(step: int, name: str, reason: str = ""):
    results.append({"step": step, "status": "SKIP", "name": name, "detail": reason})
    mark = f"{YELLOW}~ SKIP{RESET}"
    print(f"  {mark}  {name}" + (f"  {DIM}{reason}{RESET}" if reason else ""))


def section(n: int, title: str):
    print(f"\n{BOLD}{CYAN}── Step {n}: {title}{RESET}")


# ─── Helpers ───────────────────────────────────────────────────────────────────

def file_exists(path: str) -> bool:
    return Path(path).exists()


def try_import(module: str) -> tuple[bool, str]:
    try:
        importlib.import_module(module)
        return True, ""
    except Exception as e:
        return False, str(e)


def run_python(code: str) -> tuple[bool, str]:
    """Run a snippet via subprocess using current venv Python."""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return False, (result.stderr or result.stdout).strip()
    return True, result.stdout.strip()


def run_cmd(cmd: list[str], timeout: int = 30) -> tuple[bool, str]:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    ok = result.returncode == 0
    out = (result.stdout + result.stderr).strip()
    return ok, out


# ─── Step verifications ────────────────────────────────────────────────────────

def verify_step_1():
    section(1, "pyproject.toml")
    if file_exists("pyproject.toml"):
        passed(1, "pyproject.toml exists")
        content = Path("pyproject.toml").read_text()
        for pkg in ["fastapi", "langgraph", "chromadb", "pydantic-settings"]:
            if pkg in content:
                passed(1, f"dependency: {pkg}")
            else:
                failed(1, f"dependency: {pkg}", "not found in pyproject.toml")
    else:
        failed(1, "pyproject.toml exists", "file not found")


def verify_step_2():
    section(2, ".env.example + .gitignore")
    for fname, required_keys in [
        (".env.example", ["OPENAI_API_KEY", "AWS_REGION", "CHROMA_PERSIST_DIR"]),
        (".gitignore", ["__pycache__", ".env", "chroma_data"]),
    ]:
        if file_exists(fname):
            passed(2, f"{fname} exists")
            content = Path(fname).read_text()
            for key in required_keys:
                if key in content:
                    passed(2, f"{fname} contains '{key}'")
                else:
                    failed(2, f"{fname} contains '{key}'", "key missing")
        else:
            failed(2, f"{fname} exists", "file not found")


def verify_step_3():
    section(3, "config.py — Settings")
    ok, err = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.config import settings; "
        "assert settings.openai_model == 'gpt-4o-mini', f'got {settings.openai_model}'; "
        "print(settings.openai_model)"
    )
    if ok:
        passed(3, "Settings importable, openai_model=gpt-4o-mini")
    else:
        failed(3, "Settings import", err)

    ok2, err2 = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.config import settings; "
        "assert settings.retrieval_top_k == 5; print('ok')"
    )
    if ok2:
        passed(3, "retrieval_top_k default = 5")
    else:
        failed(3, "retrieval_top_k default", err2)


def verify_step_4():
    section(4, "main.py — FastAPI /health")
    if not file_exists("src/qa_policy_agent/main.py"):
        failed(4, "main.py exists", "file not found"); return
    passed(4, "main.py exists")
    content = Path("src/qa_policy_agent/main.py").read_text()
    for token in ["FastAPI", "/health", "status", "ok"]:
        if token in content:
            passed(4, f"main.py contains '{token}'")
        else:
            failed(4, f"main.py contains '{token}'", "token missing")


def verify_step_5():
    section(5, "llm/provider.py — LLM factory")
    ok, err = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.llm.provider import get_chat_model; "
        "m = get_chat_model(); print(type(m).__name__)"
    )
    if ok:
        passed(5, f"get_chat_model() returns {ok and 'object'}")
    else:
        failed(5, "get_chat_model() import", err)


def verify_step_6():
    section(6, "rag/embeddings.py — BedrockEmbeddings")
    ok, err = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.rag.embeddings import get_embeddings; "
        "e = get_embeddings(); print(type(e).__name__)"
    )
    if ok:
        passed(6, "get_embeddings() importable & instantiates")
    else:
        failed(6, "get_embeddings() import", err)

    if SKIP_NETWORK:
        skipped(6, "embed_query live test", "--skip-network")
    else:
        ok2, err2 = run_python(
            "import sys; sys.path.insert(0,'src'); "
            "from qa_policy_agent.rag.embeddings import get_embeddings; "
            "e = get_embeddings(); v = e.embed_query('test'); "
            "assert len(v) > 0; print(len(v))"
        )
        if ok2:
            passed(6, f"embed_query returns vector (dim={err2 or '?'})")
        else:
            failed(6, "embed_query live test", err2)


def verify_step_7():
    section(7, "rag/store.py — PolicyStore")
    ok, err = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.rag.store import PolicyStore; print('import ok')"
    )
    if ok:
        passed(7, "PolicyStore importable")
    else:
        failed(7, "PolicyStore import", err); return

    if SKIP_NETWORK:
        skipped(7, "PolicyStore().count() live test", "--skip-network")
        return

    ok2, err2 = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.rag.store import PolicyStore; "
        "s = PolicyStore(); c = s.count(); print(c)"
    )
    if ok2:
        passed(7, f"PolicyStore().count() returns {err2}")
    else:
        failed(7, "PolicyStore().count()", err2)


def verify_step_8():
    section(8, "rag/chunker.py — Markdown chunker")
    ok, err = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.rag.chunker import chunk_markdown; "
        "content = '## Điều kiện\\n\\nThu nhập tối thiểu 10 triệu.'; "
        "chunks = chunk_markdown(content, {'document_title': 'Test'}); "
        "assert len(chunks) == 1, f'got {len(chunks)}'; "
        "assert '10 triệu' in chunks[0].text; print('single section ok')"
    )
    if ok:
        passed(8, "single section chunk — OK")
    else:
        failed(8, "single section chunk", err)

    ok2, err2 = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.rag.chunker import chunk_markdown; "
        "content = '## Section A\\n\\nContent A.\\n\\n## Section B\\n\\nContent B.'; "
        "chunks = chunk_markdown(content, {'document_title': 'Test'}); "
        "assert len(chunks) == 2, f'got {len(chunks)}'; print('multi section ok')"
    )
    if ok2:
        passed(8, "multiple sections chunk — OK")
    else:
        failed(8, "multiple sections chunk", err2)

    ok3, err3 = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.rag.chunker import chunk_markdown; "
        "big = '## Big\\n\\n' + ('word ' * 300); "
        "chunks = chunk_markdown(big, {'document_title': 'T'}, max_chunk_size=200); "
        "assert len(chunks) > 1, f'expected split, got {len(chunks)}'; print(len(chunks))"
    )
    if ok3:
        passed(8, f"large section splits correctly ({err3} chunks)")
    else:
        failed(8, "large section split", err3)


def verify_step_9():
    section(9, "data/policies/ — sample policy docs")
    for fpath in [
        "data/policies/lending/personal_loan_policy.md",
        "data/policies/deposit/term_deposit_policy.md",
        "data/policies/compliance/kyc_policy.md",
    ]:
        if file_exists(fpath):
            passed(9, f"{fpath} exists")
        else:
            failed(9, f"{fpath} exists", "file not found")


def verify_step_10():
    section(10, "rag/seed.py — seed script")
    ok, err = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.rag.seed import extract_frontmatter; "
        "meta, body = extract_frontmatter('---\\ntitle: Test\\n---\\nbody text'); "
        "assert meta.get('title') == 'Test'; assert 'body' in body; print('ok')"
    )
    if ok:
        passed(10, "extract_frontmatter parses YAML frontmatter")
    else:
        failed(10, "extract_frontmatter", err)

    ok2, err2 = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.rag.seed import extract_frontmatter; "
        "meta, body = extract_frontmatter('plain content, no frontmatter'); "
        "assert meta == {}; print('ok')"
    )
    if ok2:
        passed(10, "extract_frontmatter handles missing frontmatter")
    else:
        failed(10, "extract_frontmatter no-frontmatter case", err2)


def verify_step_11():
    section(11, "agent/state.py — AgentState")
    ok, err = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.agent.state import AgentState, DocumentChunk, "
        "ClassificationResult, VerificationResult; print('all imported')"
    )
    if ok:
        passed(11, "AgentState + all TypedDicts importable")
    else:
        failed(11, "agent.state import", err)


def verify_step_12():
    section(12, "llm/prompts/classification.py")
    ok, err = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.llm.prompts.classification import CLASSIFICATION_SYSTEM_PROMPT; "
        "assert 'block' in CLASSIFICATION_SYSTEM_PROMPT; "
        "assert 'JSON' in CLASSIFICATION_SYSTEM_PROMPT; print('ok')"
    )
    if ok:
        passed(12, "CLASSIFICATION_SYSTEM_PROMPT importable & has required tokens")
    else:
        failed(12, "classification prompt import", err)


def verify_step_13():
    section(13, "agent/nodes/classify.py")
    ok, err = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.agent.nodes.classify import classify_request; print('import ok')"
    )
    if ok:
        passed(13, "classify_request importable")
    else:
        failed(13, "classify_request import", err)

    # Structural check: function is async
    ok2, err2 = run_python(
        "import sys, inspect; sys.path.insert(0,'src'); "
        "from qa_policy_agent.agent.nodes.classify import classify_request; "
        "assert inspect.iscoroutinefunction(classify_request); print('async ok')"
    )
    if ok2:
        passed(13, "classify_request is async")
    else:
        failed(13, "classify_request async check", err2)


def verify_step_14():
    section(14, "agent/nodes/retrieve.py")
    ok, err = run_python(
        "import sys, inspect; sys.path.insert(0,'src'); "
        "from qa_policy_agent.agent.nodes.retrieve import retrieve_context; "
        "assert inspect.iscoroutinefunction(retrieve_context); print('ok')"
    )
    if ok:
        passed(14, "retrieve_context importable & async")
    else:
        failed(14, "retrieve_context import", err)


def verify_step_15():
    section(15, "agent/nodes/relevance.py")
    ok, err = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "import asyncio; "
        "from qa_policy_agent.agent.nodes.relevance import check_relevance; "
        "state = {'retrieved_chunks': ["
        "  {'score': 0.9, 'text':'a','source_file':'f','document_title':'d','section':'s'},"
        "  {'score': 0.3, 'text':'b','source_file':'f','document_title':'d','section':'s'}"
        "]}; "
        "result = asyncio.run(check_relevance(state)); "
        "assert len(result['relevant_chunks']) == 1, f'got {len(result[\"relevant_chunks\"])}'; "
        "print('filter ok')"
    )
    if ok:
        passed(15, "check_relevance filters by similarity_threshold correctly")
    else:
        failed(15, "check_relevance filter test", err)


def verify_step_16():
    section(16, "llm/prompts/generation.py")
    ok, err = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.llm.prompts.generation import GENERATION_SYSTEM_PROMPT; "
        "assert '{context}' in GENERATION_SYSTEM_PROMPT; "
        "assert 'Source' in GENERATION_SYSTEM_PROMPT; print('ok')"
    )
    if ok:
        passed(16, "GENERATION_SYSTEM_PROMPT has {context} placeholder and 'Source'")
    else:
        failed(16, "generation prompt import", err)


def verify_step_17():
    section(17, "agent/nodes/generate.py — citation extraction")
    ok, err = run_python(
        r"""
import sys, re; sys.path.insert(0,'src')
# Test the citation regex pattern directly
pattern = r"\[Source:\s*(.+?)\s*\|\s*(.+?)\]"
test_answer = "Theo quy định [Source: lending/personal_loan_policy.md | Điều kiện vay], thu nhập tối thiểu là 10 triệu."
matches = re.findall(pattern, test_answer)
assert len(matches) == 1, f"got {len(matches)}"
assert matches[0][0] == "lending/personal_loan_policy.md"
assert matches[0][1] == "Điều kiện vay"
print("citation regex ok")
"""
    )
    if ok:
        passed(17, "citation regex pattern extracts correctly")
    else:
        failed(17, "citation regex test", err)

    ok2, err2 = run_python(
        "import sys, inspect; sys.path.insert(0,'src'); "
        "from qa_policy_agent.agent.nodes.generate import generate_answer; "
        "assert inspect.iscoroutinefunction(generate_answer); print('ok')"
    )
    if ok2:
        passed(17, "generate_answer importable & async")
    else:
        failed(17, "generate_answer import", err2)


def verify_step_18():
    section(18, "agent/nodes/verify.py")
    ok, err = run_python(
        "import sys, inspect; sys.path.insert(0,'src'); "
        "from qa_policy_agent.agent.nodes.verify import verify_answer; "
        "assert inspect.iscoroutinefunction(verify_answer); print('ok')"
    )
    if ok:
        passed(18, "verify_answer importable & async")
    else:
        failed(18, "verify_answer import", err)

    ok2, err2 = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.agent.nodes.verify import VERIFY_PROMPT; "
        "assert '{chunks}' in VERIFY_PROMPT; "
        "assert '{answer}' in VERIFY_PROMPT; print('ok')"
    )
    if ok2:
        passed(18, "VERIFY_PROMPT has {chunks} and {answer} placeholders")
    else:
        failed(18, "VERIFY_PROMPT placeholders", err2)


def verify_step_19():
    section(19, "agent/graph.py — LangGraph assembly")
    ok, err = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.agent.graph import build_graph; "
        "g = build_graph(); print(type(g).__name__)"
    )
    if ok:
        passed(19, f"build_graph() returns compiled graph ({err})")
    else:
        failed(19, "build_graph()", err)

    ok2, err2 = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.agent.graph import build_graph; "
        "g = build_graph(); "
        "mermaid = g.get_graph().draw_mermaid(); "
        "assert 'classify_request' in mermaid; "
        "assert 'retrieve_context' in mermaid; "
        "assert 'generate_answer' in mermaid; "
        "print('nodes present')"
    )
    if ok2:
        passed(19, "Mermaid graph contains all expected nodes")
    else:
        failed(19, "Mermaid graph check", err2)


def verify_step_20():
    section(20, "models.py — Request/Response Pydantic models")
    ok, err = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.models import AskRequest, AskSuccess, AskError, NoAnswer, "
        "NeedsClarification, Citation; print('all imported')"
    )
    if ok:
        passed(20, "All models importable")
    else:
        failed(20, "models import", err); return

    ok2, err2 = run_python(
        "import sys, json; sys.path.insert(0,'src'); "
        "from qa_policy_agent.models import AskSuccess, Citation; "
        "obj = AskSuccess(answer='test', citations=[Citation(source_file='f.md', section='s')], confidence=0.9); "
        "schema = json.loads(obj.model_dump_json()); "
        "assert schema['status'] == 'success'; print('ok')"
    )
    if ok2:
        passed(20, "AskSuccess serializes correctly with status='success'")
    else:
        failed(20, "AskSuccess serialization", err2)


def verify_step_21():
    section(21, "main.py — /ask endpoint")
    if not file_exists("src/qa_policy_agent/main.py"):
        failed(21, "main.py exists", "file not found"); return
    content = Path("src/qa_policy_agent/main.py").read_text()
    for token in ["/ask", "AskRequest", "build_graph", "agent.ainvoke"]:
        if token in content:
            passed(21, f"main.py contains '{token}'")
        else:
            failed(21, f"main.py contains '{token}'", "missing")

    ok, err = run_python(
        "import sys; sys.path.insert(0,'src'); "
        "from qa_policy_agent.main import app; "
        "routes = [r.path for r in app.routes]; "
        "assert '/ask' in routes, f'routes: {routes}'; "
        "assert '/health' in routes; print('routes ok')"
    )
    if ok:
        passed(21, "/ask and /health routes registered")
    else:
        failed(21, "routes check", err)


def verify_step_22():
    section(22, "tests/ — pytest unit tests")
    for fpath in [
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/unit/test_chunker.py",
        "tests/unit/test_config.py",
    ]:
        if file_exists(fpath):
            passed(22, f"{fpath} exists")
        else:
            failed(22, f"{fpath} exists", "file not found")

    ok, err = run_cmd([sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=short"], timeout=60)
    if ok:
        passed(22, "pytest tests/unit/ — all green")
    else:
        failed(22, "pytest tests/unit/", err[-500:] if len(err) > 500 else err)


def verify_step_23():
    section(23, "Dockerfile + docker-compose.yml")
    for fname in ["Dockerfile", "docker-compose.yml"]:
        if file_exists(fname):
            passed(23, f"{fname} exists")
        else:
            failed(23, f"{fname} exists", "file not found")

    if file_exists("Dockerfile"):
        content = Path("Dockerfile").read_text()
        for token in ["python:3.12", "EXPOSE 8000", "uvicorn"]:
            if token in content:
                passed(23, f"Dockerfile contains '{token}'")
            else:
                failed(23, f"Dockerfile contains '{token}'", "missing")

    if SKIP_NETWORK:
        skipped(23, "docker compose build", "--skip-network")
        return
    ok, err = run_cmd(["docker", "compose", "config", "--quiet"], timeout=10)
    if ok:
        passed(23, "docker-compose.yml syntax valid")
    else:
        failed(23, "docker-compose.yml syntax", err)


def verify_step_24():
    section(24, "data/policies — extended policy docs")
    for fpath in [
        "data/policies/deposit/savings_account_policy.md",
        "data/policies/card/credit_card_policy.md",
        "data/policies/general/fee_schedule.md",
    ]:
        if file_exists(fpath):
            passed(24, f"{fpath} exists")
        else:
            failed(24, f"{fpath} exists", "file not found")


def verify_step_25():
    section(25, "SSE Streaming — /ask/stream endpoint")
    if not file_exists("src/qa_policy_agent/main.py"):
        failed(25, "main.py exists", "file not found"); return
    content = Path("src/qa_policy_agent/main.py").read_text()
    for token in ["/ask/stream", "EventSourceResponse", "event_generator"]:
        if token in content:
            passed(25, f"main.py contains '{token}'")
        else:
            failed(25, f"main.py contains '{token}'", "missing — SSE not implemented yet")


# ─── Step registry ─────────────────────────────────────────────────────────────

STEPS: dict[int, tuple[str, Callable]] = {
    1:  ("pyproject.toml",                  verify_step_1),
    2:  (".env.example + .gitignore",        verify_step_2),
    3:  ("config.py — Settings",             verify_step_3),
    4:  ("main.py — FastAPI /health",        verify_step_4),
    5:  ("llm/provider.py",                  verify_step_5),
    6:  ("rag/embeddings.py",                verify_step_6),
    7:  ("rag/store.py — PolicyStore",       verify_step_7),
    8:  ("rag/chunker.py",                   verify_step_8),
    9:  ("data/policies/ — sample docs",     verify_step_9),
    10: ("rag/seed.py",                      verify_step_10),
    11: ("agent/state.py",                   verify_step_11),
    12: ("llm/prompts/classification.py",    verify_step_12),
    13: ("agent/nodes/classify.py",          verify_step_13),
    14: ("agent/nodes/retrieve.py",          verify_step_14),
    15: ("agent/nodes/relevance.py",         verify_step_15),
    16: ("llm/prompts/generation.py",        verify_step_16),
    17: ("agent/nodes/generate.py",          verify_step_17),
    18: ("agent/nodes/verify.py",            verify_step_18),
    19: ("agent/graph.py",                   verify_step_19),
    20: ("models.py",                        verify_step_20),
    21: ("main.py — /ask endpoint",          verify_step_21),
    22: ("tests/ — pytest",                  verify_step_22),
    23: ("Dockerfile + docker-compose",      verify_step_23),
    24: ("extended policy docs",             verify_step_24),
    25: ("SSE streaming /ask/stream",        verify_step_25),
}


# ─── Summary ───────────────────────────────────────────────────────────────────

def print_summary():
    print(f"\n{'─'*60}")
    print(f"{BOLD}SUMMARY{RESET}")
    print(f"{'─'*60}")

    by_step: dict[int, list[dict]] = {}
    for r in results:
        by_step.setdefault(r["step"], []).append(r)

    total_pass = total_fail = total_skip = 0
    for step_n in sorted(by_step):
        step_results = by_step[step_n]
        passes = sum(1 for r in step_results if r["status"] == "PASS")
        fails  = sum(1 for r in step_results if r["status"] == "FAIL")
        skips  = sum(1 for r in step_results if r["status"] == "SKIP")
        total_pass += passes; total_fail += fails; total_skip += skips

        if fails > 0:
            icon = f"{RED}✗{RESET}"
        elif skips > 0 and passes == 0:
            icon = f"{YELLOW}~{RESET}"
        else:
            icon = f"{GREEN}✓{RESET}"

        name = STEPS[step_n][0]
        print(f"  {icon}  Step {step_n:>2}  {name:<40}  "
              f"{GREEN}{passes}P{RESET} {RED}{fails}F{RESET} {YELLOW}{skips}S{RESET}")

    print(f"{'─'*60}")
    overall = "ALL PASSED" if total_fail == 0 else f"{total_fail} FAILED"
    color = GREEN if total_fail == 0 else RED
    print(f"  {BOLD}{color}{overall}{RESET}  "
          f"({total_pass} passed, {total_fail} failed, {total_skip} skipped)")
    print(f"{'─'*60}\n")
    return total_fail


# ─── Entry point ───────────────────────────────────────────────────────────────

def main():
    global SKIP_NETWORK

    parser = argparse.ArgumentParser(description="Verify PLAN.md implementation steps")
    parser.add_argument("--step", type=int, help="Run only this step number")
    parser.add_argument("--skip-network", action="store_true",
                        help="Skip tests that require AWS / live network calls")
    args = parser.parse_args()

    SKIP_NETWORK = args.skip_network

    print(f"\n{BOLD}QA Policy Agent — Step Verifier{RESET}")
    print(f"Python: {sys.version.split()[0]}  |  cwd: {Path.cwd()}")
    if SKIP_NETWORK:
        print(f"{YELLOW}⚠  --skip-network: AWS/live tests will be skipped{RESET}")
    print()

    if args.step:
        if args.step not in STEPS:
            print(f"{RED}Unknown step: {args.step}{RESET}")
            sys.exit(1)
        STEPS[args.step][1]()
    else:
        for n in sorted(STEPS):
            STEPS[n][1]()

    fail_count = print_summary()
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
