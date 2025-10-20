package tui

import (
	tea "github.com/charmbracelet/bubbletea/v2"
)

// handleReportInput handles keyboard input for the report screen
func (m Model) handleReportInput(msg tea.KeyMsg) (Model, tea.Cmd) {
	var cmds []tea.Cmd

	if m.evalState == nil {
		return m, nil
	}

	switch msg.String() {
	case "b":
		if m.reportHistory != nil {
			m.reportHistory.Blur()
		}
		m.currentScreen = DashboardScreen
		return m, nil

	case "r":
		// Regenerate summary if we have job ID (force refresh)
		if m.evalState.JobID != "" && !m.summarySpinner.IsActive() {
			// Allow manual regeneration by resetting the flag
			m.evalState.SummaryGenerated = false
			m.summarySpinner.SetActive(true)
			return m, tea.Batch(m.summarySpinner.Start(), m.summaryGenerationCmd())
		}
		return m, nil

	case "home":
		// Go to top of report
		if m.reportHistory != nil {
			m.reportHistory.GotoTop()
		}
		return m, nil

	case "end":
		// Go to bottom of report
		if m.reportHistory != nil {
			m.reportHistory.GotoBottom()
		}
		return m, nil

	case "up", "down", "pgup", "pgdown":
		// Scroll the report
		if m.reportHistory != nil {
			switch msg.String() {
			case "up":
				m.reportHistory.ScrollUp(1)
			case "down":
				m.reportHistory.ScrollDown(1)
			case "pgup":
				m.reportHistory.ScrollUp(10)
			case "pgdown":
				m.reportHistory.ScrollDown(10)
			}
			cmd := m.reportHistory.Update(msg)
			if cmd != nil {
				cmds = append(cmds, cmd)
			}
		}
		return m, tea.Batch(cmds...)

	default:
		// No action for other keys
		return m, nil
	}
}
