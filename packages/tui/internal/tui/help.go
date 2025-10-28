package tui

import (
	_ "embed"
	"log"
	"strings"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

//go:embed help.md
var helpContent string

// RenderHelp renders the help screen with viewport for scrollable content
func (m Model) RenderHelp() string {
	t := theme.CurrentTheme()

	// Viewport configuration
	viewportWidth := m.width - 11
	viewportHeight := m.height - 9
	contentWidth := viewportWidth - 6

	// Render markdown with correct width for viewport content
	renderer := GetMarkdownRenderer(contentWidth, t.Background())
	contentStr := strings.ReplaceAll(helpContent, "\r\n", "\n")
	renderedContent, err := renderer.Render(contentStr)
	if err != nil {
		log.Printf("Error rendering markdown: %v", err)
		renderedContent = helpContent
	}

	// Main container style
	mainStyle := lipgloss.NewStyle().
		Width(m.width).
		Height(viewportHeight - 4).
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

	viewport := m.helpViewport
	viewport.SetSize(contentWidth, viewportHeight)
	viewport.SetContent(renderedContent)

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

	// Help text style
	helpStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(m.width).
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
