# MessageHistoryView Component - Reusable Scrollable Message Display

The `MessageHistoryView` component is a lightweight, reusable component for displaying and scrolling through message history. Perfect for chat interfaces, logs, conversation displays, and any scenario where you need to show a scrollable list of messages.

## Features

- **Scrollable Viewport**: Auto-scrolling message display with manual scroll control
- **Focus Management**: Can be focused for scrolling or blurred
- **Smart Auto-Scroll**: Auto-scrolls to bottom when new messages arrive (only if not focused)
- **Loading Indicator**: Built-in spinner for async operations
- **Customizable**: Custom prefixes, colors, and styling
- **Lightweight**: Single responsibility - just message display and scrolling

## Basic Usage

```go
// Create a new MessageHistoryView
messageHistory := NewMessageHistoryView(id, width, height)

// Add messages
messageHistory.AddMessage("assistant", "Hello! How can I help you?")
messageHistory.AddMessage("user", "I need some help with...")

// Enable loading spinner
messageHistory.SetSpinner(true)

// Render the view
content := messageHistory.View(theme)
```

## Customization

```go
// Custom message prefixes
messageHistory.SetPrefixes("👨 User: ", "🤖 Bot: ")

// Custom colors (hex or ANSI color names)
messageHistory.SetColors("#FF5733", "#3366FF")

// Resize
messageHistory.SetSize(newWidth, newHeight)
```

## Focus and Scrolling

```go
// Focus the viewport for scrolling
messageHistory.Focus()

// Check if focused
if messageHistory.IsFocused() {
    // Handle focused state
}

// Scroll programmatically
messageHistory.ScrollUp(1)
messageHistory.ScrollDown(1)

// Check if at bottom
if messageHistory.AtBottom() {
    // User has scrolled to bottom
}

// Jump to bottom
messageHistory.GotoBottom()

// Blur (unfocus) the viewport
messageHistory.Blur()
```

## Loading State

```go
// Show loading spinner
messageHistory.SetSpinner(true)

// Start spinner animation (returns tea.Cmd)
cmd := messageHistory.StartSpinner()

// Stop spinner
messageHistory.StopSpinner()
```

## Message Management

```go
// Get all messages
messages := messageHistory.GetMessages()

// Clear all messages
messageHistory.ClearMessages()

// Messages can be iterated
for _, msg := range messages {
    fmt.Printf("%s: %s\n", msg.Role, msg.Content)
}
```

## Rendering Options

```go
// Render with border (default)
content := messageHistory.View(theme)

// Render without border (just viewport content)
content := messageHistory.ViewWithoutBorder(theme)
```

## Auto-Scroll Behavior

The component implements smart auto-scrolling:

- **When NOT focused**: Automatically scrolls to bottom when new messages are added
- **When focused**: Maintains user's scroll position (they're reading old messages)
- **When scrolled to bottom and DOWN is pressed**: Can trigger focus change (handled by parent)

## Integration with ChatView

`ChatView` now uses `MessageHistoryView` internally:

```go
type ChatView struct {
    messageHistory *MessageHistoryView
    input          *TextArea
    // ...
}
```

This makes `ChatView` cleaner and allows reuse of `MessageHistoryView` elsewhere.

## Standalone Usage Examples

### Simple Log Display

```go
logView := NewMessageHistoryView(1, 80, 20)
logView.SetPrefixes("[INFO] ", "[ERROR] ")
logView.AddMessage("assistant", "Application started")
logView.AddMessage("user", "Connection failed")
```

### Conversation History (Read-Only)

```go
history := NewMessageHistoryView(2, 100, 30)
history.SetPrefixes("Customer: ", "Agent: ")

// Load conversation from database
for _, msg := range dbMessages {
    history.AddMessage(msg.Sender, msg.Text)
}

// Display (read-only, no input field needed)
content := history.View(theme)
```

### AI Assistant Response Display

```go
responseView := NewMessageHistoryView(3, 120, 40)
responseView.SetSpinner(true) // Show loading while AI thinks

// When response arrives
responseView.AddMessage("assistant", aiResponse)
responseView.SetSpinner(false)
```

## Benefits

✅ **Focused**: Single responsibility - just message display  
✅ **Reusable**: Drop anywhere you need scrollable messages  
✅ **Independent**: Works standalone or as part of larger components  
✅ **Smart**: Auto-scroll only when appropriate  
✅ **Lightweight**: Minimal dependencies  
✅ **Flexible**: With/without borders, custom colors, custom prefixes

## Comparison with ChatView

| Feature         | MessageHistoryView | ChatView                    |
| --------------- | ------------------ | --------------------------- |
| Message display | ✅                 | ✅ (via MessageHistoryView) |
| Scrolling       | ✅                 | ✅ (delegated)              |
| Input field     | ❌                 | ✅                          |
| Help text       | ❌                 | ✅                          |
| Error display   | ❌                 | ✅                          |
| Standalone      | ✅                 | ✅                          |
| Use case        | Any message list   | Full chat interface         |

## When to Use

**Use MessageHistoryView when:**

- You need a scrollable message display
- You don't need an input field
- You want maximum flexibility
- You're building a custom chat-like interface

**Use ChatView when:**

- You need a complete chat interface
- You want input + history combined
- You need help text and error handling
- You want a ready-to-use solution
