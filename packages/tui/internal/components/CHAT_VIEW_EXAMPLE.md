# ChatView Component - Reusable Chat Interface

The `ChatView` component is a reusable, self-contained chat interface with message history, input field, and scrolling capabilities.

## Features

- **Message History**: Scrollable viewport displaying conversation
- **Multi-line Input**: TextArea for user input with shift+enter support
- **Focus Management**: Tab navigation between viewport and input
- **Smart Scrolling**:
  - Auto-scroll to bottom when new messages arrive (only if not manually scrolling)
  - Up/Down arrows scroll when viewport is focused
  - Down arrow at bottom automatically shifts focus to input
- **Loading State**: Built-in spinner for async operations
- **Error Handling**: Display error messages
- **Customizable**: Configurable prefixes, labels, and placeholders

## Basic Usage

```go
// Create a new ChatView
chatView := NewChatView(id, width, height, theme)

// Add messages
chatView.AddMessage("assistant", "Hello! How can I help you?")
chatView.AddMessage("user", "I need some help with...")

// Set loading state
chatView.SetLoading(true)

// Handle keyboard input
cmd := chatView.Update(keyMsg)

// Render the view
content := chatView.View(theme)
```

## Customization

```go
// Custom message prefixes
chatView.SetPrefixes("🧑 User: ", "🤖 Bot: ")

// Custom input label and placeholder
chatView.SetInputLabel("Ask a question:")
chatView.SetInputPlaceholder("Type your question here...")

// Show progress bar
chatView.SetProgressBar(true, 5) // Enable progress, max 5 responses

// Resize
chatView.SetSize(newWidth, newHeight)
```

## State Management

```go
// Get input value
message := chatView.GetInputValue()

// Clear input
chatView.ClearInput()

// Check if loading
if chatView.IsLoading() {
    // Handle loading state
}

// Check if viewport is focused
if chatView.IsViewportFocused() {
    // Viewport is focused for scrolling
}

// Focus control
chatView.FocusInput()
chatView.FocusViewport()

// Error handling
chatView.SetError("Connection failed")
chatView.ClearError()

// Get all messages
messages := chatView.GetMessages()

// Clear all messages
chatView.ClearMessages()
```

## Keyboard Controls

### Normal Mode (Input or Viewport)

- **Tab**: Switch focus between viewport and input
- **Shift+Tab**: Switch focus (reverse direction)
- **↑**: Focus viewport / Scroll up when focused
- **↓**: Scroll down when viewport focused / Move to input when at bottom
- **Enter**: Send message (when input focused)
- **Shift+Enter**: New line in input

### Automatic Behaviors

- When viewport is at bottom and user presses ↓, focus automatically moves to input
- Auto-scrolls to bottom when new messages arrive (unless viewport is manually focused)
- Help text updates based on current focus state

## Integration Example

See `scenario_interview.go` for a complete integration example, including:

- Custom approval mode with additional button
- Interview progress tracking
- Session management
- Error handling

## Component Structure

```
ChatView
├── Viewport (message history)
├── TextArea (user input)
├── Spinner (loading indicator)
└── State (focus, loading, errors)
```

## Benefits

✅ **Reusable**: Drop into any part of your TUI
✅ **Self-contained**: Manages its own state and components
✅ **Accessible**: Clear focus indicators and keyboard navigation
✅ **Smart**: Auto-scroll, auto-focus, context-aware help
✅ **Flexible**: Customizable appearance and behavior
