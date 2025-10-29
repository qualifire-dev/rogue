package help

import (
	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/rogue/tui/internal/components"
)

// HandleInput handles keyboard input for the help screen
// Returns the updated viewport and any commands
func HandleInput(viewport *components.Viewport, msg tea.KeyMsg) (*components.Viewport, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg.String() {
	case "home":
		// Go to top of help content
		viewport.GotoTop()
		return viewport, nil

	case "end":
		// Go to bottom of help content
		viewport.GotoBottom()
		return viewport, nil

	default:
		// Update the help viewport for scrolling
		updatedViewport, cmd := viewport.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		return updatedViewport, tea.Batch(cmds...)
	}
}
