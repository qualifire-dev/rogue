package tui

import (
	"fmt"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/components"
	"github.com/rogue/tui/internal/theme"
)

// Screen represents different screens in the TUI
type Screen int

const (
	DashboardScreen Screen = iota
	EvaluationsScreen
	EvaluationDetailScreen
	NewEvaluationScreen
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
	currentScreen Screen
	width         int
	height        int
	input         string
	cursor        int
	evaluations   []Evaluation
	scenarios     []Scenario
	config        Config
	version       string
	commandInput  components.CommandInput
	dialog        *components.Dialog
	dialogStack   []components.Dialog
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
	ServerURL string            `toml:"server_url"`
	Theme     string            `toml:"theme"`
	APIKeys   map[string]string `toml:"api_keys"`
}

// NewApp creates a new TUI application
func NewApp() *App {
	// Load themes before starting the app
	if err := theme.LoadThemesFromJSON(); err != nil {
		fmt.Printf("Warning: Failed to load themes: %v\n", err)
		// Create a fallback theme if loading fails
		theme.RegisterTheme("default", theme.NewSystemTheme(nil, true))
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
			Theme:     "dark",
			APIKeys:   make(map[string]string),
		},
		version:      "v0.1.0",
		commandInput: components.NewCommandInput(),
	}

	// Set command input as focused by default
	model.commandInput.SetFocus(true)

	p := tea.NewProgram(model, tea.WithAltScreen(), tea.WithMouseCellMotion())
	a.program = p

	_, err := p.Run()
	return err
}

// Init initializes the model
func (m Model) Init() tea.Cmd {
	return nil
}

// Update handles messages and updates the model
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		// Update command input width
		m.commandInput.SetWidth(msg.Width - 8) // Leave some margin
		return m, nil

	case components.CommandSelectedMsg:
		// Handle command selection
		switch msg.Command.Action {
		case "new_evaluation":
			m.currentScreen = NewEvaluationScreen
		case "list_models":
			m.currentScreen = EvaluationsScreen
		case "configuration":
			m.currentScreen = ConfigurationScreen
		case "help":
			m.currentScreen = HelpScreen
		case "dialog_info":
			// Show example info dialog
			dialog := components.NewInfoDialog(
				"Information",
				"This is an example information dialog. It demonstrates how modal dialogs can overlay existing content using lipgloss v2.",
			)
			m.dialog = &dialog
			return m, nil
		case "dialog_input":
			// Show example input dialog
			dialog := components.NewInputDialog(
				"Input Required",
				"Please enter your name:",
				"",
			)
			m.dialog = &dialog
			return m, nil
		case "dialog_error":
			// Show example error dialog
			dialog := components.ShowErrorDialog(
				"Error",
				"This is an example error dialog with a danger-styled button.",
			)
			m.dialog = &dialog
			return m, nil
		case "dialog_about":
			// Show about dialog
			dialog := components.ShowAboutDialog(
				"Rogue TUI",
				m.version,
				"A terminal user interface for the Rogue agent evaluation system. Built with Bubble Tea and Lipgloss v2.",
			)
			m.dialog = &dialog
			return m, nil
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

	case components.DialogClosedMsg:
		// Handle dialog closure
		if m.dialog != nil {
			switch msg.Action {
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
				}
			case "cancel":
				// Handle cancel action
			}
			m.dialog = nil
		}
		return m, nil

	case tea.KeyMsg:
		// Handle dialog input first if dialog is open
		if m.dialog != nil {
			*m.dialog, cmd = m.dialog.Update(msg)
			if cmd != nil {
				cmds = append(cmds, cmd)
			}
			return m, tea.Batch(cmds...)
		}

		// Let the command input handle its own key events first
		if m.commandInput.IsFocused() {
			m.commandInput, cmd = m.commandInput.Update(msg)
			if cmd != nil {
				cmds = append(cmds, cmd)
			}
			return m, tea.Batch(cmds...)
		} else {
			// Handle other key events when command input is not focused
			switch msg.String() {
			case "ctrl+c", "q":
				return m, tea.Quit

			case "/":
				// Focus the command input and start with "/"
				m.commandInput.SetFocus(true)
				m.commandInput.SetValue("/")
				return m, nil

			case "ctrl+h", "?":
				m.currentScreen = HelpScreen
				return m, nil

			case "ctrl+n":
				m.currentScreen = NewEvaluationScreen
				return m, nil

			case "ctrl+i":
				m.currentScreen = InterviewScreen
				return m, nil

			case "ctrl+s":
				m.currentScreen = ConfigurationScreen
				return m, nil

			case "ctrl+d":
				// Show example info dialog
				dialog := components.NewInfoDialog(
					"Dialog Demo",
					"This dialog was opened with Ctrl+D. You can navigate with Tab/Shift+Tab and close with Escape or Enter.",
				)
				m.dialog = &dialog
				return m, nil

			case "esc":
				m.currentScreen = DashboardScreen
				m.commandInput.SetFocus(true) // Keep focused when returning to dashboard
				m.commandInput.SetValue("")
				return m, nil

			case "enter":
				// Handle enter key based on current screen
				if m.currentScreen == DashboardScreen {
					// Focus the command input on enter
					m.commandInput.SetFocus(true)
				}
				return m, nil
			}
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
		screen = m.renderEvaluations()
	case EvaluationDetailScreen:
		screen = m.RenderChat()
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

	// If dialog is open, render it as an overlay
	if m.dialog != nil {
		return m.dialog.ViewWithBackdrop(m.width, m.height)
	}

	return mainLayout
}

// renderEvaluations renders the evaluations list
func (m Model) renderEvaluations() string {
	style := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("62")).
		Padding(1, 2).
		Width(m.width - 4).
		Height(m.height - 4)

	title := lipgloss.NewStyle().
		Foreground(lipgloss.Color("205")).
		Bold(true).
		Render("📊 Evaluations")

	content := fmt.Sprintf(`%s

No evaluations found.

Press Ctrl+N to create a new evaluation.
Press Esc to return to dashboard.
`, title)

	return style.Render(content)
}

// getKeyStatus returns the status of an API key
func getKeyStatus(key string) string {
	if key == "" {
		return "Not set"
	}
	return "Set"
}
