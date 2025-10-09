package components

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/styles"
	"github.com/rogue/tui/internal/theme"
)

// ChatMessage represents a single message in the chat
type ChatMessage struct {
	Role    string // "user" or "assistant"
	Content string
}

// ChatView is a reusable chat component with message history and input
type ChatView struct {
	// Messages
	messages []ChatMessage

	// Layout
	width  int
	height int

	// Components
	viewport        *Viewport
	input           *TextArea
	spinner         *Spinner
	viewportFocused bool // true when viewport is focused for scrolling

	// State
	loading      bool
	errorMessage string

	// Config
	userPrefix       string
	assistantPrefix  string
	inputLabel       string
	inputPlaceholder string
	showProgressBar  bool
	maxResponses     int // For progress display (0 = no limit)
	baseID           int // Base ID for sub-components
}

// NewChatView creates a new chat view component
func NewChatView(id int, width, height int, t theme.Theme) *ChatView {
	viewport := NewViewport(id, width-4, height-24)
	viewport.WrapContent = true

	input := NewTextArea(id+100, width-6, 4, t)
	input.Placeholder = "Type your message..."
	input.ShowLineNumbers = false // Disable line numbers for chat input
	input.Focus()

	spinner := NewSpinner(id + 200)

	return &ChatView{
		messages:         make([]ChatMessage, 0),
		width:            width,
		height:           height,
		viewport:         &viewport,
		input:            &input,
		spinner:          &spinner,
		viewportFocused:  false,
		loading:          false,
		errorMessage:     "",
		userPrefix:       "👤 You: ",
		assistantPrefix:  "🤖 AI:  ",
		inputLabel:       "Your Response:",
		inputPlaceholder: "Type your message...",
		showProgressBar:  false,
		maxResponses:     0,
		baseID:           id,
	}
}

// SetSize updates the component dimensions
func (c *ChatView) SetSize(width, height int) {
	c.width = width
	c.height = height
	if c.viewport != nil {
		c.viewport.Width = width - 4
		c.viewport.Height = height - 24
	}
	if c.input != nil {
		c.input.Width = width - 4
	}
}

// SetPrefixes customizes the message prefixes
func (c *ChatView) SetPrefixes(userPrefix, assistantPrefix string) {
	c.userPrefix = userPrefix
	c.assistantPrefix = assistantPrefix
}

// SetInputLabel customizes the input label
func (c *ChatView) SetInputLabel(label string) {
	c.inputLabel = label
}

// SetInputPlaceholder customizes the input placeholder
func (c *ChatView) SetInputPlaceholder(placeholder string) {
	c.inputPlaceholder = placeholder
	if c.input != nil {
		c.input.Placeholder = placeholder
	}
}

// SetProgressBar enables/disables progress display
func (c *ChatView) SetProgressBar(enabled bool, maxResponses int) {
	c.showProgressBar = enabled
	c.maxResponses = maxResponses
}

// AddMessage adds a message to the chat history
func (c *ChatView) AddMessage(role, content string) {
	c.messages = append(c.messages, ChatMessage{
		Role:    role,
		Content: content,
	})
}

// ClearMessages removes all messages
func (c *ChatView) ClearMessages() {
	c.messages = make([]ChatMessage, 0)
}

// GetMessages returns all messages
func (c *ChatView) GetMessages() []ChatMessage {
	return c.messages
}

// GetError returns the current error message
func (c *ChatView) GetError() string {
	return c.errorMessage
}

// SetLoading sets the loading state
func (c *ChatView) SetLoading(loading bool) {
	c.loading = loading
	if c.spinner != nil {
		c.spinner.SetActive(loading)
	}
}

// StartSpinner starts the spinner animation
func (c *ChatView) StartSpinner() tea.Cmd {
	if c.spinner != nil {
		return c.spinner.Start()
	}
	return nil
}

// IsLoading returns the loading state
func (c *ChatView) IsLoading() bool {
	return c.loading
}

// SetError sets an error message
func (c *ChatView) SetError(err string) {
	c.errorMessage = err
}

// ClearError clears the error message
func (c *ChatView) ClearError() {
	c.errorMessage = ""
}

// GetInputValue returns the current input value
func (c *ChatView) GetInputValue() string {
	if c.input != nil {
		return c.input.GetValue()
	}
	return ""
}

// ClearInput clears the input field
func (c *ChatView) ClearInput() {
	if c.input != nil {
		c.input.SetValue("")
	}
}

// IsViewportFocused returns true if viewport is focused
func (c *ChatView) IsViewportFocused() bool {
	return c.viewportFocused
}

// FocusViewport focuses the viewport for scrolling
func (c *ChatView) FocusViewport() {
	c.viewportFocused = true
	if c.input != nil {
		c.input.Blur()
	}
}

// FocusInput focuses the input field
func (c *ChatView) FocusInput() {
	c.viewportFocused = false
	if c.input != nil {
		c.input.Focus()
	}
}

// Update handles keyboard input for the chat view
func (c *ChatView) Update(msg tea.Msg) tea.Cmd {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		return c.handleKeyPress(msg)
	case SpinnerTickMsg:
		if c.spinner != nil {
			updatedSpinner, cmd := c.spinner.Update(msg)
			*c.spinner = updatedSpinner
			return cmd
		}
	}
	return nil
}

// handleKeyPress processes keyboard input
func (c *ChatView) handleKeyPress(msg tea.KeyMsg) tea.Cmd {
	switch msg.String() {
	case "tab", "shift+tab":
		// Toggle focus between viewport and input
		if !c.loading {
			c.viewportFocused = !c.viewportFocused
			if c.input != nil {
				if c.viewportFocused {
					c.input.Blur()
				} else {
					c.input.Focus()
				}
			}
		}
		return nil

	case "up":
		// When viewport is focused: scroll up
		// When input is focused: move focus to viewport
		if !c.loading {
			if c.viewportFocused {
				// Scroll viewport up
				if c.viewport != nil {
					c.viewport.ScrollUp(1)
				}
			} else {
				// Move focus to viewport
				c.viewportFocused = true
				if c.input != nil {
					c.input.Blur()
				}
			}
		}
		return nil

	case "down":
		// When viewport is focused: scroll down or move to input if at bottom
		if !c.loading {
			if c.viewportFocused {
				// Check if viewport is at bottom
				if c.viewport != nil && c.viewport.AtBottom() {
					// At bottom - shift focus to input
					c.viewportFocused = false
					if c.input != nil {
						c.input.Focus()
					}
				} else if c.viewport != nil {
					// Not at bottom - scroll down
					c.viewport.ScrollDown(1)
				}
			}
		}
		return nil

	case "shift+enter":
		// Insert newline in the input
		if c.input != nil && !c.loading && !c.viewportFocused {
			c.input.InsertNewline()
			return nil
		}
		return nil

	default:
		// Forward to TextArea for text input (only when input is focused)
		if c.input != nil && !c.loading && !c.viewportFocused {
			updatedTextArea, cmd := c.input.Update(msg)
			*c.input = *updatedTextArea
			return cmd
		}
		return nil
	}
}

// ViewWithoutHelp renders the chat view without the help/error section at the bottom
// Useful when you want to add custom UI elements below the chat
func (c *ChatView) ViewWithoutHelp(t theme.Theme) string {
	return c.renderChatContent(t, false)
}

// View renders the chat view
func (c *ChatView) View(t theme.Theme) string {
	return c.renderChatContent(t, true)
}

// renderChatContent renders the chat view with optional help section
func (c *ChatView) renderChatContent(t theme.Theme, includeHelp bool) string {
	// Calculate message count (user messages only)
	userMsgCount := 0
	for _, msg := range c.messages {
		if msg.Role == "user" {
			userMsgCount++
		}
	}

	// Header with optional progress
	var header string
	if c.showProgressBar && c.maxResponses > 0 {
		header = lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.Primary()).
			Bold(true).
			Render(fmt.Sprintf("\n🤖 Chat (%d/%d responses)", userMsgCount, max(c.maxResponses, userMsgCount)))
	} else {
		header = lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.Primary()).
			Bold(true).
			Render("\n🤖 Chat")
	}

	// Render message history
	messageLines := c.renderMessages(t)

	// Add loading indicator with spinner if loading
	if c.loading {
		spinnerView := c.spinner.View()
		if spinnerView != "" {
			textStyle := lipgloss.NewStyle().Foreground(t.Accent()).Background(t.Background())
			loadingLine := spinnerView + textStyle.Render(" thinking...")
			messageLines = append(messageLines, loadingLine)
		}
	}

	// Update viewport with message history
	messageHistory := ""
	if c.viewport != nil {
		c.viewport.SetContent(strings.Join(messageLines, "\n"))
		// Only auto-scroll to bottom when viewport is not manually focused
		if !c.viewportFocused {
			c.viewport.GotoBottom()
		}
		messageHistory = c.viewport.View()
	} else {
		messageHistory = strings.Join(messageLines, "\n")
	}

	// Message history section with border
	borderColor := t.TextMuted()
	if c.viewportFocused {
		borderColor = t.Primary()
	}

	historyStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(borderColor).
		Background(t.Background()).
		Padding(1, 1).
		Width(c.width - 4).
		Height(c.height - 24)

	borderedHistory := historyStyle.Render(messageHistory)

	// Input section
	inputLabelStyled := lipgloss.NewStyle().
		Background(t.Background()).
		Foreground(t.Accent()).
		Padding(1, 0).
		Render(c.inputLabel)

	// Input area with focus-dependent border
	var inputArea string
	if c.input != nil {
		inputFocused := !c.viewportFocused
		borderColor := t.TextMuted()
		if inputFocused {
			borderColor = t.Primary()
		}

		inputArea = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(borderColor).
			Render(c.input.View())
	}

	// Build the view
	var contentParts []string
	contentParts = append(contentParts, header, borderedHistory, inputLabelStyled, inputArea)

	// Only add help/error section if requested
	if includeHelp {
		// Help text - context-aware based on focus
		var helpText string
		if c.viewportFocused {
			helpText = "↑↓ scroll  Tab switch focus"
		} else {
			helpText = "↑ to scroll history  Tab switch focus  Enter send  Shift+Enter new line"
		}
		help := lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.TextMuted()).
			Padding(1, 0).
			Render(helpText)

		help = lipgloss.Place(
			c.width-4,
			3,
			lipgloss.Right,
			lipgloss.Top,
			help,
			styles.WhitespaceStyle(t.Background()),
		)

		// Error display
		errorLine := ""
		if c.errorMessage != "" {
			errorLine = lipgloss.NewStyle().
				Background(t.Background()).
				Foreground(t.Error()).
				Padding(1, 0).
				Render("⚠ " + c.errorMessage)
		}

		if errorLine != "" {
			contentParts = append(contentParts, errorLine)
		} else {
			contentParts = append(contentParts, help)
		}
	}

	return strings.Join(contentParts, "\n")
}

// renderMessages renders all messages with proper formatting
func (c *ChatView) renderMessages(t theme.Theme) []string {
	var messageLines []string

	for _, msg := range c.messages {
		var prefix string
		var textStyle lipgloss.Style

		if msg.Role == "assistant" {
			textStyle = lipgloss.NewStyle().Foreground(t.Accent())
			prefix = c.assistantPrefix
		} else {
			textStyle = lipgloss.NewStyle().Foreground(t.Primary())
			prefix = c.userPrefix
		}

		// Calculate available width for text
		visualPrefixWidth := 8
		availableWidth := c.width - visualPrefixWidth - 8
		if availableWidth < 40 {
			availableWidth = 40
		}

		// Preserve newlines by processing each paragraph separately
		paragraphs := strings.Split(msg.Content, "\n")
		var allLines []string
		for _, para := range paragraphs {
			if strings.TrimSpace(para) == "" {
				allLines = append(allLines, "")
			} else {
				wrapped := wrapText(para, availableWidth)
				allLines = append(allLines, strings.Split(wrapped, "\n")...)
			}
		}

		for i, line := range allLines {
			if i == 0 {
				// First line with prefix
				messageLines = append(messageLines, textStyle.Render(prefix+line))
			} else {
				// Continuation lines with indentation
				messageLines = append(messageLines, textStyle.Render("        "+line))
			}
		}
		messageLines = append(messageLines, "") // Blank line between messages
	}

	return messageLines
}
