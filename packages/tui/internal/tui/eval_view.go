package tui

import (
	"context"
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// Render New Evaluation form and Evaluation Detail

func (m Model) renderNewEvaluation() string {
	t := theme.CurrentTheme()
	if m.evalState == nil {
		return lipgloss.NewStyle().
			Width(m.width).
			Height(m.height).
			Background(t.Background()).
			Foreground(t.Text()).
			Align(lipgloss.Center, lipgloss.Center).
			Render("New evaluation not initialized")
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

	title := titleStyle.Render("🧪 New Evaluation")

	// Helper function to render a field with inline label and value
	renderField := func(fieldIndex int, label, value string) string {
		active := m.evalState.currentField == fieldIndex

		labelStyle := lipgloss.NewStyle().
			Foreground(t.TextMuted()).
			Background(t.Background()).
			Width(20).
			Align(lipgloss.Right)

		valueStyle := lipgloss.NewStyle().
			Foreground(t.Text()).
			Background(t.Background()).
			Padding(0, 1)

		if active {
			labelStyle = labelStyle.Foreground(t.Primary()).Bold(true)
			valueStyle = valueStyle.
				Foreground(t.Primary()).
				Background(t.Background())
			// Add cursor at the correct position for active field
			runes := []rune(value)
			cursorPos := m.evalState.cursorPos
			if cursorPos > len(runes) {
				cursorPos = len(runes)
			}
			value = string(runes[:cursorPos]) + "█" + string(runes[cursorPos:])
		} else {
			valueStyle = valueStyle.
				Background(t.Background())
		}

		// Create a full-width container for the field
		fieldContainer := lipgloss.NewStyle().
			Width(m.width-4).
			Background(t.Background()).
			Padding(0, 2)

		fieldContent := lipgloss.JoinHorizontal(lipgloss.Left,
			labelStyle.Render(label),
			valueStyle.Render(value),
		)

		return fieldContainer.Render(fieldContent)
	}

	// Prepare field values
	agent := m.evalState.AgentURL
	judge := m.evalState.JudgeModel
	parallel := fmt.Sprintf("%d", m.evalState.ParallelRuns)
	deep := "false"
	if m.evalState.DeepTest {
		deep = "true"
	}

	// Helper function to render the start button
	renderStartButton := func() string {
		active := m.evalState.currentField == 4
		buttonText := "[ Start Evaluation ]"

		buttonStyle := lipgloss.NewStyle().
			Foreground(t.Background()).
			Background(t.Primary()).
			Padding(0, 2).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(t.Primary())

		if active {
			// Highlight when focused
			buttonStyle = buttonStyle.
				Background(t.Accent()).
				BorderForeground(t.Accent()).
				Bold(true)
			buttonText = "▶ [ Start Evaluation ] ◀"
		}

		// Center the button in a full-width container
		buttonContainer := lipgloss.NewStyle().
			Width(m.width-4).
			Background(t.Background()).
			Align(lipgloss.Center).
			Padding(1, 0)

		return buttonContainer.Render(buttonStyle.Render(buttonText))
	}

	// Info section style
	infoStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(m.width-4).
		Align(lipgloss.Center).
		Padding(0, 2)

	// Help text style (for bottom of screen)
	helpStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(m.width).
		Align(lipgloss.Center).
		Padding(0, 1)

	// Build the content sections
	formSection := lipgloss.JoinVertical(lipgloss.Left,
		renderField(0, "Agent URL:", agent),
		renderField(1, "Judge LLM:", judge),
		renderField(2, "Parallel Runs:", parallel),
		renderField(3, "Deep Test:", deep),
	)

	infoSection := lipgloss.JoinVertical(lipgloss.Center,
		infoStyle.Render(fmt.Sprintf("Server: %s", m.evalState.ServerURL)),
		infoStyle.Render(fmt.Sprintf("Scenarios: %d", len(m.evalState.Scenarios))),
	)

	buttonSection := renderStartButton()

	helpText := helpStyle.Render("t Test Server   ↑/↓ switch fields   ←/→ move cursor   Tab/Enter config model   Space toggle   Enter activate   Esc Back")

	// Calculate content area height (excluding title and help)
	contentHeight := m.height - 6 // title(3) + help(1) + margins(2)

	// Create content area with proper spacing
	contentArea := lipgloss.NewStyle().
		Width(m.width).
		Height(contentHeight).
		Background(t.Background())

	// Create spacing with background color
	spacer := lipgloss.NewStyle().Background(t.Background()).Width(m.width).Render("")

	// Arrange content with spacing
	content := lipgloss.JoinVertical(lipgloss.Center,
		spacer, // spacing
		formSection,
		spacer, // spacing
		infoSection,
		spacer, // spacing
		buttonSection,
	)

	// Place content in the content area
	mainContent := contentArea.Render(
		lipgloss.Place(
			m.width,
			contentHeight,
			lipgloss.Center,
			lipgloss.Center,
			content,
			lipgloss.WithWhitespaceStyle(lipgloss.NewStyle().Background(t.Background())),
		),
	)

	// Combine all sections
	fullLayout := lipgloss.JoinVertical(lipgloss.Left,
		title,
		mainContent,
		helpText,
	)

	return mainStyle.Render(fullLayout)
}

// Start eval on Enter key (hook from Update)
func (m *Model) handleNewEvalEnter() {
	if m.evalState == nil || m.evalState.Running {
		return
	}
	ctx := context.Background()
	m.startEval(ctx, m.evalState)
	// move to detail screen
	m.currentScreen = EvaluationDetailScreen
}

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
		Foreground(t.Primary()).
		Background(t.BackgroundPanel()).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Primary()).
		Padding(0, 2).
		Width(m.width - 4).
		Align(lipgloss.Center)

	status := statusStyle.Render(fmt.Sprintf("Status: %s", m.evalState.Status))

	// Calculate available height for events (and summary if present)
	availableHeight := m.height - 12 // Leave space for header, status, help
	var summaryHeight int

	// If evaluation completed and we have a summary, reserve space for it
	if m.evalState.Completed && m.evalState.Summary != "" {
		summaryHeight = 8                    // Reserve space for summary
		availableHeight -= summaryHeight + 2 // +2 for spacing
	}

	// Events container
	eventsStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.BackgroundPanel()).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Border()).
		Padding(1, 2).
		Width(m.width - 4).
		Height(availableHeight)

	// Show last few events
	max := 20
	start := 0
	if len(m.evalState.Events) > max {
		start = len(m.evalState.Events) - max
	}
	lines := []string{}
	for _, ev := range m.evalState.Events[start:] {
		switch ev.Type {
		case "status":
			lines = append(lines, lipgloss.NewStyle().Foreground(t.Success()).Render(fmt.Sprintf("✓ %s", ev.Status)))
		case "chat":
			lines = append(lines, renderChatMessage(t, ev.Role, ev.Content))
		case "error":
			lines = append(lines, lipgloss.NewStyle().Foreground(t.Error()).Render(fmt.Sprintf("⚠ ERROR: %s", ev.Message)))
		}
	}

	if len(lines) == 0 {
		lines = append(lines, lipgloss.NewStyle().Foreground(t.TextMuted()).Italic(true).Render("Waiting for evaluation events..."))
	}

	eventsContent := eventsStyle.Render(strings.Join(lines, "\n"))

	// Help text style (for bottom of screen)
	helpStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(m.width).
		Align(lipgloss.Center).
		Padding(0, 1)

	var helpMsg string
	if m.evalState.Completed {
		helpMsg = "b Back  s Stop  r Report"
	} else {
		helpMsg = "b Back  s Stop"
	}
	helpText := helpStyle.Render(helpMsg)

	// Calculate content area height
	contentHeight := m.height - 6 // title(3) + help(1) + margins(2)

	// Create content area
	contentArea := lipgloss.NewStyle().
		Width(m.width).
		Height(contentHeight).
		Background(t.Background())

	// Create spacing with background color
	spacer := lipgloss.NewStyle().Background(t.Background()).Width(m.width).Render("")

	// Create summary section if available
	var summaryContent string
	if m.evalState.Completed && m.evalState.Summary != "" {
		summaryStyle := lipgloss.NewStyle().
			Foreground(t.Text()).
			Background(t.BackgroundPanel()).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(t.Primary()).
			Padding(1, 2).
			Width(m.width - 4).
			Height(summaryHeight)

		summaryTitle := lipgloss.NewStyle().
			Foreground(t.Primary()).
			Bold(true).
			Render("📊 Evaluation Summary")

		// Show first few lines of summary
		summaryLines := strings.Split(m.evalState.Summary, "\n")
		var displayLines []string
		for i, line := range summaryLines {
			if i >= summaryHeight-3 { // -3 for title, padding, border
				break
			}
			displayLines = append(displayLines, line)
		}

		summaryText := strings.Join(displayLines, "\n")
		summaryBody := summaryTitle + "\n" + summaryText
		summaryContent = summaryStyle.Render(summaryBody)
	}

	// Arrange content with proper spacing
	var contentParts []string
	contentParts = append(contentParts, spacer, status, spacer, eventsContent)

	if summaryContent != "" {
		contentParts = append(contentParts, spacer, summaryContent)
	}

	content := lipgloss.JoinVertical(lipgloss.Center, contentParts...)

	// Place content in the content area
	mainContent := contentArea.Render(
		lipgloss.Place(
			m.width,
			contentHeight,
			lipgloss.Center,
			lipgloss.Top,
			content,
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

// renderChatMessage renders a chat message with role-specific styling
func renderChatMessage(t theme.Theme, role, content string) string {
	var emoji string
	var roleStyle lipgloss.Style
	var messageStyle lipgloss.Style

	// Determine styling based on role
	switch role {
	case "Rogue", "judge", "evaluator", "Evaluator Agent":
		// Rogue/Judge - the evaluator (our system)
		emoji = "🔍" // magnifying glass for evaluation
		roleStyle = lipgloss.NewStyle().
			Foreground(t.Primary()).
			Bold(true)
		messageStyle = lipgloss.NewStyle().
			Foreground(t.Text()).
			Background(t.BackgroundPanel()).
			Padding(0, 1).
			MarginLeft(2)

	case "agent", "Agent", "user":
		// Agent under test
		emoji = "🤖" // robot for the agent being tested
		roleStyle = lipgloss.NewStyle().
			Foreground(t.Accent()).
			Bold(true)
		messageStyle = lipgloss.NewStyle().
			Foreground(t.Text()).
			Background(t.BackgroundPanel()).
			Padding(0, 1).
			MarginLeft(2)

	case "system", "System":
		// System messages
		emoji = "⚙️" // gear for system
		roleStyle = lipgloss.NewStyle().
			Foreground(t.TextMuted()).
			Italic(true)
		messageStyle = lipgloss.NewStyle().
			Foreground(t.TextMuted()).
			Italic(true).
			MarginLeft(2)

	default:
		// Unknown role - fallback
		emoji = "💬" // generic chat
		roleStyle = lipgloss.NewStyle().
			Foreground(t.Text())
		messageStyle = lipgloss.NewStyle().
			Foreground(t.Text()).
			MarginLeft(2)
	}

	// Format: [emoji] Role:
	//          Content (indented)
	roleHeader := fmt.Sprintf("%s %s:", emoji, role)
	roleText := roleStyle.Render(roleHeader)

	// Wrap content for better readability
	contentText := messageStyle.Render(content)

	// Add a subtle separator for visual distinction
	separator := lipgloss.NewStyle().
		Foreground(t.Border()).
		Render("─────")

	return fmt.Sprintf("%s\n%s\n%s", roleText, contentText, separator)
}
