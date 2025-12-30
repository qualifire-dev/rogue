// Package redteam provides persistence for red team configuration.
package redteam

import (
	"fmt"
	"os"
	"path/filepath"

	"gopkg.in/yaml.v3"
)

// RedTeamConfig represents the serializable red team configuration
type RedTeamConfigFile struct {
	ScanType                string          `yaml:"scan_type"`
	SelectedVulnerabilities []string        `yaml:"vulnerabilities"`
	SelectedAttacks         []string        `yaml:"attacks"`
	SelectedFrameworks      []string        `yaml:"frameworks,omitempty"`
	AttacksPerVulnerability int             `yaml:"attacks_per_vulnerability"`
	QualifireAPIKey         string          `yaml:"qualifire_api_key,omitempty"`
	CategoryExpanded        map[string]bool `yaml:"category_expanded,omitempty"`
}

// discoverRedTeamConfigFile walks up from CWD to root to find .rogue/redteam.yaml
func discoverRedTeamConfigFile() string {
	// Walk up from CWD to root to find .rogue/redteam.yaml
	wd, err := os.Getwd()
	if err == nil {
		dir := wd
		for {
			p := filepath.Join(dir, ".rogue", "redteam.yaml")
			if _, err := os.Stat(p); err == nil {
				return p
			}
			parent := filepath.Dir(dir)
			if parent == dir {
				break
			}
			dir = parent
		}
	}
	// Fallback to CWD/.rogue/redteam.yaml (may not exist yet)
	if err == nil {
		return filepath.Join(wd, ".rogue", "redteam.yaml")
	}
	return ".rogue/redteam.yaml"
}

// SaveRedTeamConfig saves the red team configuration to .rogue/redteam.yaml
func SaveRedTeamConfig(state *RedTeamConfigState) error {
	filePath := discoverRedTeamConfigFile()

	// Create .rogue directory if it doesn't exist
	dir := filepath.Dir(filePath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create .rogue directory: %w", err)
	}

	// Convert state to serializable format
	config := RedTeamConfigFile{
		ScanType:                string(state.ScanType),
		AttacksPerVulnerability: state.AttacksPerVulnerability,
		QualifireAPIKey:         state.QualifireAPIKey,
		CategoryExpanded:        state.CategoryExpanded,
	}

	// Convert selected vulnerabilities map to slice
	for id, selected := range state.SelectedVulnerabilities {
		if selected {
			config.SelectedVulnerabilities = append(config.SelectedVulnerabilities, id)
		}
	}

	// Convert selected attacks map to slice
	for id, selected := range state.SelectedAttacks {
		if selected {
			config.SelectedAttacks = append(config.SelectedAttacks, id)
		}
	}

	// Convert selected frameworks map to slice
	for id, selected := range state.SelectedFrameworks {
		if selected {
			config.SelectedFrameworks = append(config.SelectedFrameworks, id)
		}
	}

	// Marshal to YAML
	data, err := yaml.Marshal(&config)
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	// Write to file
	if err := os.WriteFile(filePath, data, 0644); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	return nil
}

// LoadRedTeamConfig loads the red team configuration from .rogue/redteam.yaml
func LoadRedTeamConfig(state *RedTeamConfigState) error {
	filePath := discoverRedTeamConfigFile()

	// Check if config file exists
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		// Config file doesn't exist, use defaults (already set in NewRedTeamConfigState)
		return nil
	}

	// Read config file
	data, err := os.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("failed to read config file: %w", err)
	}

	// Unmarshal YAML
	var config RedTeamConfigFile
	if err := yaml.Unmarshal(data, &config); err != nil {
		return fmt.Errorf("failed to unmarshal config: %w", err)
	}

	// Apply loaded config to state
	state.ScanType = ScanType(config.ScanType)
	state.AttacksPerVulnerability = config.AttacksPerVulnerability
	if config.QualifireAPIKey != "" {
		state.QualifireAPIKey = config.QualifireAPIKey
	}

	// Load category expansion state
	if config.CategoryExpanded != nil {
		for key, expanded := range config.CategoryExpanded {
			state.CategoryExpanded[key] = expanded
		}
	}

	// Load selected vulnerabilities
	state.SelectedVulnerabilities = make(map[string]bool)
	for _, id := range config.SelectedVulnerabilities {
		state.SelectedVulnerabilities[id] = true
	}

	// Load selected attacks
	state.SelectedAttacks = make(map[string]bool)
	for _, id := range config.SelectedAttacks {
		state.SelectedAttacks[id] = true
	}

	// Load selected frameworks
	state.SelectedFrameworks = make(map[string]bool)
	for _, id := range config.SelectedFrameworks {
		state.SelectedFrameworks[id] = true
	}

	return nil
}

// GetRedTeamConfigPath returns the path where the config file is (or will be) saved
func GetRedTeamConfigPath() string {
	return discoverRedTeamConfigFile()
}
