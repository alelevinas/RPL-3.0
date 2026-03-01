from typing import List, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rpl_activities.src.repositories.models.activity import Activity
    from rpl_activities.src.repositories.models.rpl_file import RPLFile
    from rpl_activities.src.repositories.models.test_execution_log import TestsExecutionLog

from sqlalchemy import ForeignKey

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base, BigInt, AutoDateTime, IntPK, Str


class ActivitySubmission(Base):
    __tablename__ = "activity_submissions"

    id: Mapped[IntPK]
    is_final_solution: Mapped[bool]
    activity_id: Mapped[BigInt] = mapped_column(ForeignKey("activities.id"))
    user_id: Mapped[BigInt]
    solution_rplfile_id: Mapped[BigInt] = mapped_column(ForeignKey("rpl_files.id"))
    status: Mapped[Str]
    ai_hint: Mapped[Optional[Str]]
    date_created: Mapped[AutoDateTime]
    last_updated: Mapped[AutoDateTime]

    activity: Mapped["Activity"] = relationship(back_populates="submissions")
    solution_rplfile: Mapped["RPLFile"] = relationship(back_populates="submission")
    tests_execution_log: Mapped[Optional["TestsExecutionLog"]] = relationship(back_populates="submission")
