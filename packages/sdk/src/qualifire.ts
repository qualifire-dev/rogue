import { EvaluationResult, ReportSummaryRequest, StructuredSummary } from "./types";

interface QualifireReportPayload {
  job_id: string;
  evaluations: EvaluationResult;
  structured: StructuredSummary | null;
  deep_test: boolean;
  start_time: string;
  judge_model: string | null;
}

export interface QualifireClientOptions {
  logger?: (message: string) => void;
}

export class QualifireClient {
  private static convertWithStructuredSummary(
    evaluationResults: EvaluationResult,
    request: ReportSummaryRequest
  ): QualifireReportPayload {
    return {
      job_id: request.job_id,
      evaluations: evaluationResults,
      structured: request.structuredSummary || null,
      deep_test: request.deepTest ?? false,
      start_time: request.startTime ?? new Date().toISOString(),
      judge_model: request.judgeModel || null,
    };
  }

  /**
   * Reports evaluation summary to Qualifire.
   * 
   * @param evaluationResults - The evaluation results to report
   * @param request - Configuration including Qualifire URL, API key, and metadata
   * @throws {Error} If the API request fails or returns a non-2xx status
   * @returns A promise that resolves when the report is successfully submitted
   */
  public static async reportSummaryToQualifire(
    evaluationResults: EvaluationResult,
    request: ReportSummaryRequest,
    options?: QualifireClientOptions
  ): Promise<void> {
    options?.logger?.("Reporting summary to Qualifire");

    const apiKey = request.qualifireApiKey;
    const baseUrl = request.qualifireUrl ?? "https://api.qualifire.com";
    const endpoint = `${baseUrl}/api/v1/evaluations`;

    if (!apiKey) {
      throw new Error("qualifireApiKey is required but was undefined");
    }

    if (!baseUrl || baseUrl === "undefined") {
      throw new Error("Invalid qualifireUrl provided");
    }

    const apiEvaluationResult = this.convertWithStructuredSummary(
      evaluationResults,
      request
    );

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Qualifire-API-Key": apiKey,
        },
        body: JSON.stringify(apiEvaluationResult),
        signal: controller.signal
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(
          `Qualifire report failed: ${response.status} ${response.statusText} - ${errText}`
        );
      }
      clearTimeout(timeoutId);
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Qualifire report timed out after 30 seconds');
      }
      throw error;
    }
  }
}
