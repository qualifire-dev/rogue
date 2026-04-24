package scenarios

import (
	"encoding/json"
	"testing"
)

// Helper function for tests
func stringPtr(s string) *string { return &s }

func TestScenarioEditorBusinessContext(t *testing.T) {
	editor := NewScenarioEditor()

	// Newly-constructed editor has no scenario loaded; the editing buffer's
	// MultiTurn field is nil, which defaults to on → 5 visible fields
	// (scenario, expected outcome, multi-turn toggle, max turns, save).
	if editor.numFields() != 5 {
		t.Errorf("Expected 5 fields with multi-turn on by default, got %d", editor.numFields())
	}

	// Flip multi-turn off on the editing buffer and verify the Max Turns field
	// drops out of the cycle.
	off := false
	editor.editing.MultiTurn = &off
	if editor.numFields() != 4 {
		t.Errorf("Expected 4 fields with multi-turn off, got %d", editor.numFields())
	}

	// Test global business context handling
	editor.businessContext = stringPtr("Test business context")

	if editor.businessContext == nil {
		t.Error("Expected business context to be set")
	} else if *editor.businessContext != "Test business context" {
		t.Errorf("Expected 'Test business context', got '%s'", *editor.businessContext)
	}

	editor.businessContext = nil
	if editor.businessContext != nil {
		t.Error("Expected business context to be cleared")
	}
}

func TestScenarioDataDefaults(t *testing.T) {
	// Missing multi_turn / max_turns in the JSON should default to on / 10.
	raw := `{"scenario":"legacy","scenario_type":"policy"}`
	var s ScenarioData
	if err := json.Unmarshal([]byte(raw), &s); err != nil {
		t.Fatalf("unmarshal failed: %v", err)
	}
	if !s.MultiTurnEnabled() {
		t.Errorf("expected MultiTurnEnabled() == true for legacy JSON, got false")
	}
	if s.MaxTurnsValue() != MaxTurnsDefault {
		t.Errorf("expected MaxTurnsValue() == %d, got %d", MaxTurnsDefault, s.MaxTurnsValue())
	}

	// Explicit values should be preserved through (un)marshal.
	off := false
	maxT := 5
	withFlags := ScenarioData{
		Scenario:     "test",
		ScenarioType: "policy",
		MultiTurn:    &off,
		MaxTurns:     &maxT,
	}
	b, err := json.Marshal(withFlags)
	if err != nil {
		t.Fatalf("marshal failed: %v", err)
	}
	var roundtrip ScenarioData
	if err := json.Unmarshal(b, &roundtrip); err != nil {
		t.Fatalf("round-trip unmarshal failed: %v", err)
	}
	if roundtrip.MultiTurnEnabled() != false {
		t.Errorf("expected MultiTurn=false after round trip, got true")
	}
	if roundtrip.MaxTurnsValue() != 5 {
		t.Errorf("expected MaxTurns=5 after round trip, got %d", roundtrip.MaxTurnsValue())
	}
}

func TestValidateEditingClampsMaxTurns(t *testing.T) {
	editor := &ScenarioEditor{
		editing: ScenarioData{Scenario: "x"},
	}

	// Out of range → error.
	editor.maxTurnsBuffer = "0"
	if err := editor.validateEditing(); err == nil {
		t.Error("expected validation error for max_turns=0")
	}
	editor.maxTurnsBuffer = "500"
	if err := editor.validateEditing(); err == nil {
		t.Error("expected validation error for max_turns=500")
	}

	// Empty buffer → defaults to current editing value (or MaxTurnsDefault).
	editor.editing = ScenarioData{Scenario: "x"}
	editor.maxTurnsBuffer = ""
	if err := editor.validateEditing(); err != nil {
		t.Fatalf("unexpected validation error: %v", err)
	}
	if editor.editing.MaxTurnsValue() != MaxTurnsDefault {
		t.Errorf("expected default max_turns=%d, got %d", MaxTurnsDefault, editor.editing.MaxTurnsValue())
	}

	// Explicit in-range value is accepted and stored.
	editor.editing = ScenarioData{Scenario: "x"}
	editor.maxTurnsBuffer = "7"
	if err := editor.validateEditing(); err != nil {
		t.Fatalf("unexpected validation error: %v", err)
	}
	if editor.editing.MaxTurnsValue() != 7 {
		t.Errorf("expected max_turns=7, got %d", editor.editing.MaxTurnsValue())
	}
	if !editor.editing.MultiTurnEnabled() {
		t.Error("expected multi-turn to default to true after validateEditing")
	}
}

func TestNextFieldSkipsMaxTurnsWhenMultiTurnOff(t *testing.T) {
	off := false
	editor := &ScenarioEditor{
		editing: ScenarioData{Scenario: "x", MultiTurn: &off},
	}
	// From the toggle field, forward should skip Max Turns and go to Save.
	if got := editor.nextField(editFieldMultiTurnToggle, +1); got != editFieldSave {
		t.Errorf("expected nextField to skip Max Turns and reach Save (%d), got %d", editFieldSave, got)
	}
	// Turn multi-turn on — cycle should now land on Max Turns.
	on := true
	editor.editing.MultiTurn = &on
	if got := editor.nextField(editFieldMultiTurnToggle, +1); got != editFieldMaxTurns {
		t.Errorf("expected nextField to reach Max Turns (%d) with multi-turn on, got %d", editFieldMaxTurns, got)
	}
}
