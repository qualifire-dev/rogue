package tui

import (
	"strings"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/components"
)

// RenderMainScreen renders the main dashboard
func (m Model) RenderMainScreen() string {
	effectiveWidth := m.width - 4

	baseStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("205")).
		Padding(1, 2).
		Width(m.width - 4).
		Height(m.height - 4).
		Align(lipgloss.Center)

	title := lipgloss.NewStyle().
		Foreground(lipgloss.Color("205")).
		Bold(true).
		Render(components.Logo)

	versionStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color("245")).
		Width(lipgloss.Width(title)).
		Align(lipgloss.Right)

	version := versionStyle.Render(m.version)

	cmds := `
	/new           New evaluation       Ctrl+N 
	/models        Models               Ctrl+M 
	/config        Configuration		Ctrl+S 
	/help          Help                 Ctrl+H 
	/quit          Quit                 Q 
	`

	commandsView := lipgloss.NewStyle().
		Width(lipgloss.Width(title)).
		Align(lipgloss.Left)

	lines := []string{}
	lines = append(lines, "")
	lines = append(lines, "")
	lines = append(lines, title)
	lines = append(lines, "\n")
	lines = append(lines, version)
	lines = append(lines, "\n")
	lines = append(lines, "\n")
	lines = append(lines, commandsView.Render(cmds))
	lines = append(lines, "\n")
	lines = append(lines, "\n")

	mainLayout := lipgloss.Place(
		effectiveWidth,
		m.height,
		lipgloss.Center,
		lipgloss.Center,
		baseStyle.Render(strings.Join(lines, "")),
	)

	return mainLayout
}
