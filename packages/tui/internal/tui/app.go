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
		case "quit":
			return m, tea.Quit
			// Add more cases as needed
		}
		return m, nil

	case tea.KeyMsg:
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

			case "esc":
				m.currentScreen = DashboardScreen
				m.commandInput.SetFocus(true)  // Keep focused when returning to dashboard
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
