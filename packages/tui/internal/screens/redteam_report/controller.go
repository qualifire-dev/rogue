package redteam_report

import (
	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/rogue/tui/internal/components"
)

// InputAction represents actions that can be triggered by input
type InputAction int

const (
	ActionNone InputAction = iota
	ActionBackToEvalDetail
	ActionExportCSV
)

// InputResult contains the result of handling input
type InputResult struct {
	Viewport *components.Viewport
	Action   InputAction
	Cmd      tea.Cmd
}

// HandleInput handles keyboard input for the red team report screen
func HandleInput(viewport *components.Viewport, msg tea.KeyMsg) InputResult {
	result := InputResult{
		Viewport: viewport,
		Action:   ActionNone,
	}

	var cmds []tea.Cmd

	switch msg.String() {
	case "b", "esc":
		// Back to evaluation detail screen
		result.Action = ActionBackToEvalDetail
		return result

	case "e":
		// Export CSV (action handled by caller)
		result.Action = ActionExportCSV
		return result

	case "home":
		// Go to top of report
		viewport.GotoTop()
		return result

	case "end":
		// Go to bottom of report
		viewport.GotoBottom()
		return result

	case "up", "down", "pgup", "pgdown", "k", "j":
		// Handle scrolling - forward to viewport
		updatedViewport, cmd := viewport.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		result.Viewport = updatedViewport
		result.Cmd = tea.Batch(cmds...)
		return result

	default:
		// For any other keys, try forwarding to viewport
		updatedViewport, cmd := viewport.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		result.Viewport = updatedViewport
		result.Cmd = tea.Batch(cmds...)
		return result
	}
}
