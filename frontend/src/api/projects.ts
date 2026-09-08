/**
 * Projects API endpoints client.
 */

import { ApiClient, defaultApiClient } from "./client";
import { Project } from "./types";

export class ProjectsApi {
  constructor(private client: ApiClient = defaultApiClient) {}

  async list(skip = 0, limit = 100): Promise<Project[]> {
    return this.client.request<Project[]>(`/api/v1/projects?skip=${skip}&limit=${limit}`);
  }

  async get(id: number): Promise<Project> {
    return this.client.request<Project>(`/api/v1/projects/${id}`);
  }

  async create(name: string, description?: string): Promise<Project> {
    return this.client.request<Project>("/api/v1/projects", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    });
  }

  async update(id: number, data: Partial<Project>): Promise<Project> {
    return this.client.request<Project>(`/api/v1/projects/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async delete(id: number): Promise<void> {
    return this.client.request<void>(`/api/v1/projects/${id}`, {
      method: "DELETE",
    });
  }
}

export const projectsApi = new ProjectsApi();
