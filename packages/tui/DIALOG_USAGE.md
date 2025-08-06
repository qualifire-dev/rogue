# Dialog System Usage

The TUI now includes a comprehensive dialog system built with lipgloss v2 that provides modal overlay capabilities.

## Features

- **Modal Overlays**: Dialogs render as overlays on top of existing content
- **Multiple Dialog Types**: Info, Confirmation, Input, and Custom dialogs
- **Keyboard Navigation**: Full keyboard support with Tab/Shift+Tab navigation
- **Theme Integration**: Dialogs use the existing theme system for consistent styling
- **Backdrop Effects**: Semi-transparent backdrop for visual separation

## Dialog Types

### Info Dialog
Simple message dialog with an OK button.
```go
dialog := components.NewInfoDialog("Title", "Message")
```

### Confirmation Dialog
Yes/No or OK/Cancel dialog for user confirmation.
```go
dialog := components.NewConfirmationDialog("Title", "Are you sure?")
```

### Input Dialog
Dialog with text input field for user input.
```go
dialog := components.NewInputDialog("Title", "Enter value:", "placeholder")
```

### Custom Dialog
Flexible dialog with custom content rendering.
```go
dialog := components.NewCustomDialog("Title", customViewFunc, buttons)
```

## Helper Functions

The `dialog_helpers.go` file provides utility functions for common dialog patterns:

- `ShowErrorDialog()` - Error dialog with danger-styled button
- `ShowWarningDialog()` - Warning dialog with continue/cancel options
- `ShowDeleteConfirmationDialog()` - Delete confirmation with safety defaults
- `ShowAboutDialog()` - About dialog with app information

## Keyboard Controls

When a dialog is open:
- **Tab/Right Arrow**: Navigate to next button
- **Shift+Tab/Left Arrow**: Navigate to previous button
- **Enter**: Activate selected button
- **Escape**: Cancel/close dialog
- **Text Input** (Input dialogs): Type to enter text
- **Ctrl+A/Ctrl+E**: Move cursor to start/end of input

## Usage Examples

### Opening Dialogs via Commands
- `/dialog-info` - Show info dialog example
- `/dialog-input` - Show input dialog example
- `/dialog-error` - Show error dialog example
- `/dialog-about` - Show about dialog
- `/quit` - Show quit confirmation dialog

### Opening Dialogs via Keyboard
- **Ctrl+D** - Show demo dialog

### Programmatic Usage
```go
// Open a dialog
dialog := components.NewInfoDialog("Title", "Message")
model.dialog = &dialog

// Handle dialog result in Update()
case components.DialogClosedMsg:
    if msg.Action == "ok" {
        // Handle OK action
    }
    model.dialog = nil
```

## Implementation Details

- Dialogs are rendered using lipgloss v2's `Place` function for precise positioning
- The backdrop uses Unicode characters for a semi-transparent effect
- Dialog state is managed in the main Model struct
- Input handling prioritizes dialog events when a dialog is open
- The dialog system supports nested dialogs via a dialog stack (future enhancement)

## Styling

Dialogs automatically use the current theme colors:
- **Primary buttons**: Use theme primary color
- **Secondary buttons**: Use theme border color
- **Danger buttons**: Use theme error color
- **Backgrounds**: Use theme panel background
- **Borders**: Use theme primary color for active dialogs
