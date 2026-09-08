"""Signal file and signal metadata database models."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class SignalFile(Base):
    __tablename__ = "signal_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    original_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    format: Mapped[str] = mapped_column(String(50), nullable=False)  # WAV, IQ, SIGMF
    data_type: Mapped[str] = mapped_column(String(50), default="complex64")
    iq_order: Mapped[str] = mapped_column(String(10), default="IQ")
    sample_count: Mapped[int] = mapped_column(BigInteger, default=0)
    sample_rate: Mapped[float] = mapped_column(Float, default=0.0)
    center_frequency: Mapped[float] = mapped_column(Float, default=0.0)
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="signal_files")
    metadata_records: Mapped[List["SignalMetadata"]] = relationship(
        "SignalMetadata", back_populates="signal_file", cascade="all, delete-orphan"
    )
    analysis_runs: Mapped[List["AnalysisRun"]] = relationship(
        "AnalysisRun", back_populates="signal_file", cascade="all, delete-orphan"
    )


class SignalMetadata(Base):
    __tablename__ = "signal_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signal_file_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("signal_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parameter_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    parameter_value: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="CALCULATED", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    signal_file: Mapped["SignalFile"] = relationship("SignalFile", back_populates="metadata_records")
