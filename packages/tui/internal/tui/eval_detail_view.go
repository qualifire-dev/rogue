package tui

import (
	"fmt"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/screens/evaluations"
	"github.com/rogue/tui/internal/theme"
)

// RenderEvaluationDetail renders the evaluation detail/running screen
func (m Model) RenderEvaluationDetail() string {
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

	// Note: Red team report is now shown via RedTeamReportScreen, not inline here
	// This allows users to view the chat first and navigate to report with 'r'

	// Calculate available height for content area
	availableHeight := m.height - 5 // header(3) + helpText(2)
	statusAndSpacersHeight := 5

	var eventsHeight, summaryHeight int
	var showSummary bool

	// Determine if we show summary
	if m.evalState.Completed && (m.evalState.Summary != "" || m.summarySpinner.IsActive()) {
		showSummary = true
		statusAndSpacersHeight = 6
		remainingHeight := availableHeight - statusAndSpacersHeight
		eventsHeight = remainingHeight / 2
		summaryHeight = remainingHeight - eventsHeight
	} else {
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

	// Update size and customize prefixes
	m.eventsHistory.SetSize(m.width, eventsHeight)
	m.eventsHistory.SetPrefixes("🔍 Rogue: ", "🤖 Agent: ")
	m.eventsHistory.SetColors(t.Primary(), t.Text())

	// Set focus state for events history before rendering
	if m.focusedViewport == 0 && showSummary {
		m.eventsHistory.Focus()
	} else if showSummary {
		m.eventsHistory.Blur()
	}

	// Render events using MessageHistoryView
	eventsContent := m.eventsHistory.View(t)

	// Build summary content if needed
	var summaryContent string
	if showSummary {
		m.summaryHistory.ClearMessages()

		if m.summarySpinner.IsActive() {
			m.summaryHistory.AddMessage("system", "Generating evaluation summary...")
		} else if m.evalState.Summary != "" {
			m.summaryHistory.AddMessage("assistant", m.evalState.Summary)
		} else {
			m.summaryHistory.AddMessage("system", "Summary not available")
		}

		m.summaryHistory.SetSize(m.width, summaryHeight)
		m.summaryHistory.SetPrefixes("", "")
		m.summaryHistory.SetColors(t.Success(), t.Text())

		renderer := m.getMarkdownRenderer()
		m.summaryHistory.SetMarkdownRenderer(renderer)

		// Set focus state for summary history before rendering
		if m.focusedViewport == 1 {
			m.summaryHistory.Focus()
		} else {
			m.summaryHistory.Blur()
		}

		summaryContent = m.summaryHistory.View(t)
	}

	// Convert to DetailState
	detailState := &evaluations.DetailState{
		Width:  m.width,
		Height: m.height,

		Status:    m.evalState.Status,
		Progress:  m.evalState.Progress,
		Completed: m.evalState.Completed,

		EvaluationMode: string(m.evalState.EvaluationMode),

		FocusedViewport: m.focusedViewport,

		EvalSpinnerActive:    m.evalSpinner.IsActive(),
		EvalSpinnerView:      m.evalSpinner.View(),
		SummarySpinnerActive: m.summarySpinner.IsActive(),
		SummarySpinnerView:   m.summarySpinner.View(),

		EventsContent:  eventsContent,
		SummaryContent: summaryContent,
		HasSummary:     showSummary,
	}

	return evaluations.RenderDetail(detailState)
}
