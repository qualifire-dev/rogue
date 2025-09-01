package components

import (
	"strings"
	"unicode/utf8"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
)

// ViewportKeyMap defines the keybindings for the viewport. Note that you don't
// necessarily need to use keybindings at all; the viewport can be controlled
// programmatically with methods like ScrollDown(1). See the GoDocs for details.
type ViewportKeyMap struct {
	PageDown     []string
	PageUp       []string
	HalfPageUp   []string
	HalfPageDown []string
	Down         []string
	Up           []string
	Left         []string
	Right        []string
}

// DefaultViewportKeyMap returns a set of pager-like default keybindings
func DefaultViewportKeyMap() ViewportKeyMap {
	return ViewportKeyMap{
		PageDown:     []string{"pgdown", " ", "f"},
		PageUp:       []string{"pgup", "b"},
		HalfPageUp:   []string{"u", "ctrl+u"},
		HalfPageDown: []string{"d", "ctrl+d"},
		Up:           []string{"up", "k"},
		Down:         []string{"down", "j"},
		Left:         []string{"left", "h"},
		Right:        []string{"right", "l"},
	}
}

// keyMatches checks if the given key matches any of the keys in the binding
func keyMatches(keyMsg tea.KeyMsg, keys []string) bool {
	keyString := keyMsg.String()
	for _, k := range keys {
		if keyString == k {
			return true
		}
	}
	return false
}

// Viewport represents a scrollable content area
type Viewport struct {
	ID                int
	Width             int
	Height            int
	KeyMap            ViewportKeyMap
	MouseWheelEnabled bool
	MouseWheelDelta   int
	YOffset           int
	XOffset           int
	HorizontalStep    int
	Style             lipgloss.Style
	content           string
	lines             []string
	maxYOffset        int
	maxXOffset        int
	mouseWheelDeltaX  int
	mouseWheelDeltaY  int
}

// NewViewport creates a new viewport with the given width and height
func NewViewport(id int, width, height int) Viewport {
	return Viewport{
		ID:                id,
		Width:             width,
		Height:            height,
		KeyMap:            DefaultViewportKeyMap(),
		MouseWheelEnabled: true,
		MouseWheelDelta:   3,
		HorizontalStep:    4,
		Style:             lipgloss.NewStyle(),
		YOffset:           0,
		XOffset:           0,
		lines:             []string{},
		maxYOffset:        0,
		maxXOffset:        0,
		mouseWheelDeltaX:  0,
		mouseWheelDeltaY:  3,
	}
}

// SetSize sets the viewport's width and height
func (v *Viewport) SetSize(width, height int) {
	v.Width = width
	v.Height = height
	v.updateBounds()
}

// SetContent sets the viewport's text content
func (v *Viewport) SetContent(content string) {
	v.content = content
	v.lines = strings.Split(content, "\n")
	v.updateBounds()
}

// GetContent returns the viewport's content
func (v Viewport) GetContent() string {
	return v.content
}

// SetYOffset sets the Y offset (vertical scroll position)
func (v *Viewport) SetYOffset(offset int) {
	v.YOffset = max(0, min(offset, v.maxYOffset))
}

// SetXOffset sets the X offset (horizontal scroll position)
func (v *Viewport) SetXOffset(offset int) {
	v.XOffset = max(0, min(offset, v.maxXOffset))
}

// SetHorizontalStep sets the default amount of columns to scroll left or right
func (v *Viewport) SetHorizontalStep(step int) {
	v.HorizontalStep = max(1, step)
}

// ScrollUp moves the view up by the given number of lines
func (v *Viewport) ScrollUp(lines int) {
	v.SetYOffset(v.YOffset - lines)
}

// ScrollDown moves the view down by the given number of lines
func (v *Viewport) ScrollDown(lines int) {
	v.SetYOffset(v.YOffset + lines)
}

// ScrollLeft moves the viewport to the left by the given number of columns
func (v *Viewport) ScrollLeft(columns int) {
	v.SetXOffset(v.XOffset - columns)
}

// ScrollRight moves the viewport to the right by the given number of columns
func (v *Viewport) ScrollRight(columns int) {
	v.SetXOffset(v.XOffset + columns)
}

// PageUp moves the view up by one height of the viewport
func (v *Viewport) PageUp() {
	v.ScrollUp(v.Height)
}

// PageDown moves the view down by the number of lines in the viewport
func (v *Viewport) PageDown() {
	v.ScrollDown(v.Height)
}

// HalfPageUp moves the view up by half the height of the viewport
func (v *Viewport) HalfPageUp() {
	v.ScrollUp(v.Height / 2)
}

// HalfPageDown moves the view down by half the height of the viewport
func (v *Viewport) HalfPageDown() {
	v.ScrollDown(v.Height / 2)
}

// GotoTop sets the viewport to the top position
func (v *Viewport) GotoTop() {
	v.SetYOffset(0)
}

// GotoBottom sets the viewport to the bottom position
func (v *Viewport) GotoBottom() {
	v.SetYOffset(v.maxYOffset)
}

// AtTop returns whether the viewport is at the very top position
func (v Viewport) AtTop() bool {
	return v.YOffset <= 0
}

// AtBottom returns whether the viewport is at or past the very bottom position
func (v Viewport) AtBottom() bool {
	return v.YOffset >= v.maxYOffset
}

// PastBottom returns whether the viewport is scrolled beyond the last line
func (v Viewport) PastBottom() bool {
	return v.YOffset > v.maxYOffset
}

// ScrollPercent returns the amount scrolled as a float between 0 and 1
func (v Viewport) ScrollPercent() float64 {
	if v.maxYOffset == 0 {
		return 0.0
	}
	return float64(v.YOffset) / float64(v.maxYOffset)
}

// HorizontalScrollPercent returns the amount horizontally scrolled as a float between 0 and 1
func (v Viewport) HorizontalScrollPercent() float64 {
	if v.maxXOffset == 0 {
		return 0.0
	}
	return float64(v.XOffset) / float64(v.maxXOffset)
}

// TotalLineCount returns the total number of lines (both hidden and visible) within the viewport
func (v Viewport) TotalLineCount() int {
	return len(v.lines)
}

// VisibleLineCount returns the number of visible lines within the viewport
func (v Viewport) VisibleLineCount() int {
	return min(v.Height, len(v.lines)-v.YOffset)
}

// Update handles standard message-based viewport updates
func (v *Viewport) Update(msg tea.Msg) (*Viewport, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch {
		case keyMatches(msg, v.KeyMap.Up):
			v.ScrollUp(1)
		case keyMatches(msg, v.KeyMap.Down):
			v.ScrollDown(1)
		case keyMatches(msg, v.KeyMap.Left):
			v.ScrollLeft(v.HorizontalStep)
		case keyMatches(msg, v.KeyMap.Right):
			v.ScrollRight(v.HorizontalStep)
		case keyMatches(msg, v.KeyMap.PageUp):
			v.PageUp()
		case keyMatches(msg, v.KeyMap.PageDown):
			v.PageDown()
		case keyMatches(msg, v.KeyMap.HalfPageUp):
			v.HalfPageUp()
		case keyMatches(msg, v.KeyMap.HalfPageDown):
			v.HalfPageDown()
		}

	case tea.MouseMsg:
		// Mouse wheel support can be added when needed
		// For now, focus on keyboard navigation
		_ = msg // prevent unused variable warning

	case tea.WindowSizeMsg:
		// Automatically adjust size when window changes (optional behavior)
		// Can be disabled by not calling this
		v.SetSize(msg.Width, msg.Height)
	}

	return v, nil
}

// View renders the viewport into a string
func (v Viewport) View() string {
	if len(v.lines) == 0 {
		// Return empty styled area if no content
		return v.Style.Render(strings.Repeat("\n", max(0, v.Height-1)))
	}

	var visibleLines []string

	// Calculate which lines to show
	startLine := v.YOffset
	endLine := min(startLine+v.Height, len(v.lines))

	if startLine >= len(v.lines) {
		// If we're past the end, show empty lines
		visibleLines = make([]string, v.Height)
		for i := range visibleLines {
			visibleLines[i] = ""
		}
	} else {
		// Get the visible lines
		visibleLines = make([]string, v.Height)
		lineIndex := 0

		// Add actual content lines
		for i := startLine; i < endLine && lineIndex < v.Height; i++ {
			line := v.lines[i]

			// Apply horizontal scrolling
			if v.XOffset > 0 && utf8.RuneCountInString(line) > v.XOffset {
				runes := []rune(line)
				if v.XOffset < len(runes) {
					line = string(runes[v.XOffset:])
				} else {
					line = ""
				}
			}

			// Wrap content to viewport width
			if v.Width > 0 && utf8.RuneCountInString(line) > v.Width {
				runes := []rune(line)
				if v.Width < len(runes) {
					line = string(runes[:v.Width])
				}
			}

			visibleLines[lineIndex] = line
			lineIndex++
		}

		// Fill remaining lines with empty strings
		for lineIndex < v.Height {
			visibleLines[lineIndex] = ""
			lineIndex++
		}
	}

	// Pad each line to full width to ensure proper background color coverage
	for i, line := range visibleLines {
		// Use lipgloss.Width to get the actual display width (accounting for ANSI codes)
		lineWidth := lipgloss.Width(line)
		if lineWidth < v.Width {
			// Pad with spaces to fill the width
			padding := v.Width - lineWidth
			visibleLines[i] = line + strings.Repeat(" ", padding)
		}
	}

	content := strings.Join(visibleLines, "\n")
	return v.Style.
		Width(v.Width).
		MaxWidth(v.Width).
		Render(content)
}

// updateBounds calculates the maximum scroll offsets based on content and viewport size
func (v *Viewport) updateBounds() {
	if len(v.lines) <= v.Height {
		v.maxYOffset = 0
	} else {
		v.maxYOffset = len(v.lines) - v.Height
	}

	// Calculate max horizontal offset based on the longest line
	maxLineWidth := 0
	for _, line := range v.lines {
		width := lipgloss.Width(line)
		if width > maxLineWidth {
			maxLineWidth = width
		}
	}

	if maxLineWidth <= v.Width {
		v.maxXOffset = 0
	} else {
		v.maxXOffset = maxLineWidth - v.Width
	}

	// Clamp current offsets to valid ranges
	v.SetYOffset(v.YOffset)
	v.SetXOffset(v.XOffset)
}

// Helper functions for Go compatibility (only needed if not using Go 1.21+)
// In Go 1.21+, min and max are built-in functions
