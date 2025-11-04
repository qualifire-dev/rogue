package scenarios

import (
	"testing"
)

// Helper function for tests
func stringPtr(s string) *string { return &s }

func TestScenarioEditorBusinessContext(t *testing.T) {
	editor := NewScenarioEditor()

	// Test that business context is now global (not a per-scenario field)
	if editor.numFields() != 3 {
		t.Errorf("Expected 3 fields (scenario, expected outcome, save), got %d", editor.numFields())
	}

	// Test global business context handling
	editor.businessContext = stringPtr("Test business context")

	// Test business context text handling
	if editor.businessContext == nil {
		t.Error("Expected business context to be set")
	} else if *editor.businessContext != "Test business context" {
		t.Errorf("Expected 'Test business context', got '%s'", *editor.businessContext)
	}

	// Test clearing business context
	editor.businessContext = nil
	if editor.businessContext != nil {
		t.Error("Expected business context to be cleared")
	}
}
