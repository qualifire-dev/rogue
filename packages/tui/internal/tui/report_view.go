package tui

import (
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// renderReport renders the evaluation report screen with summary
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

	// Report container
	reportStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.BackgroundPanel()).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Border()).
		Padding(1, 2).
		Width(m.width - 4).
		Height(m.height - 8) // Leave space for header and help

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

	// Note: spacing handled by content area placement

	// Help text style
	helpStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(m.width).
		Align(lipgloss.Center).
		Padding(0, 1)

	helpText := helpStyle.Render("r Refresh   b Back to Dashboard   Esc Exit")

	// Calculate content area height
	contentHeight := m.height - 6 // title(3) + help(1) + margins(2)

	// Create content area
	contentArea := lipgloss.NewStyle().
		Width(m.width).
		Height(contentHeight).
		Background(t.Background())

	// Place report in the content area
	mainContent := contentArea.Render(
		lipgloss.Place(
			m.width,
			contentHeight,
			lipgloss.Center,
			lipgloss.Top,
			reportStyle.Render(reportContent),
			lipgloss.WithWhitespaceStyle(lipgloss.NewStyle().Background(t.Background())),
		),
	)

	// Combine all sections
	fullLayout := lipgloss.JoinVertical(lipgloss.Left,
		header,
		mainContent,
		helpText,
	)

	return mainStyle.Render(fullLayout)
}
