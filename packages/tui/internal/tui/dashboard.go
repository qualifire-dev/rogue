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
	contentWidth := effectiveWidth
	if contentWidth > 80 {
		contentWidth = 80
	}

	baseStyle := styles.NewStyle().Background(t.Background())

	// Create the main content (logo, version, instructions) - this stays fixed
	title := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Align(lipgloss.Center).
		Bold(true).
		Width(contentWidth).
		Render(components.Logo)

	versionStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Width(contentWidth).
		Align(lipgloss.Center).
		Background(t.Background())

	version := versionStyle.Render(m.version)

	instructionStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(contentWidth).
		Align(lipgloss.Center).
		Padding(1, 0)

	instructions := instructionStyle.Render("Type '/' for commands or press Enter to start")

	// Build the main content without command input
	mainContent := lipgloss.JoinVertical(
		lipgloss.Center,
		title,
		"",
		version,
		"",
		"",
		instructions,
	)

	// Get just the input field (no suggestions)
	inputField := m.commandInput.ViewInput()
	inputFieldCentered := lipgloss.NewStyle().
		Width(contentWidth).
		Align(lipgloss.Center).
		Render(inputField)

	// Build the base layout with main content and input
	fullContent := lipgloss.JoinVertical(
		lipgloss.Center,
		mainContent,
		"",
		inputFieldCentered,
	)

	// Create the base screen
	baseScreen := lipgloss.Place(
		effectiveWidth,
		m.height-1,
		lipgloss.Center,
		lipgloss.Center,
		baseStyle.Render(fullContent),
		styles.WhitespaceStyle(t.Background()),
	)

	// If suggestions are showing, create overlay-style layout
	if m.commandInput.HasSuggestions() {
		suggestions := m.commandInput.ViewSuggestions()
		suggestionsCentered := lipgloss.NewStyle().
			Width(contentWidth).
			Align(lipgloss.Center).
			Render(suggestions)

		// Create a layout that visually simulates overlay:
		// Suggestions at top, minimal gap, input at bottom
		overlayLayout := lipgloss.JoinVertical(
			lipgloss.Center,
			"",
			"",
			suggestionsCentered,
			"", // Small gap between suggestions and input
			inputFieldCentered,
		)

		return lipgloss.Place(
			effectiveWidth,
			m.height-1,
			lipgloss.Center,
			lipgloss.Center,
			baseStyle.Render(overlayLayout),
			styles.WhitespaceStyle(t.Background()),
		)
	}

	return baseScreen
}
