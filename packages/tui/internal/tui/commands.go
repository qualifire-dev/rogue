package tui

import (
	"context"
	"fmt"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea/v2"
)

// autoRefreshCmd creates a command that sends AutoRefreshMsg after a delay
func autoRefreshCmd() tea.Cmd {
	return tea.Tick(500*time.Millisecond, func(time.Time) tea.Msg {
		return AutoRefreshMsg{}
	})
}

// healthCheckCmd performs a health check in the background
func (m *Model) healthCheckCmd() tea.Cmd {
	return tea.Cmd(func() tea.Msg {
		status, err := m.CheckServerHealth(context.Background(), m.config.ServerURL)
		return HealthCheckResultMsg{
			Status: status,
			Err:    err,
		}
	})
}

// startEvaluationCmd delays then starts the evaluation
func startEvaluationCmd() tea.Cmd {
	return tea.Tick(800*time.Millisecond, func(time.Time) tea.Msg {
		return StartEvaluationMsg{}
	})
}

// summaryGenerationCmd performs summary generation in the background
func (m *Model) summaryGenerationCmd() tea.Cmd {
	return tea.Cmd(func() tea.Msg {
		if m.evalState == nil || m.evalState.JobID == "" {
			return SummaryGeneratedMsg{
				Summary: "",
				Err:     fmt.Errorf("no evaluation job available"),
			}
		}

		sdk := NewRogueSDK(m.config.ServerURL)

		// Use the judge model and API key from config
		judgeModel := m.evalState.JudgeModel
		var apiKey string
		var awsAccessKeyID, awsSecretAccessKey, awsRegion *string

		// Extract provider from judge model (e.g. "openai/gpt-4" -> "openai" or "bedrock/anthropic.claude-..." -> "bedrock")
		if parts := strings.Split(judgeModel, "/"); len(parts) >= 2 {
			provider := parts[0]

			// For Bedrock, extract AWS credentials from config (don't use api_key)
			if provider == "bedrock" {
				if accessKey, ok := m.config.APIKeys["bedrock_access_key"]; ok && accessKey != "" {
					awsAccessKeyID = &accessKey
				}
				if secretKey, ok := m.config.APIKeys["bedrock_secret_key"]; ok && secretKey != "" {
					awsSecretAccessKey = &secretKey
				}
				if region, ok := m.config.APIKeys["bedrock_region"]; ok && region != "" {
					awsRegion = &region
				}
				// Don't set apiKey for Bedrock - use AWS credentials only
			} else {
				// For non-Bedrock providers, extract API key
				if key, ok := m.config.APIKeys[provider]; ok {
					apiKey = key
				}
			}
		}

		// Create a context with longer timeout for summary generation
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
		defer cancel()
		parsedAPIKey := &m.config.QualifireAPIKey
		if !m.config.QualifireEnabled {
			parsedAPIKey = nil
		}
		structuredSummary, err := sdk.GenerateSummary(
			ctx,
			m.evalState.JobID,
			judgeModel,
			apiKey,
			parsedAPIKey,
			m.evalState.DeepTest,
			judgeModel,
			awsAccessKeyID,
			awsSecretAccessKey,
			awsRegion,
		)

		if err != nil {
			return SummaryGeneratedMsg{
				Summary: "",
				Err:     err,
			}
		}

		m.evalState.StructuredSummary = structuredSummary.Summary

		overallSummary := structuredSummary.Summary.OverallSummary
		keyFindings := structuredSummary.Summary.KeyFindings
		parsedKeyFindings := ""
		for _, finding := range keyFindings {
			parsedKeyFindings += "- " + finding + "\n"
		}
		recommendations := structuredSummary.Summary.Recommendations
		parsedRecommendations := ""
		for _, recommendation := range recommendations {
			parsedRecommendations += "- " + recommendation + "\n"
		}

		detailedBreakdown := structuredSummary.Summary.DetailedBreakdown
		parsedDetailedBreakdown := ""
		if len(detailedBreakdown) > 0 {
			// Create Markdown table header
			parsedDetailedBreakdown = "| Scenario | Status | Outcome |\n"
			parsedDetailedBreakdown += "|----------|--------|---------|\n"

			// Add table rows with escaped content
			for _, breakdown := range detailedBreakdown {
				escapedScenario := escapeMarkdownTableCell(breakdown.Scenario)
				escapedStatus := escapeMarkdownTableCell(breakdown.Status)
				escapedOutcome := escapeMarkdownTableCell(breakdown.Outcome)
				parsedDetailedBreakdown += "| " + escapedScenario + " | " + escapedStatus + " | " + escapedOutcome + " |\n"
			}
		}

		summary := "## Overall Summary\n\n" + overallSummary +
			"\n\n" + "## Key Findings\n\n" + parsedKeyFindings +
			"\n\n" + "## Recommendations\n\n" + parsedRecommendations +
			"\n\n" + "## Detailed Breakdown\n\n" + parsedDetailedBreakdown

		return SummaryGeneratedMsg{
			Summary: summary,
			Err:     err,
		}
	})
}

// clampToInt parses a string of digits appended to an int and returns a safe int (falls back on 0 on error)
func clampToInt(s string) int {
	var n int
	_, err := fmt.Sscanf(s, "%d", &n)
	if err != nil {
		return 0
	}
	if n < 0 {
		n = 0
	}
	if n > 9999 {
		n = 9999
	}
	return n
}

// escapeMarkdownTableCell escapes special characters in markdown table cells
func escapeMarkdownTableCell(s string) string {
	// Replace pipe characters with HTML entity to prevent table structure break
	s = strings.ReplaceAll(s, "|", "&#124;")
	// Replace newlines with spaces to keep content on single line
	s = strings.ReplaceAll(s, "\n", " ")
	s = strings.ReplaceAll(s, "\r", " ")
	// Trim extra whitespace
	s = strings.TrimSpace(s)
	return s
}
