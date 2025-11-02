package tui

import (
	"context"
	"fmt"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/glamour"
	"github.com/rogue/tui/internal/screens/scenarios"
	"github.com/rogue/tui/internal/shared"
	"github.com/rogue/tui/internal/theme"
)

// startInterviewCmd starts a new interview session
func (m *Model) startInterviewCmd() tea.Cmd {
	return func() tea.Msg {
		ctx := context.Background()
		sdk := NewRogueSDK(m.config.ServerURL)

		// Get interview model and API key from scenario editor config
		interviewModel := m.scenarioEditor.InterviewModel
		interviewAPIKey := m.scenarioEditor.InterviewAPIKey

		if interviewModel == "" {
			// Fall back to judge model if not set
			return scenarios.InterviewStartedMsg{
				Error: fmt.Errorf("AI model not set, please use /models to set an AI model"),
			}
		}

		if interviewAPIKey == "" {
			return scenarios.InterviewStartedMsg{
				Error: fmt.Errorf("AI API key not set, please use /models to set an AI API key"),
			}
		}

		// Start interview
		resp, err := sdk.StartInterview(ctx, interviewModel, interviewAPIKey)
		if err != nil {
			return scenarios.InterviewStartedMsg{
				Error: err,
			}
		}

		return scenarios.InterviewStartedMsg{
			SessionID:      resp.SessionID,
			InitialMessage: resp.InitialMessage,
			Error:          nil,
		}
	}
}

// sendInterviewMessageCmd sends a message in the interview
func (m *Model) sendInterviewMessageCmd(sessionID, message string) tea.Cmd {
	return func() tea.Msg {
		ctx := context.Background()
		sdk := NewRogueSDK(m.config.ServerURL)

		// Send message
		resp, err := sdk.SendInterviewMessage(ctx, sessionID, message)
		if err != nil {
			return scenarios.InterviewResponseMsg{
				Error: err,
			}
		}

		return scenarios.InterviewResponseMsg{
			Response:     resp.Response,
			IsComplete:   resp.IsComplete,
			MessageCount: resp.MessageCount,
			Error:        nil,
		}
	}
}

// generateScenariosCmd generates scenarios from business context
func (m *Model) generateScenariosCmd(businessContext string) tea.Cmd {
	return func() tea.Msg {
		ctx := context.Background()
		sdk := NewRogueSDK(m.config.ServerURL)

		// Get interview model and API key
		interviewModel := m.scenarioEditor.InterviewModel
		interviewAPIKey := m.scenarioEditor.InterviewAPIKey

		if interviewModel == "" {
			interviewModel = "openai/gpt-4o"
		}

		// Generate scenarios
		request := ScenarioGenerationRequest{
			BusinessContext: businessContext,
			Model:           interviewModel,
			APIKey:          interviewAPIKey,
			Count:           10, // Default to 10 scenarios
		}

		resp, err := sdk.GenerateScenarios(ctx, request)
		if err != nil {
			return scenarios.ScenariosGeneratedMsg{
				Error: err,
			}
		}

		// Convert SDK scenario data to component scenario data
		var scenariosList []scenarios.ScenarioData
		for _, s := range resp.Scenarios.Scenarios {
			scenariosList = append(scenariosList, scenarios.ScenarioData{
				Scenario:          s.Scenario,
				ScenarioType:      s.ScenarioType,
				Dataset:           s.Dataset,
				ExpectedOutcome:   s.ExpectedOutcome,
				DatasetSampleSize: s.DatasetSampleSize,
			})
		}

		return scenarios.ScenariosGeneratedMsg{
			Scenarios:       scenariosList,
			BusinessContext: businessContext,
			Error:           nil,
		}
	}
}

// configureScenarioEditorWithInterviewModel configures the scenario editor with interview model settings
func (m *Model) configureScenarioEditorWithInterviewModel() {
	interviewModel := "openai/gpt-4o" // Default fallback
	if m.config.InterviewProvider != "" && m.config.InterviewModel != "" {
		interviewModel = m.config.InterviewProvider + "/" + m.config.InterviewModel
	} else if m.config.SelectedProvider != "" && m.config.SelectedModel != "" {
		// Fall back to selected judge model if interview model not set
		interviewModel = m.config.SelectedProvider + "/" + m.config.SelectedModel
	}
	interviewAPIKey := ""
	if m.config.InterviewProvider != "" {
		if key, ok := m.config.APIKeys[m.config.InterviewProvider]; ok {
			interviewAPIKey = key
		}
	} else if m.config.SelectedProvider != "" {
		if key, ok := m.config.APIKeys[m.config.SelectedProvider]; ok {
			interviewAPIKey = key
		}
	}
	m.scenarioEditor.SetConfig(m.config.ServerURL, interviewModel, interviewAPIKey)

	// Set markdown renderer for interview responses
	renderer := m.getMarkdownRenderer()
	m.scenarioEditor.SetMarkdownRenderer(renderer)
}

// getMarkdownRenderer returns a markdown renderer configured for the current dimensions and theme
// Uses caching to avoid recreating the renderer unnecessarily
func (m *Model) getMarkdownRenderer() *glamour.TermRenderer {
	t := theme.CurrentTheme()
	currentThemeName := theme.CurrentThemeName()

	// Use a reasonable width for markdown rendering, accounting for padding/margins
	width := m.width - 8
	if width < 40 {
		width = 40
	}

	// Check if we need to recreate the renderer
	needsRecreate := m.markdownRenderer == nil ||
		m.rendererCachedWidth != width ||
		m.rendererCachedTheme != currentThemeName

	if needsRecreate {
		m.markdownRenderer = shared.GetMarkdownRenderer(width, t.Background())
		m.rendererCachedWidth = width
		m.rendererCachedTheme = currentThemeName
	}

	return m.markdownRenderer
}
