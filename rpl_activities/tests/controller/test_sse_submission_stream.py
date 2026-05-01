import json
from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from rpl_activities.src.repositories.models import aux_models
from rpl_activities.src.repositories.models.activity import Activity
from rpl_activities.src.repositories.models.activity_submission import ActivitySubmission
from rpl_activities.src.repositories.models.unit_test_suite import UnitTestSuite


def _parse_sse(text: str) -> list[dict]:
    """Parse SSE response body into a list of {event, data} dicts."""
    events = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event_type = "message"
        data = None
        for line in block.split("\n"):
            if line.startswith("event: "):
                event_type = line[7:].strip()
            elif line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                except json.JSONDecodeError:
                    data = line[6:]
        if data is not None:
            events.append({"event": event_type, "data": data})
    return events


def _stream_url(course_id: int, submission_id: int) -> str:
    return f"/api/v3/courses/{course_id}/submissions/{submission_id}/stream"


# ─── Auth ─────────────────────────────────────────────────────────────────────


def test_stream_requires_auth(
    activities_api_client: TestClient,
    example_failed_submission: ActivitySubmission,
):
    response = activities_api_client.get(
        _stream_url(example_failed_submission.activity.course_id, example_failed_submission.id)
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ─── Headers ──────────────────────────────────────────────────────────────────


def test_stream_returns_event_stream_content_type(
    activities_api_client: TestClient,
    example_unit_test_suite: UnitTestSuite,
    example_failed_submission: ActivitySubmission,
    admin_auth_headers: dict[str, str],
):
    response = activities_api_client.get(
        _stream_url(example_failed_submission.activity.course_id, example_failed_submission.id),
        headers=admin_auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert "text/event-stream" in response.headers["content-type"]


# ─── Terminal submission ───────────────────────────────────────────────────────


def test_stream_for_terminal_submission_closes_without_sleeping(
    activities_api_client: TestClient,
    example_unit_test_suite: UnitTestSuite,
    example_failed_submission: ActivitySubmission,
    admin_auth_headers: dict[str, str],
):
    """A submission already in a terminal state should stream and close in a
    single iteration — no time.sleep calls."""
    with patch("rpl_activities.src.services.submissions.time.sleep") as mock_sleep:
        response = activities_api_client.get(
            _stream_url(example_failed_submission.activity.course_id, example_failed_submission.id),
            headers=admin_auth_headers,
        )

    assert response.status_code == status.HTTP_200_OK
    mock_sleep.assert_not_called()

    events = _parse_sse(response.text)
    event_types = [e["event"] for e in events]
    assert event_types == ["status", "result"]

    status_event = next(e for e in events if e["event"] == "status")
    assert status_event["data"]["status"] == aux_models.SubmissionStatus.FAILURE

    result_event = next(e for e in events if e["event"] == "result")
    assert result_event["data"]["id"] == example_failed_submission.id
    assert result_event["data"]["submission_status"] == aux_models.SubmissionStatus.FAILURE


# ─── Non-existent submission ──────────────────────────────────────────────────


def test_stream_for_nonexistent_submission_returns_error_event(
    activities_api_client: TestClient,
    example_activity: Activity,
    admin_auth_headers: dict[str, str],
):
    response = activities_api_client.get(
        _stream_url(example_activity.course_id, 99999),
        headers=admin_auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    events = _parse_sse(response.text)
    assert len(events) == 1
    assert events[0]["event"] == "error"


# ─── Status transitions ───────────────────────────────────────────────────────


def test_stream_emits_status_events_as_submission_progresses(
    activities_api_client: TestClient,
    activities_api_dbsession: Session,
    example_unit_test_suite: UnitTestSuite,
    example_submission: ActivitySubmission,
    admin_auth_headers: dict[str, str],
):
    """Each status transition (PENDING → PROCESSING → SUCCESS) should produce a
    separate 'status' SSE event, followed by a final 'result' event."""
    call_count = 0

    def advance_status(_seconds):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            example_submission.status = aux_models.SubmissionStatus.PROCESSING
            activities_api_dbsession.commit()
        elif call_count == 2:
            example_submission.status = aux_models.SubmissionStatus.SUCCESS
            activities_api_dbsession.commit()

    with patch("rpl_activities.src.services.submissions.time.sleep", side_effect=advance_status):
        response = activities_api_client.get(
            _stream_url(example_submission.activity.course_id, example_submission.id),
            headers=admin_auth_headers,
        )

    assert response.status_code == status.HTTP_200_OK

    events = _parse_sse(response.text)
    status_events = [e for e in events if e["event"] == "status"]
    emitted_statuses = [e["data"]["status"] for e in status_events]

    assert aux_models.SubmissionStatus.PENDING in emitted_statuses
    assert aux_models.SubmissionStatus.PROCESSING in emitted_statuses
    assert aux_models.SubmissionStatus.SUCCESS in emitted_statuses

    result_events = [e for e in events if e["event"] == "result"]
    assert len(result_events) == 1
    assert result_events[0]["data"]["submission_status"] == aux_models.SubmissionStatus.SUCCESS


def test_stream_does_not_repeat_unchanged_status(
    activities_api_client: TestClient,
    activities_api_dbsession: Session,
    example_unit_test_suite: UnitTestSuite,
    example_submission: ActivitySubmission,
    admin_auth_headers: dict[str, str],
):
    """If the status hasn't changed between two polls, no duplicate status event
    should be emitted."""
    call_count = 0

    def advance_status(_seconds):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            # Status stays PENDING on first poll; only transitions on second sleep
            example_submission.status = aux_models.SubmissionStatus.SUCCESS
            activities_api_dbsession.commit()

    with patch("rpl_activities.src.services.submissions.time.sleep", side_effect=advance_status):
        response = activities_api_client.get(
            _stream_url(example_submission.activity.course_id, example_submission.id),
            headers=admin_auth_headers,
        )

    events = _parse_sse(response.text)
    status_events = [e for e in events if e["event"] == "status"]
    emitted_statuses = [e["data"]["status"] for e in status_events]

    # PENDING should only appear once despite two polls with that status
    assert emitted_statuses.count(aux_models.SubmissionStatus.PENDING) == 1
    assert aux_models.SubmissionStatus.SUCCESS in emitted_statuses
