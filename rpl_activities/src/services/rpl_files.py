import logging
from fastapi import HTTPException, status
from fastapi.responses import Response
import json

from rpl_activities.src.deps.auth import CurrentCourseUser
from rpl_activities.src.deps.tar_utils import ExtractedFilesDict
from rpl_activities.src.deps import tar_utils
from rpl_activities.src.repositories.models import aux_models
from rpl_activities.src.repositories.models.rpl_file import RPLFile
from rpl_activities.src.repositories.rpl_files import RPLFilesRepository
from rpl_activities.src.services.activities import ActivitiesService


class RPLFilesService:
    def __init__(self, db):
        self.rpl_files_repo = RPLFilesRepository(db)
        self.activities_service = ActivitiesService(db)

    def __get_extracted_rplfile(self, rplfile_id: int) -> ExtractedFilesDict:
        rplfile = self.rpl_files_repo.get_by_id(rplfile_id)
        if not rplfile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        is_gzip = (
            rplfile.data and rplfile.data[:2] == b'\x1f\x8b'
        )
        if not is_gzip:
            return {rplfile.file_name: rplfile.data.decode()}
        return tar_utils.extract_tar_gz_to_dict_of_files(rplfile.data)

    def __get_displayable_files_only(self, extracted_rplfile, general_metadata_dict):
        filtered_files: ExtractedFilesDict = {}
        for filename, file_content in extracted_rplfile.items():
            if filename == tar_utils.METADATA_FILENAME:
                filtered_files[filename] = file_content
            if filename not in general_metadata_dict:
                filtered_files[filename] = file_content
            else:
                metadata_for_current_file = general_metadata_dict[filename]
                if "display" in metadata_for_current_file:
                    if metadata_for_current_file["display"] != "hidden":
                        filtered_files[filename] = file_content
        return filtered_files

    def __get_extracted_rplfile_for_student(self, rplfile_id: int) -> ExtractedFilesDict:
        extracted_rplfile: ExtractedFilesDict = self.__get_extracted_rplfile(rplfile_id)
        if not extracted_rplfile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No files extracted")

        if tar_utils.METADATA_FILENAME not in extracted_rplfile:
            return extracted_rplfile
        raw_metadata_file = extracted_rplfile[tar_utils.METADATA_FILENAME]
        try:
            general_metadata_dict = json.loads(raw_metadata_file)
        except json.JSONDecodeError:
            logging.warning(f"Metadata file: JSON decode error for {rplfile_id}: {raw_metadata_file}")
            return {}
        return self.__get_displayable_files_only(extracted_rplfile, general_metadata_dict)

    # ==============================================================================

    def get_raw_rplfile_for_runner(self, rplfile_id: int) -> Response:
        rplfile = self.rpl_files_repo.get_by_id(rplfile_id)
        if not rplfile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        return Response(
            content=rplfile.data,
            media_type=rplfile.file_type,
            headers={
                "Content-Disposition": f"attachment; filename={rplfile.file_name}",
                "Content-Type": rplfile.file_type,
            },
        )

    def get_extracted_rplfile_for_teacher(
        self, rplfile_id: int, current_course_user: CurrentCourseUser
    ) -> ExtractedFilesDict:
        self.activities_service.verify_permission_to_manage(current_course_user)
        return self.__get_extracted_rplfile(rplfile_id)

    def get_extracted_rplfile_for_student(
        self, rplfile_id: int, current_course_user: CurrentCourseUser
    ) -> ExtractedFilesDict:
        self.activities_service.verify_permission_to_view(current_course_user)
        return self.__get_extracted_rplfile_for_student(rplfile_id)

    def get_multiple_extracted_rplfiles_for_student(
        self, raw_rplfiles_ids: str, current_course_user: CurrentCourseUser
    ) -> list[ExtractedFilesDict]:
        self.activities_service.verify_permission_to_view(current_course_user)
        try:
            rplfiles_ids: list[int] = [int(rplfile_id) for rplfile_id in raw_rplfiles_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid RPL file IDs format")
        extracted_rplfiles: list[ExtractedFilesDict] = []
        for rplfile_id in rplfiles_ids:
            extracted_rplfile = self.__get_extracted_rplfile_for_student(rplfile_id)
            extracted_rplfiles.append(extracted_rplfile)
        return extracted_rplfiles
