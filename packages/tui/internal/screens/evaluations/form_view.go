package evaluations

import (
	"fmt"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// RenderForm renders the new evaluation form screen
func RenderForm(state *FormState) string {
	t := theme.CurrentTheme()
	if state == nil {
		return lipgloss.NewStyle().
			Width(80).
			Height(24).
			Background(t.Background()).
			Foreground(t.Text()).
			Align(lipgloss.Center, lipgloss.Center).
			Render("New evaluation not initialized")
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

	title := titleStyle.Render("🧪 New Evaluation")

	// Helper function to render a text field with inline label and value
	renderTextField := func(fieldIndex int, label, value string) string {
		active := state.CurrentField == fieldIndex

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
			cursorPos := state.CursorPos
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
			Width(state.Width-4).
			Background(t.Background()).
			Padding(0, 2)

		fieldContent := lipgloss.JoinHorizontal(lipgloss.Left,
			labelStyle.Render(label),
			valueStyle.Render(value),
		)

		return fieldContainer.Render(fieldContent)
	}

	// Helper function to render a dropdown field with indicators
	renderDropdownField := func(fieldIndex int, label, value string) string {
		active := state.CurrentField == fieldIndex

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
				Background(t.Background()).
				Bold(true)
			// Add dropdown indicators
			value = "◀ " + value + " ▶"
		}

		// Create a full-width container for the field
		fieldContainer := lipgloss.NewStyle().
			Width(state.Width-4).
			Background(t.Background()).
			Padding(0, 2)

		fieldContent := lipgloss.JoinHorizontal(lipgloss.Left,
			labelStyle.Render(label),
			valueStyle.Render(value),
		)

		return fieldContainer.Render(fieldContent)
	}

	// Helper function to render a toggle field
	renderToggleField := func(fieldIndex int, label, value string) string {
		active := state.CurrentField == fieldIndex

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
				Background(t.Background()).
				Bold(true)
		}

		// Create a full-width container for the field
		fieldContainer := lipgloss.NewStyle().
			Width(state.Width-4).
			Background(t.Background()).
			Padding(0, 2)

		fieldContent := lipgloss.JoinHorizontal(lipgloss.Left,
			labelStyle.Render(label),
			valueStyle.Render(value),
		)

		return fieldContainer.Render(fieldContent)
	}

	// Helper function to render a dropdown field with indicators
	renderDropdownField := func(fieldIndex int, label, value string) string {
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
				Background(t.Background()).
				Bold(true)
			// Add dropdown indicators
			value = "◀ " + value + " ▶"
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

	// Helper function to render a toggle field
	renderToggleField := func(fieldIndex int, label, value string) string {
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
				Background(t.Background()).
				Bold(true)
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
	protocol := string(m.evalState.AgentProtocol)
	transport := string(m.evalState.AgentTransport)
	judge := m.evalState.JudgeModel
	deep := "❌"
	if state.DeepTest {
		deep = "✅"
	}

	// Helper function to render the start button
	renderStartButton := func() string {
		active := m.evalState.currentField == 5
		var buttonText string

		if state.EvalSpinnerActive {
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

		if active && !state.EvalSpinnerActive {
			// Highlight when focused (but not when spinning)
			buttonStyle = buttonStyle.
				Background(t.Accent()).
				BorderForeground(t.Accent()).
				Bold(true)
			buttonText = "▶ [ Start Evaluation ] ◀"
		} else if state.EvalSpinnerActive {
			// Different style when loading
			buttonStyle = buttonStyle.
				Background(t.TextMuted()).
				BorderForeground(t.TextMuted())
		}

		// Center the button in a full-width container
		buttonContainer := lipgloss.NewStyle().
			Width(state.Width-4).
			Background(t.Background()).
			Align(lipgloss.Center).
			Padding(1, 0)

		return buttonContainer.Render(buttonStyle.Render(buttonText))
	}

	// Info section style
	infoStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(state.Width-4).
		Align(lipgloss.Center).
		Padding(0, 2)

	// Help text style (for bottom of screen)
	helpStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(state.Width).
		Align(lipgloss.Center).
		Padding(0, 1)

	// Build the content sections
	formSection := lipgloss.JoinVertical(lipgloss.Left,
		renderTextField(0, "Agent URL:", agent),
		renderDropdownField(1, "Protocol:", protocol),
		renderDropdownField(2, "Transport:", transport),
		renderTextField(3, "Judge LLM:", judge),
		renderToggleField(4, "Deep Test:", deep),
	)

	var infoLines []string
	if state.HealthSpinnerActive {
		infoLines = append(infoLines, infoStyle.Render(fmt.Sprintf("Server: %s %s", state.ServerURL, state.HealthSpinnerView)))
	} else {
		infoLines = append(infoLines, infoStyle.Render(fmt.Sprintf("Server: %s", state.ServerURL)))
	}
	infoLines = append(infoLines, infoStyle.Render(fmt.Sprintf("Scenarios: %d", state.ScenariosCount)))

	infoSection := lipgloss.JoinVertical(lipgloss.Center, infoLines...)

	buttonSection := renderStartButton()

	helpText := helpStyle.Render("t Test Server   ↑/↓ switch fields   ←/→ move cursor/cycle dropdown    Space toggle   Enter activate   Esc Back")

	// Calculate content area height (excluding title and help)
	contentHeight := state.Height - 6 // title(3) + help(1) + margins(2)

	// Create content area with proper spacing
	contentArea := lipgloss.NewStyle().
		Width(state.Width).
		Height(contentHeight).
		Background(t.Background())

	// Create spacing with background color
	spacer := lipgloss.NewStyle().Background(t.Background()).Width(state.Width).Render("")

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
			state.Width,
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
