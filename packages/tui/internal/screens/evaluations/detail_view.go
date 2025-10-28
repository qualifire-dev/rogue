package evaluations

import (
	"fmt"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// RenderDetail renders the evaluation detail/running screen
func RenderDetail(state *DetailState) string {
	t := theme.CurrentTheme()
	if state == nil {
		return lipgloss.NewStyle().
			Width(80).
			Height(24).
			Background(t.Background()).
			Foreground(t.Text()).
			Align(lipgloss.Center, lipgloss.Center).
			Render("No evaluation active")
	}

	// Main container style with full width and height background
	mainStyle := lipgloss.NewStyle().
		Width(state.Width).
		Height(state.Height - 1). // -1 for footer
		Background(t.Background())

	// Title style
	titleStyle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Bold(true).
		Width(state.Width).
		Align(lipgloss.Center).
		Padding(1, 0)

	header := titleStyle.Render("📡 Evaluation Running")

	// Status style
	statusStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.BackgroundPanel()).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Primary()).
		Padding(0, 2).
		Width(state.Width - 4).
		Align(lipgloss.Center)

	var statusText string
	if state.Status != "completed" && state.EvalSpinnerActive {
		statusText = fmt.Sprintf("Status: %s %s", state.Status, state.EvalSpinnerView)
	} else {
		statusText = fmt.Sprintf("Status: %s", state.Status)
		statusStyle = statusStyle.
			Foreground(t.Success())
	}
	status := statusStyle.Render(statusText)

	// Calculate available height for content area
	availableHeight := state.Height - 5 // header(3) + helpText(2)

	// Determine if we show summary section
	showSummary := state.HasSummary

	// Help text style (for bottom of screen)
	helpStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(state.Width).
		Align(lipgloss.Center).
		Padding(0, 1)

	var helpMsg string
	if state.Completed && showSummary {
		helpMsg = "b Back  s Stop  r Report  Tab Switch Focus  ↑↓ scroll end auto-scroll"
	} else if state.Completed {
		helpMsg = "b Back  s Stop  r Report  ↑↓ scroll end auto-scroll"
	} else {
		helpMsg = "b Back  s Stop  ↑↓ scroll end auto-scroll"
	}
	helpText := helpStyle.Render(helpMsg)

	// Calculate main content area height
	mainContentHeight := availableHeight

	// Create content area
	contentArea := lipgloss.NewStyle().
		Width(state.Width).
		Height(mainContentHeight).
		Background(t.Background())

	// Create spacing with background color
	spacer := lipgloss.NewStyle().Background(t.Background()).Width(state.Width).Render("")

	// Build content based on whether summary is shown
	var mainContent string
	if showSummary {
		// Create summary section
		var summaryTitleText string
		if state.SummarySpinnerActive {
			summaryTitleText = fmt.Sprintf("📊 Evaluation Summary %s", state.SummarySpinnerView)
		} else {
			summaryTitleText = "📊 Evaluation Summary"
		}

		summaryTitle := lipgloss.NewStyle().
			Foreground(t.Accent()).
			Background(t.Background()).
			Bold(true).
			Width(state.Width).
			Align(lipgloss.Center).
			Render(summaryTitleText)

		// Arrange: status, spacer, events, spacer, summaryTitle, summary
		content := lipgloss.JoinVertical(lipgloss.Left,
			status,
			spacer,
			state.EventsContent,
			spacer,
			summaryTitle,
			state.SummaryContent,
		)

		mainContent = contentArea.Render(
			lipgloss.Place(
				state.Width,
				mainContentHeight,
				lipgloss.Center,
				lipgloss.Top,
				content,
				lipgloss.WithWhitespaceStyle(lipgloss.NewStyle().Background(t.Background())),
			),
		)
	} else {
		// Just events
		content := lipgloss.JoinVertical(lipgloss.Left,
			status,
			spacer,
			state.EventsContent,
		)

		mainContent = contentArea.Render(
			lipgloss.Place(
				state.Width,
				mainContentHeight,
				lipgloss.Center,
				lipgloss.Top,
				content,
				lipgloss.WithWhitespaceStyle(lipgloss.NewStyle().Background(t.Background())),
			),
		)
	}

	// Combine all sections
	fullLayout := lipgloss.JoinVertical(lipgloss.Left,
		header,
		mainContent,
		helpText,
	)

	return mainStyle.Render(fullLayout)
}
