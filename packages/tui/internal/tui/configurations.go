package tui

import (
	"strings"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// ConfigField represents different configuration fields
type ConfigField int

const (
	ConfigFieldServerURL ConfigField = iota
	ConfigFieldTheme
)

// RenderConfiguration renders the configuration screen
func (m Model) RenderConfiguration() string {
	t := theme.CurrentTheme()

	// Main container style
	containerStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Border()).
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

	// Field label style
	labelStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.BackgroundPanel()).
		Bold(true).
		Width(15)

	// Field value style
	valueStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.BackgroundPanel()).
		Padding(0, 1)

	// Active field style
	activeValueStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.BackgroundElement()).
		Padding(0, 1)

	// Theme option style
	themeOptionStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.BackgroundPanel()).
		Padding(0, 1)

	// Selected theme option style
	selectedThemeStyle := lipgloss.NewStyle().
		Foreground(t.Background()).
		Background(t.Primary()).
		Padding(0, 1).
		Bold(true)

	// Footer style
	footerStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.BackgroundPanel()).
		Align(lipgloss.Center).
		MarginTop(2).
		Width(m.width - 8)

	// Build content sections
	var sections []string

	// Title
	sections = append(sections, titleStyle.Render("⚙️ Configuration"))

	// Server Configuration Section
	sections = append(sections, sectionHeaderStyle.Render("🌐 Server Settings"))

	// Server URL field
	var serverURLDisplay string
	if m.configState != nil && m.configState.ActiveField == ConfigFieldServerURL {
		// Show editable field with cursor
		urlText := m.configState.ServerURL
		if m.configState.CursorPos <= len(urlText) {
			urlText = urlText[:m.configState.CursorPos] + "█" + urlText[m.configState.CursorPos:]
		}
		serverURLDisplay = activeValueStyle.Width(40).Render(urlText)
	} else {
		serverURLDisplay = valueStyle.Width(40).Render(m.config.ServerURL)
	}

	serverURLLine := lipgloss.JoinHorizontal(lipgloss.Left,
		labelStyle.Render("Server URL:"),
		serverURLDisplay,
	)
	sections = append(sections, "  "+serverURLLine)

	// Theme Configuration Section
	sections = append(sections, sectionHeaderStyle.Render("🎨 Theme Settings"))

	// Get available themes
	availableThemes := theme.AvailableThemes()
	currentTheme := theme.CurrentThemeName()

	// Theme selector
	var themeLines []string
	if m.configState != nil && m.configState.ActiveField == ConfigFieldTheme && m.configState.IsEditing {
		// Show theme selection list only when editing
		for i, themeName := range availableThemes {
			var themeDisplay string
			if i == m.configState.ThemeIndex {
				themeDisplay = selectedThemeStyle.Render("● " + themeName)
			} else if themeName == currentTheme {
				themeDisplay = themeOptionStyle.Foreground(t.Primary()).Render("● " + themeName)
			} else {
				themeDisplay = themeOptionStyle.Render("○ " + themeName)
			}
			themeLines = append(themeLines, "    "+themeDisplay)
		}
	} else {
		// Show current theme with active field styling if selected
		var themeDisplay string
		if m.configState != nil && m.configState.ActiveField == ConfigFieldTheme {
			themeDisplay = activeValueStyle.Width(20).Render(currentTheme)
		} else {
			themeDisplay = valueStyle.Width(20).Render(currentTheme)
		}

		themeLine := lipgloss.JoinHorizontal(lipgloss.Left,
			labelStyle.Render("Theme:"),
			themeDisplay,
		)
		themeLines = append(themeLines, "  "+themeLine)
	}
	sections = append(sections, strings.Join(themeLines, "\n"))

	// Instructions Section
	sections = append(sections, sectionHeaderStyle.Render("📋 Instructions"))
	instructions := `• Use ↑/↓ arrows to navigate between fields
• Enter to edit the selected field  
• ↑/↓ arrows to select theme options (when editing)
• ←/→ arrows to move cursor in text fields
• Enter to save changes
• Esc to cancel editing or return to dashboard`
	sections = append(sections, lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.BackgroundPanel()).
		MarginLeft(2).
		Render(instructions))

	// Footer
	sections = append(sections, footerStyle.Render("↑/↓: Navigate • Enter: Edit/Save • Esc: Cancel/Back"))

	content := strings.Join(sections, "\n")
	return containerStyle.Render(content)
}

// renderScenarios renders the scenarios screen
func (m Model) renderScenarios() string {
	return m.scenarioEditor.View()
}
