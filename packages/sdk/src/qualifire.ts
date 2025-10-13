import { EvaluationResult, ReportSummaryRequest } from "./types";

export class QualifireClient {
  private static convertWithStructuredSummary(
    evaluationResults: EvaluationResult,
    request: ReportSummaryRequest
  ): any {
    return {
      evaluations: evaluationResults,
      structured: request.structuredSummary,
      deep_test: request.deepTest,
      start_time: request.startTime,
      judge_model: request.judgeModel || null,
    };
  }

  public static async reportSummaryToQualifire(
    evaluationResults: EvaluationResult,
    request: ReportSummaryRequest
  ): Promise<void> {
    console.info("Reporting summary to Qualifire");

    const apiEvaluationResult = this.convertWithStructuredSummary(
      evaluationResults,
      request
    );

    const response = await fetch(`${request.qualifireUrl}/api/rogue/v1/report`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-qualifire-key": request.qualifireApiKey,
      },
      body: JSON.stringify(apiEvaluationResult),
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(
        `Qualifire report failed: ${response.status} ${response.statusText} - ${errText}`
      );
    }
  }
}
