package components

import (
	"fmt"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
)

// TextAreaExample demonstrates how to use the TextArea component
type TextAreaExample struct {
	textarea TextArea
	message  string
}

// NewTextAreaExample creates a new textarea example
func NewTextAreaExample() TextAreaExample {
	ta := NewTextArea(1, 50, 10)
	ta.Placeholder = "Enter your text here..."
	ta.Prompt = "> "
	ta.PromptWidth = 2
	ta.ShowLineNumbers = true
	ta.Focus()

	return TextAreaExample{
		textarea: ta,
		message:  "Press Ctrl+C to exit",
	}
}

// Init initializes the example
func (m TextAreaExample) Init() tea.Cmd {
	return nil
}

// Update handles messages
func (m TextAreaExample) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c":
			return m, tea.Quit
		}
	}

	// Update the textarea
	ta, cmd := m.textarea.Update(msg)
	m.textarea = *ta

	return m, cmd
}

// View renders the example
func (m TextAreaExample) View() string {
	title := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("63")).
		Render("TextArea Component Example")

	instructions := lipgloss.NewStyle().
		Foreground(lipgloss.Color("240")).
		Render(m.message)

	content := m.textarea.View()

	info := lipgloss.NewStyle().
		Foreground(lipgloss.Color("240")).
		Render(fmt.Sprintf("Lines: %d, Characters: %d", m.textarea.LineCount(), m.textarea.Length()))

	return fmt.Sprintf("%s\n\n%s\n\n%s\n\n%s", title, instructions, content, info)
}

// RunTextAreaExample runs the textarea example
func RunTextAreaExample() error {
	p := tea.NewProgram(NewTextAreaExample())
	_, err := p.Run()
	return err
}
