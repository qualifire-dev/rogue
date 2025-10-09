package components

import (
	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/styles"
	"github.com/rogue/tui/internal/theme"
)

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

	// Interview mode
	interviewMode               bool      // true when in interview mode
	interviewSessionID          string    // current interview session
	interviewChatView           *ChatView // reusable chat component
	lastUserMessage             string    // track last user message for display
	awaitingBusinessCtxApproval bool      // waiting for user to approve/edit business context
	proposedBusinessContext     string    // the AI-generated business context for review
	approveButtonFocused        bool      // true when approve button is focused instead of input

	// Configuration (set by parent app) - exported so app.go can access
	ServerURL       string // Rogue server URL
	InterviewModel  string // model for interview (e.g., "openai/gpt-4o")
	InterviewAPIKey string // API key for interview model

	// File management
	filePath string // path to .rogue/scenarios.json

	// UX
	errorMsg string
	infoMsg  string
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

	// Interview chat view will be initialized when entering interview mode
	// (lazy initialization to have proper dimensions)

	// Discover scenarios.json location and load
	editor.filePath = discoverScenariosFile()
	_ = editor.loadScenarios()
	editor.rebuildFilter()
	return editor
}

// SetConfig sets the configuration for interview mode
func (e *ScenarioEditor) SetConfig(serverURL, interviewModel, interviewAPIKey string) {
	e.ServerURL = serverURL
	e.InterviewModel = interviewModel
	e.InterviewAPIKey = interviewAPIKey
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

	// Update interview chat view size
	if e.interviewChatView != nil {
		e.interviewChatView.SetSize(width, height)
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
	case SpinnerTickMsg:
		// Update interview chat view spinner
		if e.interviewChatView != nil {
			cmd := e.interviewChatView.Update(msg)
			return e, cmd
		}
		return e, nil
	// StartInterviewMsg is NOT handled here - it bubbles up to app.go
	// app.go will make the API call and send back InterviewStartedMsg
	case InterviewStartedMsg:
		return e.handleInterviewStarted(m)
	case InterviewResponseMsg:
		return e.handleInterviewResponse(m)
	case ScenariosGeneratedMsg:
		return e.handleScenariosGenerated(m)
	case DialogClosedMsg:
		// Handle dialog results (e.g., from interview cancellation)
		if e.mode == InterviewMode && m.Action == "ok" {
			// User confirmed they want to exit interview - return to list mode
			e.mode = ListMode
			e.interviewMode = false
			e.interviewSessionID = ""
			e.awaitingBusinessCtxApproval = false
			e.proposedBusinessContext = ""
			e.approveButtonFocused = false
			e.lastUserMessage = ""
			e.interviewChatView = nil
			e.infoMsg = "Interview cancelled"
		}
		return e, nil
	case tea.PasteMsg:
		// Forward paste message to the appropriate TextArea based on mode
		switch e.mode {
		case BusinessContextMode:
			if e.bizTextArea != nil {
				updatedTextArea, cmd := e.bizTextArea.Update(msg)
				*e.bizTextArea = *updatedTextArea
				return e, cmd
			}
		case InterviewMode:
			if e.interviewChatView != nil && !e.interviewChatView.IsLoading() {
				cmd := e.interviewChatView.Update(msg)
				return e, cmd
			}
		case EditMode, AddMode:
			// Forward to the currently focused TextArea
			var cmd tea.Cmd
			if e.currentField == 0 && e.scenarioTextArea != nil {
				updatedTextArea, taCmd := e.scenarioTextArea.Update(msg)
				*e.scenarioTextArea = *updatedTextArea
				cmd = taCmd
			} else if e.currentField == 1 && e.expectedOutcomeTextArea != nil {
				updatedTextArea, taCmd := e.expectedOutcomeTextArea.Update(msg)
				*e.expectedOutcomeTextArea = *updatedTextArea
				cmd = taCmd
			}
			return e, cmd
		}
		return e, nil
	case tea.KeyMsg:
		switch e.mode {
		case ListMode:
			return e.handleListMode(m)
		case EditMode, AddMode:
			return e.handleEditMode(m)
		case BusinessContextMode:
			return e.handleBusinessContextMode(m)
		case InterviewMode:
			return e.handleInterviewMode(m)
		}
	}
	return e, nil
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
	case InterviewMode:
		return lipgloss.Place(
			e.width,
			e.height-1,
			lipgloss.Left,
			lipgloss.Top,
			e.renderInterviewView(t),
			styles.WhitespaceStyle(t.Background()),
		)

	default:
		return ""
	}
}
