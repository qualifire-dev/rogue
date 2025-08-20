package styles

import (
	"image/color"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/charmbracelet/lipgloss/v2/compat"
)

// Theme colors
var (
	// Primary colors
	Primary   = lipgloss.Color("205") // Pink
	Secondary = lipgloss.Color("62")  // Blue
	Success   = lipgloss.Color("42")  // Green
	Warning   = lipgloss.Color("214") // Orange
	Error     = lipgloss.Color("196") // Red
	Info      = lipgloss.Color("39")  // Cyan

	// Neutral colors
	TextColor = lipgloss.Color("255") // White
	TextMuted = lipgloss.Color("245") // Light gray
	Border    = lipgloss.Color("238") // Dark gray
)

func IsNoColor(c color.Color) bool {
	_, ok := c.(lipgloss.NoColor)
	return ok
}

// Background sets the background color, handling "none" appropriately
func (s Style) Background(c compat.AdaptiveColor) Style {
	if IsNoColor(c.Dark) && IsNoColor(c.Light) {
		return Style{s.Style.UnsetBackground()}
	}
	return Style{s.Style.Background(c)}
}

// Style wraps lipgloss.Style to provide a fluent API for handling "none" colors
type Style struct {
	lipgloss.Style
}

// NewStyle creates a new Style with proper handling of "none" colors
func NewStyle() Style {
	return Style{lipgloss.NewStyle()}
}

// List styles
var (
	// List item style
	ListItem = lipgloss.NewStyle().
			PaddingLeft(2)

	// Selected list item style
	SelectedListItem = lipgloss.NewStyle().
				PaddingLeft(2).
				Foreground(Primary).
				Bold(true)

	// List header style
	ListHeader = lipgloss.NewStyle().
			Foreground(Secondary).
			Bold(true).
			Underline(true).
			MarginBottom(1)
)
