package components

import (
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/glamour"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/styles"
	"github.com/rogue/tui/internal/theme"
)

// ChatView is a reusable chat component with message history and input
type ChatView struct {
	// Layout
	width  int
	height int

	// Components
	messageHistory *MessageHistoryView
	input          *TextArea

	// State
	errorMessage string

	// Config
	inputLabel       string
	inputPlaceholder string
	showHeader       bool
	headerText       string
	baseID           int // Base ID for sub-components
}

// NewChatView creates a new chat view component
func NewChatView(id int, width, height int, t theme.Theme) *ChatView {
	// Create message history view
	messageHistory := NewMessageHistoryView(id, width, height-24, t)

	// Create input
	input := NewTextArea(id+100, width-6, 4, t)
	input.Placeholder = "Type your message..."
	input.ShowLineNumbers = false // Disable line numbers for chat input
	input.Focus()

	return &ChatView{
		width:            width,
		height:           height,
		messageHistory:   messageHistory,
		input:            &input,
		errorMessage:     "",
		inputLabel:       "Your Response:",
		inputPlaceholder: "Type your message...",
		showHeader:       false,
		headerText:       "",
		baseID:           id,
	}
}

// SetSize updates the component dimensions
func (c *ChatView) SetSize(width, height int) {
	c.width = width
	c.height = height
	if c.messageHistory != nil {
		c.messageHistory.SetSize(width, height-24)
	}
	if c.input != nil {
		c.input.Width = width - 4
	}
}

// SetPrefixes customizes the message prefixes
func (c *ChatView) SetPrefixes(userPrefix, assistantPrefix string) {
	if c.messageHistory != nil {
		c.messageHistory.SetPrefixes(userPrefix, assistantPrefix)
	}
}

// SetMarkdownRenderer enables markdown rendering with the provided renderer
func (c *ChatView) SetMarkdownRenderer(renderer *glamour.TermRenderer) {
	if c.messageHistory != nil {
		c.messageHistory.SetMarkdownRenderer(renderer)
	}
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

// SetHeader sets a custom header text for the chat view
func (c *ChatView) SetHeader(text string) {
	c.showHeader = text != ""
	c.headerText = text
}

// HideHeader hides the header
func (c *ChatView) HideHeader() {
	c.showHeader = false
	c.headerText = ""
}

// AddMessage adds a message to the chat history
func (c *ChatView) AddMessage(role, content string) {
	if c.messageHistory != nil {
		c.messageHistory.AddMessage(role, content)
	}
}

// ClearMessages removes all messages
func (c *ChatView) ClearMessages() {
	if c.messageHistory != nil {
		c.messageHistory.ClearMessages()
	}
}

// GetMessages returns all messages
func (c *ChatView) GetMessages() []Message {
	if c.messageHistory != nil {
		return c.messageHistory.GetMessages()
	}
	return []Message{}
}

// GetError returns the current error message
func (c *ChatView) GetError() string {
	return c.errorMessage
}

// SetLoading sets the loading state
func (c *ChatView) SetLoading(loading bool) {
	if c.messageHistory != nil {
		c.messageHistory.SetSpinner(loading)
	}
}

// StartSpinner starts the spinner animation
func (c *ChatView) StartSpinner() tea.Cmd {
	if c.messageHistory != nil {
		return c.messageHistory.StartSpinner()
	}
	return nil
}

// IsLoading returns the loading state
func (c *ChatView) IsLoading() bool {
	if c.messageHistory != nil {
		return c.messageHistory.showSpinner
	}
	return false
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
	if c.messageHistory != nil {
		return c.messageHistory.IsFocused()
	}
	return false
}

// IsViewportFocused returns true if viewport is focused
func (c *ChatView) IsInputFocused() bool {
	if c.input != nil {
		return c.input.IsFocused()
	}
	return false
}

// FocusViewport focuses the viewport for scrolling
func (c *ChatView) FocusViewport() {
	if c.messageHistory != nil {
		c.messageHistory.Focus()
	}
	if c.input != nil {
		c.input.Blur()
	}
}

// FocusInput focuses the input field
func (c *ChatView) FocusInput() {
	if c.messageHistory != nil {
		c.messageHistory.Blur()
	}
	if c.input != nil {
		c.input.Focus()
	}
}

// Update handles keyboard input for the chat view
func (c *ChatView) Update(msg tea.Msg) tea.Cmd {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		return c.handleKeyPress(msg)
	case tea.PasteMsg:
		// Forward paste to input if not loading and not scrolling
		if c.input != nil && !c.IsLoading() && c.IsInputFocused() {
			updatedTextArea, cmd := c.input.Update(msg)
			*c.input = *updatedTextArea
			return cmd
		}
		return nil
	case SpinnerTickMsg:
		if c.messageHistory != nil {
			return c.messageHistory.Update(msg)
		}
	}
	return nil
}

// handleKeyPress processes keyboard input
func (c *ChatView) handleKeyPress(msg tea.KeyMsg) tea.Cmd {
	switch msg.String() {
	case "tab", "shift+tab":
		// Toggle focus between viewport and input
		if !c.IsLoading() {
			if c.IsViewportFocused() {
				c.FocusInput()
			} else {
				c.FocusViewport()
			}
		}
		return nil

	case "up":
		// When viewport is focused: scroll up
		// When input is focused: move focus to viewport
		if !c.IsLoading() {
			if c.IsViewportFocused() {
				// Scroll viewport up
				if c.messageHistory != nil {
					c.messageHistory.ScrollUp(1)
				}
			} else {
				// Move focus to viewport
				c.FocusViewport()
			}
		}
		return nil

	case "down":
		// When viewport is focused: scroll down or move to input if at bottom
		if !c.IsLoading() {
			if c.IsViewportFocused() {
				// Check if viewport is at bottom
				if c.messageHistory != nil && !c.messageHistory.AtBottom() {
					// Not at bottom - scroll down
					c.messageHistory.ScrollDown(1)
				} else {
					// At bottom or messageHistory is nil - shift focus to input
					c.FocusInput()
				}
			}
		}
		return nil

	case "shift+enter":
		// Insert newline in the input
		if c.input != nil && !c.IsLoading() && c.IsInputFocused() {
			c.input.InsertNewline()
			return nil
		}
		return nil

	default:
		// Forward to TextArea for text input (only when input is focused)
		if c.input != nil && !c.IsLoading() && c.IsInputFocused() {
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
	// Header (optional)
	var header string
	if c.showHeader {
		header = lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.Primary()).
			Bold(true).
			Render("\n" + c.headerText)
	}

	// Render message history using MessageHistoryView
	var borderedHistory string
	if c.messageHistory != nil {
		borderedHistory = c.messageHistory.View(t)
	}

	// Input section
	inputLabelStyled := lipgloss.NewStyle().
		Background(t.Background()).
		Foreground(t.Accent()).
		Padding(1, 0).
		Render(c.inputLabel)

	// Input area with focus-dependent border
	var inputArea string
	if c.input != nil {
		borderColor := t.TextMuted()
		if c.IsInputFocused() {
			borderColor = t.Primary()
		}

		inputArea = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(borderColor).
			Render(c.input.View())
	}

	// Build the view
	contentParts := make([]string, 0, 5)
	if c.showHeader && header != "" {
		contentParts = append(contentParts, header)
	}
	contentParts = append(contentParts, borderedHistory, inputLabelStyled, inputArea)

	// Only add help/error section if requested
	if includeHelp {
		// Help text - context-aware based on focus
		var helpText string
		if c.IsViewportFocused() {
			helpText = "↑↓ scroll  Tab switch focus"
		} else {
			helpText = "↑ to scroll history  Tab switch focus  Enter send  Shift+Enter new line"
		}
		helpStyle := lipgloss.NewStyle().
			Background(t.Background()).
			Foreground(t.TextMuted()).
			Padding(1, 0).
			Render(helpText)

		help := lipgloss.Place(
			c.width-4,
			3,
			lipgloss.Right,
			lipgloss.Top,
			helpStyle,
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
