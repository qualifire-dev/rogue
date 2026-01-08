package redteam

import (
	"os"
	"path/filepath"
	"testing"
)

func TestSaveAndLoadRedTeamConfig(t *testing.T) {
	// Create a temporary directory for testing
	tmpDir := t.TempDir()
	originalWd, _ := os.Getwd()
	defer os.Chdir(originalWd)

	// Change to temp directory
	os.Chdir(tmpDir)

	// Create initial state with some selections
	state := NewRedTeamConfigState()
	state.ScanType = ScanTypeCustom
	state.AttacksPerVulnerability = 5
	state.QualifireAPIKey = "test-api-key-123"
	state.SelectedVulnerabilities["prompt-extraction"] = true
	state.SelectedVulnerabilities["sql-injection"] = true
	state.SelectedAttacks["base64"] = true
	state.SelectedAttacks["social-engineering-prompt-extraction"] = true
	state.CategoryExpanded["Content Safety"] = true

	// Save the configuration
	err := SaveRedTeamConfig(state)
	if err != nil {
		t.Fatalf("Failed to save config: %v", err)
	}

	// Check that the file was created
	configPath := filepath.Join(tmpDir, ".rogue", "redteam.yaml")
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		t.Fatalf("Config file was not created at %s", configPath)
	}

	// Create a new state and load the configuration
	loadedState := NewRedTeamConfigState()
	// Clear the default values to test loading
	loadedState.ScanType = ScanTypeBasic
	loadedState.AttacksPerVulnerability = 3
	loadedState.QualifireAPIKey = ""
	loadedState.SelectedVulnerabilities = make(map[string]bool)
	loadedState.SelectedAttacks = make(map[string]bool)
	loadedState.CategoryExpanded = make(map[string]bool)

	err = LoadRedTeamConfig(loadedState)
	if err != nil {
		t.Fatalf("Failed to load config: %v", err)
	}

	// Verify the loaded values match the saved values
	if loadedState.ScanType != ScanTypeCustom {
		t.Errorf("Expected ScanType %v, got %v", ScanTypeCustom, loadedState.ScanType)
	}

	if loadedState.AttacksPerVulnerability != 5 {
		t.Errorf("Expected AttacksPerVulnerability 5, got %d", loadedState.AttacksPerVulnerability)
	}

	if loadedState.QualifireAPIKey != "test-api-key-123" {
		t.Errorf("Expected QualifireAPIKey 'test-api-key-123', got %s", loadedState.QualifireAPIKey)
	}

	if !loadedState.SelectedVulnerabilities["prompt-extraction"] {
		t.Error("Expected prompt-extraction to be selected")
	}

	if !loadedState.SelectedVulnerabilities["sql-injection"] {
		t.Error("Expected sql-injection to be selected")
	}

	if !loadedState.SelectedAttacks["base64"] {
		t.Error("Expected base64 to be selected")
	}

	if !loadedState.SelectedAttacks["social-engineering-prompt-extraction"] {
		t.Error("Expected social-engineering-prompt-extraction to be selected")
	}

	if !loadedState.CategoryExpanded["Content Safety"] {
		t.Error("Expected 'Content Safety' category to be expanded")
	}
}

func TestLoadNonExistentConfig(t *testing.T) {
	// Create a temporary directory for testing
	tmpDir := t.TempDir()
	originalWd, _ := os.Getwd()
	defer os.Chdir(originalWd)

	// Change to temp directory (no config file exists)
	os.Chdir(tmpDir)

	// Create a new state
	state := NewRedTeamConfigState()

	// Loading non-existent config should not error, just use defaults
	err := LoadRedTeamConfig(state)
	if err != nil {
		t.Fatalf("Expected no error loading non-existent config, got: %v", err)
	}

	// Verify defaults are still in place
	if state.ScanType != ScanTypeBasic {
		t.Errorf("Expected default ScanType %v, got %v", ScanTypeBasic, state.ScanType)
	}

	if state.AttacksPerVulnerability != 3 {
		t.Errorf("Expected default AttacksPerVulnerability 3, got %d", state.AttacksPerVulnerability)
	}
}
