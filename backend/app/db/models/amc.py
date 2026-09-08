"""AMC, Model Registry, Dataset, and Training Run database models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class Classification(Base):
    __tablename__ = "classifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analysis_runs.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    predicted_class: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    class_probabilities: Mapped[Optional[Dict[str, float]]] = mapped_column(JSON, nullable=True)
    model_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("models.id", ondelete="SET NULL"), nullable=True
    )
    model_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    feature_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    warnings: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis_run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="classification")
    model: Mapped[Optional["Model"]] = relationship("Model", back_populates="classifications")


class Model(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model_type: Mapped[str] = mapped_column(String(100), default="XGBoost", nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    feature_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    classes: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    training_dataset_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True
    )
    metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    training_dataset: Mapped[Optional["Dataset"]] = relationship("Dataset", back_populates="models")
    training_runs: Mapped[List["TrainingRun"]] = relationship("TrainingRun", back_populates="model")
    classifications: Mapped[List["Classification"]] = relationship("Classification", back_populates="model")


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(50), default="SYNTHETIC", nullable=False
    )  # USER_UPLOAD, SYNTHETIC, IMPORTED_PUBLIC_DATASET
    version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    feature_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    classes: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    models: Mapped[List["Model"]] = relationship("Model", back_populates="training_dataset")
    training_runs: Mapped[List["TrainingRun"]] = relationship("TrainingRun", back_populates="dataset")


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True
    )
    model_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("models.id", ondelete="SET NULL"), nullable=True
    )
    algorithm: Mapped[str] = mapped_column(String(100), default="XGBoost", nullable=False)
    configuration: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="QUEUED", nullable=False, index=True
    )  # QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
    training_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    validation_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    test_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precision: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    f1_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    dataset: Mapped[Optional["Dataset"]] = relationship("Dataset", back_populates="training_runs")
    model: Mapped[Optional["Model"]] = relationship("Model", back_populates="training_runs")
    metrics: Mapped[List["TrainingMetric"]] = relationship(
        "TrainingMetric", back_populates="training_run", cascade="all, delete-orphan"
    )


class TrainingMetric(Base):
    __tablename__ = "training_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    training_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("training_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    training_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    validation_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    training_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    validation_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    training_run: Mapped["TrainingRun"] = relationship("TrainingRun", back_populates="metrics")
