package tui

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/v2/table"
	tea "github.com/charmbracelet/bubbletea/v2"

	"github.com/pelletier/go-toml/v2"
	"github.com/rogue/tui/internal/components"
	"github.com/rogue/tui/internal/theme"
)

// AutoRefreshMsg is sent periodically to refresh the evaluation screen
type AutoRefreshMsg struct{}

// HealthCheckResultMsg contains the result of a health check
type HealthCheckResultMsg struct {
	Status string
	Err    error
}

// StartEvaluationMsg signals to start the evaluation
type StartEvaluationMsg struct{}

// SummaryGeneratedMsg contains the result of summary generation
type SummaryGeneratedMsg struct {
	Summary string
	Err     error
}

// autoRefreshCmd creates a command that sends AutoRefreshMsg after a delay
func autoRefreshCmd() tea.Cmd {
	return tea.Tick(500*time.Millisecond, func(time.Time) tea.Msg {
		return AutoRefreshMsg{}
	})
}

// healthCheckCmd performs a health check in the background
func (m *Model) healthCheckCmd() tea.Cmd {
	return tea.Cmd(func() tea.Msg {
		status, err := m.CheckServerHealth(context.Background(), m.config.ServerURL)
		return HealthCheckResultMsg{
			Status: status,
			Err:    err,
		}
	})
}

// startEvaluationCmd delays then starts the evaluation
func startEvaluationCmd() tea.Cmd {
	return tea.Tick(800*time.Millisecond, func(time.Time) tea.Msg {
		return StartEvaluationMsg{}
	})
}

// summaryGenerationCmd performs summary generation in the background
func (m *Model) summaryGenerationCmd() tea.Cmd {
	return tea.Cmd(func() tea.Msg {
		if m.evalState == nil || m.evalState.JobID == "" {
			return SummaryGeneratedMsg{
				Summary: "",
				Err:     fmt.Errorf("no evaluation job available"),
			}
		}

		sdk := NewRogueSDK(m.config.ServerURL)

		// Use the judge model and API key from config
		judgeModel := m.evalState.JudgeModel
		var apiKey string

		// Extract provider from judge model (e.g. "openai/gpt-4" -> "openai")
		if parts := strings.Split(judgeModel, "/"); len(parts) >= 2 {
			provider := parts[0]
			if key, ok := m.config.APIKeys[provider]; ok {
				apiKey = key
			}
		}

		// Create a context with longer timeout for summary generation
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
		defer cancel()
		parsedAPIKey := &m.config.QualifireAPIKey
		if m.config.QualifireEnabled == false {
			parsedAPIKey = nil
		}
		structuredSummary, err := sdk.GenerateSummary(
			ctx,
			m.evalState.JobID,
			judgeModel,
			apiKey,
			parsedAPIKey,
			m.evalState.DeepTest,
			judgeModel,
		)

		if err != nil {
			return SummaryGeneratedMsg{
				Summary: "",
				Err:     err,
			}
		}

		m.evalState.StructuredSummary = structuredSummary.Summary

		overallSummary := structuredSummary.Summary.OverallSummary
		keyFindings := structuredSummary.Summary.KeyFindings
		parsedKeyFindings := ""
		for _, finding := range keyFindings {
			parsedKeyFindings += "- " + finding + "\n"
		}
		recommendations := structuredSummary.Summary.Recommendations
		parsedRecommendations := ""
		for _, recommendation := range recommendations {
			parsedRecommendations += "- " + recommendation + "\n"
		}

		detailedBreakdown := structuredSummary.Summary.DetailedBreakdown
		parsedDetailedBreakdown := ""
		for _, breakdown := range detailedBreakdown {
			parsedDetailedBreakdown += "- " + breakdown.Scenario + " - " + breakdown.Status + " - " + breakdown.Outcome + "\n"
		}

		summary := "## Overall Summary\n\n" + overallSummary +
			"\n\n" + "## Key Findings\n\n" + parsedKeyFindings +
			"\n\n" + "## Recommendations\n\n" + parsedRecommendations +
			"\n\n" + "## Detailed Breakdown\n\n" + parsedDetailedBreakdown

		return SummaryGeneratedMsg{
			Summary: summary,
			Err:     err,
		}
	})
}

// clampToInt parses a string of digits appended to an int and returns a safe int (falls back on 0 on error)
func clampToInt(s string) int {
	var n int
	_, err := fmt.Sscanf(s, "%d", &n)
	if err != nil {
		return 0
	}
	if n < 0 {
		n = 0
	}
	if n > 9999 {
		n = 9999
	}
	return n
}

// Screen represents different screens in the TUI
type Screen int

const (
	DashboardScreen Screen = iota
	EvaluationsScreen
	EvaluationDetailScreen
	NewEvaluationScreen
	ReportScreen
	InterviewScreen
	ConfigurationScreen
	ScenariosScreen
	HelpScreen
)

// App represents the main TUI application
type App struct {
	program *tea.Program
}

// Model represents the main application state
type Model struct {
	currentScreen     Screen
	width             int
	height            int
	input             string
	cursor            int
	evaluations       []Evaluation
	scenarios         []Scenario
	config            Config
	version           string
	commandInput      components.CommandInput
	dialog            *components.Dialog
	dialogStack       []components.Dialog
	llmDialog         *components.LLMConfigDialog
	scenarioEditor    components.ScenarioEditor
	detailedBreakdown []table.Row

	// Spinners for loading states
	healthSpinner  components.Spinner
	summarySpinner components.Spinner
	evalSpinner    components.Spinner

	// Viewports for scrollable content
	eventsViewport   components.Viewport
	summaryViewport  components.Viewport
	reportViewport   components.Viewport
	focusedViewport  int  // 0 = events, 1 = summary
	eventsAutoScroll bool // Track if events should auto-scroll to bottom

	// /eval state
	evalState *EvaluationViewState

	// Configuration state
	configState *ConfigState
}

// Evaluation represents an evaluation
type Evaluation struct {
	ID     string
	Status string
	Agent  string
}

// Scenario represents a test scenario
type Scenario struct {
	ID          string
	Name        string
	Description string
}

// Config represents application configuration
type Config struct {
	ServerURL               string            `toml:"server_url"`
	Theme                   string            `toml:"theme"`
	APIKeys                 map[string]string `toml:"api_keys"`
	SelectedModel           string            `toml:"selected_model"`
	SelectedProvider        string            `toml:"selected_provider"`
	QualifireAPIKey         string            `toml:"qualifire_api_key"`
	QualifireEnabled        bool              `toml:"qualifire_enabled"`
	DontShowQualifirePrompt bool              `toml:"dont_show_qualifire_prompt"`
}

// ConfigState represents the configuration screen state
type ConfigState struct {
	ActiveField      ConfigField
	ServerURL        string
	CursorPos        int
	ThemeIndex       int
	IsEditing        bool
	HasChanges       bool
	QualifireEnabled bool
}

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
		version:        "v0.1.6",
		commandInput:   components.NewCommandInput(),
		scenarioEditor: components.NewScenarioEditor(),

		// Initialize spinners
		healthSpinner:  components.NewSpinner(1),
		summarySpinner: components.NewSpinner(2),
		evalSpinner:    components.NewSpinner(3),

		// Initialize viewports
		eventsViewport:   components.NewViewport(1, 80, 20),
		summaryViewport:  components.NewViewport(2, 80, 20),
		reportViewport:   components.NewViewport(3, 80, 15),
		focusedViewport:  0,    // Start with events viewport focused
		eventsAutoScroll: true, // Start with auto-scroll enabled
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
	var cmd tea.Cmd
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.PasteMsg:
		if m.llmDialog != nil {
			*m.llmDialog, cmd = m.llmDialog.Update(msg)
			if cmd != nil {
				cmds = append(cmds, cmd)
			}
			return m, tea.Batch(cmds...)
		}

		if m.dialog != nil {
			clipboardText, err := components.GetClipboardContent()
			if err != nil {
				// If clipboard reading fails, just return without error
				return m, nil
			}

			// Clean the clipboard text (remove newlines and trim whitespace)
			cleanText := strings.TrimSpace(strings.ReplaceAll(clipboardText, "\n", ""))

			if cleanText == "" {
				return m, nil
			}

			m.dialog.Input += cleanText
			m.dialog.InputCursor = len(m.dialog.Input)
			return m, nil
		}
	case components.SpinnerTickMsg:
		// Update spinners
		m.healthSpinner, cmd = m.healthSpinner.Update(msg)
		cmds = append(cmds, cmd)
		m.summarySpinner, cmd = m.summarySpinner.Update(msg)
		cmds = append(cmds, cmd)
		m.evalSpinner, cmd = m.evalSpinner.Update(msg)
		cmds = append(cmds, cmd)
		return m, tea.Batch(cmds...)

	case HealthCheckResultMsg:
		// Stop health spinner and show result
		m.healthSpinner.SetActive(false)
		if msg.Err != nil {
			d := components.ShowErrorDialog("Server Health", fmt.Sprintf("%v", msg.Err))
			m.dialog = &d
		} else {
			d := components.NewInfoDialog("Server Health", fmt.Sprintf("%s", msg.Status))
			m.dialog = &d
		}
		return m, nil

	case StartEvaluationMsg:
		// Actually start the evaluation (keep spinner running during evaluation)
		if m.evalState != nil && !m.evalState.Running {
			ctx := context.Background()
			m.startEval(ctx, m.evalState)
			// move to detail screen
			m.currentScreen = EvaluationDetailScreen
			// Reset viewport focus to events when entering detail screen
			m.focusedViewport = 0
			// Enable auto-scroll for new evaluation
			m.eventsAutoScroll = true
			return m, autoRefreshCmd()
		}
		return m, nil

	case SummaryGeneratedMsg:
		// Stop summary spinner and update summary
		m.summarySpinner.SetActive(false)
		if msg.Err != nil {
			if m.evalState != nil {
				m.evalState.Summary = fmt.Sprintf("# Summary Generation Failed\n\nError: %v", msg.Err)
				// Update report viewport if we're on the report screen
				if m.currentScreen == ReportScreen {
					m.reportViewport.SetContent(m.evalState.Summary)
				}
			}
		} else {
			if m.evalState != nil {
				m.evalState.Summary = msg.Summary
				// Update report viewport if we're on the report screen
				if m.currentScreen == ReportScreen {
					m.reportViewport.SetContent(m.evalState.Summary)
				}
			}
		}
		return m, nil

	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		// Update command input width
		m.commandInput.SetWidth(msg.Width - 8) // Leave some margin
		// Update scenario editor size
		m.scenarioEditor.SetSize(msg.Width, msg.Height)
		// Update viewport sizes
		viewportWidth := msg.Width - 4
		viewportHeight := msg.Height - 8
		m.eventsViewport.SetSize(viewportWidth, viewportHeight)
		m.summaryViewport.SetSize(viewportWidth, viewportHeight)
		m.reportViewport.SetSize(viewportWidth, viewportHeight)
		return m, nil

	case AutoRefreshMsg:
		// Auto-refresh evaluation screen while running
		if m.currentScreen == EvaluationDetailScreen && m.evalState != nil {
			if m.evalState.Running {
				return m, autoRefreshCmd()
			} else if m.evalState.Completed {
				// Stop eval spinner when evaluation completes
				m.evalSpinner.SetActive(false)
				if m.evalState.Summary == "" && !m.evalState.SummaryGenerated && !m.summarySpinner.IsActive() {
					// Trigger summary generation for completed evaluations (only once and if we don't have one yet)
					m.evalState.SummaryGenerated = true // Mark as attempted to prevent multiple generations
					m.triggerSummaryGeneration()
					return m, m.summaryGenerationCmd()
				}
			}
		}
		return m, nil

	case components.CommandSelectedMsg:
		// Handle command selection
		switch msg.Command.Action {
		case "new_evaluation":
			m.currentScreen = NewEvaluationScreen
			// initialize eval state with values from config
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
			}
		case "configure_models":
			// Open LLM configuration dialog
			llmDialog := components.NewLLMConfigDialog(m.config.APIKeys, m.config.SelectedProvider, m.config.SelectedModel)
			m.llmDialog = &llmDialog
			return m, nil
		case "open_editor":
			m.currentScreen = ScenariosScreen
		case "configuration":
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
		case "help":
			m.currentScreen = HelpScreen
		case "quit":
			// Show confirmation dialog before quitting
			dialog := components.NewConfirmationDialog(
				"Quit Application",
				"Are you sure you want to quit?",
			)
			m.dialog = &dialog
			return m, nil
			// Add more cases as needed
		}
		return m, nil

	case components.DialogOpenMsg:
		// Open a new dialog
		m.dialog = &msg.Dialog
		return m, nil

	case components.LLMConfigResultMsg:
		// Handle LLM configuration result
		if m.llmDialog != nil {
			switch msg.Action {
			case "configure":
				// Save the API key and selected model to config
				if m.config.APIKeys == nil {
					m.config.APIKeys = make(map[string]string)
				}
				m.config.APIKeys[msg.Provider] = msg.APIKey
				m.config.SelectedProvider = msg.Provider
				m.config.SelectedModel = msg.Model

				// If we're on the evaluation screen, update the judge model
				if m.currentScreen == NewEvaluationScreen && m.evalState != nil {
					m.evalState.JudgeModel = msg.Provider + "/" + msg.Model
				}

				// Save config to file
				err := m.saveConfig()
				if err != nil {
					// Show error dialog
					dialog := components.ShowErrorDialog(
						"Configuration Error",
						fmt.Sprintf("Failed to save configuration: %v", err),
					)
					m.dialog = &dialog
				} else {
					// Show success dialog
					dialog := components.NewInfoDialog(
						"Configuration Saved",
						fmt.Sprintf("Successfully configured %s with model %s", msg.Provider, msg.Model),
					)
					m.dialog = &dialog
				}
				m.llmDialog = nil
				return m, nil
			}
		}
		return m, nil
	case components.LLMDialogClosedMsg:
		// Handle LLM dialog closure with specific message
		if m.llmDialog != nil {
			m.llmDialog = nil
		}
		return m, nil

	case components.DialogClosedMsg:
		// Handle dialog closure
		if m.dialog != nil {
			switch msg.Action {
			case "save_qualifire_and_report":
				// Handle Qualifire API key save and report persistence
				if m.dialog != nil && m.dialog.Title == "Configure Qualifire API Key" {
					// Save the API key to config (allow empty to clear the key)
					m.config.QualifireAPIKey = msg.Input
					// Only enable integration if there's an API key
					if msg.Input != "" {
						m.config.QualifireEnabled = true
						if m.configState != nil {
							m.configState.QualifireEnabled = true
							m.configState.HasChanges = true
						}
					}

					// immediately report the summary
					if m.evalState != nil && m.evalState.Completed {
						parsedAPIKey := m.config.QualifireAPIKey
						if m.config.QualifireEnabled == false {
							parsedAPIKey = ""
						}

						sdk := NewRogueSDK(m.config.ServerURL)
						err := sdk.ReportSummary(
							context.Background(),
							m.evalState.JobID,
							m.evalState.StructuredSummary,
							m.evalState.DeepTest,
							m.evalState.JudgeModel,
							parsedAPIKey,
						)
						if err != nil {
							// Show error dialog
							errorDialog := components.ShowErrorDialog(
								"Report Summary Error",
								fmt.Sprintf("Failed to report summary: %v", err),
							)
							m.dialog = &errorDialog
						}

						err = m.saveConfig()
						if err != nil {
							// Show error dialog
							errorDialog := components.ShowErrorDialog(
								"Configuration Error",
								fmt.Sprintf("Failed to save Qualifire configuration: %v", err),
							)
							m.dialog = &errorDialog
							return m, nil
						} else {
							// Show appropriate success dialog
							var message string
							if msg.Input != "" {
								message = "Qualifire API key has been successfully saved and integration is now enabled. Your evaluation report will now be automatically persisted."
							} else {
								message = "Qualifire API key has been cleared and integration is now disabled."
							}
							successDialog := components.NewInfoDialog(
								"Qualifire Configured",
								message,
							)
							m.dialog = &successDialog
							return m, nil
						}
					}
				}
			case "save_qualifire":
				// Handle Qualifire API key save
				if m.dialog != nil && m.dialog.Title == "Configure Qualifire API Key" {
					// Save the API key to config (allow empty to clear the key)
					m.config.QualifireAPIKey = msg.Input
					// Only enable integration if there's an API key
					if msg.Input != "" {
						m.config.QualifireEnabled = true
						if m.configState != nil {
							m.configState.QualifireEnabled = true
							m.configState.HasChanges = true
						}
					} else {
						// If API key is cleared, disable integration
						m.config.QualifireEnabled = false
						if m.configState != nil {
							m.configState.QualifireEnabled = false
							m.configState.HasChanges = true
						}
					}

					// Save config to file
					err := m.saveConfig()
					if err != nil {
						// Show error dialog
						errorDialog := components.ShowErrorDialog(
							"Configuration Error",
							fmt.Sprintf("Failed to save Qualifire configuration: %v", err),
						)
						m.dialog = &errorDialog
						return m, nil
					} else {
						// Show appropriate success dialog
						var message string
						if msg.Input != "" {
							message = "Qualifire API key has been successfully saved and integration is now enabled. Your evaluation report will now be automatically persisted."
						} else {
							message = "Qualifire API key has been cleared and integration is now disabled."
						}
						successDialog := components.NewInfoDialog(
							"Qualifire Configured",
							message,
						)
						m.dialog = &successDialog
						return m, nil
					}
				}
			case "configure_qualifire":
				// Handle "Configure Qualifire" from report persistence dialog
				if m.dialog != nil && m.dialog.Title == "Preserve Evaluation Report" {
					// Close current dialog and open Qualifire API key dialog
					dialog := components.NewInputDialog(
						"Configure Qualifire API Key",
						"Enter your Qualifire API key to enable integration:",
						m.config.QualifireAPIKey,
					)
					// Customize the buttons for this specific use case
					dialog.Buttons = []components.DialogButton{
						{Label: "Save", Action: "save_qualifire_and_report", Style: components.PrimaryButton},
					}
					// Position cursor at end of existing key if there is one
					dialog.InputCursor = len(m.config.QualifireAPIKey)
					dialog.SelectedBtn = 0
					m.dialog = &dialog
					return m, nil
				}
			case "dont_show_again":
				// Handle "Don't Show Again" from report persistence dialog
				if m.dialog != nil && m.dialog.Title == "Preserve Evaluation Report" {
					// Save the preference and exit to dashboard
					m.config.DontShowQualifirePrompt = true
					m.saveConfig()
					m.dialog = nil
					m.currentScreen = DashboardScreen
					m.commandInput.SetFocus(true)
					m.commandInput.SetValue("")
					return m, nil
				}
			case "ok":
				// Handle OK action based on dialog context
				if m.dialog.Title == "Quit Application" {
					return m, tea.Quit
				} else if m.dialog.Title == "Input Required" && msg.Input != "" {
					// Show a confirmation with the entered input
					dialog := components.NewInfoDialog(
						"Input Received",
						"Hello, "+msg.Input+"! Your input was successfully captured.",
					)
					m.dialog = &dialog
					return m, nil
				} else if m.dialog.Title == "Search Scenarios" {
					// Apply search query to scenario editor
					m.scenarioEditor.SetSearchQuery(msg.Input)
					m.dialog = nil
					return m, nil
				} else if m.dialog.Title == "Confirm Delete" {
					// If OK was pressed and the button was labeled Delete (handled below), fall through
					return m, nil
				}
			case "delete":
				if m.dialog.Title == "Confirm Delete" {
					m.scenarioEditor.ConfirmDelete()
					m.dialog = nil
					return m, nil
				}
			case "cancel":
				// Handle cancel action
				if m.dialog != nil && m.dialog.Title == "Preserve Evaluation Report" {
					// Close dialog and return to main screen
					m.dialog = nil
					m.currentScreen = DashboardScreen
					m.commandInput.SetFocus(true)
					m.commandInput.SetValue("")
					return m, nil
				}
				// Close LLM dialog if it was cancelled
				if m.llmDialog != nil {
					m.llmDialog = nil
				}
				// No further action for other dialogs
			}
			m.dialog = nil
		}

		// Handle LLM dialog closure - this should close the LLM dialog
		if m.llmDialog != nil {
			m.llmDialog = nil
		}

		return m, nil

	case components.ScenarioEditorMsg:
		// Handle scenario editor messages
		switch msg.Action {
		case "saved":
			// Show success message
			dialog := components.NewInfoDialog(
				"Scenarios Saved",
				"Scenarios have been successfully saved to scenarios.json",
			)
			m.dialog = &dialog
		case "exit":
			// Exit scenarios screen back to dashboard
			m.currentScreen = DashboardScreen
			m.commandInput.SetFocus(true)
			m.commandInput.SetValue("")
		}
		return m, nil

	case tea.KeyMsg:
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
			m.currentScreen = NewEvaluationScreen
			return m, nil

		case "ctrl+l":
			// Open LLM configuration dialog
			llmDialog := components.NewLLMConfigDialog(m.config.APIKeys, m.config.SelectedProvider, m.config.SelectedModel)
			m.llmDialog = &llmDialog
			return m, nil

		case "ctrl+e":
			m.currentScreen = ScenariosScreen
			return m, nil

		case "ctrl+g":
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

		case "ctrl+h", "?":
			m.currentScreen = HelpScreen
			return m, nil

		case "ctrl+i":
			m.currentScreen = InterviewScreen
			return m, nil

		case "/":
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

		case "esc":
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
			m.currentScreen = DashboardScreen
			m.commandInput.SetFocus(true) // Keep focused when returning to dashboard
			m.commandInput.SetValue("")
			return m, nil

		case "enter":
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
				if m.configState.IsEditing {
					// Save changes
					m.handleConfigSave()
					return m, nil
				} else {
					// Handle field-specific actions
					if m.configState.ActiveField == ConfigFieldQualifire {
						// Toggle Qualifire integration
						if !m.configState.QualifireEnabled {
							// Show API key input dialog (pre-populate with existing key if available)
							dialog := components.NewInputDialog(
								"Configure Qualifire API Key",
								"Enter your Qualifire API key to enable integration:",
								m.config.QualifireAPIKey,
							)
							// Customize the buttons for this specific use case
							dialog.Buttons = []components.DialogButton{
								{Label: "Save", Action: "save_qualifire", Style: components.PrimaryButton},
							}
							// Position cursor at end of existing key if there is one
							dialog.InputCursor = len(m.config.QualifireAPIKey)
							// Set the selected button to 0 since there's only one button now
							dialog.SelectedBtn = 0
							m.dialog = &dialog
							return m, nil
						} else {
							// Toggle the enabled state (keep API key stored)
							m.configState.QualifireEnabled = !m.configState.QualifireEnabled
							m.config.QualifireEnabled = m.configState.QualifireEnabled
							m.configState.HasChanges = true
							// Save the updated enabled state
							m.saveConfig()
							return m, nil
						}
					} else {
						// Start editing the active field
						m.configState.IsEditing = true
						if m.configState.ActiveField == ConfigFieldServerURL {
							m.configState.CursorPos = len(m.configState.ServerURL)
						}
						return m, nil
					}
				}
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
					return m, startEvaluationCmd()
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

		default:
			// Handle configuration screen input
			if m.currentScreen == ConfigurationScreen && m.configState != nil {
				return m.handleConfigInput(msg)
			}

			// Handle scenario editor input when on scenarios screen
			if m.currentScreen == ScenariosScreen {
				m.scenarioEditor, cmd = m.scenarioEditor.Update(msg)
				if cmd != nil {
					cmds = append(cmds, cmd)
				}
				return m, tea.Batch(cmds...)
			}

			// New evaluation keys
			if m.currentScreen == NewEvaluationScreen && m.evalState != nil {
				switch msg.String() {
				case "t":
					// Start health check spinner and background health check
					m.healthSpinner.SetActive(true)
					return m, m.healthCheckCmd()
				case "up":
					if m.evalState.currentField > 0 {
						m.evalState.currentField--
						m.evalState.cursorPos = 0 // Reset cursor when switching fields
					}
					return m, nil
				case "down":
					if m.evalState.currentField < 3 { // Now includes start button (0-3)
						m.evalState.currentField++
						m.evalState.cursorPos = 0 // Reset cursor when switching fields
					}
					return m, nil
				case "left":
					if m.evalState.currentField <= 1 && m.evalState.cursorPos > 0 { // Text fields 0-2
						m.evalState.cursorPos--
					}
					return m, nil
				case "right":
					if m.evalState.currentField <= 1 { // Text fields 0-1
						// Get current field length to limit cursor
						var fieldLen int
						switch m.evalState.currentField {
						case 0:
							fieldLen = len(m.evalState.AgentURL)
						case 1:
							fieldLen = len(m.evalState.JudgeModel)
						case 2:
							fieldLen = len(fmt.Sprintf("%d", m.evalState.ParallelRuns))
						}
						if m.evalState.cursorPos < fieldLen {
							m.evalState.cursorPos++
						}
					}
					return m, nil
				case "space":
					if m.evalState.currentField == 2 { // DeepTest field is now index 2
						m.evalState.DeepTest = !m.evalState.DeepTest
						return m, nil
					}
				case "tab":
					// Open LLM config dialog when on Judge Model field
					if m.evalState.currentField == 1 { // JudgeModel field
						llmDialog := components.NewLLMConfigDialog(m.config.APIKeys, m.config.SelectedProvider, m.config.SelectedModel)
						m.llmDialog = &llmDialog
						return m, nil
					}
				case "backspace":
					// Handle backspace for text fields
					if m.evalState.currentField <= 1 && m.evalState.cursorPos > 0 {
						switch m.evalState.currentField {
						case 0: // AgentURL
							runes := []rune(m.evalState.AgentURL)
							if m.evalState.cursorPos <= len(runes) {
								m.evalState.AgentURL = string(runes[:m.evalState.cursorPos-1]) + string(runes[m.evalState.cursorPos:])
								m.evalState.cursorPos--
							}
						case 1: // JudgeModel
							runes := []rune(m.evalState.JudgeModel)
							if m.evalState.cursorPos <= len(runes) {
								m.evalState.JudgeModel = string(runes[:m.evalState.cursorPos-1]) + string(runes[m.evalState.cursorPos:])
								m.evalState.cursorPos--
							}
						case 2: // ParallelRuns (special handling for numbers)
							if m.evalState.ParallelRuns >= 10 {
								m.evalState.ParallelRuns /= 10
								m.evalState.cursorPos--
							} else if m.evalState.ParallelRuns > 0 {
								m.evalState.ParallelRuns = 1 // Don't allow 0
								m.evalState.cursorPos = 0
							}
						}
						return m, nil
					}
				}
				// insert character into text fields
				s := msg.String()
				if len(s) == 1 && m.evalState.currentField <= 2 { // Text fields 0-2
					switch m.evalState.currentField {
					case 0: // AgentURL
						runes := []rune(m.evalState.AgentURL)
						m.evalState.AgentURL = string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
						m.evalState.cursorPos++
					case 1: // JudgeModel
						runes := []rune(m.evalState.JudgeModel)
						m.evalState.JudgeModel = string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
						m.evalState.cursorPos++
					case 2: // ParallelRuns (numeric only)
						if s[0] >= '0' && s[0] <= '9' {
							numStr := fmt.Sprintf("%d", m.evalState.ParallelRuns)
							runes := []rune(numStr)
							newNumStr := string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
							m.evalState.ParallelRuns = clampToInt(newNumStr)
							m.evalState.cursorPos++
						}
					}
					return m, nil
				}
			}
		}

		// Evaluation detail keys
		if m.currentScreen == EvaluationDetailScreen && m.evalState != nil {
			switch msg.String() {
			case "b":
				// Check if we should show the Qualifire persistence dialog
				shouldShowDialog := m.evalState.Completed &&
					m.config.QualifireAPIKey == "" &&
					!m.config.DontShowQualifirePrompt

				if shouldShowDialog {
					// Show report persistence dialog
					dialog := components.NewReportPersistenceDialog()
					m.dialog = &dialog
					return m, nil
				}
				// If no dialog needed, proceed to dashboard
				m.currentScreen = DashboardScreen
				// Reset viewport focus when leaving detail screen
				m.focusedViewport = 0
				return m, nil
			case "s":
				if m.evalState.cancelFn != nil {
					_ = m.evalState.cancelFn()
				}
				return m, nil
			case "r":
				// Navigate to report if evaluation completed
				if m.evalState.Completed {
					m.currentScreen = ReportScreen
					// Update report viewport content when entering report screen
					var reportContent string
					if m.evalState.Summary == "" {
						reportContent = "Generating summary, please wait..."
					} else {
						reportContent = m.evalState.Summary
					}
					m.reportViewport.SetContent(reportContent)
				}
				return m, nil
			case "tab":
				// Switch focus between viewports
				// Only switch if both viewports are visible (evaluation completed with summary)
				if m.evalState.Completed && (m.evalState.Summary != "" || m.summarySpinner.IsActive()) {
					m.focusedViewport = (m.focusedViewport + 1) % 2
				}
				return m, nil
			case "end":
				// Go to bottom and re-enable auto-scroll for events viewport
				if m.focusedViewport == 0 {
					m.eventsViewport.GotoBottom()
					m.eventsAutoScroll = true
				} else if m.focusedViewport == 1 {
					m.summaryViewport.GotoBottom()
				}
				return m, nil
			case "home":
				// Go to top and disable auto-scroll for events viewport
				if m.focusedViewport == 0 {
					m.eventsViewport.GotoTop()
					m.eventsAutoScroll = false
				} else if m.focusedViewport == 1 {
					m.summaryViewport.GotoTop()
				}
				return m, nil
			default:
				// Update only the focused viewport for scrolling
				if m.focusedViewport == 0 {
					// Events viewport is focused - disable auto-scroll when user manually scrolls
					m.eventsAutoScroll = false
					eventsViewportPtr, cmd := m.eventsViewport.Update(msg)
					if cmd != nil {
						cmds = append(cmds, cmd)
					}
					m.eventsViewport = *eventsViewportPtr
				} else if m.focusedViewport == 1 {
					// Summary viewport is focused
					summaryViewportPtr, cmd := m.summaryViewport.Update(msg)
					if cmd != nil {
						cmds = append(cmds, cmd)
					}
					m.summaryViewport = *summaryViewportPtr
				}

				return m, tea.Batch(cmds...)
			}
		}

		// Report screen keys
		if m.currentScreen == ReportScreen && m.evalState != nil {
			switch msg.String() {
			case "b":
				m.currentScreen = DashboardScreen
				return m, nil
			case "r":
				// Regenerate summary if we have job ID (force refresh)
				if m.evalState.JobID != "" && !m.summarySpinner.IsActive() {
					// Allow manual regeneration by resetting the flag
					m.evalState.SummaryGenerated = false
					m.summarySpinner.SetActive(true)
					return m, m.summaryGenerationCmd()
				}
				return m, nil
			case "home":
				// Go to top of report
				m.reportViewport.GotoTop()
				return m, nil
			case "end":
				// Go to bottom of report
				m.reportViewport.GotoBottom()
				return m, nil
			default:
				// Update the report viewport for scrolling
				reportViewportPtr, cmd := m.reportViewport.Update(msg)
				if cmd != nil {
					cmds = append(cmds, cmd)
				}
				m.reportViewport = *reportViewportPtr
				return m, tea.Batch(cmds...)
			}
		}

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

// saveConfig saves the current configuration to file
func (m *Model) saveConfig() error {
	// Get user config directory
	configDir, err := os.UserConfigDir()
	if err != nil {
		return fmt.Errorf("failed to get config directory: %w", err)
	}

	// Create rogue config directory if it doesn't exist
	rogueConfigDir := filepath.Join(configDir, "rogue")
	if err := os.MkdirAll(rogueConfigDir, 0755); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	// Config file path
	configFile := filepath.Join(rogueConfigDir, "config.toml")

	// Marshal config to TOML
	data, err := toml.Marshal(m.config)
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	// Write to file
	if err := os.WriteFile(configFile, data, 0644); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	return nil
}

// loadConfig loads configuration from file
func (m *Model) loadConfig() error {
	// Get user config directory
	configDir, err := os.UserConfigDir()
	if err != nil {
		return fmt.Errorf("failed to get config directory: %w", err)
	}

	// Config file path
	configFile := filepath.Join(configDir, "rogue", "config.toml")

	// Check if config file exists
	if _, err := os.Stat(configFile); os.IsNotExist(err) {
		// Config file doesn't exist, use defaults
		return nil
	}

	// Read config file
	data, err := os.ReadFile(configFile)
	if err != nil {
		return fmt.Errorf("failed to read config file: %w", err)
	}

	// Unmarshal TOML
	if err := toml.Unmarshal(data, &m.config); err != nil {
		return fmt.Errorf("failed to unmarshal config: %w", err)
	}

	return nil
}

// findCurrentThemeIndex returns the index of the current theme in the available themes list
func (m *Model) findCurrentThemeIndex() int {
	currentTheme := theme.CurrentThemeName()
	availableThemes := theme.AvailableThemes()
	for i, themeName := range availableThemes {
		if themeName == currentTheme {
			return i
		}
	}
	return 0 // Default to first theme if not found
}

// handleConfigSave saves configuration changes
func (m *Model) handleConfigSave() {
	if m.configState == nil {
		return
	}

	// Save server URL if it changed
	if m.configState.ActiveField == ConfigFieldServerURL {
		m.config.ServerURL = m.configState.ServerURL
		m.configState.HasChanges = true
	}

	// Save theme if it changed
	if m.configState.ActiveField == ConfigFieldTheme {
		availableThemes := theme.AvailableThemes()
		if m.configState.ThemeIndex >= 0 && m.configState.ThemeIndex < len(availableThemes) {
			selectedTheme := availableThemes[m.configState.ThemeIndex]
			if selectedTheme != theme.CurrentThemeName() {
				m.config.Theme = selectedTheme
				theme.SetTheme(selectedTheme)
				m.configState.HasChanges = true
			}
		}
	}

	// Save Qualifire integration state if it changed
	if m.configState.ActiveField == ConfigFieldQualifire {
		// Update config enabled state to match the UI state
		m.config.QualifireEnabled = m.configState.QualifireEnabled
		m.configState.HasChanges = true
	}

	// Exit editing mode
	m.configState.IsEditing = false

	// Save to file if there were changes
	if m.configState.HasChanges {
		m.saveConfig()
		m.configState.HasChanges = false
	}
}

// handleConfigInput handles keyboard input for the configuration screen
func (m Model) handleConfigInput(msg tea.KeyMsg) (Model, tea.Cmd) {
	if m.configState == nil {
		return m, nil
	}

	switch msg.String() {
	case "up":
		if m.configState.IsEditing && m.configState.ActiveField == ConfigFieldTheme {
			// Navigate theme options
			availableThemes := theme.AvailableThemes()
			if m.configState.ThemeIndex > 0 {
				m.configState.ThemeIndex--
			} else {
				m.configState.ThemeIndex = len(availableThemes) - 1
			}
		} else {
			// Navigate between fields (works both when editing and not editing)
			if m.configState.ActiveField == ConfigFieldTheme {
				// If we were editing theme, exit edit mode
				if m.configState.IsEditing {
					m.configState.IsEditing = false
				}
				m.configState.ActiveField = ConfigFieldQualifire
				// Qualifire field doesn't auto-enter edit mode
			} else if m.configState.ActiveField == ConfigFieldQualifire {
				m.configState.ActiveField = ConfigFieldServerURL
				// Automatically enter edit mode for server URL field
				m.configState.IsEditing = true
				m.configState.CursorPos = len(m.configState.ServerURL)
			}
		}
		return m, nil

	case "down":
		if m.configState.IsEditing && m.configState.ActiveField == ConfigFieldTheme {
			// Navigate theme options
			availableThemes := theme.AvailableThemes()
			if m.configState.ThemeIndex < len(availableThemes)-1 {
				m.configState.ThemeIndex++
			} else {
				m.configState.ThemeIndex = 0
			}
		} else {
			// Navigate between fields (works both when editing and not editing)
			if m.configState.ActiveField == ConfigFieldServerURL {
				// If we were editing server URL, save changes and exit edit mode
				if m.configState.IsEditing {
					m.configState.IsEditing = false
				}
				m.configState.ActiveField = ConfigFieldQualifire
				// Qualifire field doesn't auto-enter edit mode
			} else if m.configState.ActiveField == ConfigFieldQualifire {
				m.configState.ActiveField = ConfigFieldTheme
				// Theme field doesn't auto-enter edit mode - user must press Enter to select themes
			}
		}
		return m, nil

	case "left":
		if m.configState.IsEditing && m.configState.ActiveField == ConfigFieldServerURL {
			if m.configState.CursorPos > 0 {
				m.configState.CursorPos--
			}
		}
		return m, nil

	case "right":
		if m.configState.IsEditing && m.configState.ActiveField == ConfigFieldServerURL {
			if m.configState.CursorPos < len(m.configState.ServerURL) {
				m.configState.CursorPos++
			}
		}
		return m, nil

	case "backspace":
		if m.configState.IsEditing && m.configState.ActiveField == ConfigFieldServerURL {
			if m.configState.CursorPos > 0 && len(m.configState.ServerURL) > 0 {
				m.configState.ServerURL = m.configState.ServerURL[:m.configState.CursorPos-1] +
					m.configState.ServerURL[m.configState.CursorPos:]
				m.configState.CursorPos--
			}
		}
		return m, nil

	case "space", " ":
		// Handle space key for Qualifire toggle
		if m.configState.ActiveField == ConfigFieldQualifire && !m.configState.IsEditing {
			// Toggle Qualifire integration (same logic as Enter key)
			if !m.configState.QualifireEnabled {
				// Show API key input dialog (pre-populate with existing key if available)
				dialog := components.NewInputDialog(
					"Configure Qualifire API Key",
					"Enter your Qualifire API key to enable integration:",
					m.config.QualifireAPIKey,
				)
				// Customize the buttons for this specific use case
				dialog.Buttons = []components.DialogButton{
					{Label: "Save", Action: "save_qualifire", Style: components.PrimaryButton},
				}
				// Position cursor at end of existing key if there is one
				dialog.InputCursor = len(m.config.QualifireAPIKey)
				// Set the selected button to 0 since there's only one button now
				dialog.SelectedBtn = 0
				m.dialog = &dialog
				return m, nil
			} else {
				// Toggle the enabled state (keep API key stored)
				m.configState.QualifireEnabled = !m.configState.QualifireEnabled
				m.config.QualifireEnabled = m.configState.QualifireEnabled
				m.configState.HasChanges = true
				// Save the updated enabled state
				m.saveConfig()
				return m, nil
			}
		}
		// Fall through to default for other cases
		fallthrough

	default:
		// Handle character input for server URL
		if m.configState.IsEditing && m.configState.ActiveField == ConfigFieldServerURL {
			keyStr := msg.String()

			// Special handling for space key since it might have special representation
			if keyStr == " " || keyStr == "space" {
				m.configState.ServerURL = m.configState.ServerURL[:m.configState.CursorPos] +
					" " + m.configState.ServerURL[m.configState.CursorPos:]
				m.configState.CursorPos++
			} else if len(keyStr) == 1 {
				char := keyStr
				m.configState.ServerURL = m.configState.ServerURL[:m.configState.CursorPos] +
					char + m.configState.ServerURL[m.configState.CursorPos:]
				m.configState.CursorPos++
			}
		}
		return m, nil
	}
}
