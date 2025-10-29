package help

import (
	_ "embed"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/components"
	"github.com/rogue/tui/internal/theme"
)

//go:embed help.md
var helpContent string

// GetHelpContent returns the embedded help markdown content
func GetHelpContent() string {
	return helpContent
}

// Render renders the help screen with viewport for scrollable content
func Render(width, height int, viewport *components.Viewport) string {
	t := theme.CurrentTheme()

	// Viewport configuration - content is initialized separately in initializeHelpViewport
	// Just render the viewport as-is without modifying it
	viewportWidth := width - 11
	viewportHeight := height - 9

	// Main container style
	mainStyle := lipgloss.NewStyle().
		Width(width).
		Height(height - 1).
		Background(t.Background())

	// Title style
	titleStyle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Bold(true).
		Width(width).
		Align(lipgloss.Center).
		Padding(1, 0)

	header := titleStyle.Render("❓ Rogue")

	// Style the viewport with border
	viewportStyle := lipgloss.NewStyle().
		Width(viewportWidth).
		Height(viewportHeight).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Border()).
		BorderBackground(t.BackgroundPanel()).
		Background(t.Background()).
		Padding(1, 2)

	viewportContent := viewportStyle.Render(viewport.View())

	// Center the viewport
	contentArea := lipgloss.NewStyle().
		Width(width).
		Height(viewportHeight).
		Background(t.Background())

	centeredViewport := contentArea.Render(
		lipgloss.Place(
			width,
			viewportHeight,
			lipgloss.Center,
			lipgloss.Top,
			viewportContent,
			lipgloss.WithWhitespaceStyle(lipgloss.NewStyle().Background(t.Background())),
		),
	)

	// Help text style
	helpStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(width).
		Align(lipgloss.Center).
		Padding(0, 1)

	scrollInfo := ""
	if !viewport.AtTop() || !viewport.AtBottom() {
		scrollInfo = "↑↓ Scroll   "
	}
	helpText := helpStyle.Render(scrollInfo + "Esc Back to Dashboard")

	// Combine all sections
	fullLayout := lipgloss.JoinVertical(lipgloss.Left,
		header,
		centeredViewport,
		helpText,
	)

	return mainStyle.Render(fullLayout)
}
