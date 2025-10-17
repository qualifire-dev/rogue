package tui

import (
	"fmt"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// renderEvaluationDetail renders the evaluation detail/running screen
func (m Model) renderEvaluationDetail() string {
	t := theme.CurrentTheme()
	if m.evalState == nil {
		return lipgloss.NewStyle().
			Width(m.width).
			Height(m.height).
			Background(t.Background()).
			Foreground(t.Text()).
			Align(lipgloss.Center, lipgloss.Center).
			Render("No evaluation active")
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

	header := titleStyle.Render("📡 Evaluation Running")

	// Status style
	statusStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.BackgroundPanel()).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Primary()).
		Padding(0, 2).
		Width(m.width - 4).
		Align(lipgloss.Center)

	var statusText string
	if m.evalState.Status != "completed" && m.evalSpinner.IsActive() {
		m.evalSpinner.Style = lipgloss.NewStyle().Foreground(t.Success())
		statusText = fmt.Sprintf("Status: %s %s", m.evalState.Status, m.evalSpinner.View())
	} else {
		statusText = fmt.Sprintf("Status: %s", m.evalState.Status)
		statusStyle = lipgloss.NewStyle().
			Foreground(t.Success()).
			Background(t.BackgroundPanel()).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(t.Primary()).
			Padding(0, 2).
			Width(m.width - 4).
			Align(lipgloss.Center)
	}
	status := statusStyle.Render(statusText)

	// Calculate available height for content area
	// Total layout: header(3) + mainContent + helpText(2) = m.height
	// mainContent contains: status(3) + spacers(2-3) + events + [spacer + summary]
	// Start with total height minus header and help
	availableHeight := m.height - 5 // header(3) + helpText(2)

	// Subtract status bar and spacers
	statusAndSpacersHeight := 5 // status(3) + spacers(2)

	var eventsHeight, summaryHeight int
	var showSummary bool

	// If evaluation completed and we have a summary OR are generating one, split 50/50
	if m.evalState.Completed && (m.evalState.Summary != "" || m.summarySpinner.IsActive()) {
		showSummary = true
		// Add one more spacer between events and summary
		statusAndSpacersHeight = 6 // status(3) + spacers(3)

		// Remaining height split between events and summary
		remainingHeight := availableHeight - statusAndSpacersHeight
		eventsHeight = remainingHeight / 2
		summaryHeight = remainingHeight - eventsHeight
	} else {
		// No summary, events take full remaining height
		remainingHeight := availableHeight - statusAndSpacersHeight
		eventsHeight = remainingHeight
		summaryHeight = 0
	}

	// Clear existing messages and rebuild from events
	m.eventsHistory.ClearMessages()

	// Process events and add as messages
	for _, ev := range m.evalState.Events {
		switch ev.Type {
		case "status":
			if ev.Status != "running" {
				m.eventsHistory.AddMessage("system", fmt.Sprintf("✓ %s", ev.Status))
			}
		case "chat":
			// Normalize role for MessageHistoryView
			normalizedRole := normalizeEvaluationRole(ev.Role)
			m.eventsHistory.AddMessage(normalizedRole, ev.Content)
		case "error":
			m.eventsHistory.AddMessage("system", fmt.Sprintf("⚠ ERROR: %s", ev.Message))
		}
	}

	// Check if we have any messages
	if len(m.eventsHistory.GetMessages()) == 0 {
		m.eventsHistory.AddMessage("system", "Waiting for evaluation events...")
	}

	// Update size
	m.eventsHistory.SetSize(m.width, eventsHeight)

	// Customize prefixes to match the evaluation context
	m.eventsHistory.SetPrefixes("🔍 Rogue: ", "🤖 Agent: ")

	m.eventsHistory.SetColors(t.Primary(), t.Text())

	// Render events using MessageHistoryView
	var eventsContent string
	if m.eventsHistory != nil {
		eventsContent = m.eventsHistory.View(t)
	}

	// Help text style (for bottom of screen)
	helpStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(m.width).
		Align(lipgloss.Center).
		Padding(0, 1)

	var helpMsg string
	if m.evalState.Completed && (m.evalState.Summary != "" || m.summarySpinner.IsActive()) {
		// Both viewports are visible, show tab navigation
		helpMsg = "b Back  s Stop  r Report  Tab Switch Focus  ↑↓ scroll end auto-scroll"
	} else if m.evalState.Completed {
		helpMsg = "b Back  s Stop  r Report  ↑↓ scroll end auto-scroll"
	} else {
		helpMsg = "b Back  s Stop  ↑↓ scroll end auto-scroll"
	}
	helpText := helpStyle.Render(helpMsg)

	// Calculate main content area height (space between header and footer)
	// This should match availableHeight calculated above
	mainContentHeight := availableHeight

	// Create content area for the main content (between header and footer)
	contentArea := lipgloss.NewStyle().
		Width(m.width).
		Height(mainContentHeight).
		Background(t.Background())

	// Create spacing with background color
	spacer := lipgloss.NewStyle().Background(t.Background()).Width(m.width).Render("")

	// Create summary section if available
	var summaryContent string
	if showSummary {
		var summaryTitleText string
		if m.summarySpinner.IsActive() {
			summaryTitleText = fmt.Sprintf("📊 Evaluation Summary %s", m.summarySpinner.View())
		} else {
			summaryTitleText = "📊 Evaluation Summary"
		}

		// Clear existing summary messages
		m.summaryHistory.ClearMessages()

		// Add title as a system message
		m.summaryHistory.AddMessage("system", summaryTitleText)

		if m.evalState.Summary == "" && m.summarySpinner.IsActive() {
			// Show loading message when generating summary
			m.summaryHistory.AddMessage("system", "Generating summary with LLM...")
		} else if m.evalState.Summary != "" {
			// Add summary content as a single message
			m.summaryHistory.AddMessage("assistant", m.evalState.Summary)
		}

		// Update size for summary history
		m.summaryHistory.SetSize(m.width, summaryHeight)

		// Customize prefixes for summary view
		m.summaryHistory.SetPrefixes("", "")

		// Set colors for summary
		m.summaryHistory.SetColors(t.Success(), t.Text())

		// Enable markdown rendering for summary content
		renderer := m.getMarkdownRenderer()
		m.summaryHistory.SetMarkdownRenderer(renderer)

		// Set focus state for border color
		if m.focusedViewport == 1 {
			m.summaryHistory.Focus()
		} else {
			m.summaryHistory.Blur()
		}

		// Render summary using MessageHistoryView
		summaryContent = m.summaryHistory.View(t)
	}

	// Arrange content based on whether we have a summary or not
	var mainContent string

	if showSummary {
		// Split layout: events on top, summary on bottom
		upperSection := lipgloss.JoinVertical(lipgloss.Center, spacer, status, spacer, eventsContent)
		lowerSection := summaryContent

		// Create split layout
		content := lipgloss.JoinVertical(lipgloss.Center, upperSection, spacer, lowerSection)

		mainContent = contentArea.Render(
			lipgloss.Place(
				m.width,
				mainContentHeight,
				lipgloss.Center,
				lipgloss.Top,
				content,
				lipgloss.WithWhitespaceStyle(lipgloss.NewStyle().Background(t.Background())),
			),
		)
	} else {
		// Single layout: events take full space
		content := lipgloss.JoinVertical(lipgloss.Center, spacer, status, spacer, eventsContent)

		mainContent = contentArea.Render(
			lipgloss.Place(
				m.width,
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
