package tui

import (
	"fmt"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
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
		version: "v0.1.0",
	}

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
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		return m, nil

	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit

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
			return m, nil

		case "/":
			// Handle slash commands
			return m, nil

		case "enter":
			// Handle enter key based on current screen
			return m, nil
		}
	}

	return m, nil
}

// View renders the current screen
func (m Model) View() string {
	switch m.currentScreen {
	case DashboardScreen:
		return m.RenderMainScreen()
	case NewEvaluationScreen:
		return m.renderEvaluations()
	case EvaluationDetailScreen:
		return m.RenderChat()
	case InterviewScreen:
		return m.RenderInterview()
	case ConfigurationScreen:
		return m.RenderConfiguration()
	case ScenariosScreen:
		return m.renderScenarios()
	case HelpScreen:
		return m.RenderHelp()
	default:
		return m.RenderMainScreen()
	}
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
