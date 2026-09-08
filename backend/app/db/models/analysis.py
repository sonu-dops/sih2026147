"""Analysis Run, Analysis Result, and Feature database models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    signal_file_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("signal_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="QUEUED", nullable=False, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    pipeline_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    configuration: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="analysis_runs")
    signal_file: Mapped["SignalFile"] = relationship("SignalFile", back_populates="analysis_runs")
    result: Mapped[Optional["AnalysisResult"]] = relationship(
        "AnalysisResult", back_populates="analysis_run", uselist=False, cascade="all, delete-orphan"
    )
    features: Mapped[List["Feature"]] = relationship(
        "Feature", back_populates="analysis_run", cascade="all, delete-orphan"
    )
    classification: Mapped[Optional["Classification"]] = relationship(
        "Classification", back_populates="analysis_run", uselist=False, cascade="all, delete-orphan"
    )
    processing_jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob", back_populates="analysis_run", cascade="all, delete-orphan"
    )
    processing_history: Mapped[List["ProcessingHistory"]] = relationship(
        "ProcessingHistory", back_populates="analysis_run", cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report", back_populates="analysis_run", cascade="all, delete-orphan"
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analysis_runs.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    carrier_frequency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    carrier_offset: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    symbol_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    occupied_bandwidth: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bandwidth_3db: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    snr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    signal_power: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    noise_floor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dc_offset_i: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dc_offset_q: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimation_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    quality: Mapped[str] = mapped_column(String(50), default="HIGH", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis_run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="result")


class Feature(Base):
    __tablename__ = "features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    feature_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    feature_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    validity: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    analysis_run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="features")
