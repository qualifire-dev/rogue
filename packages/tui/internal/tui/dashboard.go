package tui

import (
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/components"
	"github.com/rogue/tui/internal/styles"
	"github.com/rogue/tui/internal/theme"
)

// RenderMainScreen renders the main dashboard
func (m Model) RenderMainScreen(t theme.Theme) string {
	effectiveWidth := m.width - 4

	// Calculate content width for proper centering
	contentWidth := effectiveWidth
	baseStyle := styles.NewStyle().Background(t.Background())

	// Title - centered within content width
	title := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Align(lipgloss.Center).
		Bold(true).
		Width(contentWidth).
		Render(components.Logo)

	// Version - centered within content width
	versionStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Width(contentWidth).
		Align(lipgloss.Center).
		Background(t.Background())

	version := versionStyle.Render(m.version)

	// Instructions text - centered within content width
	instructionStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(contentWidth).
		Align(lipgloss.Center).
		Padding(1, 0)

	instructions := instructionStyle.Render("Type '/' for commands or press Enter to start")

	// Render the command input component and center it
	commandInputView := m.commandInput.View()

	// Center the command input within the content width
	commandInputCentered := lipgloss.NewStyle().
		Width(contentWidth).
		Align(lipgloss.Center).
		Render(commandInputView)

	// Build the content with proper spacing
	content := lipgloss.JoinVertical(
		lipgloss.Center,
		title,
		"",
		version,
		"",
		"",
		instructions,
		"",
		commandInputCentered,
	)

	// Center the entire content block within the screen
	mainLayout := lipgloss.Place(
		effectiveWidth,
		m.height-1,
		lipgloss.Center,
		lipgloss.Center,
		baseStyle.Render(content),
		styles.WhitespaceStyle(t.Background()),
	)

	return mainLayout
}
