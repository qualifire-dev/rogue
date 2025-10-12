package tui

import (
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// renderReport renders the evaluation report screen with summary using MessageHistoryView for scrollable content
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

	// Calculate available height: header(3) + helpText(2) = 5
	reportHeight := m.height - 5

	// Clear existing messages and rebuild report content
	m.reportHistory.ClearMessages()

	// Add title as system message
	m.reportHistory.AddMessage("system", "📊 Evaluation Report")

	// Add report content
	if m.evalState.Summary == "" {
		if m.evalState.Completed {
			// Evaluation completed but no summary yet
			m.reportHistory.AddMessage("system", "Generating summary, please wait...")
		} else {
			// Evaluation not completed
			m.reportHistory.AddMessage("system", "Evaluation not completed yet. Complete an evaluation to see the report.")
		}
	} else {
		// Show the actual summary as an assistant message
		m.reportHistory.AddMessage("assistant", m.evalState.Summary)
	}

	// Update size for report history
	m.reportHistory.SetSize(m.width, reportHeight)

	// Customize prefixes for report view (no prefixes for cleaner look)
	m.reportHistory.SetPrefixes("", "")

	// Set colors for report
	m.reportHistory.SetColors(t.Success(), t.Text())

	// Render report using MessageHistoryView
	reportContent := m.reportHistory.View(t)

	// Help text style
	helpStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(m.width).
		Align(lipgloss.Center).
		Padding(0, 1)

	// Include scroll indicators in help text
	scrollInfo := ""
	if m.reportHistory != nil && (!m.reportHistory.AtTop() || !m.reportHistory.AtBottom()) {
		scrollInfo = "↑↓ Scroll   "
	}
	helpText := helpStyle.Render(scrollInfo + "r Refresh   b Back to Dashboard   Esc Exit")

	// Create content area
	contentArea := lipgloss.NewStyle().
		Width(m.width).
		Height(reportHeight).
		Background(t.Background())

	centeredReport := contentArea.Render(
		lipgloss.Place(
			m.width,
			reportHeight,
			lipgloss.Center,
			lipgloss.Top,
			reportContent,
			lipgloss.WithWhitespaceStyle(lipgloss.NewStyle().Background(t.Background())),
		),
	)

	// Combine all sections
	fullLayout := lipgloss.JoinVertical(lipgloss.Left,
		header,
		centeredReport,
		helpText,
	)

	return mainStyle.Render(fullLayout)
}
