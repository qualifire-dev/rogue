package components

import (
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/glamour"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/charmbracelet/lipgloss/v2/compat"
	"github.com/rogue/tui/internal/theme"
)

// Message represents a single message in the history
type Message struct {
	Role    string // "user", "assistant", or custom role
	Content string
}

// MessageHistoryView is a reusable scrollable message display component
type MessageHistoryView struct {
	// Messages
	messages []Message

	// Layout
	width  int
	height int

	// Components
	viewport *Viewport
	focused  bool // true when focused for scrolling

	// Config
	userPrefix      string
	assistantPrefix string
	showSpinner     bool
	spinner         *Spinner

	// Markdown rendering
	renderMarkdown   bool
	markdownRenderer *glamour.TermRenderer

	// Rendering
	userColor      compat.AdaptiveColor
	assistantColor compat.AdaptiveColor
}

// NewMessageHistoryView creates a new message history viewport
func NewMessageHistoryView(id int, width, height int, t theme.Theme) *MessageHistoryView {
	viewport := NewViewport(id, width-4, height)
	viewport.WrapContent = true

	spinner := NewSpinner(id + 100)

	return &MessageHistoryView{
		messages:        make([]Message, 0),
		width:           width,
		height:          height,
		viewport:        &viewport,
		focused:         false,
		userPrefix:      "👤 You: ",
		assistantPrefix: "🤖 AI:  ",
		showSpinner:     false,
		spinner:         &spinner,
		userColor:       t.Text(), // Will use theme Primary
		assistantColor:  t.Text(), // Will use theme Accent
	}
}

// SetSize updates the component dimensions
func (m *MessageHistoryView) SetSize(width, height int) {
	m.width = width
	m.height = height
	if m.viewport != nil {
		m.viewport.Width = width - 4
		// Account for border (2) + padding (2) = 4 lines total
		m.viewport.Height = height - 4
	}
}

// SetPrefixes customizes the message prefixes
func (m *MessageHistoryView) SetPrefixes(userPrefix, assistantPrefix string) {
	m.userPrefix = userPrefix
	m.assistantPrefix = assistantPrefix
}

// SetColors customizes the message colors
func (m *MessageHistoryView) SetColors(userColor, assistantColor compat.AdaptiveColor) {
	m.userColor = userColor
	m.assistantColor = assistantColor
}

// SetMarkdownRenderer enables markdown rendering with the provided renderer
func (m *MessageHistoryView) SetMarkdownRenderer(renderer *glamour.TermRenderer) {
	m.markdownRenderer = renderer
	m.renderMarkdown = true
}

// SetRenderMarkdown enables or disables markdown rendering
func (m *MessageHistoryView) SetRenderMarkdown(enabled bool) {
	m.renderMarkdown = enabled
}

// AddMessage adds a message to the history
func (m *MessageHistoryView) AddMessage(role, content string) {
	m.messages = append(m.messages, Message{
		Role:    role,
		Content: content,
	})
}

// ClearMessages removes all messages
func (m *MessageHistoryView) ClearMessages() {
	m.messages = make([]Message, 0)
}

// GetMessages returns all messages
func (m *MessageHistoryView) GetMessages() []Message {
	return m.messages
}

// SetSpinner enables/disables the loading spinner
func (m *MessageHistoryView) SetSpinner(enabled bool) {
	m.showSpinner = enabled
	if m.spinner != nil {
		m.spinner.SetActive(enabled)
	}
}

// StartSpinner starts the spinner animation
func (m *MessageHistoryView) StartSpinner() tea.Cmd {
	m.showSpinner = true
	if m.spinner != nil {
		return m.spinner.Start()
	}
	return nil
}

// StopSpinner stops the spinner
func (m *MessageHistoryView) StopSpinner() {
	m.SetSpinner(false)
}

// IsFocused returns true if the viewport is focused for scrolling
func (m *MessageHistoryView) IsFocused() bool {
	return m.focused
}

// Focus focuses the viewport for scrolling
func (m *MessageHistoryView) Focus() {
	m.focused = true
}

// Blur removes focus from the viewport
func (m *MessageHistoryView) Blur() {
	m.focused = false
}

// ScrollUp scrolls the viewport up by n lines
func (m *MessageHistoryView) ScrollUp(lines int) {
	if m.viewport != nil {
		m.viewport.ScrollUp(lines)
	}
}

// ScrollDown scrolls the viewport down by n lines
func (m *MessageHistoryView) ScrollDown(lines int) {
	if m.viewport != nil {
		m.viewport.ScrollDown(lines)
	}
}

// AtBottom returns true if scrolled to bottom
func (m *MessageHistoryView) AtBottom() bool {
	if m.viewport != nil {
		return m.viewport.AtBottom()
	}
	return true
}

// AtTop returns true if scrolled to top
func (m *MessageHistoryView) AtTop() bool {
	if m.viewport != nil {
		return m.viewport.AtTop()
	}
	return true
}

// GotoBottom scrolls to the bottom
func (m *MessageHistoryView) GotoBottom() {
	if m.viewport != nil {
		m.viewport.GotoBottom()
	}
}

// GotoTop scrolls to the top
func (m *MessageHistoryView) GotoTop() {
	if m.viewport != nil {
		m.viewport.GotoTop()
	}
}

// Update handles messages for the history view
func (m *MessageHistoryView) Update(msg tea.Msg) tea.Cmd {
	switch msg := msg.(type) {
	case SpinnerTickMsg:
		if m.spinner != nil {
			updatedSpinner, cmd := m.spinner.Update(msg)
			*m.spinner = updatedSpinner
			return cmd
		}
	}
	return nil
}

// View renders the message history with border
func (m *MessageHistoryView) View(t theme.Theme) string {
	// Render messages
	messageLines := m.renderMessages(t)

	// Add loading spinner if enabled
	if m.showSpinner && m.spinner != nil {
		spinnerView := m.spinner.View()
		if spinnerView != "" {
			textStyle := lipgloss.NewStyle().Foreground(t.Accent()).Background(t.Background())
			loadingLine := spinnerView + textStyle.Render(" thinking...")
			messageLines = append(messageLines, loadingLine)
		}
	}

	// Update viewport content
	if m.viewport != nil {
		m.viewport.SetContent(strings.Join(messageLines, "\n"))
		// Auto-scroll to bottom when not focused
		if !m.focused {
			m.viewport.GotoBottom()
		}
	}

	messageHistory := ""
	if m.viewport != nil {
		messageHistory = m.viewport.View()
	} else {
		messageHistory = strings.Join(messageLines, "\n")
	}

	// Border color based on focus
	borderColor := t.TextMuted()
	if m.focused {
		borderColor = t.Primary()
	}

	// Calculate content height (viewport height) to prevent overflow
	// Viewport is already sized to m.height - 4 to account for border/padding
	contentHeight := m.height - 4
	if contentHeight < 0 {
		contentHeight = 0
	}

	historyStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(borderColor).
		Background(t.Background()).
		Padding(1, 1).
		Width(m.width - 4).
		Height(contentHeight)

	return historyStyle.Render(messageHistory)
}

// ViewWithoutBorder renders without the border (just the viewport content)
func (m *MessageHistoryView) ViewWithoutBorder(t theme.Theme) string {
	// Render messages
	messageLines := m.renderMessages(t)

	// Add loading spinner if enabled
	if m.showSpinner && m.spinner != nil {
		spinnerView := m.spinner.View()
		if spinnerView != "" {
			textStyle := lipgloss.NewStyle().Foreground(t.Accent()).Background(t.Background())
			loadingLine := spinnerView + textStyle.Render(" thinking...")
			messageLines = append(messageLines, loadingLine)
		}
	}

	// Update viewport content
	if m.viewport != nil {
		m.viewport.SetContent(strings.Join(messageLines, "\n"))
		// Auto-scroll to bottom when not focused
		if !m.focused {
			m.viewport.GotoBottom()
		}
		return m.viewport.View()
	}

	return strings.Join(messageLines, "\n")
}

// renderMessages renders all messages with proper formatting
func (m *MessageHistoryView) renderMessages(t theme.Theme) []string {
	var messageLines []string

	for _, msg := range m.messages {
		var prefix string
		var textStyle lipgloss.Style

		// Determine prefix and color based on role
		if msg.Role == "assistant" {
			prefix = m.assistantPrefix
			if m.assistantColor != (compat.AdaptiveColor{}) {
				textStyle = lipgloss.NewStyle().Foreground(m.assistantColor)
			} else {
				textStyle = lipgloss.NewStyle().Foreground(t.Accent())
			}
		} else if msg.Role == "system" {
			// System messages use success/muted color
			prefix = m.assistantPrefix
			textStyle = lipgloss.NewStyle().Foreground(t.Success())
		} else {
			// Default to user style
			prefix = m.userPrefix
			if m.userColor != (compat.AdaptiveColor{}) {
				textStyle = lipgloss.NewStyle().Foreground(m.userColor)
			} else {
				textStyle = lipgloss.NewStyle().Foreground(t.Primary())
			}
		}

		// Check if we should render as markdown for assistant messages
		if m.renderMarkdown && m.markdownRenderer != nil && msg.Role == "assistant" {
			// Render markdown content
			rendered, err := m.markdownRenderer.Render(msg.Content)
			if err != nil {
				// Fall back to plain text if markdown rendering fails
				rendered = msg.Content
			}

			// Split rendered content into lines and add prefix to first line only
			lines := strings.Split(strings.TrimRight(rendered, "\n"), "\n")
			if len(lines) > 0 {
				// First line with prefix
				messageLines = append(messageLines, prefix+lines[0])
				// Remaining lines without prefix but with indentation
				prefixVisualWidth := calculateVisualWidth(prefix)
				indentation := strings.Repeat(" ", prefixVisualWidth)
				for _, line := range lines[1:] {
					messageLines = append(messageLines, indentation+line)
				}
			}
		} else {
			// Regular text rendering (existing logic)
			// Calculate visual width of prefix (accounting for emojis)
			// Emojis typically take 2 visual columns in terminals
			prefixVisualWidth := calculateVisualWidth(prefix)
			availableWidth := m.width - prefixVisualWidth - 8
			if availableWidth < 40 {
				availableWidth = 40
			}

			// Create indentation string matching prefix visual width
			indentation := strings.Repeat(" ", prefixVisualWidth)

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
					// Continuation lines with indentation matching prefix width
					messageLines = append(messageLines, textStyle.Render(indentation+line))
				}
			}
		}

		messageLines = append(messageLines, "") // Blank line between messages
	}

	return messageLines
}

// calculateVisualWidth returns the visual width of a string in terminal columns
// accounting for emojis and other wide characters
func calculateVisualWidth(s string) int {
	width := 0
	for _, r := range s {
		// Emojis and wide unicode characters typically take 2 columns
		// Simple heuristic: if rune is > 0x1F300, it's likely an emoji
		if r >= 0x1F300 && r <= 0x1FAFF {
			width += 2
		} else {
			width += 1
		}
	}
	return width
}
