"""Processing Job and Processing History database models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    analysis_run_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=True, index=True
    )
    job_type: Mapped[str] = mapped_column(String(100), default="ANALYSIS", nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="QUEUED", nullable=False, index=True
    )  # QUEUED, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0 to 100
    current_stage: Mapped[str] = mapped_column(String(100), default="INITIALIZING", nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="processing_jobs")
    analysis_run: Mapped[Optional["AnalysisRun"]] = relationship("AnalysisRun", back_populates="processing_jobs")


class ProcessingHistory(Base):
    __tablename__ = "processing_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    analysis_run_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=True, index=True
    )
    stage: Mapped[str] = mapped_column(String(100), nullable=False)
    operation: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="processing_history")
    analysis_run: Mapped[Optional["AnalysisRun"]] = relationship("AnalysisRun", back_populates="processing_history")
