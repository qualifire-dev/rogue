package tui

import (
	"fmt"

	"github.com/charmbracelet/lipgloss/v2"
)

func (m Model) RenderChat() string {
	style := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("62")).
		Padding(1, 2).
		Width(m.width - 4).
		Height(m.height - 4)

	title := lipgloss.NewStyle().
		Foreground(lipgloss.Color("205")).
		Bold(true).
		Render("🆕 New Evaluation")

	content := fmt.Sprintf(`%s

Create a new evaluation:

1. Agent URL: _______________
2. Scenario: _______________
3. Model: _______________

Press Esc to cancel.
`, title)

	return style.Render(content)
}
