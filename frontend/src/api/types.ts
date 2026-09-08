/**
 * SignalInsight API Type Definitions
 */

export interface HealthResponse {
  status: string;
  database: string;
  version: string;
}

export interface DetailedHealthResponse {
  status: string;
  database: string;
  version: string;
  filesystem: string;
  dsp_engine: string;
  ml_engine: string;
  model_registry: string;
  active_jobs_count: number;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  status: string;
  created_at: string;
  updated_at: string;
  signal_files_count?: number;
  analysis_runs_count?: number;
  reports_count?: number;
}

export interface SignalMetadataItem {
  parameter_name: string;
  parameter_value: string;
  unit: string;
  source: string;
  confidence: number;
}

export interface SignalFile {
  id: number;
  project_id?: number;
  filename: string;
  original_path?: string;
  file_hash: string;
  file_size: number;
  format: string;
  data_type: string;
  iq_order: string;
  sample_count: number;
  sample_rate: number;
  center_frequency: number;
  duration: number;
  created_at: string;
  metadata_records?: SignalMetadataItem[];
}

export interface AnalysisCreateRequest {
  signal_id: number;
  project_id?: number;
  mode?: string;
  remove_dc?: boolean;
  normalize_rms?: boolean;
  estimate_parameters?: boolean;
  extract_features?: boolean;
  classify?: boolean;
  synchronize?: boolean;
  demodulate?: boolean;
  decode?: boolean;
  target_modulation?: string;
  confidence_threshold?: number;
  fec_type?: string;
}

export interface AnalysisResult {
  carrier_frequency?: number;
  carrier_offset?: number;
  symbol_rate?: number;
  occupied_bandwidth?: number;
  bandwidth_3db?: number;
  snr?: number;
  signal_power?: number;
  noise_floor?: number;
  dc_offset_i?: number;
  dc_offset_q?: number;
  estimation_method?: string;
  confidence: number;
  quality: string;
}

export interface ClassificationSummary {
  predicted_class: string;
  confidence: number;
  class_probabilities?: Record<string, number>;
  model_version: string;
  feature_version: string;
  warnings?: string[];
}

export interface FeatureItem {
  feature_name: string;
  feature_value: number;
  unit: string;
  feature_version: string;
  validity: boolean;
}

export interface ProcessingHistoryItem {
  stage: string;
  operation: string;
  status: string;
  message?: string;
  duration_ms: number;
  timestamp: string;
}

export interface FullAnalysis {
  id: number;
  project_id?: number;
  signal_file_id: number;
  status: string;
  started_at?: string;
  completed_at?: string;
  pipeline_version: string;
  error_message?: string;
  result?: AnalysisResult;
  classification?: ClassificationSummary;
  features: FeatureItem[];
  processing_history: ProcessingHistoryItem[];
}

export interface ProcessingJob {
  id: number;
  project_id?: number;
  analysis_run_id?: number;
  job_type: string;
  status: string;
  progress: number;
  current_stage: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

export interface APIErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}
