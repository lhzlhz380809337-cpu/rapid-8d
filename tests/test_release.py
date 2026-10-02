"""Release regressions: isolation, access control, persistence and provider-free operation."""
import importlib
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

PASSWORD = "Test-only-password-928!"

@pytest.fixture
def clients(monkeypatch, tmp_path):
    monkeypatch.setenv("R8D_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("R8D_ADMIN_PASSWORD", PASSWORD)
    monkeypatch.setenv("R8D_COOKIE_SECURE", "false")
    monkeypatch.setenv("R8D_ALLOWED_ORIGINS", "http://testserver")
    monkeypatch.delenv("R8D_API_KEY", raising=False)
    import backend.config as config
    config._config_instance = None
    from backend.main import app
    with TestClient(app) as admin:
        assert admin.post("/api/auth/login", json={"username":"admin","password":PASSWORD}).status_code == 200
        for name in ("alice", "bob"):
            assert admin.post("/api/auth/users", json={"username":name,"password":PASSWORD}).status_code == 200
        alice, bob, anon = TestClient(app), TestClient(app), TestClient(app)
        for client, name in ((alice,"alice"),(bob,"bob")):
            assert client.post("/api/auth/login", json={"username":name,"password":PASSWORD}).status_code == 200
        yield admin, alice, bob, anon
        alice.close(); bob.close(); anon.close()

def project(client, title="测试项目"):
    response = client.post("/api/projects", params={"title":title})
    assert response.status_code == 200, response.text
    return response.json()["project_id"]

def test_auth_fail_closed_and_csrf(clients):
    admin, alice, bob, anon = clients
    assert anon.get("/api/health").status_code == 200
    assert anon.get("/api/projects", headers={"X-User-ID":"admin"}).status_code == 401
    assert anon.post("/api/auth/login", json={"username":"admin","password":PASSWORD}, headers={"Origin":"https://evil.example"}).status_code == 403
    assert alice.put("/api/config/app", json={"report_lang":"en"}).status_code == 403
    assert alice.put("/api/config/glossary", json={"content":"bad"}).status_code == 403
    assert alice.post("/api/auth/users", json={"username":"mallory","password":PASSWORD}).status_code == 403
    assert alice.get("/api/config").status_code == 200
    assert "HttpOnly" in admin.post("/api/auth/login", json={"username":"admin","password":PASSWORD}).headers["set-cookie"]

def test_project_attachment_report_isolation(clients):
    _, alice, bob, _ = clients
    pid = project(alice)
    assert bob.get(f"/api/projects/{pid}").status_code == 404
    assert bob.get("/api/projects").json() == []
    uploaded = alice.post(f"/api/upload/{pid}", files={"file":("test.txt",b"quality evidence","text/plain")})
    assert uploaded.status_code == 200, uploaded.text
    url = uploaded.json()["url"]
    assert alice.get(url).content == b"quality evidence"
    assert bob.get(url).status_code == 404
    assert bob.post(f"/api/upload/{pid}", files={"file":("a.txt",b"x","text/plain")}).status_code == 404
    assert bob.get(f"/api/reports/{pid}/preview").status_code == 404
    assert bob.delete(f"/api/projects/{pid}").status_code == 404
    assert alice.get(f"/api/projects/{pid}").status_code == 200

def test_manual_flow_without_ai_key_and_latest_route(clients):
    _, alice, _, _ = clients
    pid = project(alice)
    assert alice.put(f"/api/project/{pid}/context/D1", json={"project_id":pid,"step":"D1","notes":"负责人：张工"}).status_code == 200
    assert alice.put(f"/api/project/{pid}/confirm-output/D1", json={"project_id":pid,"step":"D1","output":"团队已组建"}).status_code == 200
    assert alice.put("/api/chat/switch-step", json={"project_id":pid,"step":"D2"}).status_code == 200
    ctx = alice.get(f"/api/projects/{pid}/contexts/latest")
    assert ctx.status_code == 200
    assert ctx.json()["step_states"]["D1"]["context_notes"] == "负责人：张工"
    assert alice.get(f"/api/projects/{pid}/contexts/1900-01-01").status_code == 404
    exported = alice.get(f"/api/reports/{pid}/export/docx")
    assert exported.status_code == 200, exported.text
    assert exported.content[:2] == b"PK"
    pdf = alice.get(f"/api/reports/{pid}/export/pdf")
    assert pdf.status_code == 200, pdf.text
    assert pdf.content.startswith(b"%PDF")
    assert alice.post("/api/chat", json={"project_id":pid,"message":"hello"}).status_code == 403
    alice.put("/api/auth/consent", json={"accepted":True})
    assert alice.post("/api/chat", json={"project_id":pid,"message":"hello"}).status_code == 503

def test_report_active_content_removed(clients):
    _, alice, _, _ = clients
    pid = project(alice, "../../outside")
    content = '<h1>报告</h1><script>fetch("/api/projects")</script><img src="http://internal/secret" onerror="alert(1)"><table><tr><td>质量数据</td></tr></table>'
    assert alice.post(f"/api/reports/{pid}/save-report", json={"html":content}).status_code == 200
    result = alice.get(f"/api/reports/{pid}/preview")
    assert "<script" not in result.text
    assert "onerror" not in result.text
    assert "http://internal" not in result.text
    assert "质量数据" in result.text
    assert "sandbox" in result.headers["content-security-policy"]
    # User-controlled title must not be used as an output path.
    assert alice.get(f"/api/reports/{pid}/export/docx").status_code == 200

def test_quota_and_ai_success(clients, monkeypatch):
    _, alice, _, _ = clients
    pid = project(alice)
    monkeypatch.setenv("R8D_API_KEY", "test-not-a-real-key")
    monkeypatch.setenv("R8D_AI_DAILY_USER", "1")
    alice.put("/api/auth/consent", json={"accepted":True})
    from backend.llm.factory import LLMProviderFactory
    from unittest.mock import MagicMock
    provider = MagicMock()
    provider.chat.return_value = "请补充问题发生的时间。"
    with patch.object(LLMProviderFactory,"create",return_value=provider):
        first = alice.post("/api/chat", json={"project_id":pid,"message":"有产品缺陷","step":"D2"})
        assert first.status_code == 200, first.text
        assert alice.post("/api/chat", json={"project_id":pid,"message":"再问"}).status_code == 429
        assert provider.chat.call_count == 1
    assert alice.get(f"/api/projects/{pid}").status_code == 200

def test_password_revokes_sessions_and_account_delete(clients):
    _, alice, bob, anon = clients
    pid = project(bob)
    assert bob.request("DELETE", "/api/auth/account", json={"username":"bob","password":PASSWORD}).status_code == 200
    assert bob.get("/api/projects").status_code == 401
    assert anon.post("/api/auth/login", json={"username":"bob","password":PASSWORD}).status_code == 401
    assert alice.put("/api/auth/password", json={"current_password":PASSWORD,"new_password":PASSWORD+"new"}).status_code == 200
    assert alice.get("/api/projects").status_code == 401
    assert alice.post("/api/auth/login", json={"username":"alice","password":PASSWORD+"new"}).status_code == 200

def test_upload_limits_and_identifier_validation(clients, monkeypatch):
    _, alice, _, _ = clients
    pid = project(alice)
    monkeypatch.setenv("R8D_STORAGE_MB", "0")
    assert alice.post(f"/api/upload/{pid}", files={"file":("a.txt",b"x","text/plain")}).status_code == 413
    assert alice.get("/api/projects/..%5Csecret").status_code == 400
    assert alice.post("/api/chat", json={"project_id":pid,"message":"x" * 16001}).status_code in {403,422}

def test_sessions_survive_restart(clients):
    _, alice, _, _ = clients
    pid = project(alice)
    from backend.auth import initialize
    initialize()
    assert alice.get(f"/api/projects/{pid}").status_code == 200
