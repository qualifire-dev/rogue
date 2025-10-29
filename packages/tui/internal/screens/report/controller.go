package report

import (
	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/rogue/tui/internal/components"
)

// InputAction represents actions that can be triggered by input
type InputAction int

const (
	ActionNone InputAction = iota
	ActionBackToDashboard
	ActionRegenerateSummary
)

// InputResult contains the result of handling input
type InputResult struct {
	ReportHistory *components.MessageHistoryView
	Action        InputAction
	Cmd           tea.Cmd
}

// HandleInput handles keyboard input for the report screen
func HandleInput(reportHistory *components.MessageHistoryView, hasEvalState bool, canRegenerate bool, msg tea.KeyMsg) InputResult {
	result := InputResult{
		ReportHistory: reportHistory,
		Action:        ActionNone,
	}

	var cmds []tea.Cmd

	if !hasEvalState {
		return result
	}

	switch msg.String() {
	case "b":
		if reportHistory != nil {
			reportHistory.Blur()
		}
		result.Action = ActionBackToDashboard
		return result

	case "r":
		// Regenerate summary if allowed
		if canRegenerate {
			result.Action = ActionRegenerateSummary
		}
		return result

	case "home":
		// Go to top of report
		if reportHistory != nil {
			reportHistory.GotoTop()
		}
		return result

	case "end":
		// Go to bottom of report
		if reportHistory != nil {
			reportHistory.GotoBottom()
		}
		return result

	case "up", "down", "pgup", "pgdown":
		// Scroll the report
		if reportHistory != nil {
			switch msg.String() {
			case "up":
				reportHistory.ScrollUp(1)
			case "down":
				reportHistory.ScrollDown(1)
			case "pgup":
				reportHistory.ScrollUp(10)
			case "pgdown":
				reportHistory.ScrollDown(10)
			}
			cmd := reportHistory.Update(msg)
			if cmd != nil {
				cmds = append(cmds, cmd)
			}
		}
		result.Cmd = tea.Batch(cmds...)
		return result

	default:
		// No action for other keys
		return result
	}
}
