package tui

import (
	"fmt"

	tea "github.com/charmbracelet/bubbletea/v2"

	"github.com/rogue/tui/internal/components"
	"github.com/rogue/tui/internal/theme"
)

// NewApp creates a new TUI application
func NewApp() *App {
	// Load themes before starting the app
	if err := theme.LoadThemesFromJSON(); err != nil {
		fmt.Printf("Warning: Failed to load themes: %v\n", err)
		// Create a fallback theme if loading fails
		theme.RegisterTheme("default", theme.NewSystemTheme(nil, true))
		theme.SetTheme("aura")
	}

	return &App{}
}

// Run starts the TUI application
func (a *App) Run() error {
	model := Model{
		currentScreen: DashboardScreen,
		evaluations:   []Evaluation{},
		scenarios:     []Scenario{},
		config: Config{
			ServerURL: "http://localhost:8000",
			Theme:     "aura",
			APIKeys:   make(map[string]string),
		},
		version:        Version,
		commandInput:   components.NewCommandInput(),
		scenarioEditor: components.NewScenarioEditor(),

		// Initialize spinners
		healthSpinner:  components.NewSpinner(1),
		summarySpinner: components.NewSpinner(2),
		evalSpinner:    components.NewSpinner(3),

		// Initialize viewports and message history
		eventsHistory:   components.NewMessageHistoryView(1, 80, 20, theme.CurrentTheme()),
		summaryHistory:  components.NewMessageHistoryView(2, 80, 20, theme.CurrentTheme()),
		reportHistory:   components.NewMessageHistoryView(3, 80, 15, theme.CurrentTheme()),
		helpViewport:    components.NewViewport(4, 80, 20),
		focusedViewport: 0, // Start with events viewport focused
	}

	// Load existing configuration
	if err := model.loadConfig(); err != nil {
		// If config loading fails, continue with defaults
		fmt.Printf("Warning: Failed to load config: %v\n", err)
	}

	theme.SetTheme(model.config.Theme)

	// Set command input as focused by default
	model.commandInput.SetFocus(true)

	p := tea.NewProgram(model, tea.WithAltScreen(), tea.WithMouseCellMotion())
	a.program = p

	_, err := p.Run()
	return err
}

// Init initializes the model
func (m Model) Init() tea.Cmd {
	// Start all spinners (they'll only animate when active)
	return tea.Batch(
		m.healthSpinner.Start(),
		m.summarySpinner.Start(),
		m.evalSpinner.Start(),
	)
}

// Update handles messages and updates the model
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.PasteMsg:
		return m.handlePasteMsg(msg)

	case components.SpinnerTickMsg:
		return m.handleSpinnerTickMsg(msg)

	case tea.WindowSizeMsg:
		return m.handleWindowSizeMsg(msg)

	case AutoRefreshMsg:
		return m.handleAutoRefreshMsg(msg)

	case HealthCheckResultMsg:
		return m.handleHealthCheckResultMsg(msg)

	case StartEvaluationMsg:
		return m.handleStartEvaluationMsg(msg)

	case SummaryGeneratedMsg:
		return m.handleSummaryGeneratedMsg(msg)

	case components.CommandSelectedMsg:
		return m.handleCommandSelectedMsg(msg)

	case components.DialogOpenMsg:
		return m.handleDialogOpenMsg(msg)

	case components.LLMConfigResultMsg:
		return m.handleLLMConfigResultMsg(msg)

	case components.LLMDialogClosedMsg:
		return m.handleLLMDialogClosedMsg(msg)

	case components.DialogClosedMsg:
		return m.handleDialogClosedMsg(msg)

	case components.StartInterviewMsg:
		return m.handleStartInterviewMsg(msg)

	case components.SendInterviewMessageMsg:
		return m.handleSendInterviewMessageMsg(msg)

	case components.InterviewStartedMsg:
		return m.handleInterviewStartedMsg(msg)

	case components.InterviewResponseMsg:
		return m.handleInterviewResponseMsg(msg)

	case components.GenerateScenariosMsg:
		return m.handleGenerateScenariosMsg(msg)

	case components.ScenariosGeneratedMsg:
		return m.handleScenariosGeneratedMsg(msg)

	case components.ScenarioEditorMsg:
		return m.handleScenarioEditorMsg(msg)

	case tea.KeyMsg:
		return m.handleKeyMsg(msg)
	}

	return m, nil
}

// View renders the current screen
func (m Model) View() string {
	t := theme.CurrentTheme()
	var screen string
	switch m.currentScreen {
	case DashboardScreen:
		screen = m.RenderMainScreen(t)
	case NewEvaluationScreen:
		screen = m.renderNewEvaluation()
	case EvaluationDetailScreen:
		screen = m.renderEvaluationDetail()
	case ReportScreen:
		screen = m.renderReport()
	case InterviewScreen:
		screen = m.RenderInterview()
	case ConfigurationScreen:
		screen = m.RenderConfiguration()
	case ScenariosScreen:
		screen = m.renderScenarios()
	case HelpScreen:
		screen = m.RenderHelp()
	default:
		screen = m.RenderMainScreen(t)
	}

	mainLayout := m.RenderLayout(t, screen)

	// If LLM dialog is open, render it as an overlay
	if m.llmDialog != nil {
		return m.llmDialog.ViewWithBackdrop(m.width, m.height)
	}

	// If dialog is open, render it as an overlay
	if m.dialog != nil {
		return m.dialog.ViewWithBackdrop(m.width, m.height)
	}

	return mainLayout
}
