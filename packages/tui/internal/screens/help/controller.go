package help

import (
	"log"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/rogue/tui/internal/components"
)

// HandleInput handles keyboard input for the help screen
// Returns the updated viewport and any commands
func HandleInput(viewport *components.Viewport, msg tea.KeyMsg) (*components.Viewport, tea.Cmd) {
	var cmds []tea.Cmd

	log.Printf("[HELP] HandleInput called with key: %s, viewport YOffset: %d, maxYOffset: %d", msg.String(), viewport.YOffset, viewport.TotalLineCount()-viewport.Height)

	switch msg.String() {
	case "home":
		// Go to top of help content
		viewport.GotoTop()
		log.Printf("[HELP] Home pressed, YOffset now: %d", viewport.YOffset)
		return viewport, nil

	case "end":
		// Go to bottom of help content
		viewport.GotoBottom()
		log.Printf("[HELP] End pressed, YOffset now: %d", viewport.YOffset)
		return viewport, nil

	default:
		// Update the help viewport for scrolling
		log.Printf("[HELP] Calling viewport.Update with key: %s", msg.String())
		updatedViewport, cmd := viewport.Update(msg)
		log.Printf("[HELP] After viewport.Update, YOffset: %d", updatedViewport.YOffset)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		return updatedViewport, tea.Batch(cmds...)
	}
}
