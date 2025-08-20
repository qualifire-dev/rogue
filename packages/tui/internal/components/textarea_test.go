package components

import (
	"testing"
)

func TestNewTextArea(t *testing.T) {
	ta := NewTextArea(1, 50, 10)

	if ta.ID != 1 {
		t.Errorf("Expected ID 1, got %d", ta.ID)
	}

	if ta.Width != 50 {
		t.Errorf("Expected width 50, got %d", ta.Width)
	}

	if ta.Height != 10 {
		t.Errorf("Expected height 10, got %d", ta.Height)
	}

	if !ta.IsFocused() {
		t.Error("Expected textarea to be focused by default")
	}
}

func TestTextAreaSetValue(t *testing.T) {
	ta := NewTextArea(1, 50, 10)

	ta.SetValue("Hello\nWorld")

	expected := "Hello\nWorld"
	if ta.GetValue() != expected {
		t.Errorf("Expected '%s', got '%s'", expected, ta.GetValue())
	}

	if ta.LineCount() != 2 {
		t.Errorf("Expected 2 lines, got %d", ta.LineCount())
	}
}

func TestTextAreaInsertString(t *testing.T) {
	ta := NewTextArea(1, 50, 10)

	ta.InsertString("Hello")

	if ta.GetValue() != "Hello" {
		t.Errorf("Expected 'Hello', got '%s'", ta.GetValue())
	}

	ta.InsertString(" World")

	if ta.GetValue() != "Hello World" {
		t.Errorf("Expected 'Hello World', got '%s'", ta.GetValue())
	}
}

func TestTextAreaCursorMovement(t *testing.T) {
	ta := NewTextArea(1, 50, 10)
	ta.SetValue("Hello\nWorld")

	// Test cursor position
	row, col := ta.GetCursor()
	if row != 0 || col != 0 {
		t.Errorf("Expected cursor at (0,0), got (%d,%d)", row, col)
	}

	// Test setting cursor
	ta.SetCursor(1, 2)
	row, col = ta.GetCursor()
	if row != 1 || col != 2 {
		t.Errorf("Expected cursor at (1,2), got (%d,%d)", row, col)
	}
}

func TestTextAreaCharacterLimit(t *testing.T) {
	ta := NewTextArea(1, 50, 10)
	ta.CharLimit = 5

	ta.InsertString("Hello World")

	if ta.GetValue() != "Hello" {
		t.Errorf("Expected 'Hello', got '%s'", ta.GetValue())
	}
}

func TestTextAreaLineCount(t *testing.T) {
	ta := NewTextArea(1, 50, 10)

	if ta.LineCount() != 1 {
		t.Errorf("Expected 1 line, got %d", ta.LineCount())
	}

	ta.SetValue("Line 1\nLine 2\nLine 3")

	if ta.LineCount() != 3 {
		t.Errorf("Expected 3 lines, got %d", ta.LineCount())
	}
}

func TestTextAreaLength(t *testing.T) {
	ta := NewTextArea(1, 50, 10)

	if ta.Length() != 0 {
		t.Errorf("Expected length 0, got %d", ta.Length())
	}

	ta.SetValue("Hello\nWorld")

	// "Hello\nWorld" = 11 characters (including newline)
	if ta.Length() != 11 {
		t.Errorf("Expected length 11, got %d", ta.Length())
	}
}

func TestTextAreaFocus(t *testing.T) {
	ta := NewTextArea(1, 50, 10)

	if !ta.IsFocused() {
		t.Error("Expected textarea to be focused by default")
	}

	ta.Blur()
	if ta.IsFocused() {
		t.Error("Expected textarea to be blurred")
	}

	ta.Focus()
	if !ta.IsFocused() {
		t.Error("Expected textarea to be focused")
	}
}

func TestTextAreaReset(t *testing.T) {
	ta := NewTextArea(1, 50, 10)
	ta.SetValue("Hello\nWorld")

	ta.Reset()

	if ta.GetValue() != "" {
		t.Errorf("Expected empty value after reset, got '%s'", ta.GetValue())
	}

	if ta.LineCount() != 1 {
		t.Errorf("Expected 1 line after reset, got %d", ta.LineCount())
	}

	row, col := ta.GetCursor()
	if row != 0 || col != 0 {
		t.Errorf("Expected cursor at (0,0) after reset, got (%d,%d)", row, col)
	}
}
