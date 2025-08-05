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

	// Center the main content
	centeredMainContent := lipgloss.Place(
		effectiveWidth,
		m.height-1,
		lipgloss.Center,
		lipgloss.Center,
		baseStyle.Render(mainContent),
		styles.WhitespaceStyle(t.Background()),
	)

	// Get the command input view
	commandInputView := m.commandInput.View()
	commandInputCentered := lipgloss.NewStyle().
		Width(contentWidth).
		Align(lipgloss.Center).
		Render(commandInputView)

	// Check if we should show suggestions overlay
	if m.commandInput.IsFocused() && len(m.commandInput.Value()) > 0 && m.commandInput.Value()[0] == '/' {
		// Create base layout with just input at bottom (no suggestions in normal flow)
		inputOnlyView := ""
		lines := []rune(commandInputView)
		for i, r := range lines {
			if r == '\n' {
				// Only include the input line (after first newline)
				inputOnlyView = string(lines[i+1:])
				break
			}
		}
		if inputOnlyView == "" {
			inputOnlyView = commandInputView // fallback if no newline found
		}

		inputOnlyCentered := lipgloss.NewStyle().
			Width(contentWidth).
			Align(lipgloss.Center).
			Render(inputOnlyView)

		baseLayout := lipgloss.JoinVertical(
			lipgloss.Center,
			mainContent,
			"",
			inputOnlyCentered,
		)

		// Position base layout
		baseScreen := lipgloss.Place(
			effectiveWidth,
			m.height-1,
			lipgloss.Center,
			lipgloss.Center,
			baseStyle.Render(baseLayout),
			styles.WhitespaceStyle(t.Background()),
		)

		// Extract just the suggestions part and overlay it
		suggestionsOnly := ""
		lines = []rune(commandInputView)
		for i, r := range lines {
			if r == '\n' {
				// Get everything before the newline (suggestions)
				suggestionsOnly = string(lines[:i])
				break
			}
		}

		if suggestionsOnly != "" {
			suggestionsCentered := lipgloss.NewStyle().
				Width(contentWidth).
				Align(lipgloss.Center).
				Render(suggestionsOnly)

			// Position suggestions to overlay the center area
			suggestionsOverlay := lipgloss.Place(
				effectiveWidth,
				m.height-1,
				lipgloss.Center,
				lipgloss.Center,
				suggestionsCentered,
				styles.WhitespaceStyle(t.Background()),
			)

			// Combine base and overlay (this is a simple approach)
			return baseScreen // For now, return just base - we'll improve overlay next
		}

		return baseScreen
	} else {
		// Normal view with input at bottom
		fullContent := lipgloss.JoinVertical(
			lipgloss.Center,
			mainContent,
			"",
			commandInputCentered,
		)

		return lipgloss.Place(
			effectiveWidth,
			m.height-1,
			lipgloss.Center,
			lipgloss.Center,
			baseStyle.Render(fullContent),
			styles.WhitespaceStyle(t.Background()),
		)
	}
}
