package tui

import (
	"fmt"
	"log"
	"os"

	tea "github.com/charmbracelet/bubbletea/v2"

	"github.com/rogue/tui/internal/components"
	"github.com/rogue/tui/internal/screens/config"
	"github.com/rogue/tui/internal/screens/dashboard"
	"github.com/rogue/tui/internal/screens/help"
	"github.com/rogue/tui/internal/screens/interview"
	"github.com/rogue/tui/internal/screens/report"
	"github.com/rogue/tui/internal/screens/scenarios"
	"github.com/rogue/tui/internal/shared"
	"github.com/rogue/tui/internal/theme"
)

// NewApp creates a new TUI application
func NewApp() *App {
	// Set up debug logging to file
	logFile, err := os.OpenFile("/tmp/rogue-debug.log", os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
	if err != nil {
		fmt.Printf("Warning: Failed to create log file: %v\n", err)
	} else {
		log.SetOutput(logFile)
		log.SetFlags(log.Ldate | log.Ltime | log.Lmicroseconds)
		log.Println("==== Rogue TUI Debug Log Started ====")
	}

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
		version:        shared.Version,
		commandInput:   components.NewCommandInput(),
		scenarioEditor: scenarios.NewScenarioEditor(),

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
	if err := config.Load(&model.config); err != nil {
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

	case scenarios.StartInterviewMsg:
		return m.handleStartInterviewMsg(msg)

	case scenarios.SendInterviewMessageMsg:
		return m.handleSendInterviewMessageMsg(msg)

	case scenarios.InterviewStartedMsg:
		return m.handleInterviewStartedMsg(msg)

	case scenarios.InterviewResponseMsg:
		return m.handleInterviewResponseMsg(msg)

	case scenarios.GenerateScenariosMsg:
		return m.handleGenerateScenariosMsg(msg)

	case scenarios.ScenariosGeneratedMsg:
		return m.handleScenariosGeneratedMsg(msg)

	case scenarios.ScenarioEditorMsg:
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
		screen = dashboard.Render(m.width, m.height, m.version, &m.commandInput, t)
	case NewEvaluationScreen:
		screen = m.RenderNewEvaluation()
	case EvaluationDetailScreen:
		screen = m.RenderEvaluationDetail()
	case ReportScreen:
		var evalState *report.EvalState
		if m.evalState != nil {
			evalState = &report.EvalState{
				Summary:   m.evalState.Summary,
				Completed: m.evalState.Completed,
			}
		}
		screen = report.Render(m.width, m.height, evalState, m.reportHistory, m.getMarkdownRenderer())
	case InterviewScreen:
		screen = interview.Render(m.width, m.height)
	case ConfigurationScreen:
		screen = config.Render(m.width, m.height, &m.config, m.configState)
	case ScenariosScreen:
		screen = m.scenarioEditor.View()
	case HelpScreen:
		screen = help.Render(m.width, m.height, &m.helpViewport)
	default:
		screen = dashboard.Render(m.width, m.height, m.version, &m.commandInput, t)
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
