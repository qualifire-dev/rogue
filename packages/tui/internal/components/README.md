# Components

This package contains reusable UI components for the TUI application.

## TextArea Component

The `TextArea` component provides a multi-line text input interface with full keyboard navigation support.

### Features

- Multi-line text editing
- Keyboard navigation (arrow keys, word navigation, line navigation)
- Character and word deletion
- Line insertion and deletion
- Character limits
- Line number display
- Customizable prompts
- Placeholder text
- Focus management
- Styling with lipgloss

### Basic Usage

```go
package main

import (
    "github.com/rogue/tui/internal/components"
    tea "github.com/charmbracelet/bubbletea/v2"
)

type MyModel struct {
    textarea components.TextArea
}

func NewMyModel() MyModel {
    ta := components.NewTextArea(1, 50, 10)
    ta.Placeholder = "Enter your text here..."
    ta.Prompt = "> "
    ta.PromptWidth = 2
    ta.ShowLineNumbers = true
    ta.Focus()

    return MyModel{
        textarea: ta,
    }
}

func (m MyModel) Init() tea.Cmd {
    return nil
}

func (m MyModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    ta, cmd := m.textarea.Update(msg)
    m.textarea = *ta
    return m, cmd
}

func (m MyModel) View() string {
    return m.textarea.View()
}

func main() {
    p := tea.NewProgram(NewMyModel())
    p.Run()
}
```

### Key Bindings

The textarea supports the following default key bindings:

- **Navigation:**

  - `left/ctrl+b` - Move cursor left
  - `right/ctrl+f` - Move cursor right
  - `up/ctrl+p` - Move cursor up
  - `down/ctrl+n` - Move cursor down
  - `alt+left/alt+b` - Move cursor one word left
  - `alt+right/alt+f` - Move cursor one word right
  - `home/ctrl+a` - Move to beginning of line
  - `end/ctrl+e` - Move to end of line
  - `alt+</ctrl+home` - Move to beginning of text
  - `alt+>/ctrl+end` - Move to end of text

- **Editing:**
  - `backspace/ctrl+h` - Delete character before cursor
  - `delete/ctrl+d` - Delete character after cursor
  - `alt+backspace/ctrl+w` - Delete word before cursor
  - `alt+delete/alt+d` - Delete word after cursor
  - `ctrl+k` - Delete from cursor to end of line
  - `ctrl+u` - Delete from cursor to beginning of line
  - `enter/ctrl+m` - Insert newline

### Configuration

#### Styling

```go
ta := components.NewTextArea(1, 50, 10)
ta.Style = components.TextAreaStyle{
    Base:        lipgloss.NewStyle().Border(lipgloss.RoundedBorder()),
    Text:        lipgloss.NewStyle().Foreground(lipgloss.Color("15")),
    Cursor:      lipgloss.NewStyle().Background(lipgloss.Color("7")),
    Placeholder: lipgloss.NewStyle().Foreground(lipgloss.Color("240")),
}
```

#### Limits

```go
ta.CharLimit = 1000  // Maximum characters
ta.MaxHeight = 50    // Maximum lines
ta.MaxWidth = 200    // Maximum width
```

#### Display Options

```go
ta.ShowLineNumbers = true  // Show line numbers
ta.Prompt = "> "           // Custom prompt
ta.PromptWidth = 2         // Prompt width
ta.Placeholder = "Enter text..."  // Placeholder text
```

### Methods

#### Content Management

- `SetValue(string)` - Set the entire content
- `GetValue() string` - Get the entire content
- `InsertString(string)` - Insert text at cursor position
- `InsertRune(rune)` - Insert a single rune at cursor position
- `Reset()` - Clear all content

#### Cursor Control

- `SetCursor(row, col int)` - Set cursor position
- `GetCursor() (row, col int)` - Get current cursor position
- `Focus()` - Set focus
- `Blur()` - Remove focus
- `IsFocused() bool` - Check if focused

#### Information

- `Length() int` - Get total character count
- `LineCount() int` - Get number of lines
- `SetSize(width, height int)` - Resize the textarea

### Example

See `textarea_example.go` for a complete working example.

### Testing

Run the tests with:

```bash
go test ./internal/components -v
```
