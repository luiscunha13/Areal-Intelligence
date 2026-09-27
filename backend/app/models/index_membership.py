from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class IndexMembership(Base):
    __tablename__ = "index_memberships"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    index_name = Column(String(50), nullable=False, default="S&P 500")
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True) # NULL means currently active
    source = Column(String(100), default="Wikipedia / SEC")

    company = relationship("Company", back_populates="index_memberships")
