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

  getHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.baseUrl}/health`);
  }

  analyzeRepository(repositoryLocation: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/api/repository/analyze`, {
      repository_location: repositoryLocation
    });
  }

  executeChange(payload: ChangeRequestPayload): Observable<WorkflowResult> {
    const correlationId = 'ui-' + Math.random().toString(36).substring(2, 9);
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'X-Correlation-ID': correlationId
    });
    return this.http.post<WorkflowResult>(`${this.baseUrl}/api/changes/execute`, payload, { headers });
  }
}
