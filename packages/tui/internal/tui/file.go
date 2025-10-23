package tui

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
)

// discoverScenariosFile walks up from CWD to root to find .rogue/scenarios.json
func discoverScenariosFile() string {
	// Walk up from CWD to root to find .rogue/scenarios.json
	wd, err := os.Getwd()
	if err == nil {
		dir := wd
		for {
			p := filepath.Join(dir, ".rogue", "scenarios.json")
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
	// Fallback to CWD/.rogue/scenarios.json (may not exist yet)
	if err == nil {
		return filepath.Join(wd, ".rogue", "scenarios.json")
	}
	return ".rogue/scenarios.json"
}

// loadScenarios loads scenarios from filePath
func (e *ScenarioEditor) loadScenarios() error {
	if e.filePath == "" {
		e.filePath = discoverScenariosFile()
	}
	data, err := os.ReadFile(e.filePath)
	if err != nil {
		if os.IsNotExist(err) {
			e.scenarios = []ScenarioData{}
			return nil
		}
		return err
	}
	var file ScenariosFile
	if err := json.Unmarshal(data, &file); err != nil {
		return err
	}
	e.scenarios = file.Scenarios
	e.businessContext = file.BusinessContext
	return nil
}

// saveScenarios saves scenarios to filePath, creating .rogue directory if needed
func (e *ScenarioEditor) saveScenarios() error {
	if e.filePath == "" {
		e.filePath = discoverScenariosFile()
	}
	dir := filepath.Dir(e.filePath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return err
	}
	file := ScenariosFile{
		BusinessContext: e.businessContext,
		Scenarios:       e.scenarios,
	}
	data, err := json.MarshalIndent(file, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(e.filePath, data, 0644)
}

func (e ScenarioEditor) displayPath() string {
	if e.filePath == "" {
		return ".rogue/scenarios.json"
	}
	// Compact path for display
	home, _ := os.UserHomeDir()
	p := e.filePath
	if home != "" && strings.HasPrefix(p, home) {
		p = "~" + strings.TrimPrefix(p, home)
	}
	return p
}
