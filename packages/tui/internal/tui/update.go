package tui

import (
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/api"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/commands"
)

// connectToServer establishes connection to the Rogue server
func (m *Model) connectToServer() tea.Cmd {
	return tea.Batch(
		func() tea.Msg {
			// Test HTTP connection
			_, err := m.apiClient.Health()
			if err != nil {
				return connectionErrorMsg{err}
			}
			return connectionSuccessMsg{}
		},
		m.wsClient.Connect(),
	)
}

// loadInitialData loads initial data for the application
func (m *Model) loadInitialData() tea.Cmd {
	m.loading = true
	m.loadingText = "Loading initial data..."
	return m.spinner.Start()
}

// loadScreenData loads data specific to the current screen
func (m *Model) loadScreenData() tea.Cmd {
	switch m.currentScreen {
	case ScreenEvaluations:
		return m.loadEvaluations()
	case ScreenEvalDetail:
		return m.loadEvaluationDetail(m.selectedEvaluation)
	case ScreenScenarios:
		return m.loadScenarios()
	case ScreenInterview:
		if m.interviewSessionID == "" {
			return m.startInterviewSession()
		}
	}
	return nil
}

// loadEvaluations loads the list of evaluations
func (m *Model) loadEvaluations() tea.Cmd {
	return func() tea.Msg {
		evaluations, err := m.apiClient.GetEvaluations()
		if err != nil {
			return dataLoadErrorMsg{err}
		}
		return evaluationsLoadedMsg{evaluations}
	}
}

// loadEvaluationDetail loads details for a specific evaluation
func (m *Model) loadEvaluationDetail(evalID string) tea.Cmd {
	return func() tea.Msg {
		evaluation, err := m.apiClient.GetEvaluation(evalID)
		if err != nil {
			return dataLoadErrorMsg{err}
		}
		return evaluationDetailLoadedMsg{evaluation}
	}
}

// loadScenarios loads the list of scenarios
func (m *Model) loadScenarios() tea.Cmd {
	return func() tea.Msg {
		scenarios, err := m.apiClient.GetScenarios()
		if err != nil {
			return dataLoadErrorMsg{err}
		}
		return scenariosLoadedMsg{scenarios}
	}
}

// startInterviewSession starts a new interview session
func (m *Model) startInterviewSession() tea.Cmd {
	agentURL := m.config.Agent.DefaultURL

	return func() tea.Msg {
		sessionID, err := m.apiClient.StartInterviewSession(agentURL)
		if err != nil {
			return dataLoadErrorMsg{err}
		}
		return interviewSessionStartedMsg{sessionID, agentURL}
	}
}

// handleShortcutAction handles actions triggered by keyboard shortcuts
func (m *Model) handleShortcutAction(action commands.CommandAction, data map[string]interface{}) tea.Cmd {
	switch action {
	case commands.ActionSwitchScreen:
		if screen, ok := data["screen"].(string); ok {
			return m.navigateToScreen(Screen(screen))
		}

	case commands.ActionStartInterview:
		m.interviewSessionID = ""
		return m.navigateToScreen(ScreenInterview)

	case commands.ActionShowModal:
		if modalType, ok := data["modal_type"].(string); ok {
			return m.showModalOfType(modalType)
		}

	case commands.ActionRefresh:
		return m.refreshCurrentScreen()

	case commands.ActionClear:
		return m.clearScreen()

	case commands.ActionQuit:
		return tea.Quit
	}

	return nil
}

// handleCommandResult handles the result of executing a command
func (m *Model) handleCommandResult(result commands.CommandResult) tea.Cmd {
	// Show message if provided
	if result.Message != "" {
		m.footer.SetStatus(result.Message)
	}

	return m.handleShortcutAction(result.Action, result.Data)
}

// handleWebSocketMessage handles incoming WebSocket messages
func (m *Model) handleWebSocketMessage(msg api.WSMessage) tea.Cmd {
	return m.wsClient.HandleMessage(msg)
}

// handleScreenKeyMessage handles key messages specific to the current screen
func (m *Model) handleScreenKeyMessage(msg tea.KeyMsg) tea.Cmd {
	switch m.currentScreen {
	case ScreenDashboard:
		return m.handleDashboardKeys(msg)
	case ScreenEvaluations:
		return m.handleEvaluationsKeys(msg)
	case ScreenEvalDetail:
		return m.handleEvalDetailKeys(msg)
	case ScreenNewEval:
		return m.handleNewEvalKeys(msg)
	case ScreenInterview:
		return m.handleInterviewKeys(msg)
	case ScreenConfig:
		return m.handleConfigKeys(msg)
	case ScreenScenarios:
		return m.handleScenariosKeys(msg)
	}
	return nil
}

// Screen-specific key handlers
func (m *Model) handleDashboardKeys(msg tea.KeyMsg) tea.Cmd {
	switch msg.String() {
	case "1", "n":
		return m.navigateToScreen(ScreenNewEval)
	case "2", "e":
		return m.navigateToScreen(ScreenEvaluations)
	case "3", "i":
		return m.navigateToScreen(ScreenInterview)
	case "4", "c":
		return m.navigateToScreen(ScreenConfig)
	case "5", "s":
		return m.navigateToScreen(ScreenScenarios)
	}
	return nil
}

func (m *Model) handleEvaluationsKeys(msg tea.KeyMsg) tea.Cmd {
	switch msg.String() {
	case "enter":
		if m.selectedEvaluation != "" {
			return m.navigateToScreen(ScreenEvalDetail)
		}
	case "up":
		return m.selectPreviousEvaluation()
	case "down":
		return m.selectNextEvaluation()
	case "r":
		return m.refreshCurrentScreen()
	}
	return nil
}

func (m *Model) handleEvalDetailKeys(msg tea.KeyMsg) tea.Cmd {
	switch msg.String() {
	case "r":
		return m.refreshCurrentScreen()
	}
	return nil
}

func (m *Model) handleNewEvalKeys(msg tea.KeyMsg) tea.Cmd {
	// TODO: Implement new evaluation form key handling
	return nil
}

func (m *Model) handleInterviewKeys(msg tea.KeyMsg) tea.Cmd {
	// TODO: Implement interview mode key handling
	return nil
}

func (m *Model) handleConfigKeys(msg tea.KeyMsg) tea.Cmd {
	// TODO: Implement configuration key handling
	return nil
}

func (m *Model) handleScenariosKeys(msg tea.KeyMsg) tea.Cmd {
	switch msg.String() {
	case "enter":
		if m.selectedScenario != "" {
			// TODO: Navigate to scenario detail/edit
		}
	case "up":
		return m.selectPreviousScenario()
	case "down":
		return m.selectNextScenario()
	case "r":
		return m.refreshCurrentScreen()
	}
	return nil
}

// Navigation helpers
func (m *Model) selectNextEvaluation() tea.Cmd {
	if len(m.evaluations) == 0 {
		return nil
	}

	currentIndex := -1
	for i, eval := range m.evaluations {
		if eval.ID == m.selectedEvaluation {
			currentIndex = i
			break
		}
	}

	nextIndex := (currentIndex + 1) % len(m.evaluations)
	m.selectedEvaluation = m.evaluations[nextIndex].ID

	return nil
}

func (m *Model) selectPreviousEvaluation() tea.Cmd {
	if len(m.evaluations) == 0 {
		return nil
	}

	currentIndex := -1
	for i, eval := range m.evaluations {
		if eval.ID == m.selectedEvaluation {
			currentIndex = i
			break
		}
	}

	prevIndex := (currentIndex - 1 + len(m.evaluations)) % len(m.evaluations)
	m.selectedEvaluation = m.evaluations[prevIndex].ID

	return nil
}

func (m *Model) selectNextScenario() tea.Cmd {
	if len(m.scenarios) == 0 {
		return nil
	}

	currentIndex := -1
	for i, scenario := range m.scenarios {
		if scenario.ID == m.selectedScenario {
			currentIndex = i
			break
		}
	}

	nextIndex := (currentIndex + 1) % len(m.scenarios)
	m.selectedScenario = m.scenarios[nextIndex].ID

	return nil
}

func (m *Model) selectPreviousScenario() tea.Cmd {
	if len(m.scenarios) == 0 {
		return nil
	}

	currentIndex := -1
	for i, scenario := range m.scenarios {
		if scenario.ID == m.selectedScenario {
			currentIndex = i
			break
		}
	}

	prevIndex := (currentIndex - 1 + len(m.scenarios)) % len(m.scenarios)
	m.selectedScenario = m.scenarios[prevIndex].ID

	return nil
}

// Utility operations
func (m *Model) refreshCurrentScreen() tea.Cmd {
	return m.loadScreenData()
}

func (m *Model) clearScreen() tea.Cmd {
	// Clear any temporary state
	m.hideModal()
	m.hideError()
	return nil
}

func (m *Model) showModalOfType(modalType string) tea.Cmd {
	switch modalType {
	case "help":
		content := m.commandRegistry.GenerateHelpText(m.getCommandContext())
		m.showModal("help", content)
	case "theme":
		content := "Available themes:\n• dark\n• light\n• auto"
		m.showModal("theme", content)
	case "models":
		content := "Available models:\n• openai/gpt-4o-mini\n• anthropic/claude-3-haiku\n• google/gemini-pro"
		m.showModal("models", content)
	}
	return nil
}

// Message handlers for data loading
func (m *Model) handleDataMessage(msg tea.Msg) tea.Cmd {
	switch msg := msg.(type) {
	case connectionSuccessMsg:
		m.footer.SetStatus("Connected to server")
		return tea.Tick(time.Second*2, func(time.Time) tea.Msg {
			return clearStatusMsg{}
		})

	case connectionErrorMsg:
		m.showErrorMessage("Failed to connect to server: " + msg.err.Error())

	case evaluationsLoadedMsg:
		m.evaluations = msg.evaluations
		if len(m.evaluations) > 0 && m.selectedEvaluation == "" {
			m.selectedEvaluation = m.evaluations[0].ID
		}

	case evaluationDetailLoadedMsg:
		// Update the evaluation in our cache
		for i, eval := range m.evaluations {
			if eval.ID == msg.evaluation.ID {
				m.evaluations[i] = *msg.evaluation
				break
			}
		}

	case scenariosLoadedMsg:
		m.scenarios = msg.scenarios
		if len(m.scenarios) > 0 && m.selectedScenario == "" {
			m.selectedScenario = m.scenarios[0].ID
		}

	case interviewSessionStartedMsg:
		m.interviewSessionID = msg.sessionID
		// Subscribe to interview updates
		return func() tea.Msg {
			err := m.wsClient.SubscribeToInterview(msg.sessionID)
			if err != nil {
				return dataLoadErrorMsg{err}
			}
			return nil
		}

	case dataLoadErrorMsg:
		m.showErrorMessage("Data loading error: " + msg.err.Error())
	}

	return nil
}

// Message types for data operations
type (
	connectionSuccessMsg       struct{}
	connectionErrorMsg         struct{ err error }
	dataLoadErrorMsg           struct{ err error }
	evaluationsLoadedMsg       struct{ evaluations []api.Evaluation }
	evaluationDetailLoadedMsg  struct{ evaluation *api.Evaluation }
	scenariosLoadedMsg         struct{ scenarios []api.Scenario }
	interviewSessionStartedMsg struct {
		sessionID string
		agentURL  string
	}
)
