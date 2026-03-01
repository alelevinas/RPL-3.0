from sqlalchemy import select
from sqlalchemy.orm import Session
from rpl_activities.src.repositories.models.common_mistakes import CommonMistake

class CommonMistakesRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_for_language(self, language: str) -> list[CommonMistake]:
        stmt = select(CommonMistake).where(CommonMistake.language == language)
        return list(self.session.execute(stmt).scalars().all())

    def create(self, language: str, pattern: str | None, exit_code: int | None, hint: str, category: str) -> CommonMistake:
        mistake = CommonMistake(
            language=language,
            pattern=pattern,
            exit_code=exit_code,
            hint=hint,
            category=category
        )
        self.session.add(mistake)
        self.session.commit()
        self.session.refresh(mistake)
        return mistake
