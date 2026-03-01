from datetime import datetime, timedelta, timezone
import json
import logging
from typing import Optional
from fastapi import UploadFile

from rpl_activities.src.deps.auth import CurrentCourseUser
from rpl_activities.src.dtos.submission_dtos import (
    IOTestRunResultDTO,
    SubmissionCreationRequestDTO,
    UnitTestRunResultDTO,
)
from rpl_activities.src.repositories.base import BaseRepository
import sqlalchemy as sa

from rpl_activities.src.repositories.models import aux_models
from rpl_activities.src.repositories.models.activity import Activity
from rpl_activities.src.repositories.rpl_files import RPLFilesRepository
from rpl_activities.src.deps import tar_utils
from .models.activity_submission import ActivitySubmission


class SubmissionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db)
        self.rplfiles_repo = RPLFilesRepository(db)

    # =================================================================

    def get_best_submission_status_by_user_at_activity(
        self, user_id: int, activity: Activity, current_user_submissions_at_activity: list[ActivitySubmission]
    ) -> aux_models.SubmissionStatus:
        if len(current_user_submissions_at_activity) == 0:
            return aux_models.SubmissionStatus.NO_SUBMISSIONS

        statuses = [submission.status for submission in current_user_submissions_at_activity]

        status_order = list(aux_models.SubmissionStatus)
        best_status = max(statuses, key=lambda status: status_order.index(status))
        return best_status

    def get_last_submission_date_by_user_at_activity(
        self, user_id: int, activity: Activity, current_user_submissions_at_activity: list[ActivitySubmission]
    ) -> Optional[datetime]:
        if len(current_user_submissions_at_activity) == 0:
            return None
        last_submission = max(
            current_user_submissions_at_activity, key=lambda submission: submission.date_created
        )
        return last_submission.date_created - timedelta(hours=3)

    def get_all_submissions_by_user_at_activities(
        self, user_id: int, activities: list[Activity]
    ) -> list[ActivitySubmission]:
        if len(activities) == 0:
            return []
        return (
            self.db_session.execute(
                sa.select(ActivitySubmission).where(
                    ActivitySubmission.user_id == user_id,
                    ActivitySubmission.activity_id.in_([activity.id for activity in activities]),
                )
            )
            .scalars()
            .all()
        )

    def get_all_submissions_by_users_at_activities(
        self, user_ids: list[int], activities: list[Activity]
    ) -> list[ActivitySubmission]:
        if len(activities) == 0 or len(user_ids) == 0:
            return []
        return (
            self.db_session.execute(
                sa.select(ActivitySubmission).where(
                    ActivitySubmission.user_id.in_(user_ids),
                    ActivitySubmission.activity_id.in_([activity.id for activity in activities]),
                )
            )
            .scalars()
            .all()
        )

    # =================================================================

    def get_unit_tests_data_from_submission(self, submission: ActivitySubmission) -> str:
        return (
            submission.activity.unit_test_suite.test_rplfile.data.decode()
            if submission.activity.unit_test_suite
            else ""
        )

    def get_io_tests_input_data_from_submission(self, submission: ActivitySubmission) -> list[str]:
        io_tests = submission.activity.io_tests
        return [iotest.test_in for iotest in io_tests] if io_tests else []

    def get_tests_exit_msg_from_submission(self, submission: ActivitySubmission) -> str:
        return submission.tests_execution_log.exit_message if submission.tests_execution_log else ""

    def get_io_tests_run_results_from_submission(
        self, submission: ActivitySubmission
    ) -> list[IOTestRunResultDTO]:
        if (
            not submission.activity.is_io_tested
            or not submission.tests_execution_log
            or not submission.tests_execution_log.io_test_runs
        ):
            return []
        return [
            IOTestRunResultDTO(
                id=run.id,
                name=run.test_name,
                test_in=run.test_in,
                expected_output=run.expected_output,
                run_output=run.run_output,
            )
            for run in submission.tests_execution_log.io_test_runs
        ]

    def get_unit_tests_run_results_from_submission(
        self, submission: ActivitySubmission
    ) -> list[UnitTestRunResultDTO]:
        if (
            submission.activity.is_io_tested
            or not submission.activity.unit_test_suite
            or not submission.tests_execution_log
            or not submission.tests_execution_log.unit_test_runs
        ):
            return []
        return [
            UnitTestRunResultDTO(
                id=run.id, name=run.test_name, passed=run.passed, error_messages=run.error_messages
            )
            for run in submission.tests_execution_log.unit_test_runs
        ]

    def get_tests_execution_log_stdout_and_stderr_from_submission(
        self, submission: ActivitySubmission
    ) -> tuple[str, str]:
        if not submission.tests_execution_log:
            return "", ""
        return (submission.tests_execution_log.stdout or "", submission.tests_execution_log.stderr or "")

    def get_by_id(self, submission_id: int) -> ActivitySubmission | None:
        return (
            self.db_session.execute(
                sa.select(ActivitySubmission).where(ActivitySubmission.id == submission_id)
            )
            .scalars()
            .one_or_none()
        )

    def __get_verified_submission_files_to_compress(
        self, extracted_starting_files: tar_utils.ExtractedFilesDict, submission_uploadfiles: list[UploadFile]
    ) -> dict[str, bytes]:
        starting_files_metadata = extracted_starting_files.get("files_metadata")
        if not starting_files_metadata:
            return tar_utils.compress_uploadfiles_to_tar_gz(submission_uploadfiles)
        starting_files_metadata: dict[str, str] = json.loads(starting_files_metadata)
        files_to_compress = {}
        for uploadfile in submission_uploadfiles:
            if uploadfile.filename in starting_files_metadata.keys():
                if starting_files_metadata[uploadfile.filename]["display"] == "read_write":
                    files_to_compress[uploadfile.filename] = uploadfile.file.read()
                else:
                    files_to_compress[uploadfile.filename] = extracted_starting_files[
                        uploadfile.filename
                    ].encode()
            else:
                files_to_compress[uploadfile.filename] = uploadfile.file.read()

        for starting_file_name, starting_file_content in extracted_starting_files.items():
            if starting_file_name not in files_to_compress.keys():
                files_to_compress[starting_file_name] = starting_file_content.encode()

        return files_to_compress

    def create_submission_for_activity(
        self,
        new_submission_data: SubmissionCreationRequestDTO,
        activity: Activity,
        current_course_user: CurrentCourseUser,
    ) -> ActivitySubmission:
        extracted_starting_files = tar_utils.extract_tar_gz_to_dict_of_files(activity.starting_rplfile.data)
        verified_raw_submission_files = self.__get_verified_submission_files_to_compress(
            extracted_starting_files, new_submission_data.submission_files
        )
        compressed_submission_files = tar_utils.compress_files_dict_to_tar_gz(verified_raw_submission_files)
        rplfile = self.rplfiles_repo.create_rplfile(
            file_name=f"{datetime.today().strftime('%Y-%m-%d')}__{current_course_user.course_id}__{activity.id}__{current_course_user.user_id}_SUBM.tar.gz",
            file_type=aux_models.RPLFileType.GZIP,
            data=compressed_submission_files,
        )
        submission = ActivitySubmission(
            is_final_solution=False,
            activity_id=activity.id,
            user_id=current_course_user.user_id,
            solution_rplfile_id=rplfile.id,
            status=aux_models.SubmissionStatus.PENDING,
            date_created=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
        )
        self.db_session.add(submission)
        self.db_session.commit()
        self.db_session.refresh(submission)
        return submission

    def update_submission_status(
        self, submission: ActivitySubmission, new_status: aux_models.SubmissionStatus
    ) -> ActivitySubmission:
        submission.status = new_status
        submission.last_updated = datetime.now(timezone.utc)
        self.db_session.commit()
        self.db_session.refresh(submission)
        return submission

    def update_submission_ai_hint(
        self, submission: ActivitySubmission, ai_hint: str
    ) -> ActivitySubmission:
        submission.ai_hint = ai_hint
        submission.last_updated = datetime.now(timezone.utc)
        self.db_session.commit()
        self.db_session.refresh(submission)
        return submission

    def mark_submission_as_final_solution(self, submission: ActivitySubmission) -> ActivitySubmission:
        submission.is_final_solution = True
        submission.last_updated = datetime.now(timezone.utc)
        self.db_session.commit()
        self.db_session.refresh(submission)
        return submission

    def get_final_submission_by_current_user_from_activity(
        self, activity_id: int, current_course_user: CurrentCourseUser
    ) -> ActivitySubmission | None:
        return (
            self.db_session.execute(
                sa.select(ActivitySubmission).where(
                    ActivitySubmission.activity_id == activity_id,
                    ActivitySubmission.user_id == current_course_user.user_id,
                    ActivitySubmission.is_final_solution == True,
                )
            )
            .scalars()
            .one_or_none()
        )

    def get_all_final_submissions_for_activity(self, activity_id: int) -> list[ActivitySubmission]:
        return (
            self.db_session.execute(
                sa.select(ActivitySubmission).where(
                    ActivitySubmission.activity_id == activity_id,
                    ActivitySubmission.is_final_solution == True,
                )
            )
            .scalars()
            .all()
        )

    def get_all_submissions_from_activity_id_and_user_id(
        self, activity_id: int, user_id: int
    ) -> list[ActivitySubmission]:
        return (
            self.db_session.execute(
                sa.select(ActivitySubmission).where(
                    ActivitySubmission.activity_id == activity_id, ActivitySubmission.user_id == user_id
                )
            )
            .scalars()
            .all()
        )

    def get_all_pending_and_stuck_submissions(self) -> list[ActivitySubmission]:
        return (
            self.db_session.execute(
                sa.select(ActivitySubmission).where(
                    ActivitySubmission.status.in_(
                        [aux_models.SubmissionStatus.PENDING, aux_models.SubmissionStatus.PROCESSING]
                    )
                )
            )
            .scalars()
            .all()
        )
