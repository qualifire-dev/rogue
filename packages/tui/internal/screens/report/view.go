package report

import (
	"github.com/charmbracelet/glamour"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/components"
	"github.com/rogue/tui/internal/theme"
)

// EvalState contains the minimal evaluation state needed for rendering
type EvalState struct {
	Summary   string
	Completed bool
}

// Render renders the evaluation report screen with summary using MessageHistoryView for scrollable content
func Render(width, height int, evalState *EvalState, reportHistory *components.MessageHistoryView, markdownRenderer *glamour.TermRenderer) string {
	t := theme.CurrentTheme()

	if evalState == nil {
		return lipgloss.NewStyle().
			Width(width).
			Height(height).
			Background(t.Background()).
			Foreground(t.Text()).
			Align(lipgloss.Center, lipgloss.Center).
			Render("No evaluation report available")
	}

	// Main container style with full width and height background
	mainStyle := lipgloss.NewStyle().
		Width(width).
		Height(height - 1). // -1 for footer
		Background(t.Background())

	// Title style
	titleStyle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Bold(true).
		Width(width).
		Align(lipgloss.Center).
		Padding(1, 0)

	header := titleStyle.Render("📊 Evaluation Report")

	// Calculate available height: header(3) + helpText(2) = 5
	reportHeight := height - 5

	// Clear existing messages and rebuild report content
	reportHistory.ClearMessages()

	// Add title as system message
	reportHistory.AddMessage("system", "📊 Evaluation Report")

	// Add report content
	if evalState.Summary == "" {
		if evalState.Completed {
			// Evaluation completed but no summary yet
			reportHistory.AddMessage("system", "Generating summary, please wait...")
		} else {
			// Evaluation not completed
			reportHistory.AddMessage("system", "Evaluation not completed yet. Complete an evaluation to see the report.")
		}
	} else {
		// Show the actual summary as an assistant message
		reportHistory.AddMessage("assistant", evalState.Summary)
	}

	// Update size for report history
	reportHistory.SetSize(width, reportHeight)

	// Customize prefixes for report view (no prefixes for cleaner look)
	reportHistory.SetPrefixes("", "")

	// Set colors for report
	reportHistory.SetColors(t.Success(), t.Text())

	// Enable markdown rendering for report content
	renderer := markdownRenderer
	reportHistory.SetMarkdownRenderer(renderer)

	// Render report using MessageHistoryView
	reportContent := reportHistory.View(t)

	// Help text style
	helpStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(width).
		Align(lipgloss.Center).
		Padding(0, 1)

	// Include scroll indicators in help text
	scrollInfo := ""
	if reportHistory != nil && (!reportHistory.AtTop() || !reportHistory.AtBottom()) {
		scrollInfo = "↑↓ Scroll   "
	}
	helpText := helpStyle.Render(scrollInfo + "r Refresh   b Back to Dashboard   Esc Exit")

	// Create content area
	contentArea := lipgloss.NewStyle().
		Width(width).
		Height(reportHeight).
		Background(t.Background())

	centeredReport := contentArea.Render(
		lipgloss.Place(
			width,
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
