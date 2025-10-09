package components

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/styles"
	"github.com/rogue/tui/internal/theme"
)

// handleInterviewStarted processes the interview start response
func (e ScenarioEditor) handleInterviewStarted(msg InterviewStartedMsg) (ScenarioEditor, tea.Cmd) {
	if e.interviewChatView != nil {
		e.interviewChatView.SetLoading(false)
	}

	if msg.Error != nil {
		// Store error in errorMsg so it's visible in ListMode
		e.errorMsg = "Failed to start interview: " + msg.Error.Error()
		e.mode = ListMode
		return e, nil
	}

	// Store session ID and add initial message
	e.interviewSessionID = msg.SessionID
	if e.interviewChatView != nil {
		e.interviewChatView.AddMessage("assistant", msg.InitialMessage)
		e.interviewChatView.FocusInput()
	}

	return e, nil
}

// handleInterviewMode handles keyboard input during interview mode
func (e ScenarioEditor) handleInterviewMode(msg tea.KeyMsg) (ScenarioEditor, tea.Cmd) {
	// Handle business context approval state
	if e.awaitingBusinessCtxApproval {
		return e.handleApprovalMode(msg)
	}

	// Normal interview mode - handle via ChatView for most keys
	switch msg.String() {
	case "escape", "esc":
		// Exit interview with confirmation
		if e.interviewChatView != nil && !e.interviewChatView.IsLoading() {
			dialog := NewConfirmationDialog(
				"Exit Interview",
				"Are you sure you want to cancel the interview? Progress will be lost.",
			)
			return e, func() tea.Msg { return DialogOpenMsg{Dialog: dialog} }
		}
		return e, nil

	case "enter":
		// Send message if input not empty and input is focused
		if e.interviewChatView != nil && !e.interviewChatView.IsLoading() && !e.interviewChatView.IsViewportFocused() {
			message := e.interviewChatView.GetInputValue()
			if strings.TrimSpace(message) == "" {
				return e, nil
			}

			// Store user message for display
			e.lastUserMessage = message

			// Add user message to history immediately
			e.interviewChatView.AddMessage("user", message)

			// Clear input and set loading
			e.interviewChatView.ClearInput()
			e.interviewChatView.SetLoading(true)

			// Send message via command and start spinner animation
			return e, tea.Batch(
				e.sendInterviewMessageCmd(message),
				e.interviewChatView.StartSpinner(),
			)
		}
		return e, nil

	default:
		// Delegate to ChatView for navigation and text input
		if e.interviewChatView != nil {
			cmd := e.interviewChatView.Update(msg)
			return e, cmd
		}
		return e, nil
	}
}

// handleApprovalMode handles keyboard input during business context approval
func (e ScenarioEditor) handleApprovalMode(msg tea.KeyMsg) (ScenarioEditor, tea.Cmd) {
	switch msg.String() {
	case "tab":
		// Cycle through: viewport -> input -> button
		if e.interviewChatView != nil {
			if e.interviewChatView.IsViewportFocused() {
				e.interviewChatView.FocusInput()
			} else if !e.approveButtonFocused {
				e.approveButtonFocused = true
				e.interviewChatView.FocusInput() // Blur happens internally
			} else {
				// From button back to viewport
				e.approveButtonFocused = false
				e.interviewChatView.FocusViewport()
			}
		}
		return e, nil

	case "shift+tab":
		// Cycle backwards: button -> input -> viewport
		if e.interviewChatView != nil {
			if e.approveButtonFocused {
				e.approveButtonFocused = false
				e.interviewChatView.FocusInput()
			} else if !e.interviewChatView.IsViewportFocused() {
				e.interviewChatView.FocusViewport()
			} else {
				// From viewport back to button
				e.approveButtonFocused = true
			}
		}
		return e, nil

	case "down", "up":
		// Let ChatView handle scrolling when focused, otherwise navigate
		if e.interviewChatView != nil {
			if e.interviewChatView.IsViewportFocused() {
				// ChatView handles scrolling
				cmd := e.interviewChatView.Update(msg)
				return e, cmd
			} else if msg.String() == "down" && !e.approveButtonFocused {
				// From input to button
				e.approveButtonFocused = true
			} else if msg.String() == "up" && e.approveButtonFocused {
				// From button to input
				e.approveButtonFocused = false
				e.interviewChatView.FocusInput()
			} else if msg.String() == "up" && !e.interviewChatView.IsViewportFocused() {
				// From input to viewport
				e.interviewChatView.FocusViewport()
			}
		}
		return e, nil

	case "enter":
		if e.approveButtonFocused {
			// Approve and generate scenarios
			e.awaitingBusinessCtxApproval = false
			e.approveButtonFocused = false
			e.infoMsg = "Generating scenarios..."
			if e.interviewChatView != nil {
				e.interviewChatView.SetLoading(true)
				return e, tea.Batch(
					e.generateScenariosCmd(e.proposedBusinessContext),
					e.interviewChatView.StartSpinner(),
				)
			}
			return e, e.generateScenariosCmd(e.proposedBusinessContext)
		} else if e.interviewChatView != nil && !e.interviewChatView.IsViewportFocused() {
			// Send edit request message
			message := e.interviewChatView.GetInputValue()
			if strings.TrimSpace(message) != "" {
				// Request changes - continue interview
				e.awaitingBusinessCtxApproval = false

				// Add user message to history
				e.interviewChatView.AddMessage("user", message)

				// Clear input and set loading
				e.interviewChatView.ClearInput()
				e.interviewChatView.SetLoading(true)

				// Send message via command
				return e, tea.Batch(
					e.sendInterviewMessageCmd(message),
					e.interviewChatView.StartSpinner(),
				)
			}
		}
		return e, nil

	case "escape", "esc":
		// Exit interview with confirmation
		if e.interviewChatView != nil && !e.interviewChatView.IsLoading() {
			dialog := NewConfirmationDialog(
				"Exit Interview",
				"Are you sure you want to cancel the interview? Progress will be lost.",
			)
			return e, func() tea.Msg { return DialogOpenMsg{Dialog: dialog} }
		}
		return e, nil

	default:
		// Forward to ChatView for text input (only if input is focused and not on button)
		if e.interviewChatView != nil && !e.approveButtonFocused && !e.interviewChatView.IsLoading() {
			cmd := e.interviewChatView.Update(msg)
			return e, cmd
		}
		return e, nil
	}
}

// sendInterviewMessageCmd creates a command to send an interview message
func (e *ScenarioEditor) sendInterviewMessageCmd(message string) tea.Cmd {
	// This needs to be handled by app.go which has access to the SDK
	e.lastUserMessage = message

	return func() tea.Msg {
		return SendInterviewMessageMsg{
			SessionID: e.interviewSessionID,
			Message:   message,
		}
	}
}

// handleInterviewResponse processes the AI's response
func (e ScenarioEditor) handleInterviewResponse(msg InterviewResponseMsg) (ScenarioEditor, tea.Cmd) {
	if e.interviewChatView != nil {
		e.interviewChatView.SetLoading(false)

		if msg.Error != nil {
			e.interviewChatView.SetError(msg.Error.Error())
			return e, nil
		}

		// Add AI response to history
		e.interviewChatView.AddMessage("assistant", msg.Response)
		e.interviewChatView.ClearError()

		// Check if interview is complete
		if msg.IsComplete {
			// Store proposed business context for user review
			e.proposedBusinessContext = msg.Response
			e.awaitingBusinessCtxApproval = true
			e.approveButtonFocused = false
			e.infoMsg = "Review the business context. Type to request changes or navigate to button to approve."

			// Focus input for potential edits
			e.interviewChatView.FocusInput()

			return e, nil
		}

		// Re-focus input for next response
		e.interviewChatView.FocusInput()
	}

	return e, nil
}

// generateScenariosCmd creates a command to generate scenarios
func (e *ScenarioEditor) generateScenariosCmd(businessContext string) tea.Cmd {
	return func() tea.Msg {
		return GenerateScenariosMsg{
			BusinessContext: businessContext,
		}
	}
}

// handleScenariosGenerated processes generated scenarios
func (e ScenarioEditor) handleScenariosGenerated(msg ScenariosGeneratedMsg) (ScenarioEditor, tea.Cmd) {
	if e.interviewChatView != nil {
		e.interviewChatView.SetLoading(false)
	}

	if msg.Error != nil {
		// Store error in errorMsg so it's visible in ListMode
		e.errorMsg = "Failed to generate scenarios: " + msg.Error.Error()
		e.mode = ListMode
		return e, nil
	}

	// Populate editor with generated scenarios
	e.scenarios = msg.Scenarios
	e.businessContext = &msg.BusinessContext

	// Save to file
	if err := e.saveScenarios(); err != nil {
		e.errorMsg = "Failed to save scenarios: " + err.Error()
	} else {
		e.infoMsg = fmt.Sprintf("Generated %d scenarios from interview!", len(msg.Scenarios))
	}

	// Exit interview mode, return to list view
	e.mode = ListMode
	e.interviewMode = false
	e.interviewSessionID = ""
	e.awaitingBusinessCtxApproval = false
	e.proposedBusinessContext = ""
	e.approveButtonFocused = false
	e.interviewChatView = nil // Clear chat view
	e.rebuildFilter()

	return e, func() tea.Msg {
		return ScenarioEditorMsg{Action: "scenarios_generated"}
	}
}

// renderInterviewView renders the interview chat interface
func (e ScenarioEditor) renderInterviewView(t theme.Theme) string {
	if e.interviewChatView == nil {
		return "Loading chat..."
	}

	// Normal interview mode - just render the ChatView
	if !e.awaitingBusinessCtxApproval {
		return e.interviewChatView.View(t)
	}

	// Approval mode - render ChatView with custom label and approval button
	e.interviewChatView.SetInputLabel("Business Context (Review and Approve):")
	e.interviewChatView.SetInputPlaceholder("Request changes here...")

	// Use ViewWithoutHelp to avoid double help text
	chatViewContent := e.interviewChatView.ViewWithoutHelp(t)

	// Create approve button
	buttonText := "Approve & Generate"
	buttonStyle := lipgloss.NewStyle().
		Background(t.BackgroundPanel()).
		Foreground(t.Text()).
		Padding(0, 2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.TextMuted())

	if e.approveButtonFocused {
		buttonStyle = buttonStyle.
			Background(t.Primary()).
			Foreground(t.Background()).
			BorderForeground(t.Primary()).
			Bold(true)
	}

	button := buttonStyle.Render(buttonText)

	// Check for errors first
	errorMsg := e.interviewChatView.GetError()
	var bottomLine string

	if errorMsg != "" {
		// Show error instead of button
		errorLine := lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.Error()).
			Padding(1, 0).
			Render("⚠ " + errorMsg)

		// Help text on the right
		helpText := "Tab/↑↓ switch focus  Enter confirm  Shift+Enter new line  Esc cancel"
		help := lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.TextMuted()).
			Padding(1, 0).
			Render(helpText)

		bottomLine = lipgloss.JoinHorizontal(
			lipgloss.Top,
			lipgloss.Place(
				(e.width-4)/2,
				3,
				lipgloss.Left,
				lipgloss.Top,
				errorLine,
				styles.WhitespaceStyle(t.Background()),
			),
			lipgloss.Place(
				(e.width-4)/2,
				3,
				lipgloss.Right,
				lipgloss.Top,
				help,
				styles.WhitespaceStyle(t.Background()),
			),
		)
	} else {
		// Show button and help
		// Help text - context-aware based on focus
		var helpText string
		if e.interviewChatView.IsViewportFocused() {
			helpText = "↑↓ scroll  Tab switch focus  Enter confirm  Shift+Enter new line  Esc cancel"
		} else {
			helpText = "Tab/↑↓ switch focus  Enter confirm  Shift+Enter new line  Esc cancel"
		}
		help := lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.TextMuted()).
			Padding(1, 0).
			Render(helpText)

		bottomLine = lipgloss.JoinHorizontal(
			lipgloss.Top,
			lipgloss.Place(
				(e.width-4)/2,
				3,
				lipgloss.Left,
				lipgloss.Top,
				button,
				styles.WhitespaceStyle(t.Background()),
			),
			lipgloss.Place(
				(e.width-4)/2,
				3,
				lipgloss.Right,
				lipgloss.Top,
				help,
				styles.WhitespaceStyle(t.Background()),
			),
		)
	}

	return chatViewContent + "\n" + bottomLine
}
