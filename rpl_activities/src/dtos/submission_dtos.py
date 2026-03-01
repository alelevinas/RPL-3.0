from datetime import datetime
from typing import List, Optional
from fastapi import File, UploadFile
from pydantic import BaseModel

from rpl_activities.src.repositories.models import aux_models


# ==============================================================================
# User-facing DTOs


class SubmissionCreationRequestDTO(BaseModel):
    description: Optional[List[str]] = None
    submission_files: List[UploadFile] = File(...)
    model_config = {"extra": "forbid"}


class AllFinalSubmissionsResponseDTO(BaseModel):
    submission_rplfile_ids: List[int]


class IOTestRunResultDTO(BaseModel):
    id: int
    name: str
    test_in: str
    expected_output: str
    run_output: str


class UnitTestRunResultDTO(BaseModel):
    id: int
    name: str
    passed: bool
    error_messages: Optional[str] = None


class SubmissionResultResponseDTO(BaseModel):
    id: int
    activity_id: int
    submission_rplfile_name: str
    submission_rplfile_type: aux_models.RPLFileType
    submission_rplfile_id: int
    activity_starting_rplfile_name: str
    activity_starting_rplfile_type: aux_models.RPLFileType
    activity_starting_rplfile_id: int
    activity_language: aux_models.LanguageWithVersion
    is_io_tested: bool
    activity_unit_tests_content: str = ""
    activity_io_tests_input: List[str] = []
    submission_status: aux_models.SubmissionStatus
    is_final_solution: bool
    submission_date: datetime
    ai_hint: Optional[str] = None
    exit_message: Optional[str] = None
    stderr: str = ""
    stdout: str = ""
    io_tests_run_results: Optional[List[IOTestRunResultDTO]] = None
    unit_tests_run_results: Optional[List[UnitTestRunResultDTO]] = None


# ==============================================================================
# Runner-facing DTOs


class SubmissionResponseDTO(BaseModel):
    id: int
    submission_rplfile_name: str
    submission_rplfile_type: aux_models.RPLFileType
    submission_rplfile_id: int
    activity_starting_rplfile_name: str
    activity_starting_rplfile_type: aux_models.RPLFileType
    activity_starting_rplfile_id: int
    activity_language: aux_models.LanguageWithVersion
    is_io_tested: bool
    compilation_flags: str = ""
    activity_unit_tests_content: str = ""
    activity_io_tests_input: List[str] = []


class UpdateSubmissionStatusRequestDTO(BaseModel):
    status: aux_models.SubmissionStatus


class SingleUnitTestRunReportDTO(BaseModel):
    name: str
    status: str
    messages: Optional[str] = None


class UnitTestSuiteRunsSummaryDTO(BaseModel):
    amount_passed: int
    amount_failed: int
    amount_errored: int
    single_test_reports: List[SingleUnitTestRunReportDTO]


class TestsExecutionLogDTO(BaseModel):
    tests_execution_result_status: aux_models.TestsExecutionResultStatus
    tests_execution_stage: str
    tests_execution_exit_message: str
    tests_execution_stderr: str
    tests_execution_stdout: str
    all_student_only_outputs_from_iotests_runs: Optional[list[str]] = []
    unit_test_suite_result_summary: Optional[UnitTestSuiteRunsSummaryDTO] = None


# ==============================================================================
# Used by both


class SubmissionWithMetadataOnlyResponseDTO(BaseModel):
    id: int
    submission_rplfile_name: str
    submission_rplfile_type: aux_models.RPLFileType
    submission_rplfile_id: int
    activity_starting_rplfile_name: str
    activity_starting_rplfile_type: aux_models.RPLFileType
    activity_starting_rplfile_id: int
    activity_language: aux_models.LanguageWithVersion
    is_io_tested: bool
    ai_hint: Optional[str] = None
