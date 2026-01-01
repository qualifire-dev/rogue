package tui

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/rogue/tui/internal/components"
	"github.com/rogue/tui/internal/screens/help"
	"github.com/rogue/tui/internal/screens/redteam"
	"github.com/rogue/tui/internal/screens/redteam_report"
	"github.com/rogue/tui/internal/screens/report"
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
		// Initialize help viewport content if not already set
		m.initializeHelpViewport()
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
		// Check if model already has provider prefix (e.g., "bedrock/anthropic.claude-...")
		// If it does, use it as-is; otherwise, add the provider prefix
		if strings.Contains(m.config.SelectedModel, "/") {
			judgeModel = m.config.SelectedModel
		} else {
			judgeModel = m.config.SelectedProvider + "/" + m.config.SelectedModel
		}
	}
	// TODO read agent url and protocol .rogue/user_config.json
	scenariosWithContext := loadScenariosWithContextFromWorkdir()
	m.evalState = &EvaluationViewState{
		ServerURL:       m.config.ServerURL,
		AgentURL:        "http://localhost:10001",
		AgentProtocol:   ProtocolA2A,
		AgentTransport:  TransportHTTP,
		JudgeModel:      judgeModel,
		ParallelRuns:    1,
		DeepTest:        false,
		Scenarios:       scenariosWithContext.Scenarios,
		BusinessContext: scenariosWithContext.BusinessContext,
		EvaluationMode:  EvaluationModePolicy,
		RedTeamConfig:   nil,                                   // Will be initialized when switching to red team mode
		cursorPos:       len([]rune("http://localhost:10001")), // Set cursor to end of Agent URL
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
	if m.currentScreen == NewEvaluationScreen && m.evalState != nil &&
		(m.evalState.currentField == EvalFieldAgentURL || m.evalState.currentField == EvalFieldJudgeModel) {
		// Handle "/" character directly in text fields
		s := "/"
		switch m.evalState.currentField {
		case EvalFieldAgentURL:
			runes := []rune(m.evalState.AgentURL)
			m.evalState.AgentURL = string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
			m.evalState.cursorPos++
		case EvalFieldJudgeModel:
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

	if m.currentScreen == RedTeamConfigScreen {
		// Check if any dialogs are open in the red team config screen
		if m.redTeamConfigState != nil {
			if m.redTeamConfigState.ShowFrameworkDialog || m.redTeamConfigState.ShowAPIKeyDialog {
				// Close the dialog
				m.redTeamConfigState.ShowFrameworkDialog = false
				m.redTeamConfigState.ShowAPIKeyDialog = false
				m.redTeamConfigState.APIKeyInput = ""
				return m, nil
			}
		}
		// Save config and go back to evaluation form
		m.saveRedTeamConfigState()
		m.currentScreen = NewEvaluationScreen
		return m, nil
	}

	if m.currentScreen == ReportScreen {
		// go back to the evaluation view screen
		if m.reportHistory != nil {
			m.reportHistory.Blur()
		}
		m.currentScreen = EvaluationDetailScreen
		return m, nil
	}

	if m.currentScreen == RedTeamReportScreen {
		// ESC goes back to evaluation detail screen, not dashboard
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
		return HandleConfigEnter(m)
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
		// Use dynamic start button index based on evaluation mode
		// Policy mode: 6, Red Team mode: 8 (after ScanType at 6, Configure at 7)
		startButtonIdx := m.evalState.getStartButtonIndex()
		if m.evalState.currentField == startButtonIdx { // Start button field
			// Validate: Policy mode requires scenarios
			if m.evalState.EvaluationMode == EvaluationModePolicy && len(m.evalState.Scenarios) == 0 {
				errorDialog := components.ShowErrorDialog(
					"Cannot Start Evaluation",
					"Policy evaluation mode requires at least one scenario. Please add scenarios or switch to Red Team mode.",
				)
				m.dialog = &errorDialog
				return m, nil
			}
			// Validate: Full scan mode is coming soon
			if m.evalState.EvaluationMode == EvaluationModeRedTeam &&
				m.evalState.RedTeamConfig != nil &&
				m.evalState.RedTeamConfig.ScanType == ScanTypeFull {
				dialog := components.NewInfoDialog(
					"Full Scan - Coming Soon",
					"🔥 Full scan mode is coming soon!\n\nThis feature will enable comprehensive security testing with all available attacks and vulnerabilities.\n\nPlease select Basic or Custom scan type for now.",
				)
				m.dialog = &dialog
				return m, nil
			}
			m.handleNewEvalEnter()
			// Return command to start evaluation after showing spinner
			return m, tea.Batch(m.evalSpinner.Start(), startEvaluationCmd())
		} else if m.evalState.currentField == EvalFieldJudgeModel {
			// Open LLM config dialog when Enter is pressed on Judge LLM field
			llmDialog := components.NewLLMConfigDialog(m.config.APIKeys, m.config.SelectedProvider, m.config.SelectedModel)
			m.llmDialog = &llmDialog
			return m, nil
		} else if m.evalState.currentField == EvalFieldConfigureButton && m.evalState.EvaluationMode == EvaluationModeRedTeam {
			// Configure button - navigate to Red Team Config Screen
			m.currentScreen = RedTeamConfigScreen
			// Initialize red team config state if needed
			if m.redTeamConfigState == nil {
				m.redTeamConfigState = initRedTeamConfigState(m.evalState.RedTeamConfig, m.config.QualifireAPIKey)
			}
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
		return HandleConfigInput(m, msg)

	case ScenariosScreen:
		m.scenarioEditor, cmd = m.scenarioEditor.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		return m, tea.Batch(cmds...)

	case NewEvaluationScreen:
		return HandleEvalFormInput(m, msg)

	case EvaluationDetailScreen:
		return HandleEvalDetailInput(m, msg)

	case ReportScreen:
		hasEvalState := m.evalState != nil
		canRegenerate := m.evalState != nil && m.evalState.JobID != "" && !m.summarySpinner.IsActive()
		result := report.HandleInput(m.reportHistory, hasEvalState, canRegenerate, msg)
		m.reportHistory = result.ReportHistory

		// Handle actions
		switch result.Action {
		case report.ActionBackToDashboard:
			m.currentScreen = DashboardScreen
		case report.ActionRegenerateSummary:
			if m.evalState != nil {
				m.evalState.SummaryGenerated = false
				m.cachedReportSummary = "" // Clear cache to force rebuild
				m.summarySpinner.SetActive(true)
				return m, tea.Batch(result.Cmd, m.summarySpinner.Start(), m.summaryGenerationCmd())
			}
		}

		return m, result.Cmd

	case HelpScreen:
		updatedViewport, cmd := help.HandleInput(&m.helpViewport, msg)
		m.helpViewport = *updatedViewport
		return m, cmd

	case DashboardScreen:
		// Let the command input handle non-shortcut keys if it's focused
		if m.commandInput.IsFocused() {
			m.commandInput, cmd = m.commandInput.Update(msg)
			if cmd != nil {
				cmds = append(cmds, cmd)
			}
			return m, tea.Batch(cmds...)
		}

	case RedTeamConfigScreen:
		if m.redTeamConfigState != nil {
			m.redTeamConfigState, cmd = redteam.HandleKeyPress(m.redTeamConfigState, msg)
			if cmd != nil {
				cmds = append(cmds, cmd)
			}
		}
		return m, tea.Batch(cmds...)

	case RedTeamReportScreen:
		// Import redteam_report package at the top
		result := redteam_report.HandleInput(&m.redTeamReportViewport, msg)
		m.redTeamReportViewport = *result.Viewport

		// Handle actions
		switch result.Action {
		case redteam_report.ActionBackToEvalDetail:
			m.currentScreen = EvaluationDetailScreen
			return m, result.Cmd
		case redteam_report.ActionExportCSV:
			// TODO: Implement CSV export if needed
			return m, result.Cmd
		}

		return m, result.Cmd
	}

	return m, nil
}

// initRedTeamConfigState initializes the red team config state from the evaluation config
func initRedTeamConfigState(config *RedTeamConfig, qualifireAPIKey string) *redteam.RedTeamConfigState {
	state := redteam.NewRedTeamConfigState()

	// Set the API key from main config
	if qualifireAPIKey != "" {
		state.QualifireAPIKey = qualifireAPIKey
	}

	if config == nil {
		return state
	}

	// Set scan type
	switch config.ScanType {
	case ScanTypeBasic:
		state.ScanType = redteam.ScanTypeBasic
	case ScanTypeFull:
		state.ScanType = redteam.ScanTypeFull
	case ScanTypeCustom:
		state.ScanType = redteam.ScanTypeCustom
	}

	// Check if we need to apply preset selections
	hasVulnerabilities := len(config.Vulnerabilities) > 0
	hasAttacks := len(config.Attacks) > 0

	if !hasVulnerabilities && !hasAttacks {
		// No selections yet, apply preset based on scan type
		switch config.ScanType {
		case ScanTypeBasic:
			// Apply basic preset
			for _, id := range redteam.GetBasicScanVulnerabilities() {
				state.SelectedVulnerabilities[id] = true
			}
			for _, id := range redteam.GetBasicScanAttacks() {
				state.SelectedAttacks[id] = true
			}
		case ScanTypeFull:
			// Apply full preset
			for _, id := range redteam.GetFreeVulnerabilities() {
				state.SelectedVulnerabilities[id] = true
			}
			for _, id := range redteam.GetFreeAttacks() {
				state.SelectedAttacks[id] = true
			}
			// If API key present, also select premium
			if state.QualifireAPIKey != "" {
				for id, vuln := range redteam.VulnerabilityCatalog {
					if vuln.Premium {
						state.SelectedVulnerabilities[id] = true
					}
				}
				for id, attack := range redteam.AttackCatalog {
					if attack.Premium {
						state.SelectedAttacks[id] = true
					}
				}
			}
		}
	} else {
		// Copy existing selections, filtering out premium items if no API key
		for _, v := range config.Vulnerabilities {
			vuln := redteam.GetVulnerability(v)
			if vuln != nil && (!vuln.Premium || state.QualifireAPIKey != "") {
				state.SelectedVulnerabilities[v] = true
			}
		}

		for _, a := range config.Attacks {
			attack := redteam.GetAttack(a)
			if attack != nil && (!attack.Premium || state.QualifireAPIKey != "") {
				state.SelectedAttacks[a] = true
			}
		}
	}

	// Copy selected frameworks
	for _, f := range config.Frameworks {
		state.SelectedFrameworks[f] = true
	}

	// Copy attacks per vulnerability
	state.AttacksPerVulnerability = config.AttacksPerVulnerability

	return state
}

// saveRedTeamConfigState saves the red team config state back to the evaluation state
func (m *Model) saveRedTeamConfigState() {
	if m.redTeamConfigState == nil || m.evalState == nil {
		return
	}

	// Create or update RedTeamConfig
	if m.evalState.RedTeamConfig == nil {
		m.evalState.RedTeamConfig = &RedTeamConfig{}
	}

	// Set scan type
	switch m.redTeamConfigState.ScanType {
	case redteam.ScanTypeBasic:
		m.evalState.RedTeamConfig.ScanType = ScanTypeBasic
	case redteam.ScanTypeFull:
		m.evalState.RedTeamConfig.ScanType = ScanTypeFull
	case redteam.ScanTypeCustom:
		m.evalState.RedTeamConfig.ScanType = ScanTypeCustom
	}

	// Copy selected vulnerabilities
	vulnerabilities := make([]string, 0)
	for id, selected := range m.redTeamConfigState.SelectedVulnerabilities {
		if selected {
			vulnerabilities = append(vulnerabilities, id)
		}
	}
	m.evalState.RedTeamConfig.Vulnerabilities = vulnerabilities

	// Copy selected attacks
	attacks := make([]string, 0)
	for id, selected := range m.redTeamConfigState.SelectedAttacks {
		if selected {
			attacks = append(attacks, id)
		}
	}
	m.evalState.RedTeamConfig.Attacks = attacks

	// Copy selected frameworks
	frameworks := make([]string, 0)
	for id, selected := range m.redTeamConfigState.SelectedFrameworks {
		if selected {
			frameworks = append(frameworks, id)
		}
	}
	m.evalState.RedTeamConfig.Frameworks = frameworks

	// Copy attacks per vulnerability
	m.evalState.RedTeamConfig.AttacksPerVulnerability = m.redTeamConfigState.AttacksPerVulnerability

	// Set the notification flag to show subtle green text
	m.evalState.RedTeamConfigSaved = true
	vulnCount := len(vulnerabilities)
	attackCount := len(attacks)
	m.evalState.RedTeamConfigSavedMsg = fmt.Sprintf("✓ Saved: %d vulnerabilities, %d attacks → .rogue/redteam.yaml", vulnCount, attackCount)
}
