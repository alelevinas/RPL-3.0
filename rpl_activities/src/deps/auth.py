import logging
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx

from rpl_activities.src.config import env
from rpl_activities.src.dtos.auth_dtos import CourseUserResponseDTO, CurrentMainUserResponseDTO


# Dependencies =============================

auth_handler = HTTPBearer()
AuthDependency = Annotated[HTTPAuthorizationCredentials, Depends(auth_handler)]

# ==========================================


class CurrentMainUser:
    def __init__(self, user_data: CurrentMainUserResponseDTO):
        self.id = user_data.id
        self.username = user_data.username
        self.email = user_data.email
        self.name = user_data.name
        self.surname = user_data.surname
        self.student_id = user_data.student_id
        self.degree = user_data.degree
        self.university = user_data.university
        self.is_admin = user_data.is_admin


async def get_current_main_user(auth_header: AuthDependency, request: Request) -> CurrentMainUser:
    users_api_client: httpx.AsyncClient = request.state.users_api_client
    try:
        res = await users_api_client.get(
            "/api/v3/auth/externalUserMainAuth",
            headers={"Authorization": f"{auth_header.scheme} {auth_header.credentials}"},
        )
    except httpx.RequestError as e:
        logging.getLogger("uvicorn.error").error(
            f"Failed to connect to users API. Request: {request.method} {request.url}"
        )
        logging.getLogger("uvicorn.error").error(f"Error details: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Users API is currently unavailable, try again later.",
        )
    if res.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=res.status_code, detail=f"Failed to authenticate current user: {res.text}"
        )
    user_data = CurrentMainUserResponseDTO(**res.json())
    return CurrentMainUser(user_data)


CurrentMainUserDependency = Annotated[CurrentMainUser, Depends(get_current_main_user)]


# ==========================================


class CurrentCourseUser:
    def __init__(self, user_data: CourseUserResponseDTO):
        self.id = user_data.course_user_id
        self.user_id = user_data.id
        self.course_id = user_data.course_id
        self.username = user_data.username
        self.email = user_data.email
        self.name = user_data.name
        self.surname = user_data.surname
        self.student_id = user_data.student_id
        self.permissions = user_data.permissions

    def has_authority(self, authority: str) -> bool:
        return "all" in self.permissions or authority in self.permissions


def __basic_request_param_checks(course_id: Optional[str]) -> int:
    # Note: done due to direct usage of raw request. The proper handling is also done at router level, this is just an extra precaution.
    if not course_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Course ID is required in the path parameters."
        )
    try:
        course_id = int(course_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Course ID must be an integer.")
    if course_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Course ID must be a positive integer."
        )
    return course_id


async def get_current_course_user(auth_header: AuthDependency, request: Request) -> CurrentCourseUser:
    users_api_client: httpx.AsyncClient = request.state.users_api_client
    course_id = __basic_request_param_checks(request.path_params.get("course_id"))
    try:
        res = await users_api_client.get(
            "/api/v3/auth/externalCourseUserAuth",
            headers={"Authorization": f"{auth_header.scheme} {auth_header.credentials}"},
            params={"course_id": course_id},
        )
    except httpx.RequestError as e:
        logging.getLogger("uvicorn.error").error(
            f"Failed to connect to users API. Request: {request.method} {request.url}"
        )
        logging.getLogger("uvicorn.error").error(f"Error details: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Users API is currently unavailable, try again later.",
        )
    if res.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=res.status_code, detail=f"Failed to authenticate current course user: {res.text}"
        )
    course_user_data = CourseUserResponseDTO(**res.json())
    return CurrentCourseUser(course_user_data)


CurrentCourseUserDependency = Annotated[CurrentCourseUser, Depends(get_current_course_user)]

# ==========================================


class StudentCourseUser:
    def __init__(self, user_data: CourseUserResponseDTO):
        self.id = user_data.course_user_id
        self.user_id = user_data.id
        self.course_id = user_data.course_id
        self.name = user_data.name
        self.surname = user_data.surname
        self.username = user_data.username
        self.student_id = user_data.student_id


async def get_all_students_course_users_for_current_user(
    auth_header: AuthDependency, request: Request
) -> list[StudentCourseUser]:
    users_api_client: httpx.AsyncClient = request.state.users_api_client
    course_id = __basic_request_param_checks(request.path_params.get("course_id"))
    try:
        res = await users_api_client.get(
            f"/api/v3/courses/{course_id}/users",
            params={"role_name": "student"},
            headers={"Authorization": f"{auth_header.scheme} {auth_header.credentials}"},
        )
    except httpx.RequestError as e:
        logging.getLogger("uvicorn.error").error(
            f"Failed to connect to users API. Request: {request.method} {request.url}"
        )
        logging.getLogger("uvicorn.error").error(f"Error details: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Users API is currently unavailable, try again later.",
        )
    if res.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=res.status_code, detail=f"Failed to get students: {res.text}")
    students_course_users = res.json()
    return [StudentCourseUser(CourseUserResponseDTO(**student)) for student in students_course_users]


AllStudentsCourseUsersDependency = Annotated[
    list[StudentCourseUser], Depends(get_all_students_course_users_for_current_user)
]


# ==========================================


def validate_request_from_runner(auth_header: AuthDependency, request: Request) -> bool:
    if not auth_header or not auth_header.credentials:
        logging.getLogger("uvicorn.error").error(
            f"Unauthorized request to runner-exclusive endpoint. Request: {request.method} {request.url}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header is missing."
        )
    credential = auth_header.credentials
    if credential != env.RUNNER_API_KEY:
        logging.getLogger("uvicorn.error").error(
            f"Invalid API key for runner-exclusive endpoint. Request: {request.method} {request.url}"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key.")
    return True


RunnerAuthDependency = Annotated[bool, Depends(validate_request_from_runner)]
