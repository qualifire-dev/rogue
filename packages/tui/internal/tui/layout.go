package tui

import "github.com/charmbracelet/lipgloss/v2"

func (m Model) RenderLayout() string {
	style := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("62")).
		Padding(1, 2).
		Width(m.width - 4).
		Height(m.height - 4)

	return style.Render(m.View())
}
