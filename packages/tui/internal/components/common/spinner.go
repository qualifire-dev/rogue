package common

import (
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/styles"
)

// SpinnerType defines different spinner animations
type SpinnerType int

const (
	SpinnerDots SpinnerType = iota
	SpinnerLine
	SpinnerCircle
	SpinnerPulse
)

// Spinner represents a loading spinner component
type Spinner struct {
	frames   []string
	frame    int
	spinning bool
	text     string
	spinType SpinnerType
	styles   *styles.Styles
	interval time.Duration
}

// NewSpinner creates a new spinner component
func NewSpinner(styles *styles.Styles) *Spinner {
	s := &Spinner{
		spinning: false,
		text:     "",
		spinType: SpinnerDots,
		styles:   styles,
		interval: 100 * time.Millisecond,
	}

	s.setFrames()
	return s
}

// SetType sets the spinner type
func (s *Spinner) SetType(spinType SpinnerType) {
	s.spinType = spinType
	s.setFrames()
	s.frame = 0
}

// SetText sets the text to display alongside the spinner
func (s *Spinner) SetText(text string) {
	s.text = text
}

// SetInterval sets the animation interval
func (s *Spinner) SetInterval(interval time.Duration) {
	s.interval = interval
}

// Start starts the spinner animation
func (s *Spinner) Start() tea.Cmd {
	s.spinning = true
	return s.tick()
}

// Stop stops the spinner animation
func (s *Spinner) Stop() {
	s.spinning = false
}

// IsSpinning returns true if the spinner is currently spinning
func (s *Spinner) IsSpinning() bool {
	return s.spinning
}

// setFrames sets the animation frames based on spinner type
func (s *Spinner) setFrames() {
	switch s.spinType {
	case SpinnerDots:
		s.frames = []string{"⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"}

	case SpinnerLine:
		s.frames = []string{"|", "/", "-", "\\"}

	case SpinnerCircle:
		s.frames = []string{"◐", "◓", "◑", "◒"}

	case SpinnerPulse:
		s.frames = []string{"●", "○", "●", "○"}

	default:
		s.frames = []string{"⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"}
	}
}

// tick returns a command that advances the spinner frame
func (s *Spinner) tick() tea.Cmd {
	return tea.Tick(s.interval, func(time.Time) tea.Msg {
		return SpinnerTickMsg{}
	})
}

// Init initializes the spinner
func (s *Spinner) Init() tea.Cmd {
	return nil
}

// Update handles spinner tick messages
func (s *Spinner) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg.(type) {
	case SpinnerTickMsg:
		if s.spinning {
			s.frame = (s.frame + 1) % len(s.frames)
			return s, s.tick()
		}
	}

	return s, nil
}

// View renders the spinner
func (s *Spinner) View() string {
	if !s.spinning {
		if s.text != "" {
			return s.styles.Text.Copy().Render(s.text)
		}
		return ""
	}

	spinnerChar := s.frames[s.frame]
	spinnerStyle := s.styles.Spinner.Copy()

	if s.text != "" {
		return lipgloss.JoinHorizontal(
			lipgloss.Center,
			spinnerStyle.Render(spinnerChar),
			" ",
			s.styles.Text.Copy().Render(s.text),
		)
	}

	return spinnerStyle.Render(spinnerChar)
}

// ViewInline renders the spinner inline without text
func (s *Spinner) ViewInline() string {
	if !s.spinning {
		return ""
	}

	spinnerChar := s.frames[s.frame]
	return s.styles.Spinner.Copy().Render(spinnerChar)
}

// ViewWithCustomText renders the spinner with custom text
func (s *Spinner) ViewWithCustomText(text string) string {
	if !s.spinning {
		return s.styles.Text.Copy().Render(text)
	}

	spinnerChar := s.frames[s.frame]
	spinnerStyle := s.styles.Spinner.Copy()

	return lipgloss.JoinHorizontal(
		lipgloss.Center,
		spinnerStyle.Render(spinnerChar),
		" ",
		s.styles.Text.Copy().Render(text),
	)
}

// SpinnerTickMsg is sent when the spinner should advance to the next frame
type SpinnerTickMsg struct{}

// Quick spinner functions for common use cases

// LoadingSpinner creates a spinner with "Loading..." text
func LoadingSpinner(styles *styles.Styles) *Spinner {
	s := NewSpinner(styles)
	s.SetText("Loading...")
	return s
}

// ConnectingSpinner creates a spinner with "Connecting..." text
func ConnectingSpinner(styles *styles.Styles) *Spinner {
	s := NewSpinner(styles)
	s.SetText("Connecting...")
	return s
}

// ProcessingSpinner creates a spinner with "Processing..." text
func ProcessingSpinner(styles *styles.Styles) *Spinner {
	s := NewSpinner(styles)
	s.SetText("Processing...")
	return s
}

// SavingSpinner creates a spinner with "Saving..." text
func SavingSpinner(styles *styles.Styles) *Spinner {
	s := NewSpinner(styles)
	s.SetText("Saving...")
	return s
}
