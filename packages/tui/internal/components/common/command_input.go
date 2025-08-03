package common

import (
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/commands"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/styles"
)

// CommandInput represents the slash command input component
type CommandInput struct {
	input              string
	cursor             int
	focused            bool
	width              int
	placeholder        string
	suggestions        []string
	showSuggestions    bool
	selectedSuggestion int

	// Dependencies
	parser  *commands.Parser
	styles  *styles.Styles
	context commands.CommandContext
}

// NewCommandInput creates a new command input component
func NewCommandInput(parser *commands.Parser, styles *styles.Styles) *CommandInput {
	return &CommandInput{
		input:              "",
		cursor:             0,
		focused:            false,
		width:              50,
		placeholder:        "Type / for commands...",
		suggestions:        []string{},
		showSuggestions:    false,
		selectedSuggestion: 0,
		parser:             parser,
		styles:             styles,
		context:            commands.ContextGlobal,
	}
}

// Focus sets focus on the command input
func (ci *CommandInput) Focus() {
	ci.focused = true
}

// Blur removes focus from the command input
func (ci *CommandInput) Blur() {
	ci.focused = false
	ci.hideSuggestions()
}

// SetContext sets the current context for command suggestions
func (ci *CommandInput) SetContext(context commands.CommandContext) {
	ci.context = context
	ci.updateSuggestions()
}

// SetWidth sets the width of the command input
func (ci *CommandInput) SetWidth(width int) {
	ci.width = width
}

// SetPlaceholder sets the placeholder text
func (ci *CommandInput) SetPlaceholder(placeholder string) {
	ci.placeholder = placeholder
}

// Value returns the current input value
func (ci *CommandInput) Value() string {
	return ci.input
}

// SetValue sets the input value
func (ci *CommandInput) SetValue(value string) {
	ci.input = value
	ci.cursor = len(value)
	ci.updateSuggestions()
}

// Clear clears the input
func (ci *CommandInput) Clear() {
	ci.input = ""
	ci.cursor = 0
	ci.hideSuggestions()
}

// Init initializes the command input
func (ci *CommandInput) Init() tea.Cmd {
	return nil
}

// Update handles input events
func (ci *CommandInput) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		if !ci.focused {
			return ci, nil
		}

		switch msg.String() {
		case "left":
			if ci.cursor > 0 {
				ci.cursor--
			}

		case "right":
			if ci.cursor < len(ci.input) {
				ci.cursor++
			}

		case "home", "ctrl+a":
			ci.cursor = 0

		case "end", "ctrl+e":
			ci.cursor = len(ci.input)

		case "backspace":
			if ci.cursor > 0 {
				ci.input = ci.input[:ci.cursor-1] + ci.input[ci.cursor:]
				ci.cursor--
				ci.updateSuggestions()
			}

		case "delete", "ctrl+d":
			if ci.cursor < len(ci.input) {
				ci.input = ci.input[:ci.cursor] + ci.input[ci.cursor+1:]
				ci.updateSuggestions()
			}

		case "ctrl+k":
			// Delete from cursor to end
			ci.input = ci.input[:ci.cursor]
			ci.updateSuggestions()

		case "ctrl+u":
			// Delete from beginning to cursor
			ci.input = ci.input[ci.cursor:]
			ci.cursor = 0
			ci.updateSuggestions()

		case "up":
			if ci.showSuggestions && len(ci.suggestions) > 0 {
				ci.selectedSuggestion = (ci.selectedSuggestion - 1 + len(ci.suggestions)) % len(ci.suggestions)
			}

		case "down":
			if ci.showSuggestions && len(ci.suggestions) > 0 {
				ci.selectedSuggestion = (ci.selectedSuggestion + 1) % len(ci.suggestions)
			}

		case "tab":
			if ci.showSuggestions && len(ci.suggestions) > 0 {
				// Auto-complete with selected suggestion
				ci.input = ci.suggestions[ci.selectedSuggestion]
				ci.cursor = len(ci.input)
				ci.hideSuggestions()
			}

		case "esc":
			ci.hideSuggestions()
			return ci, func() tea.Msg { return BlurMsg{} }

		case "enter":
			if ci.showSuggestions && len(ci.suggestions) > 0 {
				// Use selected suggestion
				ci.input = ci.suggestions[ci.selectedSuggestion]
				ci.cursor = len(ci.input)
				ci.hideSuggestions()
			} else if ci.input != "" {
				// Execute command
				command := ci.input
				ci.Clear()
				return ci, func() tea.Msg {
					return CommandExecutedMsg{Command: command}
				}
			}

		default:
			// Regular character input
			if len(msg.String()) == 1 {
				char := msg.String()
				ci.input = ci.input[:ci.cursor] + char + ci.input[ci.cursor:]
				ci.cursor++
				ci.updateSuggestions()
			}
		}
	}

	return ci, nil
}

// updateSuggestions updates the command suggestions
func (ci *CommandInput) updateSuggestions() {
	if ci.input == "" {
		ci.hideSuggestions()
		return
	}

	suggestions := ci.parser.GetSuggestions(ci.input, ci.context)
	if len(suggestions) > 0 {
		ci.suggestions = suggestions
		ci.showSuggestions = true
		ci.selectedSuggestion = 0
	} else {
		ci.hideSuggestions()
	}
}

// hideSuggestions hides the suggestions dropdown
func (ci *CommandInput) hideSuggestions() {
	ci.showSuggestions = false
	ci.suggestions = []string{}
	ci.selectedSuggestion = 0
}

// View renders the command input
func (ci *CommandInput) View() string {
	var style lipgloss.Style
	if ci.focused {
		style = ci.styles.InputFocused
	} else {
		style = ci.styles.Input
	}

	// Prepare the input display
	displayInput := ci.input
	if ci.input == "" && !ci.focused {
		displayInput = ci.placeholder
		style = style.Copy().Foreground(ci.styles.GetTheme().GetColors().TextMuted)
	}

	// Add cursor if focused
	if ci.focused {
		if ci.cursor >= len(displayInput) {
			displayInput += "│"
		} else {
			runes := []rune(displayInput)
			displayInput = string(runes[:ci.cursor]) + "│" + string(runes[ci.cursor:])
		}
	}

	// Apply width constraint
	if len(displayInput) > ci.width-4 { // Account for padding
		if ci.cursor < ci.width-4 {
			displayInput = displayInput[:ci.width-4] + "..."
		} else {
			start := ci.cursor - (ci.width - 7)
			displayInput = "..." + displayInput[start:ci.cursor+3]
		}
	}

	inputView := style.Width(ci.width).Render(displayInput)

	// Add suggestions if visible
	if ci.showSuggestions && len(ci.suggestions) > 0 {
		suggestionsView := ci.renderSuggestions()
		return lipgloss.JoinVertical(lipgloss.Left, inputView, suggestionsView)
	}

	return inputView
}

// renderSuggestions renders the suggestions dropdown
func (ci *CommandInput) renderSuggestions() string {
	if len(ci.suggestions) == 0 {
		return ""
	}

	maxSuggestions := 5
	displaySuggestions := ci.suggestions
	if len(displaySuggestions) > maxSuggestions {
		displaySuggestions = displaySuggestions[:maxSuggestions]
	}

	var items []string
	for i, suggestion := range displaySuggestions {
		style := ci.styles.ListItem
		if i == ci.selectedSuggestion {
			style = ci.styles.ListItemSelected
		}

		items = append(items, style.Render(suggestion))
	}

	suggestionsBox := lipgloss.NewStyle().
		Background(ci.styles.GetTheme().GetColors().Surface).
		BorderStyle(lipgloss.NormalBorder()).
		BorderForeground(ci.styles.GetTheme().GetColors().Border).
		Width(ci.width).
		Render(strings.Join(items, "\n"))

	return suggestionsBox
}

// Message types for command input
type (
	CommandExecutedMsg struct {
		Command string
	}

	BlurMsg struct{}
)
