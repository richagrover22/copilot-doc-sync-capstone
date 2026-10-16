from __future__ import annotations

import re

import pytest

from app import create_app
from task_store import list_tasks


def _create_task(client, **overrides):
    values = {
        "title": "Prepare release",
        "description": "Write release notes",
        "status": "todo",
        "priority": "medium",
    }
    values.update(overrides)
    response = client.post("/tasks", data=values)
    assert response.status_code == 302
    return response


def test_home_shows_empty_state(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"No tasks yet" in response.data


def test_create_task_persists_defaults(client):
    response = client.post("/tasks", data={"title": "Plan sprint"})
    page = client.get("/")

    assert response.status_code == 302
    assert b"Plan sprint" in page.data
    assert b"Medium" in page.data
    assert b"todo" in page.data


def test_update_task_changes_fields_and_timestamp(client, app):
    _create_task(client)
    original = list_tasks(app.config["DATABASE"])[0]

    response = client.post(
        f"/tasks/{original['id']}",
        data={
            "title": "Release version 1",
            "description": "Publish notes",
            "status": "done",
            "priority": "high",
        },
    )
    page = client.get("/")

    assert response.status_code == 302
    assert b"Release version 1" in page.data
    assert b"done" in page.data
    updated = list_tasks(app.config["DATABASE"])[0]
    assert updated["updated_at"] > original["updated_at"]


def test_delete_task_removes_task(client):
    _create_task(client)
    task_page = client.get("/")
    task_id = re.search(rb"/tasks/(\d+)/delete", task_page.data).group(1).decode()

    response = client.post(f"/tasks/{task_id}/delete")
    page = client.get("/")

    assert response.status_code == 302
    assert b"Prepare release" not in page.data
    assert b"No tasks yet" in page.data


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ({"title": " "}, b"Task title is required."),
        ({"title": "x" * 201}, b"Task title must be 200 characters or fewer."),
        ({"title": "Task", "status": "blocked"}, b"Unsupported task status."),
        ({"title": "Task", "priority": "urgent"}, b"Unsupported task priority."),
    ],
)
def test_invalid_task_input_is_rejected_without_persistence(client, payload, error, app):
    response = client.post("/tasks", data=payload)

    assert response.status_code == 400
    assert error in response.data
    assert list_tasks(app.config["DATABASE"]) == []


def test_update_rejects_missing_status_or_priority(client, app):
    _create_task(client)
    task = list_tasks(app.config["DATABASE"])[0]

    response = client.post(
        f"/tasks/{task['id']}",
        data={"title": "Changed title", "description": ""},
    )

    assert response.status_code == 400
    assert b"Unsupported task status." in response.data
    assert list_tasks(app.config["DATABASE"])[0] == task


def test_filters_can_be_combined(client):
    _create_task(client, title="Urgent done", status="done", priority="high")
    _create_task(client, title="Urgent todo", status="todo", priority="high")
    _create_task(client, title="Low done", status="done", priority="low")

    response = client.get("/?status=done&priority=high")

    assert response.status_code == 200
    assert b"Urgent done" in response.data
    assert b"Urgent todo" not in response.data
    assert b"Low done" not in response.data


def test_invalid_filter_is_rejected(client):
    response = client.get("/?status=unknown")

    assert response.status_code == 400
    assert b"Unsupported status filter." in response.data


@pytest.mark.parametrize("token", [None, "invalid-token"])
def test_mutation_rejects_missing_or_invalid_csrf_token(tmp_path, token):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "csrf-tasks.db"),
            "SECRET_KEY": "test-only-secret",
            "WTF_CSRF_ENABLED": True,
        }
    )
    client = app.test_client()
    response = client.post(
        "/tasks",
        data={"title": "Must not persist", **({"csrf_token": token} if token else {})},
    )

    assert response.status_code == 400
    assert b"CSRF" in response.data
    assert list_tasks(app.config["DATABASE"]) == []


def test_valid_csrf_token_allows_mutation(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "csrf-valid-tasks.db"),
            "SECRET_KEY": "test-only-secret",
            "WTF_CSRF_ENABLED": True,
        }
    )
    client = app.test_client()
    page = client.get("/")
    token = re.search(
        rb'name="csrf_token"[^>]*value="([^"]+)"',
        page.data,
    ).group(1).decode()

    response = client.post(
        "/tasks",
        data={"title": "Protected task", "csrf_token": token},
    )

    assert response.status_code == 302
    assert list_tasks(app.config["DATABASE"])[0]["title"] == "Protected task"


def test_factory_initializes_configured_database(tmp_path):
    database_path = tmp_path / "isolated.db"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(database_path),
            "SECRET_KEY": "test-only-secret",
            "WTF_CSRF_ENABLED": False,
        }
    )

    assert app.config["DATABASE"] == str(database_path)
    assert database_path.exists()
