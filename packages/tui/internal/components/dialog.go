package components

import (
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// DialogType represents the type of dialog
type DialogType int

const (
	InfoDialog DialogType = iota
	ConfirmationDialog
	InputDialog
	CustomDialog
)

// DialogButton represents a button in the dialog
type DialogButton struct {
	Label  string
	Action string
	Style  ButtonStyle
}

// ButtonStyle represents the visual style of a button
type ButtonStyle int

const (
	PrimaryButton ButtonStyle = iota
	SecondaryButton
	DangerButton
)

// Dialog represents a modal dialog component
type Dialog struct {
	Type        DialogType
	Title       string
	Message     string
	Buttons     []DialogButton
	Input       string
	InputCursor int
	Width       int
	Height      int
	Focused     bool
	SelectedBtn int
	CustomView  func() string
	OnClose     func(action string, input string)
}

// DialogClosedMsg is sent when a dialog is closed
type DialogClosedMsg struct {
	Action string
	Input  string
}

// DialogOpenMsg is sent to open a dialog
type DialogOpenMsg struct {
	Dialog Dialog
}

// NewInfoDialog creates a new info dialog
func NewInfoDialog(title, message string) Dialog {
	return Dialog{
		Type:    InfoDialog,
		Title:   title,
		Message: message,
		Buttons: []DialogButton{
			{Label: "OK", Action: "ok", Style: PrimaryButton},
		},
		Width:       50,
		Height:      10,
		Focused:     true,
		SelectedBtn: 0,
	}
}

// NewConfirmationDialog creates a new confirmation dialog
func NewConfirmationDialog(title, message string) Dialog {
	return Dialog{
		Type:    ConfirmationDialog,
		Title:   title,
		Message: message,
		Buttons: []DialogButton{
			{Label: "Cancel", Action: "cancel", Style: SecondaryButton},
			{Label: "OK", Action: "ok", Style: PrimaryButton},
		},
		Width:       50,
		Height:      10,
		Focused:     true,
		SelectedBtn: 1, // Default to OK button
	}
}

// NewInputDialog creates a new input dialog
func NewInputDialog(title, message, placeholder string) Dialog {
	return Dialog{
		Type:    InputDialog,
		Title:   title,
		Message: message,
		Input:   placeholder,
		Buttons: []DialogButton{
			{Label: "Cancel", Action: "cancel", Style: SecondaryButton},
			{Label: "OK", Action: "ok", Style: PrimaryButton},
		},
		Width:       60,
		Height:      12,
		Focused:     true,
		SelectedBtn: 1,
	}
}

// NewCustomDialog creates a new custom dialog
func NewCustomDialog(title string, customView func() string, buttons []DialogButton) Dialog {
	return Dialog{
		Type:        CustomDialog,
		Title:       title,
		CustomView:  customView,
		Buttons:     buttons,
		Width:       60,
		Height:      15,
		Focused:     true,
		SelectedBtn: len(buttons) - 1, // Default to last button
	}
}

// Update handles dialog input and updates
func (d Dialog) Update(msg tea.Msg) (Dialog, tea.Cmd) {
	if !d.Focused {
		return d, nil
	}

	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "escape", "esc":
			return d, func() tea.Msg {
				return DialogClosedMsg{Action: "cancel", Input: d.Input}
			}

		case "enter":
			selectedAction := "ok"
			if d.SelectedBtn < len(d.Buttons) {
				selectedAction = d.Buttons[d.SelectedBtn].Action
			}
			return d, func() tea.Msg {
				return DialogClosedMsg{Action: selectedAction, Input: d.Input}
			}

		case "tab", "right":
			// In input dialogs, use left/right to move the text cursor
			if d.Type == InputDialog {
				if d.InputCursor < len(d.Input) {
					d.InputCursor++
				}
				return d, nil
			}
			if len(d.Buttons) > 1 {
				d.SelectedBtn = (d.SelectedBtn + 1) % len(d.Buttons)
			}
			return d, nil

		case "shift+tab", "left":
			// In input dialogs, use left/right to move the text cursor
			if d.Type == InputDialog {
				if d.InputCursor > 0 {
					d.InputCursor--
				}
				return d, nil
			}
			if len(d.Buttons) > 1 {
				d.SelectedBtn = (d.SelectedBtn - 1 + len(d.Buttons)) % len(d.Buttons)
			}
			return d, nil

		case "backspace":
			if d.Type == InputDialog && d.InputCursor > 0 && len(d.Input) > 0 {
				d.Input = d.Input[:d.InputCursor-1] + d.Input[d.InputCursor:]
				d.InputCursor--
			}
			return d, nil

		case "delete":
			if d.Type == InputDialog && d.InputCursor < len(d.Input) {
				d.Input = d.Input[:d.InputCursor] + d.Input[d.InputCursor+1:]
			}
			return d, nil

		case "ctrl+a":
			if d.Type == InputDialog {
				d.InputCursor = 0
			}
			return d, nil

		case "ctrl+e":
			if d.Type == InputDialog {
				d.InputCursor = len(d.Input)
			}
			return d, nil

		default:
			// Handle regular character input for InputDialog
			if d.Type == InputDialog && len(msg.String()) == 1 {
				char := msg.String()
				d.Input = d.Input[:d.InputCursor] + char + d.Input[d.InputCursor:]
				d.InputCursor++
			}
			return d, nil
		}
	}

	return d, nil
}

// View renders the dialog
func (d Dialog) View() string {
	t := theme.CurrentTheme()

	// Create dialog container style
	dialogStyle := lipgloss.NewStyle().
		Width(d.Width).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Primary()).
		Background(t.BackgroundPanel()).
		Padding(1, 2)

	// Create title style
	titleStyle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Bold(true).
		Align(lipgloss.Center).
		Width(d.Width - 4)

	// Create message style
	messageStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Width(d.Width - 4).
		Align(lipgloss.Left)

	// Build dialog content
	var content []string

	// Add title
	if d.Title != "" {
		content = append(content, titleStyle.Render(d.Title))
		content = append(content, "")
	}

	// Add message or custom content
	switch d.Type {
	case InfoDialog, ConfirmationDialog:
		if d.Message != "" {
			// Wrap message text
			wrappedMessage := d.wrapText(d.Message, d.Width-4)
			content = append(content, messageStyle.Render(wrappedMessage))
		}

	case InputDialog:
		if d.Message != "" {
			wrappedMessage := d.wrapText(d.Message, d.Width-4)
			content = append(content, messageStyle.Render(wrappedMessage))
			content = append(content, "")
		}

		// Add input field
		inputStyle := lipgloss.NewStyle().
			Width(d.Width-6).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(t.Border()).
			Background(t.Background()).
			Padding(0, 1)

		// Render input with cursor
		var inputText string
		if d.InputCursor == len(d.Input) {
			inputText = d.Input + "█"
		} else {
			inputText = d.Input[:d.InputCursor] + "█" + d.Input[d.InputCursor:]
		}

		content = append(content, inputStyle.Render(inputText))

	case CustomDialog:
		if d.CustomView != nil {
			content = append(content, d.CustomView())
		}
	}

	// Add spacing before buttons
	content = append(content, "")

	// Add buttons
	if len(d.Buttons) > 0 {
		buttonRow := d.renderButtons(t)
		content = append(content, buttonRow)
	}

	// Join all content
	dialogContent := strings.Join(content, "\n")

	return dialogStyle.Render(dialogContent)
}

// ViewWithBackdrop renders the dialog with a backdrop overlay
func (d Dialog) ViewWithBackdrop(screenWidth, screenHeight int) string {
	t := theme.CurrentTheme()
	dialogView := d.View()

	// Create backdrop character with theme background
	backdropChar := " "

	// Position dialog in center of screen with backdrop using theme background
	return lipgloss.Place(
		screenWidth,
		screenHeight,
		lipgloss.Center,
		lipgloss.Center,
		dialogView,
		lipgloss.WithWhitespaceChars(backdropChar),
		lipgloss.WithWhitespaceStyle(lipgloss.NewStyle().Background(t.Background())),
	)
}

// renderButtons renders the button row
func (d Dialog) renderButtons(t theme.Theme) string {
	if len(d.Buttons) == 0 {
		return ""
	}

	var buttons []string
	for i, btn := range d.Buttons {
		buttonStyle := lipgloss.NewStyle().
			Padding(0, 2).
			Border(lipgloss.RoundedBorder()).
			Align(lipgloss.Center)

		// Apply button styling based on type and selection
		switch btn.Style {
		case PrimaryButton:
			if i == d.SelectedBtn {
				buttonStyle = buttonStyle.
					Background(t.Primary()).
					Foreground(t.Background()).
					BorderForeground(t.Primary()).
					Bold(true)
			} else {
				buttonStyle = buttonStyle.
					Background(t.BackgroundElement()).
					Foreground(t.Primary()).
					BorderForeground(t.Primary())
			}

		case SecondaryButton:
			if i == d.SelectedBtn {
				buttonStyle = buttonStyle.
					Background(t.Border()).
					Foreground(t.Background()).
					BorderForeground(t.Border()).
					Bold(true)
			} else {
				buttonStyle = buttonStyle.
					Background(t.BackgroundElement()).
					Foreground(t.Text()).
					BorderForeground(t.Border())
			}

		case DangerButton:
			if i == d.SelectedBtn {
				buttonStyle = buttonStyle.
					Background(t.Error()).
					Foreground(t.Background()).
					BorderForeground(t.Error()).
					Bold(true)
			} else {
				buttonStyle = buttonStyle.
					Background(t.BackgroundElement()).
					Foreground(t.Error()).
					BorderForeground(t.Error())
			}
		}

		buttons = append(buttons, buttonStyle.Render(btn.Label))
	}

	// Join buttons horizontally with spacing
	buttonRow := lipgloss.JoinHorizontal(lipgloss.Center, buttons...)

	// Center the button row
	return lipgloss.NewStyle().
		Width(d.Width - 4).
		Align(lipgloss.Center).
		Render(buttonRow)
}

// wrapText wraps text to fit within the specified width
func (d Dialog) wrapText(text string, width int) string {
	if len(text) <= width {
		return text
	}

	var lines []string
	words := strings.Fields(text)
	var currentLine strings.Builder

	for _, word := range words {
		if currentLine.Len() == 0 {
			currentLine.WriteString(word)
		} else if currentLine.Len()+1+len(word) <= width {
			currentLine.WriteString(" " + word)
		} else {
			lines = append(lines, currentLine.String())
			currentLine.Reset()
			currentLine.WriteString(word)
		}
	}

	if currentLine.Len() > 0 {
		lines = append(lines, currentLine.String())
	}

	return strings.Join(lines, "\n")
}

// SetFocus sets the focus state of the dialog
func (d *Dialog) SetFocus(focused bool) {
	d.Focused = focused
}

// IsFocused returns whether the dialog is focused
func (d Dialog) IsFocused() bool {
	return d.Focused
}
