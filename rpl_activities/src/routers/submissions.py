from typing import List, Optional, Union
from fastapi import APIRouter, Form, status
from fastapi.responses import StreamingResponse
from rpl_activities.src.deps.auth import (
    CurrentCourseUserDependency,
    CurrentMainUserDependency,
    RunnerAuthDependency,
)

from rpl_activities.src.deps.database import DBSessionDependency
from rpl_activities.src.deps.mq_sender import MQSenderDependency
from rpl_activities.src.dtos.submission_dtos import (
    SubmissionCreationRequestDTO,
    AllFinalSubmissionsResponseDTO,
    SubmissionResultResponseDTO,
    SubmissionResponseDTO,
    UpdateSubmissionStatusRequestDTO,
    TestsExecutionLogDTO,
    SubmissionWithMetadataOnlyResponseDTO,
)
from rpl_activities.src.services.submissions import SubmissionsService


router = APIRouter(prefix="/api/v3", tags=["Activity Submissions"])


@router.post(
    "/courses/{course_id}/activities/{activity_id}/submissions",
    response_model=SubmissionWithMetadataOnlyResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
def create_submission(
    course_id: int,
    activity_id: int,
    current_course_user: CurrentCourseUserDependency,
    db: DBSessionDependency,
    mq_sender: MQSenderDependency,
    new_submission_data: SubmissionCreationRequestDTO = Form(..., media_type="multipart/form-data"),
):
    return SubmissionsService(db, mq_sender).create_submission(
        course_id, activity_id, new_submission_data, current_course_user
    )


@router.put(
    "/courses/{course_id}/activities/{activity_id}/submissions/{submission_id}/final",
    response_model=SubmissionWithMetadataOnlyResponseDTO,
)
def mark_submission_as_final_solution(
    course_id: int,
    activity_id: int,
    submission_id: int,
    current_course_user: CurrentCourseUserDependency,
    db: DBSessionDependency,
):
    return SubmissionsService(db).mark_submission_as_final_solution(
        course_id, activity_id, submission_id, current_course_user
    )


@router.get(
    "/courses/{course_id}/activities/{activity_id}/finalSubmission",
    response_model=SubmissionWithMetadataOnlyResponseDTO,
)
def get_final_submission_for_current_student(
    course_id: int,
    activity_id: int,
    current_course_user: CurrentCourseUserDependency,
    db: DBSessionDependency,
):
    return SubmissionsService(db).get_final_submission_for_current_student(
        course_id, activity_id, current_course_user
    )


@router.get(
    "/courses/{course_id}/activities/{activity_id}/allFinalSubmissions",
    response_model=AllFinalSubmissionsResponseDTO,
)
def get_all_final_submissions_from_activity(
    course_id: int,
    activity_id: int,
    current_course_user: CurrentCourseUserDependency,
    db: DBSessionDependency,
):
    return SubmissionsService(db).get_all_final_submissions_from_activity(
        course_id, activity_id, current_course_user
    )


@router.get("/courses/{course_id}/submissions/{submission_id}/stream")
def stream_submission_status(
    course_id: int,
    submission_id: int,
    current_course_user: CurrentCourseUserDependency,
    db: DBSessionDependency,
):
    return StreamingResponse(
        SubmissionsService(db).stream_submission_status(submission_id, current_course_user),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/courses/{course_id}/submissions/{submission_id}/result", response_model=SubmissionResultResponseDTO)
def get_submission_execution_result(
    course_id: int, 
    submission_id: int, 
    current_course_user: CurrentCourseUserDependency, 
    db: DBSessionDependency
):
    return SubmissionsService(db).get_submission_execution_result(submission_id, current_course_user)


@router.get(
    "/courses/{course_id}/activities/{activity_id}/submissions",
    response_model=List[SubmissionResultResponseDTO],
)
def get_all_current_user_submissions_results_from_activity(
    course_id: int,
    activity_id: int,
    current_course_user: CurrentCourseUserDependency,
    db: DBSessionDependency,
):
    return SubmissionsService(db).get_all_current_user_submissions_results_from_activity(
        course_id, activity_id, current_course_user
    )


@router.get(
    "/courses/{course_id}/activities/{activity_id}/students/{student_user_id}/submissions",
    response_model=List[SubmissionResultResponseDTO],
)
def get_all_submissions_results_from_activity_for_student(
    course_id: int,
    activity_id: int,
    student_user_id: int,
    current_course_user: CurrentCourseUserDependency,
    db: DBSessionDependency,
):
    return SubmissionsService(db).get_all_submissions_results_from_activity_for_student(
        activity_id, student_user_id, current_course_user
    )


# ==============================================================================


@router.get("/submissions/{submission_id}", response_model=SubmissionResponseDTO)
def get_submission(submission_id: int, runner_auth: RunnerAuthDependency, db: DBSessionDependency):
    return SubmissionsService(db).get_submission_for_runner(submission_id)


@router.put("/submissions/{submission_id}/status", response_model=SubmissionWithMetadataOnlyResponseDTO)
def update_submission_status(
    submission_id: int,
    new_status_data: UpdateSubmissionStatusRequestDTO,
    runner_auth: RunnerAuthDependency,
    db: DBSessionDependency,
):
    return SubmissionsService(db).update_submission_status(submission_id, new_status_data)


@router.post("/submissions/{submission_id}/execLog", status_code=status.HTTP_201_CREATED)
def save_tests_execution_log_for_submission(
    submission_id: int,
    new_execution_log_data: TestsExecutionLogDTO,
    runner_auth: RunnerAuthDependency,
    db: DBSessionDependency,
):
    return SubmissionsService(db).save_tests_execution_log_for_submission(
        submission_id, new_execution_log_data
    )


@router.post(
    "/submissions/reprocessAll",
    response_model=List[SubmissionWithMetadataOnlyResponseDTO],
    status_code=status.HTTP_201_CREATED,
)
def reprocess_all_pending_submissions(
    current_user: CurrentMainUserDependency, db: DBSessionDependency, mq_sender: MQSenderDependency
):
    return SubmissionsService(db, mq_sender).reprocess_all_pending_submissions(current_user)
