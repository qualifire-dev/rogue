package tui

import (
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/screens/evaluations"
	"github.com/rogue/tui/internal/theme"
)

// RenderNewEvaluation renders the new evaluation form screen
func (m Model) RenderNewEvaluation() string {
	if m.evalState == nil {
		t := theme.CurrentTheme()
		return lipgloss.NewStyle().
			Width(m.width).
			Height(m.height).
			Background(t.Background()).
			Foreground(t.Text()).
			Align(lipgloss.Center, lipgloss.Center).
			Render("New evaluation not initialized")
	}

	// Convert Model state to FormState
	formState := &evaluations.FormState{
		Width:  m.width,
		Height: m.height,

		AgentURL:       m.evalState.AgentURL,
		Protocol:       string(m.evalState.AgentProtocol),
		Transport:      string(m.evalState.AgentTransport),
		JudgeModel:     m.evalState.JudgeModel,
		DeepTest:       m.evalState.DeepTest,
		ServerURL:      m.evalState.ServerURL,
		ScenariosCount: len(m.evalState.Scenarios),

		CurrentField: m.evalState.currentField,
		CursorPos:    m.evalState.cursorPos,

		EvalSpinnerActive:   m.evalSpinner.IsActive(),
		HealthSpinnerActive: m.healthSpinner.IsActive(),
		HealthSpinnerView:   m.healthSpinner.View(),
	}

	return evaluations.RenderForm(formState)
}

// handleNewEvalEnter handles the Enter key press on the new evaluation form
func (m *Model) handleNewEvalEnter() {
	if m.evalState == nil || m.evalState.Running {
		return
	}

	// Show spinner - the actual evaluation will start after a delay
	m.evalSpinner.SetActive(true)
}
