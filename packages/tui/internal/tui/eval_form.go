package tui

import (
	"fmt"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// renderNewEvaluation renders the new evaluation form screen
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
	deep := "❌"
	if m.evalState.DeepTest {
		deep = "✅"
	}

	// Helper function to render the start button
	renderStartButton := func() string {
		active := m.evalState.currentField == 3
		var buttonText string

		if m.evalSpinner.IsActive() {
			buttonText = " Starting Evaluation..."
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
		renderField(2, "Deep Test:", deep),
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

	helpText := helpStyle.Render("t Test Server   ↑/↓ switch fields   ←/→ move cursor    Space toggle   Enter activate   Esc Back")

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

// handleNewEvalEnter handles the Enter key press on the new evaluation form
func (m *Model) handleNewEvalEnter() {
	if m.evalState == nil || m.evalState.Running {
		return
	}

	// Show spinner - the actual evaluation will start after a delay
	m.evalSpinner.SetActive(true)
}
