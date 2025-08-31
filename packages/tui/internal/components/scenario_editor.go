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

	// Scenario editing
	scenarioTextArea        *TextArea
	expectedOutcomeTextArea *TextArea

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

	ta := NewTextArea(9998, 80, 10, theme.CurrentTheme()) // Use unique ID
	ta.ApplyTheme(theme.CurrentTheme())                   // Apply current theme
	editor.bizTextArea = &ta

	// Initialize scenario editing TextAreas
	scenTA := NewTextArea(9997, 80, 8, theme.CurrentTheme()) // Scenario text area
	scenTA.ApplyTheme(theme.CurrentTheme())
	editor.scenarioTextArea = &scenTA

	outTA := NewTextArea(9996, 80, 8, theme.CurrentTheme()) // Expected outcome text area
	outTA.ApplyTheme(theme.CurrentTheme())
	editor.expectedOutcomeTextArea = &outTA

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
	// Calculate visible items more accurately based on actual UI elements
	e.calculateVisibleItems()

	// Update business context components size - make it adaptive
	if e.bizViewport != nil {
		// Use smaller business context to leave more room for scenarios
		bizHeight := 3 // Reduce from 10 to 3 lines for business context
		if height < 20 {
			bizHeight = 2 // Even smaller on very small terminals
		}
		e.bizViewport.SetSize(width-4, bizHeight)
	}
	if e.bizTextArea != nil {
		// Size will be set dynamically in renderBusinessContextView
		// Just update width here
		e.bizTextArea.SetSize(width-4, e.bizTextArea.Height)
	}

	// Update scenario editing TextAreas size
	if e.scenarioTextArea != nil {
		e.scenarioTextArea.SetSize(width-4, 8) // Height will be set dynamically in renderEditView
	}
	if e.expectedOutcomeTextArea != nil {
		e.expectedOutcomeTextArea.SetSize(width-4, 8) // Height will be set dynamically in renderEditView
	}
}

// calculateVisibleItems computes how many scenario items can fit in the available space
func (e *ScenarioEditor) calculateVisibleItems() {
	if e.mode != ListMode {
		return
	}

	// Calculate the height used by UI elements in list mode:
	// - Footer (from layout.go): 1 line
	// - Empty line after main content: 1 line
	// - File path/search info: 1 line
	// - Empty line: 1 line
	// - Business context label: 1 line
	// - Business context box (viewport): dynamic height + 2 for border
	// - Empty line: 1 line
	// - Table header: 1 line
	// - Scroll info (when present): 1 line
	// - Empty line before help: 1 line
	// - Help text: 1 line
	// - Error/info messages: up to 2 lines
	// - Extra padding/margins: 2 lines for safety

	// Calculate business context height dynamically (same as in SetSize)
	bizHeight := 3
	if e.height < 20 {
		bizHeight = 2
	}
	bizHeightWithBorder := bizHeight + 2

	usedHeight := 1 + 1 + 1 + 1 + 1 + bizHeightWithBorder + 1 + 1 + 1 + 1 + 1 + 2 + 2 // Base: 14 + bizHeightWithBorder

	availableHeight := e.height - usedHeight
	if availableHeight < 3 {
		availableHeight = 3 // Minimum to show at least a few items
	}

	e.visibleItems = availableHeight

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
	case "up":
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

	case "down":
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
		e.errorMsg = ""
		e.infoMsg = ""

		// Set up TextAreas with current values
		if e.scenarioTextArea != nil {
			e.scenarioTextArea.SetValue(e.editing.Scenario)
			e.scenarioTextArea.Focus()
		}
		if e.expectedOutcomeTextArea != nil {
			outVal := ""
			if e.editing.ExpectedOutcome != nil {
				outVal = *e.editing.ExpectedOutcome
			}
			e.expectedOutcomeTextArea.SetValue(outVal)
			e.expectedOutcomeTextArea.Blur()
		}
		return e, nil

	case "n", "a":
		// Add new scenario
		e.mode = AddMode
		e.editing = ScenarioData{ScenarioType: "policy"}
		e.currentField = 0
		e.errorMsg = ""
		e.infoMsg = ""

		// Set up TextAreas for new scenario
		if e.scenarioTextArea != nil {
			e.scenarioTextArea.SetValue("")
			e.scenarioTextArea.Focus()
		}
		if e.expectedOutcomeTextArea != nil {
			e.expectedOutcomeTextArea.SetValue("")
			e.expectedOutcomeTextArea.Blur()
		}
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
		e.calculateVisibleItems()   // Recalculate for list mode
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
	// Ensure we have valid visible items calculation
	if e.visibleItems <= 0 {
		e.calculateVisibleItems()
	}

	// Clamp scroll offset to valid bounds
	maxScroll := len(e.filteredIdx) - e.visibleItems
	if maxScroll < 0 {
		maxScroll = 0
	}

	if e.selectedIndex < e.scrollOffset {
		e.scrollOffset = e.selectedIndex
	} else if e.selectedIndex >= e.scrollOffset+e.visibleItems {
		e.scrollOffset = e.selectedIndex - e.visibleItems + 1
	}

	// Ensure scroll offset is within bounds
	if e.scrollOffset < 0 {
		e.scrollOffset = 0
	}
	if e.scrollOffset > maxScroll {
		e.scrollOffset = maxScroll
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

	help := lipgloss.NewStyle().Background(t.Background()).Foreground(t.TextMuted()).Render("Esc save and exit  Ctrl+S save  Standard text editing keys")
	errorLine := ""
	if e.errorMsg != "" {
		errorLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Error()).Render("⚠ " + e.errorMsg)
	}
	infoLine := ""
	if e.infoMsg != "" {
		infoLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Success()).Render("✓ " + e.infoMsg)
	}

	// Calculate available height for textarea and border
	usedHeight := 0
	usedHeight += 2 // title (1 line) + blank line after title
	usedHeight += 2 // border top and bottom
	usedHeight += 1 // blank line before help
	usedHeight += 1 // help line
	if errorLine != "" {
		usedHeight += 1 // error line
	}
	if infoLine != "" {
		usedHeight += 1 // info line
	}

	// Calculate maximum textarea height (subtract from total available height)
	availableHeight := e.height - 1                    // -1 for parent layout
	textAreaHeight := availableHeight - usedHeight - 5 // -5 to prevent footer overflow
	if textAreaHeight < 5 {
		textAreaHeight = 5 // Minimum height
	}

	// Update textarea size to use maximum available height (account for border padding)
	var bizTextArea string
	if e.bizTextArea != nil {
		e.bizTextArea.SetSize(e.width-10, textAreaHeight) // -8 for border and padding
		bizTextArea = e.bizTextArea.View()
	} else {
		bizTextArea = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text()).Render("TextArea not available")
	}

	// Create bordered container for the textarea (primary border when editing)
	borderStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Primary()).
		Background(t.BackgroundPanel()).
		Padding(1, 1).
		Width(e.width - 4).        // Account for outer padding
		Height(textAreaHeight + 2) // +2 for border padding

	borderedTextArea := borderStyle.Render(bizTextArea)

	content := strings.Join([]string{
		title,
		"",
		borderedTextArea,
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

	// Choose border style based on selection state
	var borderStyle lipgloss.Style
	if e.bizContextSelected {
		// Primary border and panel background when selected
		borderStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(t.Primary()).
			Background(t.BackgroundPanel()).
			BorderBackground(t.BackgroundPanel()).
			Padding(0, 1).
			Width(e.width - 8) // Account for padding and border
	} else {
		// Subtle border when not selected
		borderStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(t.TextMuted()).
			BorderBackground(t.BackgroundPanel()).
			Background(t.BackgroundPanel()).
			Padding(0, 1).
			Width(e.width - 8) // Account for padding and border
	}

	if e.bizViewport != nil {
		e.bizViewport.SetContent(bizContext)
		viewportContent := e.bizViewport.View()
		bizText = borderStyle.Render(viewportContent)
	} else {
		content := ellipsis(bizContext, e.width-20)
		bizText = borderStyle.Render(content)
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
		colWidth := remainingWidth / 2
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

		// Add scroll indicators if needed
		scrollInfo := ""
		if len(e.filteredIdx) > e.visibleItems {
			canScrollUp := e.scrollOffset > 0
			canScrollDown := e.scrollOffset+e.visibleItems < len(e.filteredIdx)

			upIndicator := " "
			downIndicator := " "
			if canScrollUp {
				upIndicator = "↑"
			}
			if canScrollDown {
				downIndicator = "↓"
			}

			visibleCount := end - start
			scrollInfo = lipgloss.NewStyle().
				Background(t.Background()).
				Foreground(t.TextMuted()).
				Render(fmt.Sprintf(" Scroll: %s%s (%d-%d of %d)",
					upIndicator, downIndicator,
					start+1,
					start+visibleCount,
					len(e.filteredIdx)))
		}

		tableContent := strings.Join(rows, "\n")
		if scrollInfo != "" {
			tableContent += "\n" + scrollInfo
		}

		// Render table within a compact width and keep it left-aligned inside the panel
		body = lipgloss.NewStyle().Width(contentWidth).Background(t.Background()).Render(tableContent)
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
