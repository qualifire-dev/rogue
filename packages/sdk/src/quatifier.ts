import { EvaluationResult, ReportSummaryRequest, StructuredSummary } from "./types";

interface QualifireReportPayload {
  job_id: string;
  evaluations: EvaluationResult;
  structured: StructuredSummary;
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
      deep_test: request.deepTest,
      start_time: request.startTime,
      judge_model: request.judgeModel || null,
    };
  }

  /**
   * Reports evaluation summary to quatifier.
   * 
   * @param evaluationResults - The evaluation results to report
   * @param request - Configuration including Qualifire URL, API key, and metadata
   * @throws {Error} If the API request fails or returns a non-2xx status
   * @returns A promise that resolves when the report is successfully submitted
   */
  public static async reportSummaryToQualifire(
    evaluationResults: EvaluationResult,
    request: ReportSummaryRequest,
    options: QualifireClientOptions
  ): Promise<void> {
    options?.logger?.("Reporting summary to Qualifire");

    const apiEvaluationResult = this.convertWithStructuredSummary(
      evaluationResults,
      request
    );

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);

    try {
      const response = await fetch(`${request.qualifireUrl}/api/evaluation/evaluate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Qualifire-API-Key": request.qualifireApiKey,
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
      clearTimeout(timeoutId)
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Qualifire report timed out after 30 seconds');
      }
      throw error;
    }
  }
}
