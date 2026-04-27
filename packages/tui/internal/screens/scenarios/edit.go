package scenarios

import (
	"encoding/json"
	"errors"
	"fmt"
	"strconv"
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// Field indices for the edit form. Max-Turns is skipped in cycling when
// multi-turn is disabled so it behaves as if not present.
const (
	editFieldScenario        = 0
	editFieldExpectedOutcome = 1
	editFieldFilePath        = 2
	editFieldKwargs          = 3
	editFieldMultiTurnToggle = 4
	editFieldMaxTurns        = 5
	editFieldSave            = 6
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
		if e.kwargsTextArea != nil {
			e.kwargsTextArea.Blur()
		}
		return e, nil

	case "tab":
		e.currentField = e.nextField(e.currentField, +1)
		e.updateTextAreaFocus()
		return e, nil

	case "shift+tab":
		e.currentField = e.nextField(e.currentField, -1)
		e.updateTextAreaFocus()
		return e, nil

	case "ctrl+l":
		// Clear the entire content of the focused text area. Only acts on
		// multi-line textareas — toggles / single-line buffers ignore it.
		switch e.currentField {
		case editFieldScenario:
			if e.scenarioTextArea != nil {
				e.scenarioTextArea.SetValue("")
			}
		case editFieldExpectedOutcome:
			if e.expectedOutcomeTextArea != nil {
				e.expectedOutcomeTextArea.SetValue("")
			}
		case editFieldKwargs:
			if e.kwargsTextArea != nil {
				e.kwargsTextArea.SetValue("")
			}
		}
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
		if e.kwargsTextArea != nil {
			e.kwargsTextArea.Blur()
		}
		return e, func() tea.Msg { return ScenarioEditorMsg{Action: "saved"} }

	default:
		// Route by current field.
		switch e.currentField {
		case editFieldScenario:
			if e.scenarioTextArea != nil {
				updatedTextArea, taCmd := e.scenarioTextArea.Update(msg)
				*e.scenarioTextArea = *updatedTextArea
				return e, taCmd
			}
		case editFieldExpectedOutcome:
			if e.expectedOutcomeTextArea != nil {
				updatedTextArea, taCmd := e.expectedOutcomeTextArea.Update(msg)
				*e.expectedOutcomeTextArea = *updatedTextArea
				return e, taCmd
			}
		case editFieldFilePath:
			s := msg.String()
			switch s {
			case "backspace":
				if len(e.filePathBuffer) > 0 {
					e.filePathBuffer = e.filePathBuffer[:len(e.filePathBuffer)-1]
				}
			default:
				if len(s) == 1 {
					e.filePathBuffer += s
				}
			}
			return e, nil
		case editFieldKwargs:
			if e.kwargsTextArea != nil {
				updatedTextArea, taCmd := e.kwargsTextArea.Update(msg)
				*e.kwargsTextArea = *updatedTextArea
				return e, taCmd
			}
		case editFieldMultiTurnToggle:
			switch msg.String() {
			case " ", "space", "enter", "x", "X":
				current := true
				if e.editing.MultiTurn != nil {
					current = *e.editing.MultiTurn
				}
				next := !current
				e.editing.MultiTurn = &next
			}
			return e, nil
		case editFieldMaxTurns:
			s := msg.String()
			switch s {
			case "backspace":
				if len(e.maxTurnsBuffer) > 0 {
					e.maxTurnsBuffer = e.maxTurnsBuffer[:len(e.maxTurnsBuffer)-1]
				}
			default:
				if len(s) == 1 && s >= "0" && s <= "9" && len(e.maxTurnsBuffer) < 3 {
					e.maxTurnsBuffer += s
				}
			}
			return e, nil
		case editFieldSave:
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
				e.calculateVisibleItems()
				e.rebuildFilter()
				e.infoMsg = "Scenario saved"
				if e.scenarioTextArea != nil {
					e.scenarioTextArea.Blur()
				}
				if e.expectedOutcomeTextArea != nil {
					e.expectedOutcomeTextArea.Blur()
				}
				if e.kwargsTextArea != nil {
					e.kwargsTextArea.Blur()
				}
				return e, func() tea.Msg { return ScenarioEditorMsg{Action: "saved"} }
			}
		}
		return e, nil
	}
}

// multiTurnOnEdit reports whether the currently-editing scenario has multi-turn on
// (the JSON-null sentinel means "not set yet" and defaults to on).
func (e *ScenarioEditor) multiTurnOnEdit() bool {
	if e.editing.MultiTurn == nil {
		return MultiTurnDefault
	}
	return *e.editing.MultiTurn
}

// nextField advances currentField by step ({+1, -1}), wrapping around and
// skipping the MaxTurns field when multi-turn is disabled.
func (e *ScenarioEditor) nextField(cur, step int) int {
	total := editFieldSave + 1
	n := cur
	for i := 0; i < total; i++ {
		n = (n + step + total) % total
		if n == editFieldMaxTurns && !e.multiTurnOnEdit() {
			continue
		}
		return n
	}
	return cur
}

func (e *ScenarioEditor) numFields() int {
	if e.multiTurnOnEdit() {
		return 7
	}
	return 6
}

// updateTextAreaFocus manages focus between TextAreas based on currentField
func (e *ScenarioEditor) updateTextAreaFocus() {
	if e.scenarioTextArea != nil {
		if e.currentField == editFieldScenario {
			e.scenarioTextArea.Focus()
		} else {
			e.scenarioTextArea.Blur()
		}
	}
	if e.expectedOutcomeTextArea != nil {
		if e.currentField == editFieldExpectedOutcome {
			e.expectedOutcomeTextArea.Focus()
		} else {
			e.expectedOutcomeTextArea.Blur()
		}
	}
	if e.kwargsTextArea != nil {
		if e.currentField == editFieldKwargs {
			e.kwargsTextArea.Focus()
		} else {
			e.kwargsTextArea.Blur()
		}
	}
}

// syncTextAreasToEditing copies TextArea contents to the editing struct.
// Kwargs JSON is parsed in validateEditing so we only stash the raw string here.
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

	// File path single-line buffer. Empty -> nil pointer (omitted from JSON).
	trimmedFilePath := strings.TrimSpace(e.filePathBuffer)
	if trimmedFilePath == "" {
		e.editing.FilePath = nil
	} else {
		e.editing.FilePath = &trimmedFilePath
	}

	// Parse the kwargs JSON textarea. Empty string -> nil map.
	if e.kwargsTextArea != nil {
		raw := strings.TrimSpace(e.kwargsTextArea.GetValue())
		if raw == "" {
			e.editing.AvailableKwargs = nil
		} else {
			var parsed map[string]any
			if err := json.Unmarshal([]byte(raw), &parsed); err != nil {
				return fmt.Errorf("available kwargs must be valid JSON object: %v", err)
			}
			e.editing.AvailableKwargs = parsed
		}
	}

	// Apply multi-turn + max_turns defaults and bounds.
	mt := e.multiTurnOnEdit()
	e.editing.MultiTurn = &mt

	// Resolve max_turns from the inline buffer; defaults to existing / default.
	resolved := e.editing.MaxTurnsValue()
	if trimmed := strings.TrimSpace(e.maxTurnsBuffer); trimmed != "" {
		n, err := strconv.Atoi(trimmed)
		if err != nil {
			return fmt.Errorf("max turns must be a number: %q", trimmed)
		}
		resolved = n
	}
	if resolved < MaxTurnsMin || resolved > MaxTurnsMax {
		return fmt.Errorf("max turns must be between %d and %d", MaxTurnsMin, MaxTurnsMax)
	}
	e.editing.MaxTurns = &resolved
	e.maxTurnsBuffer = fmt.Sprintf("%d", resolved)
	return nil
}

func (e *ScenarioEditor) applyEditing() {
	if e.mode == AddMode {
		e.scenarios = append(e.scenarios, e.editing)
	} else if e.mode == EditMode && len(e.filteredIdx) > 0 {
		if e.selectedIndex >= 0 && e.selectedIndex < len(e.filteredIdx) {
			idx := e.filteredIdx[e.selectedIndex]
			e.scenarios[idx] = e.editing
		}
	}
}

// renderEditView renders the edit/add scenario form
func (e ScenarioEditor) renderEditView(t theme.Theme) string {
	modeTitle := "Edit Scenario"
	if e.mode == AddMode {
		modeTitle = "Add New Scenario"
	}
	title := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("\n" + modeTitle)

	multiTurnOn := e.multiTurnOnEdit()

	// Calculate available height for TextAreas
	usedHeight := 0
	usedHeight += 2 // title (1 line) + blank line
	usedHeight += 2 // scenario label + blank
	usedHeight += 2 // expected outcome label + blank
	usedHeight += 2 // file path line + blank
	usedHeight += 2 // kwargs label + blank
	usedHeight += 5 // kwargs textarea (fixed-height)
	usedHeight += 2 // multi-turn + blank
	if multiTurnOn {
		usedHeight += 2 // max-turns line + blank
	}
	usedHeight += 1 // save label
	usedHeight += 2 // blank + help
	usedHeight += 1 // error line (if present)
	usedHeight += 5 // buffer

	availableHeight := e.height - 1
	textAreaHeight := (availableHeight - usedHeight) / 2
	if textAreaHeight < 4 {
		textAreaHeight = 4
	}

	// Field 0: scenario TextArea
	scenLabel := "Scenario (free-text goal or stepped plan)"
	if e.currentField == editFieldScenario {
		scenLabel = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("▶ Scenario (free-text goal or stepped plan)")
	}

	var scenText string
	if e.scenarioTextArea != nil {
		e.scenarioTextArea.SetSize(e.width-4, textAreaHeight)
		scenText = e.scenarioTextArea.View()
	} else {
		scenText = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text()).Render("TextArea not available")
	}

	// Field 1: expected_outcome TextArea
	outLabel := "Expected Outcome (drives pass/fail)"
	if e.currentField == editFieldExpectedOutcome {
		outLabel = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("▶ Expected Outcome (drives pass/fail)")
	}

	var outText string
	if e.expectedOutcomeTextArea != nil {
		e.expectedOutcomeTextArea.SetSize(e.width-4, textAreaHeight)
		outText = e.expectedOutcomeTextArea.View()
	} else {
		outText = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text()).Render("TextArea not available")
	}

	// Field 2: file path (PYTHON protocol convenience — auto-merged into kwargs pool)
	filePathLabelText := "File Path (PYTHON only, default 'file_path' kwarg)"
	filePathBuf := e.filePathBuffer
	if filePathBuf == "" {
		filePathBuf = "_"
	}
	filePathRaw := fmt.Sprintf("%s:  [ %s ]", filePathLabelText, filePathBuf)
	var filePathLine string
	if e.currentField == editFieldFilePath {
		filePathLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("▶ " + filePathRaw)
	} else {
		filePathLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text()).Render("  " + filePathRaw)
	}

	// Field 3: available kwargs (JSON, PYTHON protocol only)
	kwargsLabel := "Available Kwargs (PYTHON only, JSON object)"
	if e.currentField == editFieldKwargs {
		kwargsLabel = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("▶ Available Kwargs (PYTHON only, JSON object)")
	}

	var kwargsText string
	if e.kwargsTextArea != nil {
		e.kwargsTextArea.SetSize(e.width-4, 5)
		kwargsText = e.kwargsTextArea.View()
	} else {
		kwargsText = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text()).Render("TextArea not available")
	}

	// Field 3: multi-turn toggle
	multiTurnCheckbox := "[ ]"
	if multiTurnOn {
		multiTurnCheckbox = "[x]"
	}
	multiTurnLine := fmt.Sprintf("Multi-Turn: %s  (space to toggle — rogue drives a dynamic conversation until goal or max turns)", multiTurnCheckbox)
	if e.currentField == editFieldMultiTurnToggle {
		multiTurnLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("▶ " + multiTurnLine)
	} else {
		multiTurnLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text()).Render("  " + multiTurnLine)
	}

	// Field 3: max-turns input (only visible when multi-turn is on)
	var maxTurnsLine string
	if multiTurnOn {
		buf := e.maxTurnsBuffer
		if buf == "" {
			buf = "_"
		}
		raw := fmt.Sprintf("Max Turns:  [ %s ]  (1-%d, defaults to %d)", buf, MaxTurnsMax, MaxTurnsDefault)
		if e.currentField == editFieldMaxTurns {
			maxTurnsLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("▶ " + raw)
		} else {
			maxTurnsLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text()).Render("  " + raw)
		}
	}

	// Save button hint
	saveLabel := "Save"
	if e.currentField == editFieldSave {
		saveLabel = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("▶ Save")
	}

	help := lipgloss.NewStyle().Background(t.Background()).Foreground(t.TextMuted()).Render("Tab/Shift+Tab switch fields  ↑↓ move cursor in text  Ctrl+L clear field  Space toggle  Ctrl+S save  Esc cancel")
	errorLine := ""
	if e.errorMsg != "" {
		errorLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Error()).Render("⚠ " + e.errorMsg)
	}

	var parts []string
	parts = append(parts, title, "")
	parts = append(parts, scenLabel, scenText)
	parts = append(parts, "")
	parts = append(parts, outLabel, outText)
	parts = append(parts, "")
	parts = append(parts, filePathLine)
	parts = append(parts, "")
	parts = append(parts, kwargsLabel, kwargsText)
	parts = append(parts, "")
	parts = append(parts, multiTurnLine)
	if multiTurnOn {
		parts = append(parts, maxTurnsLine)
	}
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
