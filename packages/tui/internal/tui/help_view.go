package tui

import (
	"strings"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// RenderHelp renders the help screen with viewport for scrollable content
func (m Model) RenderHelp() string {
	t := theme.CurrentTheme()

	// Main container style with full width and height background
	mainStyle := lipgloss.NewStyle().
		Width(m.width).
		Height(m.height - 1).
		Background(t.Background())

	// Title style
	titleStyle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Bold(true).
		Width(m.width).
		Align(lipgloss.Center).
		Padding(1, 0)

	header := titleStyle.Render("❓ Rogue")

	// Section header style
	sectionHeaderStyle := lipgloss.NewStyle().
		Foreground(t.Accent()).
		Background(t.BackgroundPanel()).
		Bold(true).
		MarginTop(1)

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

	// Build content sections for viewport
	var sections []string

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

	helpContent := strings.Join(sections, "\n")

	// Calculate viewport dimensions
	viewportWidth := m.width - 8
	viewportHeight := m.height - 6

	// Create a temporary copy of the viewport to avoid modifying the original
	viewport := m.helpViewport
	viewport.SetSize(viewportWidth-4, viewportHeight-4)
	viewport.SetContent(helpContent)

	// Style the viewport with border
	viewportStyle := lipgloss.NewStyle().
		Height(viewportHeight).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Border()).
		BorderBackground(t.BackgroundPanel()).
		Background(t.BackgroundPanel())

	// Apply viewport styling
	viewport.Style = lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.BackgroundPanel()).
		Width(viewportWidth-4).
		Height(viewportHeight-4).
		Padding(1, 2)

	// Help text style
	helpStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(m.width).
		Align(lipgloss.Center).
		Padding(0, 1)

	// Include scroll indicators in help text
	scrollInfo := ""
	if !viewport.AtTop() || !viewport.AtBottom() {
		scrollInfo = "↑↓ Scroll   "
	}
	helpText := helpStyle.Render(scrollInfo + "Esc Back to Dashboard")

	// Create the viewport content area
	viewportContent := viewportStyle.Render(viewport.View())

	// Center the viewport in the available space
	contentArea := lipgloss.NewStyle().
		Width(m.width).
		Height(viewportHeight).
		Background(t.Background())

	centeredViewport := contentArea.Render(
		lipgloss.Place(
			m.width,
			viewportHeight,
			lipgloss.Center,
			lipgloss.Top,
			viewportContent,
			lipgloss.WithWhitespaceStyle(lipgloss.NewStyle().Background(t.Background())),
		),
	)

	// Combine all sections
	fullLayout := lipgloss.JoinVertical(lipgloss.Left,
		header,
		centeredViewport,
		helpText,
	)

	return mainStyle.Render(fullLayout)
}
