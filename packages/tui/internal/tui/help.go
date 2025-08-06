package tui

import (
	"fmt"

	"github.com/charmbracelet/lipgloss/v2"
)

// RenderHelp renders the help screen
func (m Model) RenderHelp() string {
	style := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("62")).
		Padding(1, 2).
		Width(m.width - 4).
		Height(m.height - 4)

	title := lipgloss.NewStyle().
		Foreground(lipgloss.Color("205")).
		Bold(true).
		Render("❓ Help")

	content := fmt.Sprintf(`%s

Keyboard Shortcuts:
• Ctrl+N - New evaluation
• Ctrl+L - Configure LLMs
• Ctrl+E - Scenario editor
• Ctrl+I - Interview mode
• Ctrl+S - Configuration
• Ctrl+H - Help
• Q - Quit application
• Esc - Back/Cancel

Slash Commands:
• /new - Start new evaluation wizard
• /models - Configure LLM providers
• /editor - Open scenario editor
• /config - Configuration settings
• /help - Show help
• /quit - Exit application

Press Esc to return to dashboard.
`, title)

	return style.Render(content)
}
