"""
Seed script for local development.
Creates: roles, admin user, teacher, students, courses, categories, activities, and submissions.
Idempotent — safe to run multiple times.

Usage: python -m scripts.seed_dev_data [--students N] [--bulk-submissions]
"""

import argparse
import random
import tarfile
import io
from datetime import datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from rpl_users.src.repositories.models.base_model import Base as UsersBase
from rpl_users.src.repositories.models.user import User
from rpl_users.src.repositories.models.course import Course
from rpl_users.src.repositories.models.course_user import CourseUser
from rpl_users.src.repositories.models.role import Role

from rpl_activities.src.repositories.models.base_model import Base as ActivitiesBase
from rpl_activities.src.repositories.models.activity import Activity
from rpl_activities.src.repositories.models.activity_category import ActivityCategory
from rpl_activities.src.repositories.models.rpl_file import RPLFile
from rpl_activities.src.repositories.models.activity_submission import ActivitySubmission
from rpl_activities.src.repositories.models.common_mistakes import CommonMistake

from rpl_users.src.deps.security import hash_password

import os

# Default password for all seed users
DEFAULT_PASSWORD = "password123"

# Load from env if available
USERS_DB_URL = os.getenv("USERS_DB_URL", "mysql+pymysql://rpl_test:rpl_test@localhost:3306/rpl_users")
ACTIVITIES_DB_URL = os.getenv("ACTIVITIES_DB_URL", "mysql+pymysql://rpl_test:rpl_test@localhost:3306/rpl_activities")

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

def create_tar_gz_bytes(filename: str, content: str) -> bytes:
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w:gz") as tar:
        content_bytes = content.encode("utf-8")
        info = tarfile.TarInfo(name=filename)
        info.size = len(content_bytes)
        tar.addfile(tarinfo=info, fileobj=io.BytesIO(content_bytes))
    return out.getvalue()

def seed_users_db(num_students=1, num_courses=1):
    engine = create_engine(USERS_DB_URL)
    UsersBase.metadata.create_all(engine)

    with Session(engine) as session:
        # --- Roles ---
        course_admin_role, _ = get_or_create(
            session, Role, name="course_admin",
            defaults={"permissions": "course_delete,course_view,course_edit,activity_view,activity_manage,activity_submit,user_view,user_manage"},
        )
        student_role, _ = get_or_create(
            session, Role, name="student",
            defaults={"permissions": "course_view,activity_view,activity_submit,user_view"},
        )

        # --- Users ---
        hashed_pw = hash_password(DEFAULT_PASSWORD)
        admin_user, _ = get_or_create(
            session, User, username="admin",
            defaults={"email": "admin@rpl.com", "password": hashed_pw, "email_validated": True, "name": "Admin", "surname": "User", "is_admin": True},
        )
        teacher_user, _ = get_or_create(
            session, User, username="teacher",
            defaults={"email": "teacher@rpl.com", "password": hashed_pw, "email_validated": True, "name": "Maria", "surname": "Garcia", "is_admin": False},
        )

        # --- Courses ---
        course_ids = []
        for i in range(num_courses):
            course_name = f"Algorithms and Data Structures {i+1}" if num_courses > 1 else "Algorithms and Data Structures"
            now = datetime.now()
            course, created = get_or_create(
                session, Course, name=course_name,
                defaults={"university": "FIUBA", "subject_id": str(7541 + i), "active": True, "semester": f"2025-{1 if i%2==0 else 2}", "semester_start_date": now - timedelta(days=30*i), "semester_end_date": now + timedelta(days=120)},
            )
            if created:
                print(f"  + Course: {course_name}")
            
            # Enroll teacher
            get_or_create(session, CourseUser, course_id=course.id, user_id=teacher_user.id, defaults={"role_id": course_admin_role.id, "accepted": True})
            course_ids.append(course.id)

        # --- Students ---
        student_ids = []
        for i in range(num_students):
            username = f"student{i+1}" if num_students > 1 else "student"
            email = f"{username}@rpl.com"
            student, created = get_or_create(
                session, User, username=username,
                defaults={"email": email, "password": hashed_pw, "email_validated": True, "name": f"Student", "surname": str(i+1), "is_admin": False, "student_id": str(200000 + i)},
            )
            if created:
                print(f"  + User: {username}")
            
            # Enroll in all courses
            for course_id in course_ids:
                get_or_create(session, CourseUser, course_id=course_id, user_id=student.id, defaults={"role_id": student_role.id, "accepted": True})
            student_ids.append(student.id)

        session.commit()
        return course_ids, student_ids

def seed_activities_db(course_ids, student_ids, activities_per_course=1, bulk_submissions=False):
    engine = create_engine(ACTIVITIES_DB_URL)
    ActivitiesBase.metadata.create_all(engine)

    with Session(engine) as session:
        for course_id in course_ids:
            # --- Category ---
            category, _ = get_or_create(session, ActivityCategory, course_id=course_id, name="General", defaults={"active": True})

            # --- Activities ---
            for i in range(activities_per_course):
                activity_name = f"Activity {i+1}"
                tar_gz_data = create_tar_gz_bytes("main.c", "int main() { return 0; }")
                starting_file, _ = get_or_create(session, RPLFile, file_name=f"starting_{course_id}_{i}.tar.gz", defaults={"file_type": "starting_files", "data": tar_gz_data})
                
                activity, created = get_or_create(
                    session, Activity, course_id=course_id, name=activity_name,
                    defaults={
                        "category_id": category.id, "description": f"Description for {activity_name}",
                        "language": "c_std11", "is_io_tested": True, "active": True, "starting_rplfile_id": starting_file.id, "points": 10
                    },
                )
                if created:
                    print(f"  + Activity: {activity.name} (Course {course_id})")

                # --- Bulk Submissions ---
                if bulk_submissions:
                    print(f"  + Generating realistic bulk submissions for {len(student_ids)} students for {activity_name}...")
                    for student_id in student_ids:
                        # Realistic student behavior: 
                        # 60% chance to eventually pass, 20% stuck on compilation, 20% stuck on logic
                        behavior = random.random()
                        if behavior < 0.6:
                            # Learner: Fails once or twice, then passes
                            attempts = random.randint(2, 4)
                            for j in range(attempts):
                                status = "PASSED" if j == attempts - 1 else random.choice(["FAILED", "COMPILATION_ERROR"])
                                _create_submission(session, activity, student_id, course_id, status, j == attempts - 1, j)
                        elif behavior < 0.8:
                            # Stuck on compilation
                            attempts = random.randint(1, 3)
                            for j in range(attempts):
                                _create_submission(session, activity, student_id, course_id, "COMPILATION_ERROR", j == attempts - 1, j)
                        else:
                            # Stuck on logic
                            attempts = random.randint(1, 3)
                            for j in range(attempts):
                                _create_submission(session, activity, student_id, course_id, random.choice(["FAILED", "TIMEOUT"]), j == attempts - 1, j)

        session.commit()

def _create_submission(session, activity, student_id, course_id, status, is_final, attempt_num):
    solution_file = create_tar_gz_bytes("main.c", f"// Attempt {attempt_num} for {activity.name}\nint main() {{ return 0; }}")
    rpl_file = RPLFile(file_name=f"sol_{course_id}_{activity.id}_{student_id}_{attempt_num}.tar.gz", file_type="solution", data=solution_file)
    session.add(rpl_file)
    session.flush()

    submission = ActivitySubmission(
        activity_id=activity.id,
        user_id=student_id,
        solution_rplfile_id=rpl_file.id,
        status=status,
        is_final_solution=is_final,
        ai_hint=f"This is a sample AI hint for attempt {attempt_num} with status {status}." if status != "PASSED" else None
    )
    session.add(submission)

def seed_common_mistakes():
    engine = create_engine(ACTIVITIES_DB_URL)
    ActivitiesBase.metadata.create_all(engine)

    with Session(engine) as session:
        mistakes = [
            {
                "language": "c_std11",
                "pattern": "Memory Leak",
                "hint": "Make sure to free() all pointers you malloc(). Use valgrind for more details.",
                "category": "memory"
            },
            {
                "language": "c_std11",
                "pattern": "Segmentation fault",
                "hint": "You're accessing memory you don't own. Check your pointer arithmetic and NULL checks.",
                "category": "runtime"
            },
            {
                "language": "python_3.12",
                "pattern": "IndentationError",
                "hint": "Check your indentation levels. Python is sensitive to whitespace!",
                "category": "compilation"
            },
            {
                "language": "c_std11",
                "pattern": "Timeout",
                "exit_code": 124,
                "hint": "Your program took too long to execute. This might be an infinite loop.",
                "category": "runtime"
            }
        ]

        for m in mistakes:
            get_or_create(session, CommonMistake, language=m["language"], pattern=m.get("pattern"), exit_code=m.get("exit_code"), defaults={"hint": m["hint"], "category": m["category"]})
        
        session.commit()
        print("  + Common Mistakes seeded.")

def main():
    parser = argparse.ArgumentParser(description="Seed RPL-3.0 development data.")
    parser.add_argument("--students", type=int, default=1, help="Number of students to create")
    parser.add_argument("--courses", type=int, default=1, help="Number of courses to create")
    parser.add_argument("--activities-per-course", type=int, default=1, help="Number of activities per course")
    parser.add_argument("--bulk-submissions", action="store_true", help="Generate random submissions for each student")
    args = parser.parse_args()

    print(f"Seeding with {args.students} students, {args.courses} courses, and {args.activities_per_course} activities per course...")
    course_ids, student_ids = seed_users_db(args.students, args.courses)
    seed_common_mistakes()
    seed_activities_db(course_ids, student_ids, args.activities_per_course, args.bulk_submissions)
    print(f"Done. All seed users have password: {DEFAULT_PASSWORD}")

if __name__ == "__main__":
    main()
