package styles

import (
	"github.com/charmbracelet/lipgloss"
)

// Styles contains all the lipgloss styles for the TUI
type Styles struct {
	theme *ThemeManager

	// Layout styles
	App     lipgloss.Style
	Header  lipgloss.Style
	Footer  lipgloss.Style
	Content lipgloss.Style
	Sidebar lipgloss.Style

	// Text styles
	Title    lipgloss.Style
	Subtitle lipgloss.Style
	Text     lipgloss.Style
	Muted    lipgloss.Style
	Bold     lipgloss.Style
	Italic   lipgloss.Style

	// Component styles
	Button           lipgloss.Style
	ButtonFocused    lipgloss.Style
	List             lipgloss.Style
	ListItem         lipgloss.Style
	ListItemSelected lipgloss.Style

	// Input styles
	Input        lipgloss.Style
	InputFocused lipgloss.Style
	CommandInput lipgloss.Style

	// Status styles
	StatusBar lipgloss.Style
	Progress  lipgloss.Style
	Spinner   lipgloss.Style

	// Modal styles
	Modal      lipgloss.Style
	ModalTitle lipgloss.Style

	// Chat styles
	ChatBubble    lipgloss.Style
	ChatUser      lipgloss.Style
	ChatAgent     lipgloss.Style
	ChatEvaluator lipgloss.Style

	// Evaluation styles
	EvalCard     lipgloss.Style
	EvalStatus   lipgloss.Style
	EvalProgress lipgloss.Style

	// Border styles
	Border        lipgloss.Style
	BorderFocused lipgloss.Style
}

// NewStyles creates a new styles instance with the given theme
func NewStyles(theme *ThemeManager) *Styles {
	colors := theme.GetColors()

	s := &Styles{
		theme: theme,
	}

	// Layout styles
	s.App = lipgloss.NewStyle().
		Background(colors.Background).
		Foreground(colors.TextPrimary)

	s.Header = lipgloss.NewStyle().
		Background(colors.Surface).
		Foreground(colors.TextPrimary).
		BorderStyle(lipgloss.NormalBorder()).
		BorderBottom(true).
		BorderForeground(colors.Border).
		Padding(0, 2).
		Bold(true)

	s.Footer = lipgloss.NewStyle().
		Background(colors.Surface).
		Foreground(colors.TextSecondary).
		BorderStyle(lipgloss.NormalBorder()).
		BorderTop(true).
		BorderForeground(colors.Border).
		Padding(0, 2)

	s.Content = lipgloss.NewStyle().
		Background(colors.Background).
		Foreground(colors.TextPrimary).
		Padding(1, 2)

	s.Sidebar = lipgloss.NewStyle().
		Background(colors.Surface).
		Foreground(colors.TextPrimary).
		BorderStyle(lipgloss.NormalBorder()).
		BorderRight(true).
		BorderForeground(colors.Border).
		Padding(1, 2).
		Width(25)

	// Text styles
	s.Title = lipgloss.NewStyle().
		Foreground(colors.Primary).
		Bold(true).
		MarginBottom(1)

	s.Subtitle = lipgloss.NewStyle().
		Foreground(colors.TextSecondary).
		Bold(true)

	s.Text = lipgloss.NewStyle().
		Foreground(colors.TextPrimary)

	s.Muted = lipgloss.NewStyle().
		Foreground(colors.TextMuted)

	s.Bold = lipgloss.NewStyle().
		Foreground(colors.TextPrimary).
		Bold(true)

	s.Italic = lipgloss.NewStyle().
		Foreground(colors.TextPrimary).
		Italic(true)

	// Component styles
	s.Button = lipgloss.NewStyle().
		Background(colors.Primary).
		Foreground(colors.TextInverse).
		Padding(0, 3).
		MarginRight(1).
		Bold(true)

	s.ButtonFocused = s.Button.Copy().
		Background(colors.Selection).
		BorderStyle(lipgloss.NormalBorder()).
		BorderForeground(colors.Accent)

	s.List = lipgloss.NewStyle().
		Background(colors.Background).
		Foreground(colors.TextPrimary).
		MarginBottom(1)

	s.ListItem = lipgloss.NewStyle().
		Foreground(colors.TextPrimary).
		Padding(0, 2).
		MarginBottom(0)

	s.ListItemSelected = s.ListItem.Copy().
		Background(colors.Selection).
		Foreground(colors.TextInverse).
		Bold(true)

	// Input styles
	s.Input = lipgloss.NewStyle().
		Background(colors.Surface).
		Foreground(colors.TextPrimary).
		BorderStyle(lipgloss.NormalBorder()).
		BorderForeground(colors.Border).
		Padding(0, 1)

	s.InputFocused = s.Input.Copy().
		BorderForeground(colors.Primary)

	s.CommandInput = lipgloss.NewStyle().
		Background(colors.Surface).
		Foreground(colors.TextPrimary).
		BorderStyle(lipgloss.RoundedBorder()).
		BorderForeground(colors.Primary).
		Padding(0, 1).
		Width(50).
		Bold(true)

	// Status styles
	s.StatusBar = lipgloss.NewStyle().
		Background(colors.Surface).
		Foreground(colors.TextSecondary).
		Padding(0, 2)

	s.Progress = lipgloss.NewStyle().
		Background(colors.Surface).
		Foreground(colors.Primary).
		BorderStyle(lipgloss.NormalBorder()).
		BorderForeground(colors.Border)

	s.Spinner = lipgloss.NewStyle().
		Foreground(colors.Primary).
		Bold(true)

	// Modal styles
	s.Modal = lipgloss.NewStyle().
		Background(colors.Surface).
		Foreground(colors.TextPrimary).
		BorderStyle(lipgloss.RoundedBorder()).
		BorderForeground(colors.Border).
		Padding(2, 4).
		Width(60)

	s.ModalTitle = lipgloss.NewStyle().
		Foreground(colors.Primary).
		Bold(true).
		Align(lipgloss.Center).
		MarginBottom(1)

	// Chat styles
	s.ChatBubble = lipgloss.NewStyle().
		Background(colors.Surface).
		Foreground(colors.TextPrimary).
		BorderStyle(lipgloss.RoundedBorder()).
		BorderForeground(colors.Border).
		Padding(1, 2).
		MarginBottom(1)

	s.ChatUser = s.ChatBubble.Copy().
		BorderForeground(colors.Info).
		Align(lipgloss.Right)

	s.ChatAgent = s.ChatBubble.Copy().
		BorderForeground(colors.Primary)

	s.ChatEvaluator = s.ChatBubble.Copy().
		BorderForeground(colors.Accent)

	// Evaluation styles
	s.EvalCard = lipgloss.NewStyle().
		Background(colors.Surface).
		Foreground(colors.TextPrimary).
		BorderStyle(lipgloss.NormalBorder()).
		BorderForeground(colors.Border).
		Padding(1, 2).
		MarginBottom(1).
		Width(70)

	s.EvalStatus = lipgloss.NewStyle().
		Bold(true).
		Padding(0, 1)

	s.EvalProgress = lipgloss.NewStyle().
		Foreground(colors.Primary).
		Bold(true)

	// Border styles
	s.Border = lipgloss.NewStyle().
		BorderStyle(lipgloss.NormalBorder()).
		BorderForeground(colors.Border)

	s.BorderFocused = lipgloss.NewStyle().
		BorderStyle(lipgloss.NormalBorder()).
		BorderForeground(colors.Primary)

	return s
}

// StatusStyle returns a style for the given status
func (s *Styles) StatusStyle(status string) lipgloss.Style {
	colors := StatusColors()
	if color, exists := colors[status]; exists {
		return s.EvalStatus.Copy().Foreground(color)
	}
	return s.EvalStatus
}

// PriorityStyle returns a style for the given priority
func (s *Styles) PriorityStyle(priority string) lipgloss.Style {
	colors := PriorityColors()
	if color, exists := colors[priority]; exists {
		return s.Text.Copy().Foreground(color).Bold(true)
	}
	return s.Text
}

// CategoryStyle returns a style for the given category
func (s *Styles) CategoryStyle(category string) lipgloss.Style {
	colors := CategoryColors()
	if color, exists := colors[category]; exists {
		return s.Text.Copy().Foreground(color)
	}
	return s.Text
}

// UpdateTheme updates all styles with a new theme
func (s *Styles) UpdateTheme(theme *ThemeManager) {
	*s = *NewStyles(theme)
}

// GetTheme returns the current theme manager
func (s *Styles) GetTheme() *ThemeManager {
	return s.theme
}
