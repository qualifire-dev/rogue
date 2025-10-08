package components

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// handleInterviewStarted processes the interview start response
func (e ScenarioEditor) handleInterviewStarted(msg InterviewStartedMsg) (ScenarioEditor, tea.Cmd) {
	e.interviewLoading = false
	e.interviewSpinner.SetActive(false) // Stop spinner

	if msg.Error != nil {
		// Store error in errorMsg so it's visible in ListMode
		e.errorMsg = "Failed to start interview: " + msg.Error.Error()
		e.mode = ListMode
		return e, nil
	}

	// Store session ID and add initial message
	e.interviewSessionID = msg.SessionID
	e.interviewMessages = append(e.interviewMessages, InterviewMessage{
		Role:    "assistant",
		Content: msg.InitialMessage,
	})

	// Focus input for user response
	if e.interviewInput != nil {
		e.interviewInput.Focus()
	}

	return e, nil
}

// handleInterviewMode handles keyboard input during interview mode
func (e ScenarioEditor) handleInterviewMode(msg tea.KeyMsg) (ScenarioEditor, tea.Cmd) {
	// Handle business context approval state
	if e.awaitingBusinessCtxApproval {
		switch msg.String() {
		case "a", "A":
			// Approve and generate scenarios
			e.awaitingBusinessCtxApproval = false
			e.infoMsg = "Generating scenarios..."
			e.interviewLoading = true
			e.interviewSpinner.SetActive(true)
			return e, tea.Batch(
				e.generateScenariosCmd(e.proposedBusinessContext),
				e.interviewSpinner.Start(),
			)

		case "e", "E":
			// Request changes - continue interview
			e.awaitingBusinessCtxApproval = false
			e.infoMsg = "You can request changes or ask for more details."

			// Pre-fill input with a suggestion
			if e.interviewInput != nil {
				e.interviewInput.Focus()
			}

			return e, nil

		case "escape", "esc":
			// Exit interview with confirmation
			if !e.interviewLoading {
				dialog := NewConfirmationDialog(
					"Exit Interview",
					"Are you sure you want to cancel the interview? Progress will be lost.",
				)
				return e, func() tea.Msg { return DialogOpenMsg{Dialog: dialog} }
			}
			return e, nil
		}
		return e, nil
	}

	// Normal interview mode handling
	switch msg.String() {
	case "escape", "esc":
		// Exit interview with confirmation
		if !e.interviewLoading {
			dialog := NewConfirmationDialog(
				"Exit Interview",
				"Are you sure you want to cancel the interview? Progress will be lost.",
			)
			// Return to list mode will be handled by dialog result
			return e, func() tea.Msg { return DialogOpenMsg{Dialog: dialog} }
		}
		return e, nil

	case "shift+enter":
		// Insert newline in the input
		if e.interviewInput != nil && !e.interviewLoading {
			e.interviewInput.InsertNewline()
			return e, nil
		}
		return e, nil

	case "enter":
		// Send message if input not empty
		if e.interviewInput != nil && !e.interviewLoading {
			message := e.interviewInput.GetValue()
			if strings.TrimSpace(message) == "" {
				return e, nil
			}

			// Store user message for display
			e.lastUserMessage = message

			// Add user message to history immediately
			e.interviewMessages = append(e.interviewMessages, InterviewMessage{
				Role:    "user",
				Content: message,
			})

			// Clear input and set loading
			e.interviewInput.SetValue("")
			e.interviewLoading = true
			e.interviewSpinner.SetActive(true) // Start spinner

			// Send message via command and start spinner animation
			return e, tea.Batch(
				e.sendInterviewMessageCmd(message),
				e.interviewSpinner.Start(),
			)
		}
		return e, nil

	default:
		// Forward to TextArea for text input
		if e.interviewInput != nil && !e.interviewLoading {
			updatedTextArea, cmd := e.interviewInput.Update(msg)
			*e.interviewInput = *updatedTextArea
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
	e.interviewLoading = false
	e.interviewSpinner.SetActive(false) // Stop spinner

	if msg.Error != nil {
		e.interviewError = msg.Error.Error()
		return e, nil
	}

	// Add AI response to history
	e.interviewMessages = append(e.interviewMessages, InterviewMessage{
		Role:    "assistant",
		Content: msg.Response,
	})

	// Clear error
	e.interviewError = ""

	// Check if interview is complete
	if msg.IsComplete {
		// Store proposed business context for user review
		e.proposedBusinessContext = msg.Response
		e.awaitingBusinessCtxApproval = true
		e.infoMsg = "Review the business context below. Press 'a' to approve or 'e' to request changes."

		// Focus input in case user wants to make changes
		if e.interviewInput != nil {
			e.interviewInput.Focus()
		}

		return e, nil
	}

	// Re-focus input for next response
	if e.interviewInput != nil {
		e.interviewInput.Focus()
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
	e.interviewSpinner.SetActive(false) // Stop spinner

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
	e.interviewMessages = nil
	e.interviewLoading = false
	e.awaitingBusinessCtxApproval = false
	e.proposedBusinessContext = ""
	e.rebuildFilter()

	return e, func() tea.Msg {
		return ScenarioEditorMsg{Action: "scenarios_generated"}
	}
}

// renderInterviewView renders the interview chat interface
func (e ScenarioEditor) renderInterviewView(t theme.Theme) string {
	// Calculate message count (user messages only)
	userMsgCount := 0
	for _, msg := range e.interviewMessages {
		if msg.Role == "user" {
			userMsgCount++
		}
	}

	// Header with progress
	header := lipgloss.NewStyle().
		Background(t.Background()).
		Foreground(t.Primary()).
		Bold(true).
		Render(fmt.Sprintf("\n🤖 AI Interview - Understanding Your Agent (%d/3 responses)", userMsgCount))

	// Render message history
	var messageLines []string
	for _, msg := range e.interviewMessages {
		var prefix string
		var textStyle lipgloss.Style

		if msg.Role == "assistant" {
			textStyle = lipgloss.NewStyle().Foreground(t.Accent())
			prefix = "🤖 AI:  "
		} else {
			textStyle = lipgloss.NewStyle().Foreground(t.Primary())
			prefix = "👤 You: "
		}

		// Calculate available width for text (accounting for visual prefix width and padding)
		// Emojis + "AI: " or "You: " take about 8 visual characters
		// Account for border (4) and some padding
		visualPrefixWidth := 8
		availableWidth := e.width - visualPrefixWidth - 8
		if availableWidth < 40 {
			availableWidth = 40
		}

		// Preserve newlines by processing each paragraph separately
		paragraphs := strings.Split(msg.Content, "\n")
		var allLines []string
		for _, para := range paragraphs {
			if strings.TrimSpace(para) == "" {
				// Preserve empty lines
				allLines = append(allLines, "")
			} else {
				// Wrap non-empty paragraphs
				wrapped := wrapText(para, availableWidth)
				allLines = append(allLines, strings.Split(wrapped, "\n")...)
			}
		}
		lines := allLines

		for i, line := range lines {
			if i == 0 {
				// First line with prefix
				messageLines = append(messageLines, textStyle.Render(prefix+line))
			} else {
				// Continuation lines with indentation (8 spaces to match visual prefix width)
				messageLines = append(messageLines, textStyle.Render("        "+line))
			}
		}
		messageLines = append(messageLines, "") // Blank line between messages
	}

	// Add loading indicator with spinner if loading
	if e.interviewLoading {
		spinnerView := e.interviewSpinner.View()
		if spinnerView != "" {
			textStyle := lipgloss.NewStyle().Foreground(t.Accent()).Background(t.Background())
			loadingLine := spinnerView + textStyle.Render(" thinking...")
			messageLines = append(messageLines, loadingLine)
		}
	}

	// Update viewport with message history
	messageHistory := ""
	if e.interviewViewport != nil {
		e.interviewViewport.SetContent(strings.Join(messageLines, "\n"))
		e.interviewViewport.GotoBottom() // Auto-scroll to bottom
		messageHistory = e.interviewViewport.View()
	} else {
		messageHistory = strings.Join(messageLines, "\n")
	}

	// Message history section with border
	historyStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Primary()).
		Background(t.Background()).
		Padding(1, 1).
		Width(e.width - 4).
		Height((e.height - 20)) // Leave room for input and help

	borderedHistory := historyStyle.Render(messageHistory)

	// Input section
	inputLabel := "Your Response:"
	var help string

	// Different UI for business context approval
	if e.awaitingBusinessCtxApproval {
		inputLabel = "Business Context (Review and Approve):"
		help = lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.TextMuted()).
			Render("a approve & generate  e request changes  Esc cancel")
	} else {
		help = lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.TextMuted()).
			Render("Enter send  Esc cancel  Shift+Enter new line")
	}

	inputLabelStyled := lipgloss.NewStyle().
		Background(t.Background()).
		Foreground(t.Accent()).
		Render(inputLabel)

	var inputArea string
	if e.interviewInput != nil {
		inputArea = e.interviewInput.View()
	}

	// Error display
	errorLine := ""
	if e.interviewError != "" {
		errorLine = lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.Error()).
			Render("⚠ " + e.interviewError)
	}

	// Completion/status message (only for generation phase, not loading)
	statusMsg := ""
	if userMsgCount >= 3 && e.interviewLoading {
		statusMsg = lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.Success()).
			Bold(true).
			Render("✓ Interview complete!")
	}

	// Build the view
	content := strings.Join([]string{
		header,
		"",
		borderedHistory,
		"",
		inputLabelStyled,
		inputArea,
		"",
		help,
		errorLine,
		statusMsg,
	}, "\n")

	return content
}
