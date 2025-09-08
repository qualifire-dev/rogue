package tui

import (
	"strings"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// RenderHelp renders the help screen
func (m Model) RenderHelp() string {
	t := theme.CurrentTheme()

	// Main container style
	containerStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Border()).
		BorderBackground(t.BackgroundPanel()).
		Padding(1, 2).
		Width(m.width - 4).
		Height(m.height - 4).
		Background(t.BackgroundPanel())

	// Title style
	titleStyle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.BackgroundPanel()).
		Bold(true).
		Align(lipgloss.Center).
		Width(m.width - 8)

	// Section header style
	sectionHeaderStyle := lipgloss.NewStyle().
		Foreground(t.Accent()).
		Background(t.BackgroundPanel()).
		Bold(true).
		MarginTop(1).
		MarginBottom(1)

	// Content style
	contentStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.BackgroundPanel()).
		MarginLeft(2)

	// Command style
	commandStyle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.BackgroundPanel()).
		Bold(true)

	// Description style
	descStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.BackgroundPanel())

	// Key binding style
	keyStyle := lipgloss.NewStyle().
		Foreground(t.Accent()).
		Background(t.BackgroundPanel()).
		Bold(true)

	// Build content sections
	var sections []string

	// Title
	sections = append(sections, titleStyle.Render("❓ Rogue"))

	// About section
	sections = append(sections, sectionHeaderStyle.Render("📖 About Rogue"))
	aboutText := `Rogue is a powerful tool designed to evaluate the performance, compliance, and reliability 
of AI agents. It pits a dynamic EvaluatorAgent against your agent using Google's A2A protocol, 
testing it with a range of scenarios to ensure it behaves exactly as intended.

Key Features:
• 🔄 Dynamic Scenario Generation - Automatically creates comprehensive test suites
• 👀 Live Evaluation Monitoring - Real-time chat interface for agent interactions  
• 📊 Comprehensive Reporting - Detailed summaries with pass/fail rates and recommendations
• 🔍 Multi-Faceted Testing - Policy compliance testing with flexible framework
• 🤖 Broad Model Support - Compatible with OpenAI, Google (Gemini), and Anthropic models`
	sections = append(sections, contentStyle.Render(aboutText))

	// Keyboard shortcuts section
	sections = append(sections, sectionHeaderStyle.Render("⌨️  Keyboard Shortcuts"))
	shortcuts := []string{
		"• " + keyStyle.Render("Ctrl+N") + descStyle.Render(" - New evaluation"),
		"• " + keyStyle.Render("Ctrl+L") + descStyle.Render(" - Configure LLMs"),
		"• " + keyStyle.Render("Ctrl+E") + descStyle.Render(" - Scenario editor"),
		"• " + keyStyle.Render("Ctrl+I") + descStyle.Render(" - Interview mode"),
		"• " + keyStyle.Render("Ctrl+S") + descStyle.Render(" - Settings"),
		"• " + keyStyle.Render("Ctrl+H") + descStyle.Render(" - Help"),
		"• " + keyStyle.Render("Esc") + descStyle.Render(" - Back/Cancel"),
	}
	sections = append(sections, contentStyle.Render(strings.Join(shortcuts, "\n")))

	// Slash commands section
	sections = append(sections, sectionHeaderStyle.Render("💬 Slash Commands"))
	commands := []string{
		"• " + commandStyle.Render("/models") + descStyle.Render(" - Configure LLM providers"),
		"• " + commandStyle.Render("/editor") + descStyle.Render(" - Open scenario editor"),
		"• " + commandStyle.Render("/eval") + descStyle.Render(" - Start new evaluation"),
		"• " + commandStyle.Render("/help") + descStyle.Render(" - Show this help screen"),
		"• " + commandStyle.Render("/settings") + descStyle.Render(" - Edit settings"),
	}
	sections = append(sections, contentStyle.Render(strings.Join(commands, "\n")))

	// Navigation section
	sections = append(sections, sectionHeaderStyle.Render("🧭 Navigation"))
	navigationText := `Type "/" in the command input to see available commands with auto-completion.`
	sections = append(sections, contentStyle.Render(navigationText))

	// Workflow section
	sections = append(sections, sectionHeaderStyle.Render("🔄 Evaluation Workflow"))
	workflowText := `1. Configure - Set up agent endpoint and authentication details
2. Generate Scenarios - Input business context to create test scenarios  
3. Run & Evaluate - Start evaluation and watch live agent interactions
4. View Report - Review detailed Markdown report with findings and recommendations`
	sections = append(sections, contentStyle.Render(workflowText))

	// Footer
	footerStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.BackgroundPanel()).
		Align(lipgloss.Center).
		MarginTop(2).
		Width(m.width - 8)
	sections = append(sections, footerStyle.Render("Press Esc to return to dashboard"))

	content := strings.Join(sections, "\n")
	return containerStyle.Render(content)
}
