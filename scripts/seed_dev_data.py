"""
Seed script for local development.
Creates: roles, admin user, teacher, student, a course, a category, and an activity.
Idempotent — safe to run multiple times.

Usage: python -m scripts.seed_dev_data
"""

import sys
from datetime import datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from rpl_users.src.repositories.models.base_model import Base as UsersBase
from rpl_users.src.repositories.models.user import User
from rpl_users.src.repositories.models.course import Course
from rpl_users.src.repositories.models.course_user import CourseUser
from rpl_users.src.repositories.models.role import Role
from rpl_users.src.repositories.models import models_metadata as users_meta

from rpl_activities.src.repositories.models.base_model import Base as ActivitiesBase
from rpl_activities.src.repositories.models.activity import Activity
from rpl_activities.src.repositories.models.activity_category import ActivityCategory
from rpl_activities.src.repositories.models.rpl_file import RPLFile
from rpl_activities.src.repositories.models import models_metadata as activities_meta

from rpl_users.src.deps.security import hash_password

# Default password for all seed users
DEFAULT_PASSWORD = "password123"

USERS_DB_URL = "mysql+pymysql://rpl_test:rpl_test@localhost:3306/rpl_users"
ACTIVITIES_DB_URL = "mysql+pymysql://rpl_test:rpl_test@localhost:3306/rpl_activities"


def get_or_create(session: Session, model, defaults=None, **kwargs):
    """Return existing row or create a new one. Match by kwargs, fill with defaults."""
    instance = session.execute(
        select(model).filter_by(**kwargs)).scalar_one_or_none()
    if instance:
        return instance, False
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    session.add(instance)
    session.flush()
    return instance, True


def seed_users_db():
    engine = create_engine(USERS_DB_URL)
    UsersBase.metadata.create_all(engine)

    with Session(engine) as session:
        # --- Roles ---
        course_admin_role, created = get_or_create(
            session, Role,
            name="course_admin",
            defaults={
                "permissions": "course_delete,course_view,course_edit,activity_view,activity_manage,activity_submit,user_view,user_manage",
            },
        )
        if created:
            print("  + Role: course_admin")

        student_role, created = get_or_create(
            session, Role,
            name="student",
            defaults={
                "permissions": "course_view,activity_view,activity_submit,user_view",
            },
        )
        if created:
            print("  + Role: student")

        # --- Users ---
        hashed_pw = hash_password(DEFAULT_PASSWORD)

        admin_user, created = get_or_create(
            session, User,
            username="admin",
            defaults={
                "email": "admin@rpl.com",
                "password": hashed_pw,
                "email_validated": True,
                "name": "Admin",
                "surname": "User",
                "student_id": "000000",
                "is_admin": True,
                "degree": "Computer Science",
                "university": "FIUBA",
            },
        )
        if created:
            print("  + User: admin (admin@rpl.com)")

        teacher_user, created = get_or_create(
            session, User,
            username="teacher",
            defaults={
                "email": "teacher@rpl.com",
                "password": hashed_pw,
                "email_validated": True,
                "name": "Maria",
                "surname": "Garcia",
                "student_id": "100000",
                "is_admin": False,
                "degree": "Computer Science",
                "university": "FIUBA",
            },
        )
        if created:
            print("  + User: teacher (teacher@rpl.com)")

        student_user, created = get_or_create(
            session, User,
            username="student",
            defaults={
                "email": "student@rpl.com",
                "password": hashed_pw,
                "email_validated": True,
                "name": "Juan",
                "surname": "Perez",
                "student_id": "200000",
                "is_admin": False,
                "degree": "Computer Science",
                "university": "FIUBA",
            },
        )
        if created:
            print("  + User: student (student@rpl.com)")

        # --- Course ---
        now = datetime.now()
        course, created = get_or_create(
            session, Course,
            name="Algorithms and Data Structures",
            defaults={
                "university": "FIUBA",
                "subject_id": "7541",
                "description": "Introductory course on algorithms, data structures, and C programming.",
                "active": True,
                "deleted": False,
                "semester": "2025-1",
                "semester_start_date": now,
                "semester_end_date": now + timedelta(days=120),
            },
        )
        if created:
            print(f"  + Course: {course.name}")

        # --- Enroll teacher as course_admin ---
        _, created = get_or_create(
            session, CourseUser,
            course_id=course.id,
            user_id=teacher_user.id,
            defaults={
                "role_id": course_admin_role.id,
                "accepted": True,
            },
        )
        if created:
            print("  + Enrolled teacher as course_admin")

        # --- Enroll student ---
        _, created = get_or_create(
            session, CourseUser,
            course_id=course.id,
            user_id=student_user.id,
            defaults={
                "role_id": student_role.id,
                "accepted": True,
            },
        )
        if created:
            print("  + Enrolled student")

        session.commit()
        return course.id

import tarfile
import gzip
import io

def create_tar_gz_bytes(filename: str, content: str) -> bytes:
    """
    Creates a .tar.gz archive in memory from a filename and string content.
    Returns the raw bytes of the compressed archive.
    """
    # 1. Create an in-memory byte stream
    out = io.BytesIO()

    # 2. Open a TarFile object writing to that stream with gzip compression ('w:gz')
    with tarfile.open(fileobj=out, mode="w:gz") as tar:
        # 3. Convert string content to bytes
        content_bytes = content.encode("utf-8")
        
        # 4. Create a TarInfo object (metadata for the file)
        info = tarfile.TarInfo(name=filename)
        info.size = len(content_bytes)
        
        # 5. Add the "file" to the archive
        tar.addfile(tarinfo=info, fileobj=io.BytesIO(content_bytes))

    # 6. Return the full buffer as a bytes object
    return out.getvalue()

# Example Usage:
file_name = "hello_world.py"
file_text = "print('Hello from the tarball!')"

tar_gz_data = create_tar_gz_bytes(file_name, file_text)

def seed_activities_db(course_id: int):
    engine = create_engine(ACTIVITIES_DB_URL)
    ActivitiesBase.metadata.create_all(engine)

    with Session(engine) as session:
        # --- Category ---
        category, created = get_or_create(
            session, ActivityCategory,
            course_id=course_id,
            name="Week 1 - Introduction",
            defaults={
                "description": "Basic exercises to get started with C.",
                "active": True,
            },
        )
        if created:
            print(f"  + Category: {category.name}")

        # --- Starting file (empty placeholder tar) ---
        starting_file, created = get_or_create(
            session, RPLFile,
            file_name="hello_world_starting.tar.gz",
            defaults={
                "file_type": "starting_files",
                "data": tar_gz_data,
            },
        )
        if created:
            print("  + RPLFile: starting files placeholder")

        # --- Activity ---
        activity, created = get_or_create(
            session, Activity,
            course_id=course_id,
            name="Hello World",
            defaults={
                "category_id": category.id,
                "description": "Write a C program that prints 'Hello, World!' to stdout.",
                "language": "c_std11",
                "is_io_tested": True,
                "active": True,
                "deleted": False,
                "starting_rplfile_id": starting_file.id,
                "points": 10,
                "compilation_flags": "",
            },
        )
        if created:
            print(f"  + Activity: {activity.name}")

        session.commit()


def main():
    print("Seeding users database...")
    course_id = seed_users_db()
    print("Seeding activities database...")
    seed_activities_db(course_id)
    print("Done. All seed users have password: " + DEFAULT_PASSWORD)


if __name__ == "__main__":
    main()
