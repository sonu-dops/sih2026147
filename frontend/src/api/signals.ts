/**
 * Signals, Analysis, and Jobs frontend API endpoints.
 */

import { ApiClient, defaultApiClient } from "./client";
import { AnalysisCreateRequest, FullAnalysis, ProcessingJob, SignalFile } from "./types";

export class SignalsApi {
  constructor(private client: ApiClient = defaultApiClient) {}

  async list(projectId?: number, skip = 0, limit = 100): Promise<SignalFile[]> {
    const q = projectId ? `&project_id=${projectId}` : "";
    return this.client.request<SignalFile[]>(`/api/v1/signals?skip=${skip}&limit=${limit}${q}`);
  }

  async get(id: number): Promise<SignalFile> {
    return this.client.request<SignalFile>(`/api/v1/signals/${id}`);
  }

  async upload(file: File, projectId?: number, sampleRate?: number, centerFrequency?: number): Promise<SignalFile> {
    const formData = new FormData();
    formData.append("file", file);
    if (projectId) formData.append("project_id", projectId.toString());
    if (sampleRate) formData.append("sample_rate", sampleRate.toString());
    if (centerFrequency) formData.append("center_frequency", centerFrequency.toString());

    return this.client.request<SignalFile>("/api/v1/signals/upload", {
      method: "POST",
      body: formData,
    });
  }

  async delete(id: number): Promise<void> {
    return this.client.request<void>(`/api/v1/signals/${id}`, {
      method: "DELETE",
    });
  }
}

export class AnalysisApi {
  constructor(private client: ApiClient = defaultApiClient) {}

  async start(req: AnalysisCreateRequest): Promise<FullAnalysis> {
    return this.client.request<FullAnalysis>("/api/v1/analysis", {
      method: "POST",
      body: JSON.stringify(req),
    });
  }

  async get(id: number): Promise<FullAnalysis> {
    return this.client.request<FullAnalysis>(`/api/v1/analysis/${id}`);
  }

  async pause(id: number): Promise<void> {
    return this.client.request<void>(`/api/v1/analysis/${id}/pause`, { method: "POST" });
  }

  async resume(id: number): Promise<void> {
    return this.client.request<void>(`/api/v1/analysis/${id}/resume`, { method: "POST" });
  }

  async cancel(id: number): Promise<void> {
    return this.client.request<void>(`/api/v1/analysis/${id}/cancel`, { method: "POST" });
  }
}

export class JobsApi {
  constructor(private client: ApiClient = defaultApiClient) {}

  async get(jobId: number): Promise<ProcessingJob> {
    return this.client.request<ProcessingJob>(`/api/v1/jobs/${jobId}`);
  }

  subscribe(jobId: number, onUpdate: (job: Partial<ProcessingJob>) => void, onError?: (err: any) => void): WebSocket {
    const wsUrl = `ws://127.0.0.1:8000/api/v1/ws/jobs/${jobId}`;
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onUpdate(data);
      } catch (e) {
        if (onError) onError(e);
      }
    };
    if (onError) ws.onerror = onError;
    return ws;
  }
}

export const signalsApi = new SignalsApi();
export const analysisApi = new AnalysisApi();
export const jobsApi = new JobsApi();
