package tui

import (
	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/rogue/tui/internal/components"
)

// HandleEvalDetailInput handles keyboard input for the evaluation detail screen
func HandleEvalDetailInput(m Model, msg tea.KeyMsg) (Model, tea.Cmd) {
	var cmds []tea.Cmd

	if m.evalState == nil {
		return m, nil
	}

	switch msg.String() {
	case "b":
		// Check if we should show the Qualifire persistence dialog
		shouldShowDialog := m.evalState.Completed &&
			m.config.QualifireAPIKey == "" &&
			!m.config.DontShowQualifirePrompt

		if shouldShowDialog {
			// Show report persistence dialog
			dialog := components.NewReportPersistenceDialog()
			m.dialog = &dialog
			return m, nil
		}
		// If no dialog needed, proceed to dashboard
		m.currentScreen = DashboardScreen
		// Reset viewport focus when leaving detail screen
		m.focusedViewport = 0
		return m, nil

	case "s":
		if m.evalState.cancelFn != nil {
			_ = m.evalState.cancelFn()
		}
		return m, nil

	case "r":
		// Navigate to report if evaluation completed
		if m.evalState.Completed {
			// For red team evaluations, navigate to RedTeamReportScreen
			if m.evalState.EvaluationMode == EvaluationModeRedTeam {
				// If we already have report data, just navigate to the report screen
				if m.redTeamReportData != nil {
					m.currentScreen = RedTeamReportScreen
					return m, nil
				}
				// Otherwise, fetch report data first (will navigate after fetch completes)
				if m.evalState.JobID != "" {
					cmd := m.fetchRedTeamReport(m.evalState.JobID)
					return m, cmd
				}
			} else {
				// For policy evaluations, navigate to ReportScreen
				m.currentScreen = ReportScreen
				// Clear cache to ensure report is rebuilt when first shown
				m.cachedReportSummary = ""
				// Report content will be built in renderReport()
				// Focus the report so user can immediately scroll
				if m.reportHistory != nil {
					m.reportHistory.Focus()
				}
			}
		}
		return m, nil

	case "tab":
		// Switch focus between viewports
		// Only switch if both viewports are visible (evaluation completed with summary)
		if m.evalState.Completed && (m.evalState.Summary != "" || m.summarySpinner.IsActive()) {
			// Blur the currently focused viewport
			if m.focusedViewport == 0 && m.eventsHistory != nil {
				m.eventsHistory.Blur()
			} else if m.focusedViewport == 1 && m.summaryHistory != nil {
				m.summaryHistory.Blur()
			}

			// Switch focus
			m.focusedViewport = (m.focusedViewport + 1) % 2

			// Focus the newly selected viewport
			if m.focusedViewport == 0 && m.eventsHistory != nil {
				m.eventsHistory.Focus()
			} else if m.focusedViewport == 1 && m.summaryHistory != nil {
				m.summaryHistory.Focus()
			}
		}
		return m, nil

	case "end":
		// Go to bottom and blur to re-enable auto-scroll
		if m.focusedViewport == 0 && m.eventsHistory != nil {
			m.eventsHistory.GotoBottom()
			m.eventsHistory.Blur()
		} else if m.focusedViewport == 1 && m.summaryHistory != nil {
			m.summaryHistory.GotoBottom()
			m.summaryHistory.Blur()
		}
		return m, nil

	case "home":
		// Go to top and focus to disable auto-scroll
		if m.focusedViewport == 0 && m.eventsHistory != nil {
			m.eventsHistory.GotoTop()
			m.eventsHistory.Focus()
		} else if m.focusedViewport == 1 && m.summaryHistory != nil {
			m.summaryHistory.GotoTop()
			m.summaryHistory.Focus()
		}
		return m, nil

	case "up", "down", "pgup", "pgdown":
		// Arrow keys: focus the active viewport and scroll
		if m.focusedViewport == 0 && m.eventsHistory != nil {
			// Special case: if at bottom and user hits down
			if msg.String() == "down" && m.eventsHistory.AtBottom() {
				// If summary is visible, switch focus to summary panel
				if m.evalState != nil && m.evalState.Completed &&
					(m.evalState.Summary != "" || m.summarySpinner.IsActive()) {
					m.eventsHistory.Blur()
					m.focusedViewport = 1 // Switch to summary
					return m, nil
				}
				// Otherwise, just blur to re-enable auto-scroll
				m.eventsHistory.Blur()
				return m, nil
			}

			// Focus events history when user starts scrolling
			m.eventsHistory.Focus()
			switch msg.String() {
			case "up":
				m.eventsHistory.ScrollUp(1)
			case "down":
				m.eventsHistory.ScrollDown(1)
			case "pgup":
				m.eventsHistory.ScrollUp(10)
			case "pgdown":
				m.eventsHistory.ScrollDown(10)
			}
			cmd := m.eventsHistory.Update(msg)
			if cmd != nil {
				cmds = append(cmds, cmd)
			}
		} else if m.focusedViewport == 1 && m.summaryHistory != nil {
			// Special case: if at top of summary and user hits up, switch back to events
			if msg.String() == "up" && m.summaryHistory.AtTop() {
				m.focusedViewport = 0 // Switch back to events
				if m.eventsHistory != nil {
					m.eventsHistory.Focus()
				}
				return m, nil
			}

			// Summary history scrolling
			m.summaryHistory.Focus()
			switch msg.String() {
			case "up":
				m.summaryHistory.ScrollUp(1)
			case "down":
				m.summaryHistory.ScrollDown(1)
			case "pgup":
				m.summaryHistory.ScrollUp(10)
			case "pgdown":
				m.summaryHistory.ScrollDown(10)
			}
			cmd := m.summaryHistory.Update(msg)
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
