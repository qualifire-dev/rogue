package tui

import (
	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/rogue/tui/internal/components"
)

// handleKeyMsg is the main keyboard input router
func (m Model) handleKeyMsg(msg tea.KeyMsg) (Model, tea.Cmd) {
	var cmd tea.Cmd
	var cmds []tea.Cmd

	// Handle ctrl+c globally - always quit regardless of dialog state
	if msg.String() == "ctrl+c" {
		return m, tea.Quit
	}

	// Handle LLM dialog input first if LLM dialog is open
	if m.llmDialog != nil {
		*m.llmDialog, cmd = m.llmDialog.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		return m, tea.Batch(cmds...)
	}

	// Handle dialog input first if dialog is open
	if m.dialog != nil {
		*m.dialog, cmd = m.dialog.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		return m, tea.Batch(cmds...)
	}

	// Handle global keyboard shortcuts first (regardless of focus state)
	switch msg.String() {
	case "ctrl+n":
		return m.handleGlobalCtrlN()

	case "ctrl+l":
		return m.handleGlobalCtrlL()

	case "ctrl+e":
		return m.handleGlobalCtrlE()

	case "ctrl+g":
		return m.handleGlobalCtrlG()

	case "ctrl+h", "?":
		m.currentScreen = HelpScreen
		return m, nil

	case "ctrl+i":
		m.currentScreen = InterviewScreen
		return m, nil

	case "/":
		return m.handleGlobalSlash(msg)

	case "esc":
		return m.handleGlobalEscape(msg)

	case "enter":
		return m.handleGlobalEnter(msg)

	default:
		// Route to screen-specific handlers
		return m.routeKeyToScreen(msg)
	}
}

// handleGlobalCtrlN handles Ctrl+N (new evaluation) shortcut
func (m Model) handleGlobalCtrlN() (Model, tea.Cmd) {
	judgeModel := "openai/gpt-4.1" // fallback default
	if m.config.SelectedModel != "" && m.config.SelectedProvider != "" {
		// Use the configured model in provider/model format
		judgeModel = m.config.SelectedProvider + "/" + m.config.SelectedModel
	}
	m.evalState = &EvaluationViewState{
		ServerURL:    m.config.ServerURL,
		AgentURL:     "http://localhost:10001",
		JudgeModel:   judgeModel,
		ParallelRuns: 1,
		DeepTest:     false,
		Scenarios:    loadScenariosFromWorkdir(),
		cursorPos:    len([]rune("http://localhost:10001")), // Set cursor to end of Agent URL
	}
	m.currentScreen = NewEvaluationScreen
	return m, nil
}

// handleGlobalCtrlL handles Ctrl+L (LLM config) shortcut
func (m Model) handleGlobalCtrlL() (Model, tea.Cmd) {
	llmDialog := components.NewLLMConfigDialog(m.config.APIKeys, m.config.SelectedProvider, m.config.SelectedModel)
	m.llmDialog = &llmDialog
	return m, nil
}

// handleGlobalCtrlE handles Ctrl+E (scenario editor) shortcut
func (m Model) handleGlobalCtrlE() (Model, tea.Cmd) {
	m.currentScreen = ScenariosScreen
	// Unfocus command input when entering scenarios screen
	m.commandInput.SetFocus(false)
	m.commandInput.SetValue("")
	// Configure scenario editor with interview model settings
	m.configureScenarioEditorWithInterviewModel()
	return m, nil
}

// handleGlobalCtrlG handles Ctrl+G (configuration) shortcut
func (m Model) handleGlobalCtrlG() (Model, tea.Cmd) {
	m.currentScreen = ConfigurationScreen
	// Initialize config state when entering configuration screen
	m.configState = &ConfigState{
		ActiveField:      ConfigFieldServerURL,
		ServerURL:        m.config.ServerURL,
		CursorPos:        len(m.config.ServerURL), // Start cursor at end of existing text
		ThemeIndex:       m.findCurrentThemeIndex(),
		IsEditing:        true, // Automatically start editing the server URL field
		HasChanges:       false,
		QualifireEnabled: m.config.QualifireAPIKey != "" && m.config.QualifireEnabled, // Set based on API key and enabled flag
	}
	return m, nil
}

// handleGlobalSlash handles "/" key for command input
func (m Model) handleGlobalSlash(msg tea.KeyMsg) (Model, tea.Cmd) {
	var cmd tea.Cmd
	var cmds []tea.Cmd

	// Check if we're editing text fields that might need "/" character
	// Don't intercept "/" if we're editing text in NewEvaluationScreen
	if m.currentScreen == NewEvaluationScreen && m.evalState != nil && m.evalState.currentField <= 1 {
		// Handle "/" character directly in text fields
		s := "/"
		switch m.evalState.currentField {
		case 0: // AgentURL
			runes := []rune(m.evalState.AgentURL)
			m.evalState.AgentURL = string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
			m.evalState.cursorPos++
		case 1: // JudgeModel
			runes := []rune(m.evalState.JudgeModel)
			m.evalState.JudgeModel = string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
			m.evalState.cursorPos++
		}
		return m, nil
	}
	// Don't intercept "/" if we're editing text in ConfigurationScreen
	if m.currentScreen == ConfigurationScreen && m.configState != nil &&
		m.configState.IsEditing && m.configState.ActiveField == ConfigFieldServerURL {
		// Handle "/" character directly in server URL field
		m.configState.ServerURL = m.configState.ServerURL[:m.configState.CursorPos] +
			"/" + m.configState.ServerURL[m.configState.CursorPos:]
		m.configState.CursorPos++
		return m, nil
	}
	// If on scenarios screen, forward to editor for search
	if m.currentScreen == ScenariosScreen {
		m.scenarioEditor, cmd = m.scenarioEditor.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		return m, tea.Batch(cmds...)
	}
	// Otherwise focus the global command input
	m.commandInput.SetFocus(true)
	m.commandInput.SetValue("/")
	return m, nil
}

// handleGlobalEscape handles ESC key
func (m Model) handleGlobalEscape(msg tea.KeyMsg) (Model, tea.Cmd) {
	var cmd tea.Cmd
	var cmds []tea.Cmd

	// Don't handle esc globally if dialogs are open - they should handle it
	if m.llmDialog != nil || m.dialog != nil {
		// Let dialogs handle escape - this shouldn't be reached due to order, but just in case
		return m, nil
	}
	if m.currentScreen == ConfigurationScreen && m.configState != nil {
		if m.configState.IsEditing {
			// Cancel editing and revert changes
			m.configState.IsEditing = false
			m.configState.ServerURL = m.config.ServerURL
			m.configState.CursorPos = 0
			m.configState.HasChanges = false
			return m, nil
		} else {
			// Exit configuration screen
			m.currentScreen = DashboardScreen
			m.configState = nil
			m.commandInput.SetFocus(true)
			m.commandInput.SetValue("")
			return m, nil
		}
	}
	if m.currentScreen == ScenariosScreen {
		// Let the editor consume ESC first
		m.scenarioEditor, cmd = m.scenarioEditor.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		return m, tea.Batch(cmds...)
	}

	if m.currentScreen == ReportScreen {
		// go back to the evaluation view screen
		if m.reportHistory != nil {
			m.reportHistory.Blur()
		}
		m.currentScreen = EvaluationDetailScreen
		return m, nil
	}
	if m.currentScreen == EvaluationDetailScreen {
		// Check if we should show the Qualifire persistence dialog
		shouldShowDialog := m.evalState != nil &&
			m.evalState.Completed &&
			m.config.QualifireAPIKey == "" &&
			!m.config.DontShowQualifirePrompt

		if shouldShowDialog {
			// Show report persistence dialog
			dialog := components.NewReportPersistenceDialog()
			m.dialog = &dialog
			return m, nil
		}
		// If no dialog needed, proceed to dashboard
	}
	// Default ESC behavior: back to dashboard
	// Blur any focused viewports when leaving
	if m.currentScreen == ReportScreen && m.reportHistory != nil {
		m.reportHistory.Blur()
	}
	m.currentScreen = DashboardScreen
	m.commandInput.SetFocus(true) // Keep focused when returning to dashboard
	m.commandInput.SetValue("")
	return m, nil
}

// handleGlobalEnter handles Enter key
func (m Model) handleGlobalEnter(msg tea.KeyMsg) (Model, tea.Cmd) {
	var cmd tea.Cmd
	var cmds []tea.Cmd

	// If command input has suggestions, let it handle the enter key
	if m.commandInput.IsFocused() && m.commandInput.HasSuggestions() {
		m.commandInput, cmd = m.commandInput.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		return m, tea.Batch(cmds...)
	}
	// Handle configuration screen enter
	if m.currentScreen == ConfigurationScreen && m.configState != nil {
		return m.handleConfigEnter()
	}
	// Forward enter to the active screen if needed
	if m.currentScreen == ScenariosScreen {
		m.scenarioEditor, cmd = m.scenarioEditor.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		return m, tea.Batch(cmds...)
	}
	// Handle NewEvaluationScreen enter for start button and LLM config
	if m.currentScreen == NewEvaluationScreen && m.evalState != nil {
		if m.evalState.currentField == 3 { // Start button field
			m.handleNewEvalEnter()
			// Return command to start evaluation after showing spinner
			return m, tea.Batch(m.evalSpinner.Start(), startEvaluationCmd())
		} else if m.evalState.currentField == 1 { // Judge LLM field
			// Open LLM config dialog when Enter is pressed on Judge LLM field
			llmDialog := components.NewLLMConfigDialog(m.config.APIKeys, m.config.SelectedProvider, m.config.SelectedModel)
			m.llmDialog = &llmDialog
			return m, nil
		}
		return m, nil // Don't process enter on other fields
	}
	// Handle enter key based on current screen
	if m.currentScreen == DashboardScreen {
		// Focus the command input on enter
		m.commandInput.SetFocus(true)
	}
	return m, nil
}

// routeKeyToScreen routes keyboard input to the appropriate screen handler
func (m Model) routeKeyToScreen(msg tea.KeyMsg) (Model, tea.Cmd) {
	var cmd tea.Cmd
	var cmds []tea.Cmd

	switch m.currentScreen {
	case ConfigurationScreen:
		return m.handleConfigInput(msg)

	case ScenariosScreen:
		m.scenarioEditor, cmd = m.scenarioEditor.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		return m, tea.Batch(cmds...)

	case NewEvaluationScreen:
		return m.handleEvalFormInput(msg)

	case EvaluationDetailScreen:
		return m.handleEvalDetailInput(msg)

	case ReportScreen:
		return m.handleReportInput(msg)

	case HelpScreen:
		return m.handleHelpInput(msg)

	case DashboardScreen:
		// Let the command input handle non-shortcut keys if it's focused
		if m.commandInput.IsFocused() {
			m.commandInput, cmd = m.commandInput.Update(msg)
			if cmd != nil {
				cmds = append(cmds, cmd)
			}
			return m, tea.Batch(cmds...)
		}
	}

	return m, nil
}
