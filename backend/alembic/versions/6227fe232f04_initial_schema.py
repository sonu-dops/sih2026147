"""initial schema

Revision ID: 6227fe232f04
Revises: 
Create Date: 2026-09-07 15:55:56.233539

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '6227fe232f04'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Projects
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_projects_name'), 'projects', ['name'], unique=False)

    # 2. Datasets
    op.create_table(
        'datasets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='SYNTHETIC'),
        sa.Column('version', sa.String(length=50), nullable=False, server_default='1.0.0'),
        sa.Column('sample_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('feature_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('classes', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_datasets_name'), 'datasets', ['name'], unique=False)

    # 3. Models
    op.create_table(
        'models',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('model_type', sa.String(length=100), nullable=False, server_default='XGBoost'),
        sa.Column('version', sa.String(length=50), nullable=False, server_default='1.0.0'),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('feature_version', sa.String(length=50), nullable=False, server_default='1.0.0'),
        sa.Column('classes', sa.JSON(), nullable=True),
        sa.Column('training_dataset_id', sa.Integer(), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['training_dataset_id'], ['datasets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_models_name'), 'models', ['name'], unique=False)

    # 4. Training Runs
    op.create_table(
        'training_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('model_id', sa.Integer(), nullable=True),
        sa.Column('algorithm', sa.String(length=100), nullable=False, server_default='XGBoost'),
        sa.Column('configuration', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='QUEUED'),
        sa.Column('training_accuracy', sa.Float(), nullable=True),
        sa.Column('validation_accuracy', sa.Float(), nullable=True),
        sa.Column('test_accuracy', sa.Float(), nullable=True),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_training_runs_status'), 'training_runs', ['status'], unique=False)

    # 5. Training Metrics
    op.create_table(
        'training_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('training_run_id', sa.Integer(), nullable=False),
        sa.Column('epoch', sa.Integer(), nullable=False),
        sa.Column('training_loss', sa.Float(), nullable=True),
        sa.Column('validation_loss', sa.Float(), nullable=True),
        sa.Column('training_accuracy', sa.Float(), nullable=True),
        sa.Column('validation_accuracy', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['training_run_id'], ['training_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_training_metrics_training_run_id'), 'training_metrics', ['training_run_id'], unique=False)

    # 6. Signal Files
    op.create_table(
        'signal_files',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_path', sa.String(length=1024), nullable=True),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('format', sa.String(length=50), nullable=False),
        sa.Column('data_type', sa.String(length=50), nullable=False, server_default='complex64'),
        sa.Column('iq_order', sa.String(length=10), nullable=False, server_default='IQ'),
        sa.Column('sample_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('sample_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('center_frequency', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('duration', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_signal_files_file_hash'), 'signal_files', ['file_hash'], unique=False)
    op.create_index(op.f('ix_signal_files_filename'), 'signal_files', ['filename'], unique=False)
    op.create_index(op.f('ix_signal_files_project_id'), 'signal_files', ['project_id'], unique=False)

    # 7. Signal Metadata
    op.create_table(
        'signal_metadata',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('signal_file_id', sa.Integer(), nullable=False),
        sa.Column('parameter_name', sa.String(length=100), nullable=False),
        sa.Column('parameter_value', sa.Text(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='CALCULATED'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['signal_file_id'], ['signal_files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_signal_metadata_parameter_name'), 'signal_metadata', ['parameter_name'], unique=False)
    op.create_index(op.f('ix_signal_metadata_signal_file_id'), 'signal_metadata', ['signal_file_id'], unique=False)

    # 8. Analysis Runs
    op.create_table(
        'analysis_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('signal_file_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='QUEUED'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('pipeline_version', sa.String(length=50), nullable=False, server_default='1.0.0'),
        sa.Column('configuration', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['signal_file_id'], ['signal_files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_analysis_runs_project_id'), 'analysis_runs', ['project_id'], unique=False)
    op.create_index(op.f('ix_analysis_runs_signal_file_id'), 'analysis_runs', ['signal_file_id'], unique=False)
    op.create_index(op.f('ix_analysis_runs_status'), 'analysis_runs', ['status'], unique=False)

    # 9. Analysis Results
    op.create_table(
        'analysis_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('analysis_run_id', sa.Integer(), nullable=False),
        sa.Column('carrier_frequency', sa.Float(), nullable=True),
        sa.Column('carrier_offset', sa.Float(), nullable=True),
        sa.Column('symbol_rate', sa.Float(), nullable=True),
        sa.Column('occupied_bandwidth', sa.Float(), nullable=True),
        sa.Column('bandwidth_3db', sa.Float(), nullable=True),
        sa.Column('snr', sa.Float(), nullable=True),
        sa.Column('signal_power', sa.Float(), nullable=True),
        sa.Column('noise_floor', sa.Float(), nullable=True),
        sa.Column('dc_offset_i', sa.Float(), nullable=True),
        sa.Column('dc_offset_q', sa.Float(), nullable=True),
        sa.Column('estimation_method', sa.String(length=100), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('quality', sa.String(length=50), nullable=False, server_default='HIGH'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('analysis_run_id'),
    )

    # 10. Features
    op.create_table(
        'features',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('analysis_run_id', sa.Integer(), nullable=False),
        sa.Column('feature_name', sa.String(length=100), nullable=False),
        sa.Column('feature_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('feature_version', sa.String(length=50), nullable=False, server_default='1.0.0'),
        sa.Column('validity', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_features_analysis_run_id'), 'features', ['analysis_run_id'], unique=False)
    op.create_index(op.f('ix_features_feature_name'), 'features', ['feature_name'], unique=False)

    # 11. Classifications
    op.create_table(
        'classifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('analysis_run_id', sa.Integer(), nullable=False),
        sa.Column('predicted_class', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('class_probabilities', sa.JSON(), nullable=True),
        sa.Column('model_id', sa.Integer(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=False, server_default='1.0.0'),
        sa.Column('feature_version', sa.String(length=50), nullable=False, server_default='1.0.0'),
        sa.Column('warnings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('analysis_run_id'),
    )
    op.create_index(op.f('ix_classifications_predicted_class'), 'classifications', ['predicted_class'], unique=False)

    # 12. Processing Jobs
    op.create_table(
        'processing_jobs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('analysis_run_id', sa.Integer(), nullable=True),
        sa.Column('job_type', sa.String(length=100), nullable=False, server_default='ANALYSIS'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='QUEUED'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_stage', sa.String(length=100), nullable=False, server_default='INITIALIZING'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_processing_jobs_analysis_run_id'), 'processing_jobs', ['analysis_run_id'], unique=False)
    op.create_index(op.f('ix_processing_jobs_project_id'), 'processing_jobs', ['project_id'], unique=False)
    op.create_index(op.f('ix_processing_jobs_status'), 'processing_jobs', ['status'], unique=False)

    # 13. Processing History
    op.create_table(
        'processing_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('analysis_run_id', sa.Integer(), nullable=True),
        sa.Column('stage', sa.String(length=100), nullable=False),
        sa.Column('operation', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='COMPLETED'),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_processing_history_analysis_run_id'), 'processing_history', ['analysis_run_id'], unique=False)
    op.create_index(op.f('ix_processing_history_project_id'), 'processing_history', ['project_id'], unique=False)

    # 14. Reports
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('analysis_run_id', sa.Integer(), nullable=True),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reports_analysis_run_id'), 'reports', ['analysis_run_id'], unique=False)
    op.create_index(op.f('ix_reports_project_id'), 'reports', ['project_id'], unique=False)

    # 15. App Settings
    op.create_table(
        'app_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )
    op.create_index(op.f('ix_app_settings_key'), 'app_settings', ['key'], unique=True)


def downgrade() -> None:
    op.drop_table('app_settings')
    op.drop_table('reports')
    op.drop_table('processing_history')
    op.drop_table('processing_jobs')
    op.drop_table('classifications')
    op.drop_table('features')
    op.drop_table('analysis_results')
    op.drop_table('analysis_runs')
    op.drop_table('signal_metadata')
    op.drop_table('signal_files')
    op.drop_table('training_metrics')
    op.drop_table('training_runs')
    op.drop_table('models')
    op.drop_table('datasets')
    op.drop_table('projects')
