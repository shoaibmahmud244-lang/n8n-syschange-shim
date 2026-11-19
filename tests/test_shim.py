from __future__ import annotations

from pathlib import Path
import re
import pytest

from shim import parse_plan

PENDING_OUTPUT = """
run id: run-20260929-abc1
risk  : high
  s1  [low]   df -h
  s2  [high]  sudo apt-get clean
        pre-test: PASS — exit=0, verify=ok, files=1
APPROVAL REQUIRED
"""

FAILED_OUTPUT = """
run id: run-20260929-def2
risk  : low
- [ok] s1: df -h -> rc=0
- [FAILED] s2: false -> rc=1
FAILED: step s2 failed
"""


def test_parse_plan_pending_approval() -> None:
    res = parse_plan(PENDING_OUTPUT)
    assert res["run_id"] == "run-20260929-abc1"
    assert res["risk"] == "high"
    assert res["approval_required"] is True
    assert res["applied"] is False
    assert res["step_count"] == 2
    assert "PASS" in res["pretest_report"]


def test_parse_plan_failed_execution_does_not_report_applied() -> None:
    res = parse_plan(FAILED_OUTPUT)
    assert res["run_id"] == "run-20260929-def2"
    assert res["approval_required"] is False
    assert res["applied"] is False
    assert res["step_count"] == 2
    assert res["steps"][1]["status"] == "failed"


def test_run_id_validation_blocks_shell_injection() -> None:
    pattern = r"run-[A-Za-z0-9-]+"
    assert re.fullmatch(pattern, "run-20260929-abc1") is not None
    assert re.fullmatch(pattern, "run-1; rm -rf /") is None
    assert re.fullmatch(pattern, "../run-1") is None


def test_negative_content_length_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import threading
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from shim import Handler

    token_file = tmp_path / "token"
    token_file.write_text("test-token\n", encoding="utf-8")
    monkeypatch.setattr("shim.TOKEN_FILE", str(token_file))

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=2)
        conn.putrequest("POST", "/plan")
        conn.putheader("X-Sandbox-Token", "test-token")
        conn.putheader("Content-Length", "-1")
        conn.endheaders()
        res = conn.getresponse()
        assert res.status == 400
        data = res.read()
        assert b"invalid Content-Length" in data
    finally:
        server.shutdown()
        server.server_close()
