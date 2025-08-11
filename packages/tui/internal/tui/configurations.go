package tui

import (
	"fmt"

	"github.com/charmbracelet/lipgloss/v2"
)

// RenderConfiguration renders the configuration screen
func (m Model) RenderConfiguration() string {
	style := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("62")).
		Padding(1, 2).
		Width(m.width - 4).
		Height(m.height - 4)

	title := lipgloss.NewStyle().
		Foreground(lipgloss.Color("205")).
		Bold(true).
		Render("⚙️ Configuration")

	content := fmt.Sprintf(`%s

Server URL: %s
Theme: %s

API Keys:
• OpenAI: %s
• Anthropic: %s

Press Esc to return to dashboard.
`, title, m.config.ServerURL, m.config.Theme,
		getKeyStatus(m.config.APIKeys["openai"]),
		getKeyStatus(m.config.APIKeys["anthropic"]))

	return style.Render(content)
}

// renderScenarios renders the scenarios screen
func (m Model) renderScenarios() string {
	return m.scenarioEditor.View()
}
