package components

import (
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/styles"
	"github.com/rogue/tui/internal/theme"
)

// Command represents a command that can be executed
type Command struct {
	Name        string
	Description string
	KeyBinding  string
	Action      string
}

// CommandInput represents the smart input component
type CommandInput struct {
	input              string
	cursor             int
	suggestions        []Command
	showingSuggestions bool
	selectedSuggestion int
	width              int
	focused            bool
	commands           []Command
}

// CommandSelectedMsg is sent when a command is selected
type CommandSelectedMsg struct {
	Command Command
}

// NewCommandInput creates a new command input component
func NewCommandInput() CommandInput {
	commands := []Command{
		{Name: "/new", Description: "New evaluation", KeyBinding: "Ctrl+N", Action: "new_evaluation"},
		{Name: "/models", Description: "List models", KeyBinding: "Ctrl+M", Action: "list_models"},
		{Name: "/editor", Description: "Open scenario editor", KeyBinding: "", Action: "open_editor"},
		{Name: "/config", Description: "Configuration", KeyBinding: "Ctrl+S", Action: "configuration"},
		{Name: "/help", Description: "Show help", KeyBinding: "Ctrl+H", Action: "help"},
		{Name: "/quit", Description: "Quit application", KeyBinding: "Q", Action: "quit"},
	}

	return CommandInput{
		commands:    commands,
		suggestions: commands,
		width:       80,
	}
}

// SetWidth sets the width of the component
func (c *CommandInput) SetWidth(width int) {
	c.width = width
}

// SetFocus sets the focus state of the component
func (c *CommandInput) SetFocus(focused bool) {
	c.focused = focused
}

// IsFocused returns whether the component is focused
func (c CommandInput) IsFocused() bool {
	return c.focused
}

// Value returns the current input value
func (c CommandInput) Value() string {
	return c.input
}

// SetValue sets the input value
func (c *CommandInput) SetValue(value string) {
	c.input = value
	c.cursor = len(value)
	c.updateSuggestions()
}

// Init implements tea.Model
func (c CommandInput) Init() tea.Cmd {
	return nil
}

// Update implements tea.Model
func (c CommandInput) Update(msg tea.Msg) (CommandInput, tea.Cmd) {
	if !c.focused {
		return c, nil
	}

	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c":
			return c, tea.Quit

		case "enter":
			if c.showingSuggestions && len(c.suggestions) > 0 {
				selected := c.suggestions[c.selectedSuggestion]
				c.input = selected.Name + " "
				c.cursor = len(c.input)
				c.showingSuggestions = false
				c.selectedSuggestion = 0
				return c, func() tea.Msg {
					return CommandSelectedMsg{Command: selected}
				}
			}
			return c, nil

		case "escape":
			if c.showingSuggestions {
				c.showingSuggestions = false
				c.selectedSuggestion = 0
				return c, nil
			}
			return c, nil

		case "up":
			if c.showingSuggestions && len(c.suggestions) > 0 {
				c.selectedSuggestion--
				if c.selectedSuggestion < 0 {
					c.selectedSuggestion = len(c.suggestions) - 1
				}
			}
			return c, nil

		case "down":
			if c.showingSuggestions && len(c.suggestions) > 0 {
				c.selectedSuggestion++
				if c.selectedSuggestion >= len(c.suggestions) {
					c.selectedSuggestion = 0
				}
			}
			return c, nil

		case "left":
			if c.cursor > 0 {
				c.cursor--
			}
			return c, nil

		case "right":
			if c.cursor < len(c.input) {
				c.cursor++
			}
			return c, nil

		case "backspace":
			if c.cursor > 0 && len(c.input) > 0 {
				c.input = c.input[:c.cursor-1] + c.input[c.cursor:]
				c.cursor--
				c.updateSuggestions()
			}
			return c, nil

		case "delete":
			if c.cursor < len(c.input) {
				c.input = c.input[:c.cursor] + c.input[c.cursor+1:]
				c.updateSuggestions()
			}
			return c, nil

		default:
			// Handle regular character input
			if len(msg.String()) == 1 {
				char := msg.String()
				c.input = c.input[:c.cursor] + char + c.input[c.cursor:]
				c.cursor++
				c.updateSuggestions()
			}
			return c, nil
		}
	}

	return c, nil
}

// updateSuggestions updates the suggestions based on current input
func (c *CommandInput) updateSuggestions() {
	c.selectedSuggestion = 0

	if strings.HasPrefix(c.input, "/") {
		c.showingSuggestions = true
		filtered := []Command{}

		query := strings.ToLower(c.input)
		for _, cmd := range c.commands {
			if strings.HasPrefix(strings.ToLower(cmd.Name), query) {
				filtered = append(filtered, cmd)
			}
		}

		c.suggestions = filtered
	} else {
		c.showingSuggestions = false
		c.suggestions = c.commands
	}
}

// ViewInput returns just the input field
func (c CommandInput) ViewInput() string {
	t := theme.CurrentTheme()
	effectiveWidth := c.width
	if effectiveWidth > 80 {
		effectiveWidth = 80
	}

	// Input field style
	inputStyle := lipgloss.NewStyle().
		Width(effectiveWidth).
		Border(lipgloss.RoundedBorder()).
		Background(t.BackgroundPanel()).
		BorderForeground(t.Border())

	if c.focused {
		inputStyle = inputStyle.BorderForeground(t.Primary())
	}

	// Render input with cursor
	var inputText string
	if c.cursor == len(c.input) {
		if c.focused {
			inputText = c.input + "█"
		} else {
			inputText = c.input + " "
		}
	} else {
		inputText = c.input[:c.cursor] + "█" + c.input[c.cursor:]
	}

	return inputStyle.Render(inputText)
}

// ViewSuggestions returns just the suggestions panel
func (c CommandInput) ViewSuggestions() string {
	if !c.showingSuggestions || len(c.suggestions) == 0 {
		return ""
	}

	t := theme.CurrentTheme()
	effectiveWidth := c.width
	if effectiveWidth > 80 {
		effectiveWidth = 80
	}

	// Render suggestions with overlay styling
	suggestionStyle := lipgloss.NewStyle().
		Width(effectiveWidth).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Primary()).
		Background(t.BackgroundPanel()).
		Padding(0, 1)

	var suggestionItems []string
	for i, cmd := range c.suggestions {
		itemStyle := lipgloss.NewStyle()

		if i == c.selectedSuggestion {
			itemStyle = itemStyle.
				Background(t.Primary()).
				Foreground(t.Background()).
				Bold(true).
				Padding(0, 1)
		} else {
			itemStyle = itemStyle.
				Foreground(t.Text()).
				Padding(0, 1)
		}

		// Format: /command    description    keybinding
		var nameStyle, descStyle, keyStyle lipgloss.Style
		if i == c.selectedSuggestion {
			nameStyle = itemStyle.Foreground(t.Background())
			descStyle = itemStyle.Foreground(t.Background())
			keyStyle = itemStyle.Foreground(t.Background())
		} else {
			nameStyle = itemStyle.Background(t.BackgroundPanel()).Foreground(t.Primary())
			descStyle = itemStyle.Background(t.BackgroundPanel()).Foreground(t.TextMuted())
			keyStyle = itemStyle.Background(t.BackgroundPanel()).Foreground(t.Accent())
		}

		var line string
		if cmd.KeyBinding != "" {
			line = lipgloss.JoinHorizontal(lipgloss.Left,
				nameStyle.Width(12).Render(cmd.Name),
				descStyle.Width(20).Render(cmd.Description),
				keyStyle.Render(cmd.KeyBinding),
			)
		} else {
			line = lipgloss.JoinHorizontal(lipgloss.Left,
				nameStyle.Width(12).Render(cmd.Name),
				descStyle.Render(cmd.Description),
			)
		}

		suggestionItems = append(suggestionItems, line)
	}

	return suggestionStyle.Render(strings.Join(suggestionItems, "\n"))
}

// HasSuggestions returns whether suggestions are currently showing
func (c CommandInput) HasSuggestions() bool {
	return c.showingSuggestions && len(c.suggestions) > 0
}

// View implements tea.Model (for backward compatibility)
func (c CommandInput) View() string {
	t := theme.CurrentTheme()
	suggestions := c.ViewSuggestions()
	input := c.ViewInput()
	content := lipgloss.JoinVertical(lipgloss.Left, suggestions, input)

	if suggestions != "" {

		return lipgloss.PlaceVertical(
			c.width,
			lipgloss.Center,
			content,
			styles.WhitespaceStyle(t.Background()),
		)

	}
	return input
}
