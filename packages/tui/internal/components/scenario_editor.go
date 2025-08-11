package components

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// ScenarioData represents a single scenario
type ScenarioData struct {
	Scenario          string      `json:"scenario"`
	ScenarioType      string      `json:"scenario_type"`
	Dataset           interface{} `json:"dataset"`
	ExpectedOutcome   string      `json:"expected_outcome"`
	DatasetSampleSize interface{} `json:"dataset_sample_size"`
}

// ScenariosFile represents the JSON file structure
type ScenariosFile struct {
	Scenarios []ScenarioData `json:"scenarios"`
}

// ScenarioEditor represents the scenario editor component
type ScenarioEditor struct {
	scenarios       []ScenarioData
	selectedIndex   int
	mode            ScenarioEditorMode
	editingScenario ScenarioData
	currentField    int
	width           int
	height          int
	scrollOffset    int
	visibleItems    int

	// Form fields for editing
	scenarioText    string
	expectedOutcome string
	scenarioCursor  int
	outcomeCursor   int
}

// ScenarioEditorMode represents the current mode of the editor
type ScenarioEditorMode int

const (
	ListMode ScenarioEditorMode = iota
	EditMode
	AddMode
)

// ScenarioEditorMsg represents messages from the scenario editor
type ScenarioEditorMsg struct {
	Action string
	Data   interface{}
}

// NewScenarioEditor creates a new scenario editor
func NewScenarioEditor() ScenarioEditor {
	editor := ScenarioEditor{
		scenarios:     []ScenarioData{},
		selectedIndex: 0,
		mode:          ListMode,
		currentField:  0,
		visibleItems:  8,
	}

	// Load existing scenarios
	editor.loadScenarios()

	return editor
}

// SetSize sets the size of the editor
func (e *ScenarioEditor) SetSize(width, height int) {
	e.width = width
	e.height = height
}

// Update handles input for the scenario editor
func (e ScenarioEditor) Update(msg tea.Msg) (ScenarioEditor, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch e.mode {
		case ListMode:
			return e.handleListMode(msg)
		case EditMode, AddMode:
			return e.handleEditMode(msg)
		}
	}
	return e, nil
}

// handleListMode handles input in list mode
func (e ScenarioEditor) handleListMode(msg tea.KeyMsg) (ScenarioEditor, tea.Cmd) {
	switch msg.String() {
	case "up", "k":
		if e.selectedIndex > 0 {
			e.selectedIndex--
			e.updateScroll()
		}
		return e, nil

	case "down", "j":
		if e.selectedIndex < len(e.scenarios)-1 {
			e.selectedIndex++
			e.updateScroll()
		}
		return e, nil

	case "enter":
		if len(e.scenarios) > 0 {
			// Edit selected scenario
			e.mode = EditMode
			e.editingScenario = e.scenarios[e.selectedIndex]
			e.scenarioText = e.editingScenario.Scenario
			e.expectedOutcome = e.editingScenario.ExpectedOutcome
			e.currentField = 0
			e.scenarioCursor = len(e.scenarioText)
			e.outcomeCursor = len(e.expectedOutcome)
		}
		return e, nil

	case "n", "a":
		// Add new scenario
		e.mode = AddMode
		e.editingScenario = ScenarioData{
			ScenarioType:      "policy",
			Dataset:           nil,
			DatasetSampleSize: nil,
		}
		e.scenarioText = ""
		e.expectedOutcome = ""
		e.currentField = 0
		e.scenarioCursor = 0
		e.outcomeCursor = 0
		return e, nil

	case "d", "delete":
		if len(e.scenarios) > 0 {
			// Delete selected scenario
			e.scenarios = append(e.scenarios[:e.selectedIndex], e.scenarios[e.selectedIndex+1:]...)
			if e.selectedIndex >= len(e.scenarios) && len(e.scenarios) > 0 {
				e.selectedIndex = len(e.scenarios) - 1
			}
			e.updateScroll()
			e.saveScenarios()
		}
		return e, nil

	case "s", "ctrl+s":
		// Save scenarios
		e.saveScenarios()
		return e, func() tea.Msg {
			return ScenarioEditorMsg{Action: "saved"}
		}
	}
	return e, nil
}

// handleEditMode handles input in edit mode
func (e ScenarioEditor) handleEditMode(msg tea.KeyMsg) (ScenarioEditor, tea.Cmd) {
	switch msg.String() {
	case "escape":
		// Cancel editing
		e.mode = ListMode
		return e, nil

	case "tab":
		// Switch between fields
		e.currentField = (e.currentField + 1) % 2
		return e, nil

	case "shift+tab":
		// Switch between fields (reverse)
		e.currentField = (e.currentField - 1 + 2) % 2
		return e, nil

	case "ctrl+s", "enter":
		// Save scenario
		e.editingScenario.Scenario = e.scenarioText
		e.editingScenario.ExpectedOutcome = e.expectedOutcome

		if e.mode == AddMode {
			e.scenarios = append(e.scenarios, e.editingScenario)
		} else {
			e.scenarios[e.selectedIndex] = e.editingScenario
		}

		e.mode = ListMode
		e.saveScenarios()
		return e, func() tea.Msg {
			return ScenarioEditorMsg{Action: "saved"}
		}

	case "backspace":
		if e.currentField == 0 {
			// Edit scenario text
			if e.scenarioCursor > 0 && len(e.scenarioText) > 0 {
				e.scenarioText = e.scenarioText[:e.scenarioCursor-1] + e.scenarioText[e.scenarioCursor:]
				e.scenarioCursor--
			}
		} else {
			// Edit expected outcome
			if e.outcomeCursor > 0 && len(e.expectedOutcome) > 0 {
				e.expectedOutcome = e.expectedOutcome[:e.outcomeCursor-1] + e.expectedOutcome[e.outcomeCursor:]
				e.outcomeCursor--
			}
		}
		return e, nil

	case "left":
		if e.currentField == 0 {
			if e.scenarioCursor > 0 {
				e.scenarioCursor--
			}
		} else {
			if e.outcomeCursor > 0 {
				e.outcomeCursor--
			}
		}
		return e, nil

	case "right":
		if e.currentField == 0 {
			if e.scenarioCursor < len(e.scenarioText) {
				e.scenarioCursor++
			}
		} else {
			if e.outcomeCursor < len(e.expectedOutcome) {
				e.outcomeCursor++
			}
		}
		return e, nil

	default:
		// Handle regular character input
		if len(msg.String()) == 1 {
			char := msg.String()
			if e.currentField == 0 {
				// Edit scenario text
				e.scenarioText = e.scenarioText[:e.scenarioCursor] + char + e.scenarioText[e.scenarioCursor:]
				e.scenarioCursor++
			} else {
				// Edit expected outcome
				e.expectedOutcome = e.expectedOutcome[:e.outcomeCursor] + char + e.expectedOutcome[e.outcomeCursor:]
				e.outcomeCursor++
			}
		}
		return e, nil
	}
}

// updateScroll updates the scroll offset to keep selected item visible
func (e *ScenarioEditor) updateScroll() {
	if e.selectedIndex < e.scrollOffset {
		e.scrollOffset = e.selectedIndex
	} else if e.selectedIndex >= e.scrollOffset+e.visibleItems {
		e.scrollOffset = e.selectedIndex - e.visibleItems + 1
	}
}

// View renders the scenario editor
func (e ScenarioEditor) View() string {
	t := theme.CurrentTheme()

	switch e.mode {
	case ListMode:
		return e.renderListView(t)
	case EditMode, AddMode:
		return e.renderEditView(t)
	}

	return ""
}

// renderListView renders the list of scenarios
func (e ScenarioEditor) renderListView(t theme.Theme) string {
	title := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Bold(true).
		Render("📝 Scenario Editor")

	if len(e.scenarios) == 0 {
		content := fmt.Sprintf(`%s

No scenarios found.

Press 'n' or 'a' to add a new scenario.
Press 'Esc' to return to dashboard.
`, title)

		return lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(t.Border()).
			Padding(1, 2).
			Width(e.width - 4).
			Height(e.height - 4).
			Render(content)
	}

	// Render scenario list
	var items []string
	start := e.scrollOffset
	end := start + e.visibleItems
	if end > len(e.scenarios) {
		end = len(e.scenarios)
	}

	for i := start; i < end; i++ {
		scenario := e.scenarios[i]
		prefix := "  "
		if i == e.selectedIndex {
			prefix = "▶ "
		}

		// Truncate long text
		scenarioText := scenario.Scenario
		if len(scenarioText) > 50 {
			scenarioText = scenarioText[:47] + "..."
		}

		itemStyle := lipgloss.NewStyle()
		if i == e.selectedIndex {
			itemStyle = itemStyle.Background(t.Primary()).Foreground(t.Background())
		} else {
			itemStyle = itemStyle.Foreground(t.Text())
		}

		items = append(items, itemStyle.Render(fmt.Sprintf("%s%s", prefix, scenarioText)))
	}

	// Show scroll indicators
	scrollInfo := ""
	if len(e.scenarios) > e.visibleItems {
		scrollInfo = fmt.Sprintf(" (%d/%d)", e.selectedIndex+1, len(e.scenarios))
	}

	content := fmt.Sprintf(`%s%s

%s

Controls:
• ↑/↓ or j/k - Navigate
• Enter - Edit scenario
• n/a - Add new scenario
• d/Delete - Delete scenario
• s/Ctrl+S - Save scenarios
• Esc - Return to dashboard
`, title, scrollInfo, strings.Join(items, "\n"))

	return lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Border()).
		Padding(1, 2).
		Width(e.width - 4).
		Height(e.height - 4).
		Render(content)
}

// renderEditView renders the edit form
func (e ScenarioEditor) renderEditView(t theme.Theme) string {
	modeTitle := "Edit Scenario"
	if e.mode == AddMode {
		modeTitle = "Add New Scenario"
	}

	title := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Bold(true).
		Render("📝 " + modeTitle)

	// Render scenario text field
	scenarioLabel := "Scenario:"
	if e.currentField == 0 {
		scenarioLabel = lipgloss.NewStyle().Foreground(t.Primary()).Bold(true).Render("▶ Scenario:")
	}

	scenarioText := e.scenarioText
	if e.currentField == 0 {
		// Add cursor
		if e.scenarioCursor == len(scenarioText) {
			scenarioText += "█"
		} else {
			scenarioText = scenarioText[:e.scenarioCursor] + "█" + scenarioText[e.scenarioCursor:]
		}
	}

	scenarioFieldStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		Padding(0, 1).
		Width(e.width - 8)

	if e.currentField == 0 {
		scenarioFieldStyle = scenarioFieldStyle.BorderForeground(t.Primary())
	} else {
		scenarioFieldStyle = scenarioFieldStyle.BorderForeground(t.Border())
	}

	scenarioField := scenarioFieldStyle.Render(scenarioText)

	// Render expected outcome field
	outcomeLabel := "Expected Outcome:"
	if e.currentField == 1 {
		outcomeLabel = lipgloss.NewStyle().Foreground(t.Primary()).Bold(true).Render("▶ Expected Outcome:")
	}

	outcomeText := e.expectedOutcome
	if e.currentField == 1 {
		// Add cursor
		if e.outcomeCursor == len(outcomeText) {
			outcomeText += "█"
		} else {
			outcomeText = outcomeText[:e.outcomeCursor] + "█" + outcomeText[e.outcomeCursor:]
		}
	}

	outcomeFieldStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		Padding(0, 1).
		Width(e.width - 8)

	if e.currentField == 1 {
		outcomeFieldStyle = outcomeFieldStyle.BorderForeground(t.Primary())
	} else {
		outcomeFieldStyle = outcomeFieldStyle.BorderForeground(t.Border())
	}

	outcomeField := outcomeFieldStyle.Render(outcomeText)

	content := fmt.Sprintf(`%s

%s
%s

%s
%s

Controls:
• Tab/Shift+Tab - Switch fields
• Enter/Ctrl+S - Save scenario
• Esc - Cancel editing
`, title, scenarioLabel, scenarioField, outcomeLabel, outcomeField)

	return lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Border()).
		Padding(1, 2).
		Width(e.width - 4).
		Height(e.height - 4).
		Render(content)
}

// loadScenarios loads scenarios from scenarios.json
func (e *ScenarioEditor) loadScenarios() error {
	data, err := os.ReadFile("scenarios.json")
	if err != nil {
		if os.IsNotExist(err) {
			// File doesn't exist, start with empty list
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
	return nil
}

// saveScenarios saves scenarios to scenarios.json
func (e *ScenarioEditor) saveScenarios() error {
	file := ScenariosFile{
		Scenarios: e.scenarios,
	}

	data, err := json.MarshalIndent(file, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile("scenarios.json", data, 0644)
}
