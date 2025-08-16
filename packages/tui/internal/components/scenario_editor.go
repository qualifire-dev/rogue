package components

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/styles"
	"github.com/rogue/tui/internal/theme"
)

// ScenarioData represents a single scenario aligned with Python schema
type ScenarioData struct {
	Scenario          string  `json:"scenario"`
	ScenarioType      string  `json:"scenario_type"`
	Dataset           *string `json:"dataset"`
	ExpectedOutcome   *string `json:"expected_outcome"`
	DatasetSampleSize *int    `json:"dataset_sample_size"`
}

// ScenariosFile represents the JSON file structure
type ScenariosFile struct {
	BusinessContext *string        `json:"business_context"`
	Scenarios       []ScenarioData `json:"scenarios"`
}

// ScenarioEditor represents the scenario editor component
type ScenarioEditor struct {
	// Data
	scenarios       []ScenarioData
	businessContext *string
	filteredIdx     []int
	searchMode      bool
	searchQuery     string

	// Selection and mode
	selectedIndex      int
	bizContextSelected bool // true when business context is selected instead of scenarios
	mode               ScenarioEditorMode
	currentField       int

	// Editing buffer
	editing   ScenarioData
	cursorPos int // for current text field

	// Layout
	width        int
	height       int
	scrollOffset int
	visibleItems int

	// Business context
	bizViewport *Viewport
	bizTextArea *TextArea

	// File management
	filePath string // path to .rogue/scenarios.json

	// UX
	errorMsg string
	infoMsg  string
}

// ScenarioEditorMode represents the current mode of the editor
type ScenarioEditorMode int

const (
	ListMode ScenarioEditorMode = iota
	EditMode
	AddMode
	BusinessContextMode
)

// ScenarioEditorMsg represents messages from the scenario editor
type ScenarioEditorMsg struct {
	Action string
	Data   any
}

// NewScenarioEditor creates a new scenario editor
func NewScenarioEditor() ScenarioEditor {
	editor := ScenarioEditor{
		scenarios:     []ScenarioData{},
		selectedIndex: 0,
		mode:          ListMode,
		currentField:  0,
		visibleItems:  10,
	}

	// Initialize business context components
	vp := NewViewport(9999, 80, 10) // Use unique ID
	editor.bizViewport = &vp

	ta := NewTextArea(9998, 80, 10) // Use unique ID
	editor.bizTextArea = &ta

	// Discover scenarios.json location and load
	editor.filePath = discoverScenariosFile()
	_ = editor.loadScenarios()
	editor.rebuildFilter()
	return editor
}

// SetSize sets the size of the editor
func (e *ScenarioEditor) SetSize(width, height int) {
	e.width = width
	e.height = height
	// Compute a reasonable number of visible list items based on height
	// Reserve rows for borders, header, subline, table header, spacing, help and messages
	// Rough overhead: ~12 rows on small terminals
	maxItems := height - 12
	if maxItems < 5 {
		maxItems = 5
	}
	e.visibleItems = maxItems

	// Update business context components size
	if e.bizViewport != nil {
		e.bizViewport.SetSize(width-4, 10) // 10 lines, account for padding
	}
	if e.bizTextArea != nil {
		e.bizTextArea.SetSize(width-4, 10) // 10 lines, account for padding
	}
}

// Update handles input for the scenario editor
func (e ScenarioEditor) Update(msg tea.Msg) (ScenarioEditor, tea.Cmd) {
	switch m := msg.(type) {
	case tea.KeyMsg:
		switch e.mode {
		case ListMode:
			return e.handleListMode(m)
		case EditMode, AddMode:
			return e.handleEditMode(m)
		case BusinessContextMode:
			return e.handleBusinessContextMode(m)
		}
	}
	return e, nil
}

// handleListMode handles input in list mode
func (e ScenarioEditor) handleListMode(msg tea.KeyMsg) (ScenarioEditor, tea.Cmd) {
	switch msg.String() {
	case "escape", "esc":
		// Request parent to exit the scenarios screen
		return e, func() tea.Msg { return ScenarioEditorMsg{Action: "exit"} }
	case "up", "k":
		if e.bizContextSelected {
			// Move from business context to last scenario
			e.bizContextSelected = false
			if len(e.filteredIdx) > 0 {
				e.selectedIndex = len(e.filteredIdx) - 1
				e.updateScroll()
			}
		} else if e.selectedIndex > 0 {
			e.selectedIndex--
			e.updateScroll()
		} else if len(e.filteredIdx) > 0 {
			// Move from first scenario to business context
			e.bizContextSelected = true
		}
		return e, nil

	case "down", "j":
		if e.bizContextSelected {
			// Move from business context to first scenario
			e.bizContextSelected = false
			e.selectedIndex = 0
			e.updateScroll()
		} else if e.selectedIndex < len(e.filteredIdx)-1 {
			e.selectedIndex++
			e.updateScroll()
		} else {
			// Move from last scenario to business context
			e.bizContextSelected = true
		}
		return e, nil

	case "b":
		// Enter business context edit mode
		e.mode = BusinessContextMode
		if e.bizTextArea != nil {
			bizContext := ""
			if e.businessContext != nil {
				bizContext = *e.businessContext
			}
			e.bizTextArea.SetValue(bizContext)
			e.bizTextArea.Focus()
		}
		return e, nil

	case "/":
		// Open a dialog to enter search query (single OK button, no Cancel)
		dialog := NewInputDialog("Search Scenarios", "Type to filter scenarios:", e.searchQuery)
		dialog.Buttons = []DialogButton{{Label: "OK", Action: "ok", Style: PrimaryButton}}
		return e, func() tea.Msg { return DialogOpenMsg{Dialog: dialog} }

	case "enter":
		if e.bizContextSelected {
			// Enter business context edit mode
			e.mode = BusinessContextMode
			if e.bizTextArea != nil {
				bizContext := ""
				if e.businessContext != nil {
					bizContext = *e.businessContext
				}
				e.bizTextArea.SetValue(bizContext)
				e.bizTextArea.Focus()
			}
			e.errorMsg = ""
			e.infoMsg = ""
			return e, nil
		}
		if len(e.filteredIdx) == 0 {
			return e, nil
		}
		idx := e.filteredIdx[e.selectedIndex]
		e.mode = EditMode
		e.editing = e.scenarios[idx]
		e.currentField = 0
		e.cursorPos = len(e.editing.Scenario)
		e.errorMsg = ""
		e.infoMsg = ""
		return e, nil

	case "n", "a":
		// Add new scenario
		e.mode = AddMode
		e.editing = ScenarioData{ScenarioType: "policy"}
		e.currentField = 0
		e.cursorPos = 0
		e.errorMsg = ""
		e.infoMsg = ""
		return e, nil

	case "d", "delete":
		if e.bizContextSelected || len(e.filteredIdx) == 0 {
			return e, nil
		}
		// Ask for confirmation using a modal dialog
		idx := e.filteredIdx[e.selectedIndex]
		name := e.scenarios[idx].Scenario
		if len(name) > 60 {
			name = name[:57] + "..."
		}
		dialog := ShowDeleteConfirmationDialog(name)
		return e, func() tea.Msg { return DialogOpenMsg{Dialog: dialog} }

	case "s", "ctrl+s":
		// Save all scenarios to file
		if err := e.saveScenarios(); err != nil {
			e.errorMsg = fmt.Sprintf("Save error: %v", err)
		} else {
			e.infoMsg = "Scenarios saved"
		}
		return e, func() tea.Msg { return ScenarioEditorMsg{Action: "saved"} }
	default:
		return e, nil
	}
}

// handleBusinessContextMode handles input in business context edit mode
func (e ScenarioEditor) handleBusinessContextMode(msg tea.KeyMsg) (ScenarioEditor, tea.Cmd) {
	switch msg.String() {
	case "escape", "esc":
		// Save and exit business context edit mode
		if e.bizTextArea != nil {
			content := e.bizTextArea.GetValue()
			if content == "" {
				e.businessContext = nil
			} else {
				e.businessContext = &content
			}
			e.bizTextArea.Blur()
		}
		e.mode = ListMode
		e.bizContextSelected = true // Keep business context selected when exiting edit mode
		e.errorMsg = ""
		e.infoMsg = ""
		return e, nil

	case "ctrl+s":
		// Save business context
		if e.bizTextArea != nil {
			content := e.bizTextArea.GetValue()
			if content == "" {
				e.businessContext = nil
			} else {
				e.businessContext = &content
			}
		}
		// Save to file
		if err := e.saveScenarios(); err != nil {
			e.errorMsg = fmt.Sprintf("Save error: %v", err)
		} else {
			e.infoMsg = "Business context saved"
		}
		return e, nil

	default:
		// Pass through to TextArea
		if e.bizTextArea != nil {
			updatedTextArea, cmd := e.bizTextArea.Update(msg)
			*e.bizTextArea = *updatedTextArea
			return e, cmd
		}
		return e, nil
	}
}

// handleEditMode handles input in edit/add mode
func (e ScenarioEditor) handleEditMode(msg tea.KeyMsg) (ScenarioEditor, tea.Cmd) {
	switch msg.String() {
	case "escape", "esc":
		// Cancel editing
		e.mode = ListMode
		e.errorMsg = ""
		e.infoMsg = ""
		return e, nil

	case "down":
		e.currentField = (e.currentField + 1) % e.numFields()
		e.resetCursorForField()
		return e, nil

	case "up":
		e.currentField = (e.currentField - 1 + e.numFields()) % e.numFields()
		e.resetCursorForField()
		return e, nil

	case "left":
		if e.currentField == 0 { // scenario_type toggle
			if e.editing.ScenarioType == "prompt_injection" {
				e.editing.ScenarioType = "policy"
				// Clear dataset fields for policy
				e.editing.Dataset = nil
				e.editing.DatasetSampleSize = nil
			}
			return e, nil
		}
		if e.cursorPos > 0 && e.isTextField(e.currentField) {
			e.cursorPos--
		}
		return e, nil

	case "right":
		if e.currentField == 0 { // scenario_type toggle
			if e.editing.ScenarioType == "policy" {
				e.editing.ScenarioType = "prompt_injection"
			}
			return e, nil
		}
		if e.isTextField(e.currentField) {
			fieldLen := len(e.currentFieldText())
			if e.cursorPos < fieldLen {
				e.cursorPos++
			}
		}
		return e, nil

	case "backspace":
		if !e.isTextField(e.currentField) {
			return e, nil
		}
		txt := e.currentFieldText()
		if e.cursorPos > 0 && len(txt) > 0 {
			newTxt := txt[:e.cursorPos-1] + txt[e.cursorPos:]
			e.setCurrentFieldText(newTxt)
			e.cursorPos--
		}
		return e, nil

	case "delete":
		if !e.isTextField(e.currentField) {
			return e, nil
		}
		txt := e.currentFieldText()
		if e.cursorPos < len(txt) {
			newTxt := txt[:e.cursorPos] + txt[e.cursorPos+1:]
			e.setCurrentFieldText(newTxt)
		}
		return e, nil

	case "enter":
		// If Save button is focused, save; otherwise insert newline at cursor
		if e.currentField >= 2 {
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
			e.rebuildFilter()
			e.infoMsg = "Scenario saved"
			return e, func() tea.Msg { return ScenarioEditorMsg{Action: "saved"} }
		}
		// Insert newline into current text field
		txt := e.currentFieldText()
		newTxt := txt[:e.cursorPos] + "\n" + txt[e.cursorPos:]
		e.setCurrentFieldText(newTxt)
		e.cursorPos++
		return e, nil

	case "ctrl+s":
		// Save via shortcut
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
		e.rebuildFilter()
		e.infoMsg = "Scenario saved"
		return e, func() tea.Msg { return ScenarioEditorMsg{Action: "saved"} }

	default:
		// Character input for text fields
		if !e.isTextField(e.currentField) {
			return e, nil
		}
		s := msg.String()
		if len(s) == 1 {
			txt := e.currentFieldText()
			newTxt := txt[:e.cursorPos] + s + txt[e.cursorPos:]
			e.setCurrentFieldText(newTxt)
			e.cursorPos++
		}
		return e, nil
	}
}

func (e *ScenarioEditor) numFields() int {
	// Two text areas + Save button focus
	return 3
}

func (e *ScenarioEditor) isTextField(field int) bool {
	// Both fields are text inputs
	return true
}

func (e *ScenarioEditor) currentFieldText() string {
	switch e.currentField {
	case 0:
		return e.editing.Scenario
	case 1:
		if e.editing.ExpectedOutcome == nil {
			return ""
		}
		return *e.editing.ExpectedOutcome
	default:
		return ""
	}
}

func (e *ScenarioEditor) setCurrentFieldText(val string) {
	switch e.currentField {
	case 0:
		e.editing.Scenario = val
	case 1:
		if val == "" {
			e.editing.ExpectedOutcome = nil
		} else {
			v := val
			e.editing.ExpectedOutcome = &v
		}
	}
}

func (e *ScenarioEditor) resetCursorForField() {
	e.cursorPos = len(e.currentFieldText())
}

// Validation based on Python model rules (policy-only editing)
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

// updateScroll updates the scroll offset to keep selected item visible
func (e *ScenarioEditor) updateScroll() {
	if e.selectedIndex < e.scrollOffset {
		e.scrollOffset = e.selectedIndex
	} else if e.selectedIndex >= e.scrollOffset+e.visibleItems {
		e.scrollOffset = e.selectedIndex - e.visibleItems + 1
	}
}

// rebuildFilter recalculates filtered indices based on fuzzy text search in scenario
func (e *ScenarioEditor) rebuildFilter() {
	e.filteredIdx = e.filteredIdx[:0]
	query := strings.ToLower(strings.TrimSpace(e.searchQuery))
	for i, s := range e.scenarios {
		if query == "" || strings.Contains(strings.ToLower(s.Scenario), query) {
			e.filteredIdx = append(e.filteredIdx, i)
		}
	}
	if e.selectedIndex >= len(e.filteredIdx) {
		e.selectedIndex = 0
	}
	if e.selectedIndex < 0 {
		e.selectedIndex = 0
	}
	// Reset business context selection when filtering
	if e.searchQuery != "" {
		e.bizContextSelected = false
	}
}

// rebuildFilterResetSelection resets selection and scroll when search changes
func (e *ScenarioEditor) rebuildFilterResetSelection() {
	e.rebuildFilter()
	e.selectedIndex = 0
	e.scrollOffset = 0
	e.bizContextSelected = false
}

// SetSearchQuery updates the search query and rebuilds the filtered list
func (e *ScenarioEditor) SetSearchQuery(query string) {
	e.searchQuery = strings.TrimSpace(query)
	e.rebuildFilterResetSelection()
}

// ClearSearchQuery clears the search query and rebuilds the filtered list
func (e *ScenarioEditor) ClearSearchQuery() {
	e.searchQuery = ""
	e.rebuildFilterResetSelection()
}

// View renders the scenario editor
func (e ScenarioEditor) View() string {
	t := theme.CurrentTheme()
	switch e.mode {
	case ListMode:
		return lipgloss.Place(
			e.width,
			e.height-1,
			lipgloss.Center,
			lipgloss.Top,
			e.renderListView(t),
			styles.WhitespaceStyle(t.Background()),
		)
	case EditMode, AddMode:
		return lipgloss.Place(
			e.width,
			e.height-1,
			lipgloss.Left,
			lipgloss.Top,
			e.renderEditView(t),
			styles.WhitespaceStyle(t.Background()),
		)
	case BusinessContextMode:
		return lipgloss.Place(
			e.width,
			e.height-1,
			lipgloss.Left,
			lipgloss.Top,
			e.renderBusinessContextView(t),
			styles.WhitespaceStyle(t.Background()),
		)

	default:
		return ""
	}
}

// renderBusinessContextView renders the business context editing view
func (e ScenarioEditor) renderBusinessContextView(t theme.Theme) string {
	title := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("\nEdit Business Context")

	var bizTextArea string
	if e.bizTextArea != nil {
		bizTextArea = e.bizTextArea.View()
		// Apply theme styling to the textarea content
		bizTextArea = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text()).Render(bizTextArea)
	} else {
		bizTextArea = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text()).Render("TextArea not available")
	}

	help := lipgloss.NewStyle().Background(t.Background()).Foreground(t.TextMuted()).Render("Esc save and exit  Ctrl+S save  Standard text editing keys")
	errorLine := ""
	if e.errorMsg != "" {
		errorLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Error()).Render("⚠ " + e.errorMsg)
	}
	infoLine := ""
	if e.infoMsg != "" {
		infoLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Success()).Render("✓ " + e.infoMsg)
	}

	content := strings.Join([]string{
		title,
		"",
		bizTextArea,
		"",
		help,
		errorLine,
		infoLine,
	}, "\n")

	return content
}

// renderListView renders the list of scenarios
func (e ScenarioEditor) renderListView(t theme.Theme) string {
	// file path and search status
	searchDisplay := e.searchQuery
	if searchDisplay == "" {
		searchDisplay = "(none)"
	}
	sub := lipgloss.NewStyle().Background(t.Background()).Foreground(t.TextMuted()).Render(
		fmt.Sprintf("File: %s  |  Search: %s  |  Matches: %d/%d", e.displayPath(), searchDisplay, len(e.filteredIdx), len(e.scenarios)),
	)

	// Business context section
	bizContext := ""
	if e.businessContext != nil {
		bizContext = *e.businessContext
	}
	bizLabel := "Business Context:"
	if e.bizContextSelected {
		bizLabel = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("› Business Context:")
	} else {
		bizLabel = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Accent()).Render("Business Context:")
	}

	// Update viewport content and render
	var bizText string
	if e.bizViewport != nil {
		e.bizViewport.SetContent(bizContext)
		bizText = e.bizViewport.View()
		// Apply theme styling to the viewport content
		bizText = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text()).Render(bizText)
	} else {
		bizText = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text()).Render(ellipsis(bizContext, e.width-20))
	}

	var body string
	if len(e.filteredIdx) == 0 {
		body = lipgloss.NewStyle().Background(t.Background()).Foreground(t.TextMuted()).Render("No scenarios. Press 'n' to add.")
	} else {
		start := e.scrollOffset
		end := start + e.visibleItems
		if end > len(e.filteredIdx) {
			end = len(e.filteredIdx)
		}

		// use near-full panel width (account for outer layout padding)
		contentWidth := e.width - 4
		if contentWidth < 60 {
			contentWidth = 60
		}
		typeWidth := 12
		remainingWidth := contentWidth - typeWidth
		colWidth := remainingWidth / 3
		if colWidth < 20 {
			colWidth = 20
		}

		// table header
		typeCol := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Accent()).Width(typeWidth).Render("Type")
		scenCol := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Accent()).Width(colWidth).Render("Scenario")
		outcomeCol := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Accent()).Width(colWidth).Render("Expected Outcome")
		rows := []string{lipgloss.JoinHorizontal(lipgloss.Left, typeCol, scenCol, outcomeCol)}

		for i := start; i < end; i++ {
			idx := e.filteredIdx[i]
			s := e.scenarios[idx]
			// Less intrusive selection: change type cell style only and use a subtle pointer
			pointer := "  "
			typeStyle := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text())
			scenStyle := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text())

			scenText := ellipsis(strings.ReplaceAll(s.Scenario, "\n", " "), colWidth-2)
			scenOutcome := ""
			if s.ExpectedOutcome != nil {
				scenOutcome = *s.ExpectedOutcome
				scenOutcome = strings.ReplaceAll(scenOutcome, "\n", " ")
			}
			scenOutcome = ellipsis(scenOutcome, colWidth-2)

			if i == e.selectedIndex && !e.bizContextSelected {
				pointer = "› "
				typeStyle = typeStyle.Background(t.Background()).Foreground(t.Primary()).Bold(true)
				scenStyle = scenStyle.Background(t.Background()).Foreground(t.Primary()).Bold(true)
			}

			line := lipgloss.JoinHorizontal(
				lipgloss.Left,
				typeStyle.Width(typeWidth).Render(pointer+s.ScenarioType),
				scenStyle.Width(colWidth).Render(scenText),
				scenStyle.Width(colWidth).Render(scenOutcome),
			)
			rows = append(rows, line)
		}
		// Render table within a compact width and keep it left-aligned inside the panel
		body = lipgloss.NewStyle().Width(contentWidth).Background(t.Background()).Render(strings.Join(rows, "\n"))
	}

	// Build lines and push help to bottom (above footer)
	help := lipgloss.NewStyle().Background(t.Background()).Foreground(t.TextMuted()).Render(
		"↑/↓ navigate scenarios & business context  Enter edit  n new  d delete  / search  Esc back",
	)

	errorLine := ""
	if e.errorMsg != "" {
		errorLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Error()).Render("⚠ " + e.errorMsg)
	}
	infoLine := ""
	if e.infoMsg != "" {
		infoLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Success()).Render("✓ " + e.infoMsg)
	}

	// Build content sections
	var contentParts []string
	contentParts = append(contentParts, "", sub, "", bizLabel, bizText, "", body, "")

	// Add error/info messages if present
	if errorLine != "" {
		contentParts = append(contentParts, errorLine)
	}
	if infoLine != "" {
		contentParts = append(contentParts, infoLine)
	}

	// Add help at the end
	contentParts = append(contentParts, "", help)

	content := strings.Join(contentParts, "\n")

	// No outer border/background; return plain content to fill full height under layout
	return content
}

// renderEditView renders the edit form
func (e ScenarioEditor) renderEditView(t theme.Theme) string {
	modeTitle := "Edit Scenario"
	if e.mode == AddMode {
		modeTitle = "Add New Scenario"
	}
	title := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("\n" + modeTitle)

	// Field 0: scenario (multiline, subtle style)
	scenLabel := "Scenario"
	if e.currentField == 0 {
		scenLabel = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("▶ Scenario")
	}
	scenText := renderTextArea(t, e.width-4, e.currentField == 0, e.editing.Scenario, e.cursorPos)

	// Field 1: expected_outcome (multiline, subtle style)
	outLabel := "Expected Outcome"
	if e.currentField == 1 {
		outLabel = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("▶ Expected Outcome")
	}
	outVal := ""
	if e.editing.ExpectedOutcome != nil {
		outVal = *e.editing.ExpectedOutcome
	}
	outText := renderTextArea(t, e.width-4, e.currentField == 1, outVal, e.cursorPos)

	// Simple Save button hint: third focus index (2)
	saveLabel := "Save"
	if e.currentField >= 2 {
		saveLabel = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("▶ Save")
	}

	help := lipgloss.NewStyle().Background(t.Background()).Foreground(t.TextMuted()).Render("↑/↓ switch fields  ←/→ move cursor  Enter newline/Save  Ctrl+S save  Esc cancel")
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

	content := strings.Join(parts, "\n\n")
	// Less intrusive: no border/background; fill width
	return content
}

// Helper rendering
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

// wrapTextWithStarts wraps text to the given width and returns lines and rune index starts for each line
func wrapTextWithStarts(text string, width int) ([]string, []int) {
	runes := []rune(text)
	var lines []string
	var starts []int
	start := 0
	col := 0
	for i := 0; i <= len(runes); i++ {
		atEnd := i == len(runes)
		if !atEnd && runes[i] == '\n' {
			lines = append(lines, string(runes[start:i]))
			starts = append(starts, start)
			start = i + 1
			col = 0
			continue
		}
		if !atEnd {
			col++
		}
		if atEnd || col >= width {
			lines = append(lines, string(runes[start:i]))
			starts = append(starts, start)
			start = i
			col = 0
		}
	}
	if len(lines) == 0 {
		lines = []string{""}
		starts = []int{0}
	}
	return lines, starts
}

func rowColForIndex(lineStarts []int, text string, width int, index int) (int, int) {
	runes := []rune(text)
	if index < 0 {
		index = 0
	}
	if index > len(runes) {
		index = len(runes)
	}
	// Find the line where index falls
	row := 0
	for i := 0; i < len(lineStarts); i++ {
		if index >= lineStarts[i] {
			row = i
		} else {
			break
		}
	}
	col := index - lineStarts[row]
	// Clamp col to wrapped width
	if col > width {
		col = width
	}
	return row, col
}

func indexForRowCol(lineStarts []int, text string, width int, row, col int) int {
	if row < 0 {
		row = 0
	}
	if row >= len(lineStarts) {
		row = len(lineStarts) - 1
	}
	lineStart := lineStarts[row]
	lineLen := 0
	runes := []rune(text)
	// Determine line length by next start or end
	if row+1 < len(lineStarts) {
		lineLen = lineStarts[row+1] - lineStart
	} else {
		lineLen = len(runes) - lineStart
	}
	if col > lineLen {
		col = lineLen
	}
	if col < 0 {
		col = 0
	}
	return lineStart + col
}

func insertAtRune(s string, idx int, insert string) string {
	r := []rune(s)
	if idx < 0 {
		idx = 0
	}
	if idx > len(r) {
		idx = len(r)
	}
	out := make([]rune, 0, len(r)+len([]rune(insert)))
	out = append(out, r[:idx]...)
	out = append(out, []rune(insert)...)
	out = append(out, r[idx:]...)
	return string(out)
}

// ConfirmDelete deletes the currently selected scenario (after a confirmation dialog)
func (e *ScenarioEditor) ConfirmDelete() {
	if len(e.filteredIdx) == 0 {
		return
	}
	idx := e.filteredIdx[e.selectedIndex]
	if idx < 0 || idx >= len(e.scenarios) {
		return
	}
	e.scenarios = append(e.scenarios[:idx], e.scenarios[idx+1:]...)
	if e.selectedIndex >= len(e.filteredIdx)-1 && e.selectedIndex > 0 {
		e.selectedIndex--
	}
	e.rebuildFilter()
	_ = e.saveScenarios()
	e.infoMsg = "Deleted scenario"
}

func ellipsis(s string, max int) string {
	if max <= 0 {
		return ""
	}
	if len(s) <= max {
		return s
	}
	if max <= 3 {
		return s[:max]
	}
	return s[:max-3] + "..."
}

// File discovery and IO
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
