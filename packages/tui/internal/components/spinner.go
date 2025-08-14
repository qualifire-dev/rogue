package components

import (
	"time"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
)

// SpinnerTickMsg is sent on each spinner tick
type SpinnerTickMsg struct {
	ID int // Unique ID to identify which spinner this tick is for
}

// Spinner represents a simple spinning animation
type Spinner struct {
	ID      int
	frames  []string
	current int
	style   lipgloss.Style
	active  bool
}

// NewSpinner creates a new spinner with default dot animation
func NewSpinner(id int) Spinner {
	return Spinner{
		ID: id,
		frames: []string{
			"⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏",
		},
		current: 0,
		style:   lipgloss.NewStyle().Foreground(lipgloss.Color("63")), // Purple
		active:  false,
	}
}

// Start returns a command to start the spinner
func (s Spinner) Start() tea.Cmd {
	return tea.Tick(100*time.Millisecond, func(time.Time) tea.Msg {
		return SpinnerTickMsg{ID: s.ID}
	})
}

// Update handles spinner tick messages
func (s Spinner) Update(msg tea.Msg) (Spinner, tea.Cmd) {
	switch msg := msg.(type) {
	case SpinnerTickMsg:
		if msg.ID == s.ID {
			if s.active {
				s.current = (s.current + 1) % len(s.frames)
			}
			return s, s.Start() // Continue spinning regardless of active state
		}
	}
	return s, nil
}

// View renders the current spinner frame
func (s Spinner) View() string {
	if !s.active {
		return ""
	}
	return s.style.Render(s.frames[s.current])
}

// SetActive sets whether the spinner should be active
func (s *Spinner) SetActive(active bool) {
	s.active = active
}

// IsActive returns whether the spinner is currently active
func (s Spinner) IsActive() bool {
	return s.active
}
