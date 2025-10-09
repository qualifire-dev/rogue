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

	// Focus input for user response, not viewport
	e.interviewViewportFocused = false
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
		case "tab":
			// Cycle through: viewport -> input -> button
			if e.interviewViewportFocused {
				e.interviewViewportFocused = false
				if e.interviewInput != nil {
					e.interviewInput.Focus()
				}
			} else if !e.approveButtonFocused {
				e.approveButtonFocused = true
				if e.interviewInput != nil {
					e.interviewInput.Blur()
				}
			} else {
				// From button back to viewport
				e.approveButtonFocused = false
				e.interviewViewportFocused = true
			}
			return e, nil

		case "shift+tab":
			// Cycle backwards: button -> input -> viewport
			if e.approveButtonFocused {
				e.approveButtonFocused = false
				if e.interviewInput != nil {
					e.interviewInput.Focus()
				}
			} else if !e.interviewViewportFocused {
				e.interviewViewportFocused = true
				if e.interviewInput != nil {
					e.interviewInput.Blur()
				}
			} else {
				// From viewport back to button
				e.interviewViewportFocused = false
				e.approveButtonFocused = true
			}
			return e, nil

		case "down":
			// Move focus down: viewport -> input -> button
			if e.interviewViewportFocused {
				// From viewport to input
				e.interviewViewportFocused = false
				if e.interviewInput != nil {
					e.interviewInput.Focus()
				}
			} else if !e.approveButtonFocused {
				// From input to button
				e.approveButtonFocused = true
				if e.interviewInput != nil {
					e.interviewInput.Blur()
				}
			}
			// If already on button, stay there
			return e, nil

		case "up":
			// Move focus up: button -> input -> viewport
			if e.approveButtonFocused {
				// From button to input
				e.approveButtonFocused = false
				if e.interviewInput != nil {
					e.interviewInput.Focus()
				}
			} else if !e.interviewViewportFocused {
				// From input to viewport
				e.interviewViewportFocused = true
				if e.interviewInput != nil {
					e.interviewInput.Blur()
				}
			}
			// If already on viewport, stay there
			return e, nil

		case "enter":
			if e.approveButtonFocused {
				// Approve and generate scenarios
				e.awaitingBusinessCtxApproval = false
				e.approveButtonFocused = false
				e.infoMsg = "Generating scenarios..."
				e.interviewLoading = true
				e.interviewSpinner.SetActive(true)
				return e, tea.Batch(
					e.generateScenariosCmd(e.proposedBusinessContext),
					e.interviewSpinner.Start(),
				)
			} else {
				// Send edit request message
				if e.interviewInput != nil {
					message := e.interviewInput.GetValue()
					if strings.TrimSpace(message) != "" {
						// Request changes - continue interview
						e.awaitingBusinessCtxApproval = false

						// Add user message to history
						e.interviewMessages = append(e.interviewMessages, InterviewMessage{
							Role:    "user",
							Content: message,
						})

						// Clear input and set loading
						e.interviewInput.SetValue("")
						e.interviewLoading = true
						e.interviewSpinner.SetActive(true)

						// Send message via command
						return e, tea.Batch(
							e.sendInterviewMessageCmd(message),
							e.interviewSpinner.Start(),
						)
					}
				}
			}
			return e, nil

		case "shift+enter":
			// Insert newline in the input if input is focused
			if !e.approveButtonFocused && e.interviewInput != nil {
				e.interviewInput.InsertNewline()
				return e, nil
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

		default:
			// Forward to TextArea for text input (only if input is focused)
			if !e.approveButtonFocused && e.interviewInput != nil && !e.interviewLoading {
				updatedTextArea, cmd := e.interviewInput.Update(msg)
				*e.interviewInput = *updatedTextArea
				return e, cmd
			}
			return e, nil
		}
	}

	// Normal interview mode handling
	switch msg.String() {
	case "tab":
		// Toggle focus between viewport and input
		if !e.interviewLoading {
			e.interviewViewportFocused = !e.interviewViewportFocused
			if e.interviewInput != nil {
				if e.interviewViewportFocused {
					e.interviewInput.Blur()
				} else {
					e.interviewInput.Focus()
				}
			}
		}
		return e, nil

	case "shift+tab":
		// Same as tab in normal mode (just two states)
		if !e.interviewLoading {
			e.interviewViewportFocused = !e.interviewViewportFocused
			if e.interviewInput != nil {
				if e.interviewViewportFocused {
					e.interviewInput.Blur()
				} else {
					e.interviewInput.Focus()
				}
			}
		}
		return e, nil

	case "up":
		// Move focus up: input -> viewport
		if !e.interviewLoading && !e.interviewViewportFocused {
			e.interviewViewportFocused = true
			if e.interviewInput != nil {
				e.interviewInput.Blur()
			}
		}
		return e, nil

	case "down":
		// Move focus down: viewport -> input
		if !e.interviewLoading && e.interviewViewportFocused {
			e.interviewViewportFocused = false
			if e.interviewInput != nil {
				e.interviewInput.Focus()
			}
		}
		return e, nil

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
		if e.interviewInput != nil && !e.interviewLoading && !e.interviewViewportFocused {
			e.interviewInput.InsertNewline()
			return e, nil
		}
		return e, nil

	case "enter":
		// Send message if input not empty and input is focused
		if e.interviewInput != nil && !e.interviewLoading && !e.interviewViewportFocused {
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
		// Forward to TextArea for text input (only when input is focused)
		if e.interviewInput != nil && !e.interviewLoading && !e.interviewViewportFocused {
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
		e.approveButtonFocused = false // Start with input focused
		e.interviewViewportFocused = false
		e.infoMsg = "Review the business context. Type to request changes or navigate to button to approve."

		// Focus input for potential edits
		if e.interviewInput != nil {
			e.interviewInput.Focus()
		}

		return e, nil
	}

	// Re-focus input for next response, not viewport
	e.interviewViewportFocused = false
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
	e.approveButtonFocused = false
	e.interviewViewportFocused = false
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
		Render(fmt.Sprintf("\n🤖 AI Interview - Understanding Your Agent (%d/%d responses)", userMsgCount, max(3, userMsgCount)))

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
	// Use primary color when viewport is focused, muted when not
	borderColor := t.TextMuted()
	if e.interviewViewportFocused {
		borderColor = t.Primary()
	}

	historyStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(borderColor).
		Background(t.Background()).
		Padding(1, 1).
		Width(e.width - 4).
		Height((e.height - 24)) // Leave room for input and help

	borderedHistory := historyStyle.Render(messageHistory)

	// Input section
	inputLabel := "Your Response:"
	var help string
	var buttonLine string

	// Different UI for business context approval
	if e.awaitingBusinessCtxApproval {
		inputLabel = "Business Context (Review and Approve):"
		e.interviewInput.Placeholder = "Request changes here..."

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

		// Help text on the right
		help = lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.TextMuted()).
			Padding(1, 0).
			Render("Tab/↑↓ switch focus  Enter confirm  Shift+Enter new line  Esc cancel")

		buttonLine = lipgloss.JoinHorizontal(
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
	} else {
		help = lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.TextMuted()).
			Padding(1, 0).
			Render("Tab/↑↓ switch focus  Enter send  Shift+Enter new line  Esc cancel")

		help = lipgloss.Place(
			(e.width - 4),
			3,
			lipgloss.Right,
			lipgloss.Top,
			help,
			styles.WhitespaceStyle(t.Background()),
		)

	}

	inputLabelStyled := lipgloss.NewStyle().
		Background(t.Background()).
		Foreground(t.Accent()).
		Padding(1, 0).
		Render(inputLabel)

	var inputArea string
	if e.interviewInput != nil {
		// Determine if input is focused
		// Input is focused when:
		// - In approval mode: not on button and not on viewport
		// - In normal mode: not on viewport
		var inputFocused bool
		if e.awaitingBusinessCtxApproval {
			inputFocused = !e.approveButtonFocused && !e.interviewViewportFocused
		} else {
			inputFocused = !e.interviewViewportFocused
		}

		// Wrap input with primary-colored border only when focused
		if inputFocused {
			inputArea = lipgloss.NewStyle().
				Border(lipgloss.RoundedBorder()).
				BorderForeground(t.Primary()).
				Render(e.interviewInput.View())
		} else {
			inputArea = lipgloss.NewStyle().
				Border(lipgloss.RoundedBorder()).
				BorderForeground(t.TextMuted()).
				Render(e.interviewInput.View())
		}
	}

	// Error display
	errorLine := ""
	if e.interviewError != "" {
		errorLine = lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.Error()).
			Width(e.width/2 - 4).
			Render("⚠ " + e.interviewError)

		errorLine = lipgloss.JoinHorizontal(
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
	}

	// Completion/status message (only for generation phase, not loading)
	statusMsg := ""
	if userMsgCount >= 3 && e.interviewLoading {
		statusMsg = lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.Success()).
			Width(e.width/2 - 4).
			Bold(true).
			Render("✓ Interview complete!")

		statusMsg = lipgloss.JoinHorizontal(
			lipgloss.Top,
			lipgloss.Place(
				(e.width-4)/2,
				3,
				lipgloss.Left,
				lipgloss.Top,
				statusMsg,
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

	// Build the view
	var contentParts []string
	contentParts = append(contentParts, header, borderedHistory, inputLabelStyled, inputArea)

	if e.awaitingBusinessCtxApproval {
		// Add button line below input in approval mode
		contentParts = append(contentParts, buttonLine)
	} else if statusMsg != "" {
		contentParts = append(contentParts, statusMsg)
	} else if errorLine != "" {
		contentParts = append(contentParts, errorLine)
	} else {
		contentParts = append(contentParts, help)
	}

	content := strings.Join(contentParts, "\n")

	return content
}
