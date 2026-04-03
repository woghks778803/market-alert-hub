from datetime import datetime
from sqlalchemy import Integer, String, Text, Boolean, DateTime, Index, Enum as SAEnum, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base
from app.core.util.datetime import utcnow
from app.core.constants import FAQCategory  

from app.domain import SupportDTO

class FAQ(Base):
    __tablename__ = "faqs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(String(255), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)  # Tiptap HTML
    
    category: Mapped[str] = mapped_column(SAEnum(FAQCategory, values_callable=lambda e: [m.value for m in e],
                                                            native_enum=True, create_constraint=True, validate_strings=True),
                                                            default=FAQCategory.GENERAL, nullable=False)
    
    display_order: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def to_dto(self) -> SupportDTO.FAQ:
        return SupportDTO.FAQ(
            id=self.id,
            question=self.question,
            answer=self.answer,
            category=self.category,
            display_order=self.display_order,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )