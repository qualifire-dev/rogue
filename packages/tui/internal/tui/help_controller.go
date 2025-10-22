package tui

import (
	tea "github.com/charmbracelet/bubbletea/v2"
)

// handleHelpInput handles keyboard input for the help screen
func (m Model) handleHelpInput(msg tea.KeyMsg) (Model, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg.String() {
	case "home":
		// Go to top of help content
		m.helpViewport.GotoTop()
		return m, nil

	case "end":
		// Go to bottom of help content
		m.helpViewport.GotoBottom()
		return m, nil

	default:
		// Update the help viewport for scrolling
		helpViewportPtr, cmd := m.helpViewport.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		m.helpViewport = *helpViewportPtr
		return m, tea.Batch(cmds...)
	}
}
