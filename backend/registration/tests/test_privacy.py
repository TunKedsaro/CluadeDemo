"""3.3: PDPA data minimisation. Only name, email, phone, consent_at are stored (no IP)."""
import os
import re
import subprocess
from pathlib import Path

import pytest
from django.db import connection

from registration.models import Registration

from .helpers import post

REPO = Path(__file__).resolve().parents[3]
ALLOWED_COLUMNS = {"id", "event_id", "name", "email", "phone", "consent_at", "status", "created_at"}


def test_registration_table_columns_are_only_agreed_fields(db):
    with connection.cursor() as cur:
        cols = {c.name for c in connection.introspection.get_table_description(
            cur, Registration._meta.db_table)}
    assert cols == ALLOWED_COLUMNS


def test_no_ip_like_column_in_any_registration_app_table(db):
    with connection.cursor() as cur:
        cur.execute(
            "select table_name, column_name from information_schema.columns "
            "where table_name like 'registration_%%' and column_name ~* '(^|_)(ip|ip_address|remote_addr|user_agent)($|_)'"
        )
        assert cur.fetchall() == []


def test_ip_address_value_is_not_stored_anywhere_in_registration_row(client, event, payload):
    client.post(f"/api/events/{event.id}/registrations", payload,
                content_type="application/json", REMOTE_ADDR="203.0.113.77",
                HTTP_X_FORWARDED_FOR="198.51.100.9", HTTP_USER_AGENT="QA-Agent/1.0")
    reg = Registration.objects.get()
    dumped = " ".join(str(getattr(reg, f.attname)) for f in Registration._meta.fields)
    assert "203.0.113.77" not in dumped and "198.51.100.9" not in dumped
    assert "QA-Agent" not in dumped


def test_registration_model_has_no_ip_field():
    names = {f.name for f in Registration._meta.get_fields()}
    assert not {n for n in names if "ip" in n.split("_") or "agent" in n}


def test_consent_at_is_saved_on_success(client, event, payload):
    post(client, event.id, payload)
    assert Registration.objects.get().consent_at is not None


def test_consent_at_is_not_saved_when_consent_rejected(client, event, payload):
    post(client, event.id, {**payload, "consent": False})
    assert Registration.objects.count() == 0


def _git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)


@pytest.mark.skipif(_git("rev-parse", "--is-inside-work-tree").returncode != 0, reason="no git")
def test_env_file_is_not_tracked_by_git():
    tracked = _git("ls-files").stdout.splitlines()
    assert not [f for f in tracked if re.search(r"(^|/)\.env$", f)]


@pytest.mark.skipif(_git("rev-parse", "--is-inside-work-tree").returncode != 0, reason="no git")
def test_env_file_is_ignored_by_git():
    assert _git("check-ignore", ".env").returncode == 0


def test_settings_secret_key_comes_from_environment():
    src = (REPO / "backend/config/settings.py").read_text()
    assert 'os.environ.get("DJANGO_SECRET_KEY")' in src


def test_no_hardcoded_secrets_in_source():
    pattern = re.compile(
        r"""(?i)(password|secret|token|api[_-]?key)\s*[:=]\s*["'][^"']{6,}["']"""
    )
    offenders = []
    for base in ("backend", "frontend"):
        for path in (REPO / base).rglob("*"):
            if path.suffix not in {".py", ".js", ".html"} or ".venv" in path.parts:
                continue
            if "tests" in path.parts or path.name == "conftest.py":
                continue
            for line in path.read_text(errors="ignore").splitlines():
                if pattern.search(line):
                    offenders.append(f"{path.relative_to(REPO)}: {line.strip()}")
    assert offenders == []


def test_env_example_has_only_placeholder_secrets():
    text = (REPO / ".env.example").read_text()
    assert "change-me" in text
    real = os.environ.get("POSTGRES_PASSWORD")
    if real:
        assert real not in text
