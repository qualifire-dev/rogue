package tui

import (
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// renderReport renders the evaluation report screen with summary using a viewport for scrollable content
func (m Model) renderReport() string {
	t := theme.CurrentTheme()

	if m.evalState == nil {
		return lipgloss.NewStyle().
			Width(m.width).
			Height(m.height).
			Background(t.Background()).
			Foreground(t.Text()).
			Align(lipgloss.Center, lipgloss.Center).
			Render("No evaluation report available")
	}

	// Main container style with full width and height background
	mainStyle := lipgloss.NewStyle().
		Width(m.width).
		Height(m.height - 1). // -1 for footer
		Background(t.Background())

	// Title style
	titleStyle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Bold(true).
		Width(m.width).
		Align(lipgloss.Center).
		Padding(1, 0)

	header := titleStyle.Render("📊 Evaluation Report")

	// Prepare report content for the viewport
	var reportContent string
	if m.evalState.Summary == "" {
		if m.evalState.Completed {
			// Evaluation completed but no summary yet
			reportContent = lipgloss.NewStyle().
				Foreground(t.TextMuted()).
				Italic(true).
				Render("Generating summary, please wait...")
		} else {
			// Evaluation not completed
			reportContent = lipgloss.NewStyle().
				Foreground(t.TextMuted()).
				Italic(true).
				Render("Evaluation not completed yet. Complete an evaluation to see the report.")
		}
	} else {
		// Show the actual summary
		reportContent = renderMarkdownSummary(t, m.evalState.Summary)
	}

	// Calculate viewport dimensions
	// Reserve space for: header (3 lines) + help text (1 line) + margins (2 lines)
	viewportWidth := m.width - 8
	viewportHeight := m.height - 6

	// Create a temporary copy of the viewport to avoid modifying the original
	viewport := m.reportViewport
	viewport.SetSize(viewportWidth-4, viewportHeight-4) // Account for border and padding
	viewport.SetContent(reportContent)

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
	helpText := helpStyle.Render(scrollInfo + "r Refresh   b Back to Dashboard   Esc Exit")

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
