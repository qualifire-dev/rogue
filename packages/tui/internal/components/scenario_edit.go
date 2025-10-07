package components

import (
	"errors"
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// handleEditMode handles keyboard input in edit/add mode
func (e ScenarioEditor) handleEditMode(msg tea.KeyMsg) (ScenarioEditor, tea.Cmd) {
	switch msg.String() {
	case "escape", "esc":
		// Cancel editing
		e.mode = ListMode
		e.calculateVisibleItems() // Recalculate for list mode
		e.errorMsg = ""
		e.infoMsg = ""
		if e.scenarioTextArea != nil {
			e.scenarioTextArea.Blur()
		}
		if e.expectedOutcomeTextArea != nil {
			e.expectedOutcomeTextArea.Blur()
		}
		return e, nil

	case "tab", "down":
		// Switch between fields
		e.currentField = (e.currentField + 1) % e.numFields()
		e.updateTextAreaFocus()
		return e, nil

	case "shift+tab", "up":
		// Switch between fields (reverse)
		e.currentField = (e.currentField - 1 + e.numFields()) % e.numFields()
		e.updateTextAreaFocus()
		return e, nil

	case "ctrl+s":
		// Save via shortcut
		e.syncTextAreasToEditing()
		if err := e.validateEditing(); err != nil {
			e.errorMsg = err.Error()
			return e, nil
		}
		e.applyEditing()
		if err := e.saveScenarios(); err != nil {
			e.errorMsg = fmt.Sprintf("Save error: %v", err)
			return e, nil
		}
		e.mode = ListMode
		e.calculateVisibleItems() // Recalculate for list mode
		e.rebuildFilter()
		e.infoMsg = "Scenario saved"
		if e.scenarioTextArea != nil {
			e.scenarioTextArea.Blur()
		}
		if e.expectedOutcomeTextArea != nil {
			e.expectedOutcomeTextArea.Blur()
		}
		return e, func() tea.Msg { return ScenarioEditorMsg{Action: "saved"} }

	default:
		// Pass input to the currently focused TextArea
		var cmd tea.Cmd
		if e.currentField == 0 && e.scenarioTextArea != nil {
			updatedTextArea, taCmd := e.scenarioTextArea.Update(msg)
			*e.scenarioTextArea = *updatedTextArea
			cmd = taCmd
		} else if e.currentField == 1 && e.expectedOutcomeTextArea != nil {
			updatedTextArea, taCmd := e.expectedOutcomeTextArea.Update(msg)
			*e.expectedOutcomeTextArea = *updatedTextArea
			cmd = taCmd
		} else if e.currentField >= 2 {
			// Save button focused, handle enter key
			if msg.String() == "enter" {
				e.syncTextAreasToEditing()
				if err := e.validateEditing(); err != nil {
					e.errorMsg = err.Error()
					return e, nil
				}
				e.applyEditing()
				if err := e.saveScenarios(); err != nil {
					e.errorMsg = fmt.Sprintf("Save error: %v", err)
					return e, nil
				}
				e.mode = ListMode
				e.calculateVisibleItems() // Recalculate for list mode
				e.rebuildFilter()
				e.infoMsg = "Scenario saved"
				if e.scenarioTextArea != nil {
					e.scenarioTextArea.Blur()
				}
				if e.expectedOutcomeTextArea != nil {
					e.expectedOutcomeTextArea.Blur()
				}
				return e, func() tea.Msg { return ScenarioEditorMsg{Action: "saved"} }
			}
		}
		return e, cmd
	}
}

func (e *ScenarioEditor) numFields() int {
	// Two text areas + Save button focus
	return 3
}

// updateTextAreaFocus manages focus between TextAreas based on currentField
func (e *ScenarioEditor) updateTextAreaFocus() {
	if e.scenarioTextArea != nil {
		if e.currentField == 0 {
			e.scenarioTextArea.Focus()
		} else {
			e.scenarioTextArea.Blur()
		}
	}
	if e.expectedOutcomeTextArea != nil {
		if e.currentField == 1 {
			e.expectedOutcomeTextArea.Focus()
		} else {
			e.expectedOutcomeTextArea.Blur()
		}
	}
}

// syncTextAreasToEditing copies TextArea contents to the editing struct
func (e *ScenarioEditor) syncTextAreasToEditing() {
	if e.scenarioTextArea != nil {
		e.editing.Scenario = e.scenarioTextArea.GetValue()
	}
	if e.expectedOutcomeTextArea != nil {
		outVal := e.expectedOutcomeTextArea.GetValue()
		if outVal == "" {
			e.editing.ExpectedOutcome = nil
		} else {
			e.editing.ExpectedOutcome = &outVal
		}
	}
}

// validateEditing validates the editing scenario based on Python model rules
func (e *ScenarioEditor) validateEditing() error {
	if strings.TrimSpace(e.editing.Scenario) == "" {
		return errors.New("scenario cannot be empty")
	}
	// Force policy-only for this version
	e.editing.ScenarioType = "policy"
	// Ensure dataset fields are cleared
	e.editing.Dataset = nil
	e.editing.DatasetSampleSize = nil
	return nil
}

func (e *ScenarioEditor) applyEditing() {
	if e.mode == AddMode {
		e.scenarios = append(e.scenarios, e.editing)
	} else if e.mode == EditMode && len(e.filteredIdx) > 0 {
		idx := e.filteredIdx[e.selectedIndex]
		e.scenarios[idx] = e.editing
	}
}

// renderEditView renders the edit/add scenario form
func (e ScenarioEditor) renderEditView(t theme.Theme) string {
	modeTitle := "Edit Scenario"
	if e.mode == AddMode {
		modeTitle = "Add New Scenario"
	}
	title := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("\n" + modeTitle)

	// Calculate available height for TextAreas
	usedHeight := 0
	usedHeight += 2 // title (1 line) + blank line after title
	usedHeight += 2 // scenario label + blank line
	usedHeight += 2 // expected outcome label + blank line
	usedHeight += 1 // save label
	usedHeight += 2 // blank lines around help
	usedHeight += 1 // help line
	usedHeight += 1 // error line (if present)
	usedHeight += 5 // extra buffer to prevent footer overflow

	availableHeight := e.height - 1                      // -1 for parent layout
	textAreaHeight := (availableHeight - usedHeight) / 2 // Split between two TextAreas
	if textAreaHeight < 4 {
		textAreaHeight = 4 // Minimum height
	}

	// Field 0: scenario TextArea
	scenLabel := "Scenario"
	if e.currentField == 0 {
		scenLabel = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("▶ Scenario")
	}

	var scenText string
	if e.scenarioTextArea != nil {
		e.scenarioTextArea.SetSize(e.width-4, textAreaHeight)
		scenText = e.scenarioTextArea.View()
	} else {
		scenText = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text()).Render("TextArea not available")
	}

	// Field 1: expected_outcome TextArea
	outLabel := "Expected Outcome"
	if e.currentField == 1 {
		outLabel = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("▶ Expected Outcome")
	}

	var outText string
	if e.expectedOutcomeTextArea != nil {
		e.expectedOutcomeTextArea.SetSize(e.width-4, textAreaHeight)
		outText = e.expectedOutcomeTextArea.View()
	} else {
		outText = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text()).Render("TextArea not available")
	}

	// Save button hint
	saveLabel := "Save"
	if e.currentField >= 2 {
		saveLabel = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("▶ Save")
	}

	help := lipgloss.NewStyle().Background(t.Background()).Foreground(t.TextMuted()).Render("Tab/↑↓ switch fields  Ctrl+S save  Esc cancel")
	errorLine := ""
	if e.errorMsg != "" {
		errorLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Error()).Render("⚠ " + e.errorMsg)
	}

	var parts []string
	parts = append(parts, title, "")
	parts = append(parts, scenLabel, scenText)
	parts = append(parts, "")
	parts = append(parts, outLabel, outText)
	parts = append(parts, "", saveLabel)
	parts = append(parts, "", help, errorLine)

	content := strings.Join(parts, "\n")
	return content
}

// renderTextArea is a helper for rendering text areas (legacy, may be unused)
func renderTextArea(t theme.Theme, width int, focused bool, text string, cursor int) string {
	// subtle box with background only
	boxStyle := lipgloss.NewStyle().
		Background(t.BackgroundPanel()).
		Padding(2, 2).
		Width(width)

	// Wrap text visually
	lines, lineStarts := wrapTextWithStarts(text, width)

	// Draw cursor if focused
	if focused {
		if cursor < 0 {
			cursor = 0
		}
		if cursor > len([]rune(text)) {
			cursor = len([]rune(text))
		}
		row, col := rowColForIndex(lineStarts, text, width, cursor)
		// Insert cursor into the appropriate line
		// Rebuild lines with cursor
		rlines := make([]string, len(lines))
		copy(rlines, lines)
		if row >= 0 && row < len(rlines) {
			line := rlines[row]
			if col > len([]rune(line)) {
				col = len([]rune(line))
			}
			rlines[row] = insertAtRune(line, col, "█")
		}
		return boxStyle.Render(strings.Join(rlines, "\n"))
	}
	return boxStyle.Render(strings.Join(lines, "\n"))
}
