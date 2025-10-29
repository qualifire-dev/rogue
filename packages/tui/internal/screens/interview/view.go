package interview

import (
	"fmt"

	"github.com/charmbracelet/lipgloss/v2"
)

// Render renders the interview screen
func Render(width, height int) string {
	style := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("62")).
		Padding(1, 2).
		Width(width - 4).
		Height(height - 4)

	title := lipgloss.NewStyle().
		Foreground(lipgloss.Color("205")).
		Bold(true).
		Render("💬 Interview Mode")

	content := fmt.Sprintf(`%s

Direct chat with agents.

No active interview session.

Press Esc to return to dashboard.
`, title)

	return style.Render(content)
}
