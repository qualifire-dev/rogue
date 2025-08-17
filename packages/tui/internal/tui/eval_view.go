package tui

import (
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
	deep := "❌"
	if m.evalState.DeepTest {
		deep = "✅"
	}

	// Helper function to render the start button
	renderStartButton := func() string {
		active := m.evalState.currentField == 4
		var buttonText string

		if m.evalSpinner.IsActive() {
			buttonText = fmt.Sprintf("%s Starting Evaluation...", m.evalSpinner.View())
		} else {
			buttonText = "[ Start Evaluation ]"
		}

		buttonStyle := lipgloss.NewStyle().
			Foreground(t.Background()).
			Background(t.Primary()).
			Padding(0, 2).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(t.Primary())

		if active && !m.evalSpinner.IsActive() {
			// Highlight when focused (but not when spinning)
			buttonStyle = buttonStyle.
				Background(t.Accent()).
				BorderForeground(t.Accent()).
				Bold(true)
			buttonText = "▶ [ Start Evaluation ] ◀"
		} else if m.evalSpinner.IsActive() {
			// Different style when loading
			buttonStyle = buttonStyle.
				Background(t.TextMuted()).
				BorderForeground(t.TextMuted())
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

	var infoLines []string
	if m.healthSpinner.IsActive() {
		infoLines = append(infoLines, infoStyle.Render(fmt.Sprintf("Server: %s %s", m.evalState.ServerURL, m.healthSpinner.View())))
	} else {
		infoLines = append(infoLines, infoStyle.Render(fmt.Sprintf("Server: %s", m.evalState.ServerURL)))
	}
	infoLines = append(infoLines, infoStyle.Render(fmt.Sprintf("Scenarios: %d", len(m.evalState.Scenarios))))

	infoSection := lipgloss.JoinVertical(lipgloss.Center, infoLines...)

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

	// Show spinner - the actual evaluation will start after a delay
	m.evalSpinner.SetActive(true)
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

	// Calculate available height for content area (excluding header, status, help)
	// header(3) + help(1) + margins(2) = 6, plus extra margin for status and spacing
	totalContentHeight := m.height - 8 // More conservative calculation to prevent footer override

	var eventsHeight, summaryHeight int
	var showSummary bool

	// If evaluation completed and we have a summary OR are generating one, split 50/50
	if m.evalState.Completed && (m.evalState.Summary != "" || m.summarySpinner.IsActive()) {
		showSummary = true
		eventsHeight = (totalContentHeight / 2) - 2           // Reduced margin to prevent overflow
		summaryHeight = totalContentHeight - eventsHeight - 1 // -1 for spacer between them
	} else {
		// No summary, events take full height with conservative margin
		eventsHeight = totalContentHeight - 2 // Leave extra space to prevent footer override
		summaryHeight = 0
	}

	// Prepare events content for viewport
	var lines []string
	for _, ev := range m.evalState.Events {
		switch ev.Type {
		case "status":
			lines = append(lines, lipgloss.NewStyle().Foreground(t.Success()).Render(fmt.Sprintf("✓ %s", ev.Status)))
		case "chat":
			// Split multi-line chat messages
			chatLines := strings.Split(renderChatMessage(t, ev.Role, ev.Content), "\n")
			lines = append(lines, chatLines...)
		case "error":
			lines = append(lines, lipgloss.NewStyle().Foreground(t.Error()).Render(fmt.Sprintf("⚠ ERROR: %s", ev.Message)))
		}
	}

	if len(lines) == 0 {
		lines = append(lines, lipgloss.NewStyle().Foreground(t.TextMuted()).Italic(true).Render("Waiting for evaluation events..."))
	}

	// Update events viewport
	// Set viewport to match the style height (which includes border and padding)
	// Use more conservative sizing to prevent content overflow
	m.eventsViewport.SetSize(m.width-4, eventsHeight-8) // -6 for padding and extra margin
	m.eventsViewport.SetContent(strings.Join(lines, "\n"))

	// Set border color based on focus
	eventsBorderFg := t.Border()
	if m.focusedViewport == 0 {
		eventsBorderFg = t.Primary()
	}

	m.eventsViewport.Style = lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.BackgroundPanel()).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(eventsBorderFg).
		Padding(1, 2).
		Width(m.width - 4).
		Height(eventsHeight)

	// Auto-scroll to bottom for new events (like a chat) only if auto-scroll is enabled
	if m.eventsAutoScroll {
		m.eventsViewport.GotoBottom()
	}

	eventsContent := m.eventsViewport.View()

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

	// Calculate content area height - use same conservative calculation as totalContentHeight
	contentHeight := m.height - 10 // title(3) + help(1) + margins(2) + extra spacing(4)

	// Create content area
	contentArea := lipgloss.NewStyle().
		Width(m.width).
		Height(contentHeight).
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

		summaryTitle := lipgloss.NewStyle().
			Foreground(t.Primary()).
			Bold(true).
			Render(summaryTitleText)

		var summaryText string
		if m.evalState.Summary == "" && m.summarySpinner.IsActive() {
			// Show loading message when generating summary
			summaryText = lipgloss.NewStyle().
				Foreground(t.TextMuted()).
				Italic(true).
				Render("Generating summary with LLM...")
		} else {
			// Render the markdown summary with styling
			summaryText = renderMarkdownSummary(t, m.evalState.Summary)
		}

		// Prepare summary content for viewport
		summaryBody := summaryTitle + "\n" + summaryText

		// Update summary viewport
		// Use conservative sizing to match events viewport
		m.summaryViewport.SetSize(m.width-4, summaryHeight-8)
		m.summaryViewport.SetContent(summaryBody)

		// Set border color based on focus
		summaryBorderFg := t.Primary() // Default border for summary
		if m.focusedViewport == 1 {
			summaryBorderFg = t.Primary() // Keep primary when focused
		} else {
			summaryBorderFg = t.Border() // Use normal border when not focused
		}

		m.summaryViewport.Style = lipgloss.NewStyle().
			Foreground(t.Text()).
			Background(t.BackgroundPanel()).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(summaryBorderFg).
			Padding(1, 2).
			Width(m.width - 4).
			Height(summaryHeight)

		summaryContent = m.summaryViewport.View()
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
				contentHeight,
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
				contentHeight,
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

// renderMarkdownSummary renders the markdown summary with basic styling
func renderMarkdownSummary(t theme.Theme, summary string) string {
	lines := strings.Split(summary, "\n")
	var styledLines []string

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			styledLines = append(styledLines, "")
			continue
		}

		// Basic markdown styling
		if strings.HasPrefix(line, "# ") {
			// H1 - Main title
			title := strings.TrimPrefix(line, "# ")
			styledLines = append(styledLines, lipgloss.NewStyle().
				Foreground(t.Primary()).
				Bold(true).
				Render("🔷 "+title))
		} else if strings.HasPrefix(line, "## ") {
			// H2 - Section headers
			title := strings.TrimPrefix(line, "## ")
			styledLines = append(styledLines, lipgloss.NewStyle().
				Foreground(t.Accent()).
				Bold(true).
				Render("▪ "+title))
		} else if strings.HasPrefix(line, "### ") {
			// H3 - Subsection headers
			title := strings.TrimPrefix(line, "### ")
			styledLines = append(styledLines, lipgloss.NewStyle().
				Foreground(t.Text()).
				Bold(true).
				Render("  • "+title))
		} else if strings.HasPrefix(line, "- ") || strings.HasPrefix(line, "* ") {
			// Bullet points
			content := strings.TrimPrefix(strings.TrimPrefix(line, "- "), "* ")
			styledLines = append(styledLines, lipgloss.NewStyle().
				Foreground(t.Text()).
				Render("    • "+content))
		} else if strings.HasPrefix(line, "**") && strings.HasSuffix(line, "**") {
			// Bold text
			content := strings.TrimSuffix(strings.TrimPrefix(line, "**"), "**")
			styledLines = append(styledLines, lipgloss.NewStyle().
				Foreground(t.Text()).
				Bold(true).
				Render(content))
		} else if strings.Contains(line, "`") {
			// Inline code (basic support)
			styled := strings.ReplaceAll(line, "`", "")
			styledLines = append(styledLines, lipgloss.NewStyle().
				Foreground(t.Success()).
				Render(styled))
		} else {
			// Regular text
			styledLines = append(styledLines, lipgloss.NewStyle().
				Foreground(t.Text()).
				Render(line))
		}
	}

	return strings.Join(styledLines, "\n")
}
