package tui

import (
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/api"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/commands"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/components/common"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/config"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/styles"
)

// Screen represents the different screens in the TUI
type Screen string

const (
	ScreenDashboard   Screen = "dashboard"
	ScreenEvaluations Screen = "evaluations"
	ScreenEvalDetail  Screen = "eval_detail"
	ScreenNewEval     Screen = "new_eval"
	ScreenInterview   Screen = "interview"
	ScreenConfig      Screen = "config"
	ScreenScenarios   Screen = "scenarios"
)

// Model is the main TUI model
type Model struct {
	// Configuration and dependencies
	config          *config.Config
	apiClient       *api.Client
	wsClient        *api.WSClient
	commandRegistry *commands.CommandRegistry
	commandParser   *commands.Parser
	keyMap          *commands.KeyMap
	themeManager    *styles.ThemeManager
	styles          *styles.Styles

	// State
	currentScreen  Screen
	previousScreen Screen
	width          int
	height         int

	// UI Components
	header       *common.Header
	footer       *common.Footer
	commandInput *common.CommandInput
	spinner      *common.Spinner

	// Screen-specific state
	selectedEvaluation string
	selectedScenario   string
	interviewSessionID string

	// Modals and overlays
	modalVisible bool
	modalType    string
	modalContent string

	// Error handling
	lastError error
	showError bool

	// Command input state
	commandMode bool

	// Data cache
	evaluations []api.Evaluation
	scenarios   []api.Scenario

	// Loading states
	loading     bool
	loadingText string
}

// New creates a new TUI model
func New(cfg *config.Config) *Model {
	// Initialize dependencies
	apiClient := api.NewClient(cfg.Server.URL)
	wsClient := api.NewWSClient(cfg.Server.URL)
	commandRegistry := commands.NewCommandRegistry()
	commandParser := commands.NewParser(commandRegistry)
	keyMap := commands.NewKeyMap()
	themeManager := styles.NewThemeManager()

	// Set theme from config
	themeManager.SetTheme(cfg.UI.Theme)
	styles := styles.NewStyles(themeManager)

	// Initialize UI components
	header := common.NewHeader(styles)
	footer := common.NewFooter(styles, keyMap)
	commandInput := common.NewCommandInput(commandParser, styles)
	spinner := common.NewSpinner(styles)

	model := &Model{
		// Configuration and dependencies
		config:          cfg,
		apiClient:       apiClient,
		wsClient:        wsClient,
		commandRegistry: commandRegistry,
		commandParser:   commandParser,
		keyMap:          keyMap,
		themeManager:    themeManager,
		styles:          styles,

		// State
		currentScreen:  ScreenDashboard,
		previousScreen: ScreenDashboard,
		width:          80,
		height:         24,

		// UI Components
		header:       header,
		footer:       footer,
		commandInput: commandInput,
		spinner:      spinner,

		// Initialize other state
		modalVisible: false,
		showError:    false,
		commandMode:  false,
		loading:      false,
		evaluations:  []api.Evaluation{},
		scenarios:    []api.Scenario{},
	}

	// Set initial context
	model.updateContext()

	return model
}

// Init initializes the TUI model
func (m *Model) Init() tea.Cmd {
	return tea.Batch(
		m.connectToServer(),
		m.loadInitialData(),
	)
}

// Update handles incoming messages
func (m *Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	// Handle window size changes
	if msg, ok := msg.(tea.WindowSizeMsg); ok {
		m.width = msg.Width
		m.height = msg.Height
		m.updateLayout()
	}

	// Update UI components
	var cmd tea.Cmd

	// Update spinner
	spinnerModel, cmd := m.spinner.Update(msg)
	if spinner, ok := spinnerModel.(*common.Spinner); ok {
		m.spinner = spinner
	}
	if cmd != nil {
		cmds = append(cmds, cmd)
	}

	// Update command input if in command mode
	if m.commandMode {
		commandInputModel, cmd := m.commandInput.Update(msg)
		if commandInput, ok := commandInputModel.(*common.CommandInput); ok {
			m.commandInput = commandInput
		}
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
	}

	// Handle key messages
	if keyMsg, ok := msg.(tea.KeyMsg); ok {
		cmd = m.handleKeyMessage(keyMsg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
	}

	// Handle custom messages
	cmd = m.handleCustomMessage(msg)
	if cmd != nil {
		cmds = append(cmds, cmd)
	}

	// Handle data loading messages - forward to update.go
	if cmd := m.handleDataMessage(msg); cmd != nil {
		cmds = append(cmds, cmd)
	}

	return m, tea.Batch(cmds...)
}

// handleKeyMessage handles keyboard input
func (m *Model) handleKeyMessage(msg tea.KeyMsg) tea.Cmd {
	key := msg.String()

	// Global key handling
	switch key {
	case "ctrl+c":
		return tea.Quit

	case "/":
		if !m.commandMode {
			m.enterCommandMode()
			return nil
		}

	case "esc":
		if m.commandMode {
			m.exitCommandMode()
			return nil
		}
		if m.modalVisible {
			m.hideModal()
			return nil
		}
		if m.showError {
			m.hideError()
			return nil
		}
		// Navigate back to previous screen
		return m.navigateBack()
	}

	// If in command mode, let command input handle it
	if m.commandMode {
		return nil
	}

	// Check for keyboard shortcuts
	if cmd := m.keyMap.HandleKey(key, m.getCommandContext()); cmd != nil {
		return cmd
	}

	// Screen-specific key handling
	return m.handleScreenKeyMessage(msg)
}

// handleCustomMessage handles custom Bubble Tea messages
func (m *Model) handleCustomMessage(msg tea.Msg) tea.Cmd {
	switch msg := msg.(type) {
	case common.CommandExecutedMsg:
		return m.executeCommand(msg.Command)

	case commands.ShortcutExecutedMsg:
		return m.handleShortcutAction(msg.Action, msg.Data)

	case api.WSConnectedMsg:
		m.footer.SetStatus("Connected to server")
		return tea.Tick(time.Second*3, func(time.Time) tea.Msg {
			return clearStatusMsg{}
		})

	case api.WSDisconnectedMsg:
		m.footer.SetStatus("Disconnected from server")
		return m.connectToServer()

	case api.WSMessageMsg:
		return m.handleWebSocketMessage(api.WSMessage(msg))

	case api.WSErrorMsg:
		m.showErrorMessage("WebSocket error: " + msg.Error())

	case loadDataCompleteMsg:
		m.loading = false
		m.spinner.Stop()

	case clearStatusMsg:
		m.footer.ClearStatus()

	case common.BlurMsg:
		m.exitCommandMode()
	}

	return nil
}

// Screen navigation methods
func (m *Model) navigateToScreen(screen Screen) tea.Cmd {
	m.previousScreen = m.currentScreen
	m.currentScreen = screen
	m.updateContext()

	// Load data for the new screen
	return m.loadScreenData()
}

func (m *Model) navigateBack() tea.Cmd {
	if m.previousScreen != m.currentScreen {
		return m.navigateToScreen(m.previousScreen)
	}
	return m.navigateToScreen(ScreenDashboard)
}

// Command execution
func (m *Model) executeCommand(command string) tea.Cmd {
	m.exitCommandMode()

	result, err := m.commandParser.QuickExecute(command, m.getCommandContext())
	if err != nil {
		m.showErrorMessage("Command error: " + err.Error())
		return nil
	}

	return m.handleCommandResult(result)
}

// Helper methods
func (m *Model) getCommandContext() commands.CommandContext {
	switch m.currentScreen {
	case ScreenDashboard:
		return commands.ContextDashboard
	case ScreenEvaluations:
		return commands.ContextEvaluations
	case ScreenEvalDetail:
		return commands.ContextEvalDetail
	case ScreenNewEval:
		return commands.ContextNewEval
	case ScreenInterview:
		return commands.ContextInterview
	case ScreenConfig:
		return commands.ContextConfig
	case ScreenScenarios:
		return commands.ContextScenarios
	default:
		return commands.ContextGlobal
	}
}

func (m *Model) updateContext() {
	context := m.getCommandContext()
	m.footer.SetContext(context)
	m.commandInput.SetContext(context)
	m.header.SetContext(string(m.currentScreen), map[string]interface{}{
		"eval_id":    m.selectedEvaluation,
		"session_id": m.interviewSessionID,
	})
}

func (m *Model) updateLayout() {
	m.header.SetWidth(m.width)
	m.footer.SetWidth(m.width)
	m.commandInput.SetWidth(m.width - 4)
}

func (m *Model) enterCommandMode() {
	m.commandMode = true
	m.commandInput.Focus()
}

func (m *Model) exitCommandMode() {
	m.commandMode = false
	m.commandInput.Blur()
	m.commandInput.Clear()
}

func (m *Model) showModal(modalType, content string) {
	m.modalVisible = true
	m.modalType = modalType
	m.modalContent = content
}

func (m *Model) hideModal() {
	m.modalVisible = false
	m.modalType = ""
	m.modalContent = ""
}

func (m *Model) showErrorMessage(message string) {
	m.lastError = &TUIError{message}
	m.showError = true
}

func (m *Model) hideError() {
	m.showError = false
	m.lastError = nil
}

// TUIError represents a TUI-specific error
type TUIError struct {
	message string
}

func (e *TUIError) Error() string {
	return e.message
}

// Message types
type (
	loadDataCompleteMsg struct{}
	clearStatusMsg      struct{}
)
