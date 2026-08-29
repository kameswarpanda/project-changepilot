import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ChangeRequestPayload, HealthResponse, WorkflowResult } from '../models';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('cp_token');
    let headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  }

  getHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.baseUrl}/health`);
  }

  listRepositories(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/api/repositories`, { headers: this.getHeaders() });
  }

  listBranches(repoId: string): Observable<string[]> {
    return this.http.get<string[]>(`${this.baseUrl}/api/repositories/${repoId}/branches`, { headers: this.getHeaders() });
  }

  connectRepository(payload: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/api/repositories/connect`, payload, { headers: this.getHeaders() });
  }

  listPipelines(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/api/pipelines`, { headers: this.getHeaders() });
  }

  analyzeRepository(repositoryLocation: string): Observable<any> {
    return this.http.post<any>(
      `${this.baseUrl}/api/repository/analyze`,
      { repository_location: repositoryLocation },
      { headers: this.getHeaders() }
    );
  }

  executeChange(payload: ChangeRequestPayload): Observable<WorkflowResult> {
    const correlationId = 'ui-' + Math.random().toString(36).substring(2, 9);
    let headers = this.getHeaders().set('X-Correlation-ID', correlationId);
    return this.http.post<WorkflowResult>(`${this.baseUrl}/api/changes/execute`, payload, { headers });
  }
}
