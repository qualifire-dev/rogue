package components

import (
	"fmt"
	"strings"
	"unicode"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// TextAreaKeyMap defines the keybindings for the textarea
type TextAreaKeyMap struct {
	CharacterBackward       []string
	CharacterForward        []string
	DeleteAfterCursor       []string
	DeleteBeforeCursor      []string
	DeleteCharacterBackward []string
	DeleteCharacterForward  []string
	DeleteWordBackward      []string
	DeleteWordForward       []string
	InsertNewline           []string
	LineEnd                 []string
	LineNext                []string
	LinePrevious            []string
	LineStart               []string
	WordBackward            []string
	WordForward             []string
	InputBegin              []string
	InputEnd                []string
}

// DefaultTextAreaKeyMap returns a set of default keybindings for text editing
func DefaultTextAreaKeyMap() TextAreaKeyMap {
	return TextAreaKeyMap{
		CharacterForward:        []string{"right", "ctrl+f"},
		CharacterBackward:       []string{"left", "ctrl+b"},
		WordForward:             []string{"alt+right", "alt+f"},
		WordBackward:            []string{"alt+left", "alt+b"},
		LineNext:                []string{"down", "ctrl+n"},
		LinePrevious:            []string{"up", "ctrl+p"},
		DeleteWordBackward:      []string{"alt+backspace", "ctrl+w"},
		DeleteWordForward:       []string{"alt+delete", "alt+d"},
		DeleteAfterCursor:       []string{"ctrl+k"},
		DeleteBeforeCursor:      []string{"ctrl+u"},
		InsertNewline:           []string{"enter", "ctrl+m"},
		DeleteCharacterBackward: []string{"backspace", "ctrl+h"},
		DeleteCharacterForward:  []string{"delete", "ctrl+d"},
		LineStart:               []string{"home", "ctrl+a", "cmd+left"},
		LineEnd:                 []string{"end", "ctrl+e", "cmd+right"},
		InputBegin:              []string{"alt+<", "ctrl+home"},
		InputEnd:                []string{"alt+>", "ctrl+end"},
	}
}

// TextAreaStyle defines the styling for the textarea
type TextAreaStyle struct {
	Base        lipgloss.Style
	Text        lipgloss.Style
	Cursor      lipgloss.Style
	Placeholder lipgloss.Style
	Panel       lipgloss.Style // For background panel and padding
}

// DefaultTextAreaStyle returns default styles for the textarea
func DefaultTextAreaStyle(th theme.Theme) TextAreaStyle {
	return TextAreaStyle{
		Base:        lipgloss.NewStyle().Background(th.BackgroundPanel()),
		Text:        lipgloss.NewStyle().Background(th.BackgroundPanel()),
		Cursor:      lipgloss.NewStyle().Background(th.Primary()),
		Placeholder: lipgloss.NewStyle().Foreground(th.TextMuted()).Background(th.BackgroundPanel()),
		Panel:       lipgloss.NewStyle().Padding(1, 2).Background(th.BackgroundPanel()),
	}
}

// ApplyTheme applies theme-based styling to the textarea
func (t *TextArea) ApplyTheme(th theme.Theme) {
	t.Style.Panel = lipgloss.NewStyle().
		Background(th.BackgroundPanel()).
		Padding(1, 2)
	t.Style.Cursor = lipgloss.NewStyle().
		Background(th.Primary()).
		Foreground(th.Background())
	t.Style.Text = lipgloss.NewStyle().
		Foreground(th.Text())
	t.Style.Placeholder = lipgloss.NewStyle().
		Foreground(th.TextMuted())
}

// TextArea represents a multi-line text input component
type TextArea struct {
	ID              int
	Width           int
	Height          int
	KeyMap          TextAreaKeyMap
	Style           TextAreaStyle
	Placeholder     string
	CharLimit       int
	MaxHeight       int
	MaxWidth        int
	ShowLineNumbers bool
	Prompt          string
	PromptWidth     int

	// Internal state
	value         [][]rune
	row           int
	col           int
	focus         bool
	cursorVisible bool
	cursorBlink   bool
	viewport      *Viewport
}

// NewTextArea creates a new textarea with the given width and height
func NewTextArea(id int, width, height int, th theme.Theme) TextArea {
	vp := NewViewport(id+1000, width, height) // Use different ID to avoid conflicts
	// Disable viewport key mappings to prevent conflicts with text input
	vp.KeyMap = ViewportKeyMap{}

	return TextArea{
		ID:              id,
		Width:           width,
		Height:          height,
		KeyMap:          DefaultTextAreaKeyMap(),
		Style:           DefaultTextAreaStyle(th),
		CharLimit:       0, // No limit
		MaxHeight:       1000,
		MaxWidth:        500,
		ShowLineNumbers: true, // Enable line numbers by default
		Prompt:          "",
		PromptWidth:     0,
		value:           make([][]rune, 1),
		row:             0,
		col:             0,
		focus:           true,
		cursorVisible:   true,
		cursorBlink:     false,
		viewport:        &vp,
	}
}

// SetSize sets the textarea's width and height
func (t *TextArea) SetSize(width, height int) {
	t.Width = width
	t.Height = height
	if t.viewport != nil {
		t.viewport.SetSize(width, height)
	}
}

// SetValue sets the textarea's content
func (t *TextArea) SetValue(s string) {
	t.Reset()
	t.InsertString(s)
	t.SetCursor(0, 0) // Reset cursor to beginning
	t.updateViewport()
}

// GetValue returns the textarea's content as a string
func (t *TextArea) GetValue() string {
	if len(t.value) == 0 {
		return ""
	}

	var result strings.Builder
	for i, line := range t.value {
		if i > 0 {
			result.WriteRune('\n')
		}
		result.WriteString(string(line))
	}
	return result.String()
}

// InsertString inserts a string at the cursor position
func (t *TextArea) InsertString(s string) {
	runes := []rune(s)
	t.insertRunes(runes)
}

// InsertRune inserts a single rune at the cursor position
func (t *TextArea) InsertRune(r rune) {
	t.insertRunes([]rune{r})
}

// insertRunes inserts runes at the current cursor position
func (t *TextArea) insertRunes(runes []rune) {
	// Check character limit
	if t.CharLimit > 0 {
		currentLength := t.Length()
		if currentLength+len(runes) > t.CharLimit {
			// Truncate to fit within limit
			allowed := t.CharLimit - currentLength
			if allowed <= 0 {
				return
			}
			runes = runes[:allowed]
		}
	}

	// Split runes by newlines
	var lines [][]rune
	lineStart := 0
	for idx, r := range runes {
		if r == '\n' {
			lines = append(lines, runes[lineStart:idx])
			lineStart = idx + 1
		}
	}
	if lineStart < len(runes) {
		lines = append(lines, runes[lineStart:])
	}

	if len(lines) == 0 {
		return
	}

	// Save the remainder of the current line
	var tail []rune
	if t.col < len(t.value[t.row]) {
		tail = make([]rune, len(t.value[t.row][t.col:]))
		copy(tail, t.value[t.row][t.col:])
	}

	// Insert the first line at cursor position
	t.value[t.row] = append(t.value[t.row][:t.col], lines[0]...)
	t.col += len(lines[0])

	// Handle additional lines
	if len(lines) > 1 {
		// Check height limit
		if t.MaxHeight > 0 && len(t.value)+len(lines)-1 > t.MaxHeight {
			allowedLines := t.MaxHeight - len(t.value) + 1
			if allowedLines <= 0 {
				return
			}
			lines = lines[:allowedLines]
		}

		// Insert new lines
		newValue := make([][]rune, len(t.value)+len(lines)-1)
		copy(newValue, t.value[:t.row+1])

		for _, line := range lines[1:] {
			t.row++
			newValue[t.row] = line
			t.col = len(line)
		}

		// Copy remaining lines
		if t.row+1 < len(t.value) {
			copy(newValue[t.row+1:], t.value[t.row+1:])
		}
		t.value = newValue
	}

	// Add the tail to the last line
	t.value[t.row] = append(t.value[t.row], tail...)

	// Update viewport after content change
	t.updateViewport()
}

// Length returns the total number of characters in the textarea
func (t *TextArea) Length() int {
	total := 0
	for _, line := range t.value {
		total += len(line)
	}
	// Add newline characters
	return total + len(t.value) - 1
}

// LineCount returns the number of lines
func (t *TextArea) LineCount() int {
	return len(t.value)
}

// SetCursor sets the cursor position
func (t *TextArea) SetCursor(row, col int) {
	if row < 0 {
		row = 0
	}
	if row >= len(t.value) {
		row = len(t.value) - 1
	}
	if row < 0 {
		row = 0
	}

	if col < 0 {
		col = 0
	}
	if col > len(t.value[row]) {
		col = len(t.value[row])
	}

	t.row = row
	t.col = col
	t.scrollToCursor()
}

// GetCursor returns the current cursor position
func (t *TextArea) GetCursor() (row, col int) {
	return t.row, t.col
}

// Focus sets the focus state
func (t *TextArea) Focus() {
	t.focus = true
}

// Blur removes the focus state
func (t *TextArea) Blur() {
	t.focus = false
}

// IsFocused returns whether the textarea is focused
func (t *TextArea) IsFocused() bool {
	return t.focus
}

// SetShowLineNumbers enables or disables line numbers
func (t *TextArea) SetShowLineNumbers(show bool) {
	t.ShowLineNumbers = show
	t.updateViewport()
}

// Reset clears the textarea content
func (t *TextArea) Reset() {
	t.value = make([][]rune, 1)
	t.row = 0
	t.col = 0
	if t.viewport != nil {
		t.viewport.GotoTop()
	}
	t.updateViewport()
}

// updateViewport updates the viewport content and ensures cursor is visible
func (t *TextArea) updateViewport() {
	if t.viewport == nil {
		return
	}

	// Calculate content area (subtract padding from total size)
	contentWidth := t.Width - 4   // 2 padding on each side
	contentHeight := t.Height - 2 // 1 padding on top and bottom

	// Account for line numbers if enabled
	if t.ShowLineNumbers {
		lineNumWidth := t.getLineNumberWidth()
		contentWidth -= lineNumWidth + 1 // +1 for space after line numbers
	}

	// Update viewport size to match content area
	t.viewport.SetSize(contentWidth, contentHeight)

	// Build content string for viewport
	var lines []string
	for i, line := range t.value {
		lineStr := string(line)

		// Add prompt if specified
		if t.Prompt != "" {
			lineStr = t.Prompt + lineStr
		}

		// Add line number if enabled
		if t.ShowLineNumbers {
			lineNumStr := t.formatLineNumber(i + 1)
			lineStr = lineNumStr + lineStr
		}

		lines = append(lines, lineStr)
	}

	content := strings.Join(lines, "\n")
	t.viewport.SetContent(content)

	// Auto-scroll to keep cursor visible
	t.scrollToCursor()
}

// scrollToCursor ensures the cursor is visible in the viewport
func (t *TextArea) scrollToCursor() {
	if t.viewport == nil {
		return
	}

	// Calculate which line the cursor is on
	cursorLine := t.row

	// Get current viewport position
	currentTop := t.viewport.YOffset
	currentBottom := currentTop + t.viewport.Height - 1

	// Check if cursor is outside visible area
	if cursorLine < currentTop {
		// Cursor is above visible area, scroll up
		t.viewport.SetYOffset(cursorLine)
	} else if cursorLine > currentBottom {
		// Cursor is below visible area, scroll down
		t.viewport.SetYOffset(cursorLine - t.viewport.Height + 1)
	}
}

// characterRight moves cursor one character to the right
func (t *TextArea) characterRight() {
	if t.col < len(t.value[t.row]) {
		t.col++
	} else if t.row < len(t.value)-1 {
		t.row++
		t.col = 0
	}
	t.scrollToCursor()
}

// characterLeft moves cursor one character to the left
func (t *TextArea) characterLeft() {
	if t.col > 0 {
		t.col--
	} else if t.row > 0 {
		t.row--
		t.col = len(t.value[t.row])
	}
	t.scrollToCursor()
}

// lineDown moves cursor down one line
func (t *TextArea) lineDown() {
	if t.row < len(t.value)-1 {
		t.row++
		if t.col > len(t.value[t.row]) {
			t.col = len(t.value[t.row])
		}
	}
	t.scrollToCursor()
}

// lineUp moves cursor up one line
func (t *TextArea) lineUp() {
	if t.row > 0 {
		t.row--
		if t.col > len(t.value[t.row]) {
			t.col = len(t.value[t.row])
		}
	}
	t.scrollToCursor()
}

// wordRight moves cursor one word to the right
func (t *TextArea) wordRight() {
	// Skip spaces
	for t.col < len(t.value[t.row]) && unicode.IsSpace(t.value[t.row][t.col]) {
		t.col++
	}

	// Skip word characters
	for t.col < len(t.value[t.row]) && !unicode.IsSpace(t.value[t.row][t.col]) {
		t.col++
	}
	t.scrollToCursor()
}

// wordLeft moves cursor one word to the left
func (t *TextArea) wordLeft() {
	// Skip spaces
	for t.col > 0 && unicode.IsSpace(t.value[t.row][t.col-1]) {
		t.col--
	}

	// Skip word characters
	for t.col > 0 && !unicode.IsSpace(t.value[t.row][t.col-1]) {
		t.col--
	}
	t.scrollToCursor()
}

// deleteCharacterBackward deletes the character before the cursor
func (t *TextArea) deleteCharacterBackward() {
	if t.col > 0 {
		t.value[t.row] = append(t.value[t.row][:t.col-1], t.value[t.row][t.col:]...)
		t.col--
	} else if t.row > 0 {
		// Merge with previous line
		prevLineLen := len(t.value[t.row-1])
		t.value[t.row-1] = append(t.value[t.row-1], t.value[t.row]...)

		// Remove current line
		t.value = append(t.value[:t.row], t.value[t.row+1:]...)
		t.row--
		t.col = prevLineLen
	}
	t.updateViewport()
}

// deleteCharacterForward deletes the character after the cursor
func (t *TextArea) deleteCharacterForward() {
	if t.col < len(t.value[t.row]) {
		t.value[t.row] = append(t.value[t.row][:t.col], t.value[t.row][t.col+1:]...)
	} else if t.row < len(t.value)-1 {
		// Merge with next line
		t.value[t.row] = append(t.value[t.row], t.value[t.row+1]...)

		// Remove next line
		t.value = append(t.value[:t.row+1], t.value[t.row+2:]...)
	}
	t.updateViewport()
}

// deleteWordBackward deletes the word before the cursor
func (t *TextArea) deleteWordBackward() {
	oldCol := t.col

	// Move to start of word
	t.wordLeft()

	// Delete from word start to old position
	if t.col < oldCol {
		t.value[t.row] = append(t.value[t.row][:t.col], t.value[t.row][oldCol:]...)
	}
	t.updateViewport()
}

// deleteWordForward deletes the word after the cursor
func (t *TextArea) deleteWordForward() {
	oldCol := t.col

	// Move to end of word
	t.wordRight()

	// Delete from old position to word end
	if t.col > oldCol {
		t.value[t.row] = append(t.value[t.row][:oldCol], t.value[t.row][t.col:]...)
		t.col = oldCol
	}
	t.updateViewport()
}

// insertNewline inserts a newline at cursor position
func (t *TextArea) insertNewline() {
	if t.MaxHeight > 0 && len(t.value) >= t.MaxHeight {
		return
	}

	// Split current line
	head := make([]rune, t.col)
	copy(head, t.value[t.row][:t.col])
	tail := make([]rune, len(t.value[t.row][t.col:]))
	copy(tail, t.value[t.row][t.col:])

	// Update current line
	t.value[t.row] = head

	// Insert new line
	t.value = append(t.value[:t.row+1], t.value[t.row:]...)
	t.value[t.row+1] = tail

	t.row++
	t.col = 0
	t.updateViewport()
}

// Update handles standard message-based textarea updates
func (t *TextArea) Update(msg tea.Msg) (*TextArea, tea.Cmd) {
	if !t.focus {
		return t, nil
	}

	switch msg := msg.(type) {
	case tea.PasteMsg:
		clipboardText, err := GetClipboardContent()
		if err != nil {
			return t, nil
		}

		cleanText := strings.TrimSpace(clipboardText)

		if cleanText == "" {
			return t, nil
		}

		t.InsertString(cleanText)
		return t, nil

	case tea.KeyMsg:
		switch {
		case keyMatches(msg, t.KeyMap.CharacterForward):
			t.characterRight()
		case keyMatches(msg, t.KeyMap.CharacterBackward):
			t.characterLeft()
		case keyMatches(msg, t.KeyMap.LineNext):
			t.lineDown()
		case keyMatches(msg, t.KeyMap.LinePrevious):
			t.lineUp()
		case keyMatches(msg, t.KeyMap.WordForward):
			t.wordRight()
		case keyMatches(msg, t.KeyMap.WordBackward):
			t.wordLeft()
		case keyMatches(msg, t.KeyMap.DeleteCharacterBackward):
			t.deleteCharacterBackward()
		case keyMatches(msg, t.KeyMap.DeleteCharacterForward):
			t.deleteCharacterForward()
		case keyMatches(msg, t.KeyMap.DeleteWordBackward):
			t.deleteWordBackward()
		case keyMatches(msg, t.KeyMap.DeleteWordForward):
			t.deleteWordForward()
		case keyMatches(msg, t.KeyMap.InsertNewline):
			t.insertNewline()
		case keyMatches(msg, t.KeyMap.LineStart):
			t.col = 0
			t.scrollToCursor()
		case keyMatches(msg, t.KeyMap.LineEnd):
			t.col = len(t.value[t.row])
			t.scrollToCursor()
		case keyMatches(msg, t.KeyMap.InputBegin):
			t.row = 0
			t.col = 0
			t.scrollToCursor()
		case keyMatches(msg, t.KeyMap.InputEnd):
			t.row = len(t.value) - 1
			t.col = len(t.value[t.row])
			t.scrollToCursor()
		default:
			// Handle regular character input
			keyStr := msg.String()

			// Special handling for space key since it might have special representation
			if keyStr == " " || keyStr == "space" {
				t.InsertRune(' ')
			} else if len(keyStr) == 1 {
				// Convert to rune properly to handle unicode characters
				runes := []rune(keyStr)
				if len(runes) == 1 {
					t.InsertRune(runes[0])
				}
			}
		}

	case tea.WindowSizeMsg:
		t.SetSize(msg.Width, msg.Height)
	}

	return t, nil
}

// View renders the textarea into a string
func (t *TextArea) View() string {
	var content string

	if len(t.value) == 0 || (len(t.value) == 1 && len(t.value[0]) == 0) {
		if t.Placeholder != "" {
			content = t.placeholderView()
		} else {
			content = ""
		}
	} else {
		// Use viewport for scrolling if available
		if t.viewport != nil {
			// Ensure viewport is up to date
			t.updateViewport()

			// Get viewport content but we need to add cursor manually
			viewportContent := t.viewport.View()

			// We need to render cursor on the visible content
			content = t.renderViewportWithCursor(viewportContent)
		} else {
			// Fallback to old rendering if no viewport
			content = t.renderDirectly()
		}
	}

	// Apply panel styling (background and padding)
	return t.Style.Panel.Width(t.Width).Height(t.Height).Render(content)
}

// renderLineWithCursor renders a line with the cursor positioned correctly
func (t *TextArea) renderLineWithCursor(lineStr string, lineIndex int) string {
	if lineIndex != t.row {
		return t.Style.Text.Render(lineStr)
	}

	// Calculate cursor position accounting for prompt and line numbers
	cursorPos := t.col
	if t.Prompt != "" {
		cursorPos += t.PromptWidth
	}
	if t.ShowLineNumbers {
		cursorPos += t.getLineNumberWidth() + 1 // +1 for space after line number
	}

	if cursorPos >= len(lineStr) {
		// Cursor at end of line
		return t.Style.Text.Render(lineStr) + t.Style.Cursor.Render(" ")
	}

	// Split line at cursor position
	before := lineStr[:cursorPos]
	atCursor := lineStr[cursorPos : cursorPos+1]
	after := lineStr[cursorPos+1:]

	return t.Style.Text.Render(before) + t.Style.Cursor.Render(atCursor) + t.Style.Text.Render(after)
}

// placeholderView renders the placeholder text
func (t *TextArea) placeholderView() string {
	var lines []string

	for i := 0; i < t.Height; i++ {
		line := ""
		if t.Prompt != "" {
			line = t.Style.Base.Render(t.Prompt)
		}
		if t.ShowLineNumbers {
			lineNumStr := t.formatLineNumber(1) // Use line 1 for placeholder
			line = t.Style.Base.Render(lineNumStr) + line
		}

		if i == 0 {
			// First line shows placeholder with cursor
			placeholder := t.Placeholder
			if len(placeholder) > t.Width {
				placeholder = placeholder[:t.Width]
			}
			line += t.Style.Placeholder.Render(placeholder)
			if len(placeholder) < t.Width {
				line += t.Style.Cursor.Render(" ")
			}
		}

		lines = append(lines, line)
	}

	return t.Style.Base.Render(strings.Join(lines, "\n"))
}

// renderViewportWithCursor renders the viewport content with cursor overlay
func (t *TextArea) renderViewportWithCursor(viewportContent string) string {
	if !t.focus {
		return viewportContent
	}

	th := theme.CurrentTheme()

	// Calculate the cursor position relative to the viewport
	cursorLine := t.row - t.viewport.YOffset

	// Only show cursor if it's in the visible area
	if cursorLine < 0 || cursorLine >= t.viewport.Height {
		return viewportContent
	}
	cursorStyle := lipgloss.NewStyle().
		Background(th.Primary()).
		Foreground(th.BackgroundPanel())

	textStyle := lipgloss.NewStyle().
		Foreground(th.Text()).
		Background(th.BackgroundPanel())

	lines := strings.Split(viewportContent, "\n")
	if cursorLine >= 0 && cursorLine < len(lines) {
		// Calculate cursor column position (accounting for prompt and line numbers)
		cursorCol := t.col
		if t.Prompt != "" {
			cursorCol += len(t.Prompt)
		}
		if t.ShowLineNumbers {
			cursorCol += t.getLineNumberWidth() + 1 // +1 for space after line number
		}

		line := lines[cursorLine]
		if cursorCol >= len(line) {
			// Cursor at end of line
			lines[cursorLine] = line + cursorStyle.Render(" ")
		} else if cursorCol >= 0 && cursorCol < len(line) {
			// Cursor in middle of line
			before := line[:cursorCol]
			atCursor := string(line[cursorCol])
			after := ""
			if cursorCol+1 < len(line) {
				after = line[cursorCol+1:]
			}

			lines[cursorLine] = textStyle.Render(before) + cursorStyle.Render(atCursor) + textStyle.Render(after)
		}
	}

	return strings.Join(lines, "\n")
}

// renderDirectly renders without using viewport (fallback)
func (t *TextArea) renderDirectly() string {
	var lines []string

	// Process each line
	for i, line := range t.value {
		lineStr := string(line)

		// Add prompt if specified
		if t.Prompt != "" {
			lineStr = t.Style.Base.Render(t.Prompt) + lineStr
		}

		// Add line number if enabled
		if t.ShowLineNumbers {
			lineNum := t.Style.Base.Render(t.formatLineNumber(i + 1))
			lineStr = lineNum + lineStr
		}

		// Apply text styling
		if i == t.row {
			// Current line with cursor
			lineStr = t.renderLineWithCursor(lineStr, i)
		} else {
			lineStr = t.Style.Text.Render(lineStr)
		}

		lines = append(lines, lineStr)
	}

	// Ensure minimum height
	for len(lines) < t.Height {
		emptyLine := ""
		if t.Prompt != "" {
			emptyLine = t.Style.Base.Render(t.Prompt)
		}
		if t.ShowLineNumbers {
			lineNumStr := t.formatLineNumber(len(lines) + 1)
			emptyLine = t.Style.Base.Render(lineNumStr) + emptyLine
		}
		lines = append(lines, emptyLine)
	}

	// Truncate to height if needed
	if len(lines) > t.Height {
		lines = lines[:t.Height]
	}

	content := strings.Join(lines, "\n")
	return t.Style.Base.Render(content)
}

// getLineNumberWidth calculates the width needed for line numbers
func (t *TextArea) getLineNumberWidth() int {
	maxLineNum := len(t.value)
	if maxLineNum == 0 {
		maxLineNum = 1
	}
	// Calculate digits needed for the maximum line number
	digits := len(fmt.Sprintf("%d", maxLineNum))
	if digits < 2 {
		digits = 2 // Minimum 2 digits for better appearance
	}
	return digits
}

// Helper function to format line numbers
func (t *TextArea) formatLineNumber(num int) string {
	width := t.getLineNumberWidth()
	return fmt.Sprintf("%*d ", width, num)
}
