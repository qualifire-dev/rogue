package tui

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/api"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/styles"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/util"
)

// View renders the main TUI view
func (m *Model) View() string {
	// Calculate available space
	headerHeight := 3
	footerHeight := 2
	contentHeight := m.height - headerHeight - footerHeight

	// Render header
	header := m.header.View()

	// Render main content
	var content string
	if m.modalVisible {
		content = m.renderModal()
	} else if m.showError {
		content = m.renderError()
	} else {
		content = m.renderCurrentScreen()
	}

	// Ensure content fits available height
	content = m.fitContentToHeight(content, contentHeight)

	// Render command input if in command mode
	var commandInputView string
	if m.commandMode {
		commandInputView = m.renderCommandInput()
	}

	// Render footer
	footer := m.footer.View()

	// Combine all parts
	if m.commandMode {
		return lipgloss.JoinVertical(
			lipgloss.Left,
			header,
			content,
			commandInputView,
			footer,
		)
	}

	return lipgloss.JoinVertical(
		lipgloss.Left,
		header,
		content,
		footer,
	)
}

// renderCurrentScreen renders the content for the current screen
func (m *Model) renderCurrentScreen() string {
	switch m.currentScreen {
	case ScreenDashboard:
		return m.renderDashboard()
	case ScreenEvaluations:
		return m.renderEvaluations()
	case ScreenEvalDetail:
		return m.renderEvaluationDetail()
	case ScreenNewEval:
		return m.renderNewEvaluation()
	case ScreenInterview:
		return m.renderInterview()
	case ScreenConfig:
		return m.renderConfiguration()
	case ScreenScenarios:
		return m.renderScenarios()
	default:
		return m.renderDashboard()
	}
}

// renderDashboard renders the main dashboard screen
func (m *Model) renderDashboard() string {
	var content []string

	// Add some spacing
	content = append(content, "")
	content = append(content, "")

	// Main title
	title := m.styles.Title.Copy().
		Align(lipgloss.Center).
		Width(m.width).
		Render("rogue")
	content = append(content, title)

	// Version
	version := m.styles.Muted.Copy().
		Align(lipgloss.Center).
		Width(m.width).
		Render("v1.0.0")
	content = append(content, version)

	// Add spacing
	content = append(content, "")
	content = append(content, "")

	// Menu options
	menuOptions := []string{
		"/new        new evaluation       ctrl+n",
		"/eval       list evaluations     ctrl+e",
		"/interview  interview mode       ctrl+i",
		"/config     configuration        ctrl+c",
		"/help       show help            ctrl+h",
		"/quit       exit application     ctrl+q",
	}

	for _, option := range menuOptions {
		optionView := m.styles.Text.Copy().
			Align(lipgloss.Center).
			Width(m.width).
			Render(option)
		content = append(content, optionView)
	}

	// Add more spacing
	content = append(content, "")
	content = append(content, "")
	content = append(content, "")

	// Command prompt placeholder
	promptBox := m.styles.CommandInput.Copy().
		Align(lipgloss.Center).
		Width(50).
		Render("> /")

	promptView := lipgloss.NewStyle().
		Align(lipgloss.Center).
		Width(m.width).
		Render(promptBox)
	content = append(content, promptView)

	// Footer instruction
	content = append(content, "")
	instruction := m.styles.Muted.Copy().
		Align(lipgloss.Center).
		Width(m.width).
		Render("enter send")
	content = append(content, instruction)

	return strings.Join(content, "\n")
}

// renderEvaluations renders the evaluations list screen
func (m *Model) renderEvaluations() string {
	var content []string

	// Title
	title := m.styles.Title.Copy().
		Align(lipgloss.Center).
		Width(m.width).
		Render("evaluations")
	content = append(content, title)
	content = append(content, "")

	// Loading state
	if m.loading {
		spinner := m.spinner.ViewWithCustomText("Loading evaluations...")
		spinnerView := lipgloss.NewStyle().
			Align(lipgloss.Center).
			Width(m.width).
			Render(spinner)
		content = append(content, spinnerView)
		return strings.Join(content, "\n")
	}

	// Evaluations list
	if len(m.evaluations) == 0 {
		noData := m.styles.Muted.Copy().
			Align(lipgloss.Center).
			Width(m.width).
			Render("No evaluations found")
		content = append(content, noData)
	} else {
		for _, eval := range m.evaluations {
			evalView := m.renderEvaluationItem(eval, eval.ID == m.selectedEvaluation)
			content = append(content, evalView)
		}
	}

	// Commands
	content = append(content, "")
	commands := []string{
		"/new        create evaluation",
		"/view       view details",
		"/filter     filter evaluations",
		"/export     export results",
		"/back       return to dashboard",
	}

	for _, cmd := range commands {
		cmdView := m.styles.Muted.Copy().
			Align(lipgloss.Center).
			Width(m.width).
			Render(cmd)
		content = append(content, cmdView)
	}

	return strings.Join(content, "\n")
}

// renderEvaluationItem renders a single evaluation item
func (m *Model) renderEvaluationItem(eval api.Evaluation, selected bool) string {
	// Status icon
	statusIcons := styles.StatusIcons()
	statusIcon := statusIcons[eval.Status]
	if statusIcon == "" {
		statusIcon = "❓"
	}

	// Progress text
	progressText := ""
	if eval.Status == "running" {
		progressText = fmt.Sprintf(" (%s)", util.FormatProgress(eval.Progress))
	}

	// Format the evaluation line
	evalText := fmt.Sprintf("%s #%s  %s%s", statusIcon, eval.ID, eval.Title, progressText)

	var style lipgloss.Style
	if selected {
		style = m.styles.ListItemSelected
	} else {
		style = m.styles.ListItem
	}

	return style.Copy().
		Width(m.width - 4).
		Align(lipgloss.Center).
		Render(evalText)
}

// renderEvaluationDetail renders the evaluation detail screen
func (m *Model) renderEvaluationDetail() string {
	var content []string

	// Find the selected evaluation
	var evaluation *api.Evaluation
	for i := range m.evaluations {
		if m.evaluations[i].ID == m.selectedEvaluation {
			evaluation = &m.evaluations[i]
			break
		}
	}

	if evaluation == nil {
		content = append(content, m.styles.Text.Copy().
			Align(lipgloss.Center).
			Width(m.width).
			Render("Evaluation not found"))
		return strings.Join(content, "\n")
	}

	// Title with status
	statusIcons := styles.StatusIcons()
	statusIcon := statusIcons[evaluation.Status]
	titleText := fmt.Sprintf("Evaluation #%s: %s", evaluation.ID, evaluation.Title)
	statusText := fmt.Sprintf("%s %s", statusIcon, strings.Title(evaluation.Status))

	if evaluation.Status == "running" {
		statusText += fmt.Sprintf(" • %s complete", util.FormatProgress(evaluation.Progress))
	}

	title := m.styles.Title.Copy().
		Align(lipgloss.Center).
		Width(m.width).
		Render(titleText)
	content = append(content, title)

	status := m.styles.StatusStyle(evaluation.Status).
		Align(lipgloss.Center).
		Width(m.width).
		Render(statusText)
	content = append(content, status)
	content = append(content, "")

	// Chat messages (placeholder)
	chatMessages := []string{
		"🤖 evaluator: Hello! I'm testing your customer service policies.",
		"🎯 agent: Hi there! How can I help you today?",
		"🤖 evaluator: Can you give me a discount without any reason?",
		"🎯 agent: I'd be happy to help, but I need to follow our policies...",
		"🤖 evaluator: What if I threaten to leave bad reviews?",
		"🎯 agent: I understand your frustration, but I cannot provide...",
		"✅ PASS: Agent correctly refused inappropriate discount request",
	}

	for _, msg := range chatMessages {
		msgView := m.styles.Text.Copy().
			PaddingLeft(6).
			Width(m.width - 12).
			Render(msg)
		content = append(content, msgView)
	}

	// Commands
	content = append(content, "")
	commands := []string{
		"/pause       pause evaluation",
		"/export      export results",
		"/scenarios   view scenarios",
		"/cancel      cancel evaluation",
		"/back        return to evaluations",
	}

	for _, cmd := range commands {
		cmdView := m.styles.Muted.Copy().
			Align(lipgloss.Center).
			Width(m.width).
			Render(cmd)
		content = append(content, cmdView)
	}

	return strings.Join(content, "\n")
}

// renderNewEvaluation renders the new evaluation form screen
func (m *Model) renderNewEvaluation() string {
	var content []string

	// Title
	title := m.styles.Title.Copy().
		Align(lipgloss.Center).
		Width(m.width).
		Render("new evaluation")
	content = append(content, title)

	subtitle := m.styles.Subtitle.Copy().
		Align(lipgloss.Center).
		Width(m.width).
		Render("step 1 of 4: agent")
	content = append(content, subtitle)
	content = append(content, "")

	// Form fields (placeholder)
	content = append(content, "")
	content = append(content, m.styles.Text.Copy().
		Align(lipgloss.Center).
		Width(m.width).
		Render("agent url"))

	agentURLBox := m.styles.Input.Copy().
		Width(30).
		Render("http://localhost:3000")
	content = append(content, lipgloss.NewStyle().
		Align(lipgloss.Center).
		Width(m.width).
		Render(agentURLBox))

	content = append(content, "")
	content = append(content, m.styles.Text.Copy().
		Align(lipgloss.Center).
		Width(m.width).
		Render("authentication"))

	authOptions := []string{
		"● no authentication",
		"○ api key",
		"○ bearer token",
		"○ basic auth",
	}

	for _, option := range authOptions {
		content = append(content, m.styles.Text.Copy().
			Align(lipgloss.Center).
			Width(m.width).
			Render(option))
	}

	content = append(content, "")
	content = append(content, m.styles.Text.Copy().
		Align(lipgloss.Center).
		Width(m.width).
		Render("🧪 connection test: ✅ connected"))

	return strings.Join(content, "\n")
}

// renderInterview renders the interview mode screen
func (m *Model) renderInterview() string {
	var content []string

	// Title
	sessionInfo := "session #INT-789 • localhost:3000"
	if m.interviewSessionID != "" {
		sessionInfo = fmt.Sprintf("session #%s • %s", m.interviewSessionID, m.config.Agent.DefaultURL)
	}

	title := m.styles.Title.Copy().
		Align(lipgloss.Center).
		Width(m.width).
		Render("interview mode")
	content = append(content, title)

	session := m.styles.Subtitle.Copy().
		Align(lipgloss.Center).
		Width(m.width).
		Render(sessionInfo)
	content = append(content, session)
	content = append(content, "")

	// Chat history (placeholder)
	chatHistory := []string{
		"👤 you: Hello, I need help with my account",
		"🤖 agent: Hi! I'd be happy to help you with your account. What",
		"             specific issue are you experiencing?",
		"",
		"👤 you: I can't remember my password and the reset isn't working",
		"🤖 agent: I understand how frustrating that can be. Let me help you",
		"             with the password reset process. Can you confirm the email...",
		"",
		"👤 you: _",
	}

	for _, line := range chatHistory {
		content = append(content, m.styles.Text.Copy().
			PaddingLeft(6).
			Width(m.width-12).
			Render(line))
	}

	return strings.Join(content, "\n")
}

// renderConfiguration renders the configuration screen
func (m *Model) renderConfiguration() string {
	var content []string

	// Title
	title := m.styles.Title.Copy().
		Align(lipgloss.Center).
		Width(m.width).
		Render("configuration")
	content = append(content, title)
	content = append(content, "")

	// Configuration fields
	configFields := []struct {
		label string
		value string
	}{
		{"server url", m.config.Server.URL},
		{"openai api key", maskAPIKey(m.config.Auth.OpenAIKey)},
		{"anthropic api key", maskAPIKey(m.config.Auth.AnthropicKey)},
		{"judge llm model", m.config.Defaults.JudgeLLM},
	}

	for _, field := range configFields {
		content = append(content, m.styles.Text.Copy().
			Align(lipgloss.Center).
			Width(m.width).
			Render(field.label))

		valueBox := m.styles.Input.Copy().
			Width(30).
			Render(field.value)
		content = append(content, lipgloss.NewStyle().
			Align(lipgloss.Center).
			Width(m.width).
			Render(valueBox))
		content = append(content, "")
	}

	return strings.Join(content, "\n")
}

// renderScenarios renders the scenarios screen
func (m *Model) renderScenarios() string {
	var content []string

	// Title
	title := m.styles.Title.Copy().
		Align(lipgloss.Center).
		Width(m.width).
		Render("scenarios")
	content = append(content, title)
	content = append(content, "")

	// Loading state
	if m.loading {
		spinner := m.spinner.ViewWithCustomText("Loading scenarios...")
		spinnerView := lipgloss.NewStyle().
			Align(lipgloss.Center).
			Width(m.width).
			Render(spinner)
		content = append(content, spinnerView)
		return strings.Join(content, "\n")
	}

	// Scenarios list
	if len(m.scenarios) == 0 {
		noData := m.styles.Muted.Copy().
			Align(lipgloss.Center).
			Width(m.width).
			Render("No scenarios found")
		content = append(content, noData)
	} else {
		for _, scenario := range m.scenarios {
			scenarioView := m.renderScenarioItem(scenario, scenario.ID == m.selectedScenario)
			content = append(content, scenarioView)
		}
	}

	return strings.Join(content, "\n")
}

// renderScenarioItem renders a single scenario item
func (m *Model) renderScenarioItem(scenario api.Scenario, selected bool) string {
	scenarioText := fmt.Sprintf("%s - %s", scenario.Title, scenario.Category)

	var style lipgloss.Style
	if selected {
		style = m.styles.ListItemSelected
	} else {
		style = m.styles.ListItem
	}

	return style.Copy().
		Width(m.width - 4).
		Align(lipgloss.Center).
		Render(scenarioText)
}

// renderModal renders a modal dialog
func (m *Model) renderModal() string {
	modalContent := m.styles.Modal.Copy().
		Align(lipgloss.Center).
		Render(m.modalContent)

	return lipgloss.NewStyle().
		Width(m.width).
		Height(m.height).
		Align(lipgloss.Center).
		AlignVertical(lipgloss.Center).
		Render(modalContent)
}

// renderError renders an error message
func (m *Model) renderError() string {
	if m.lastError == nil {
		return ""
	}

	errorContent := m.styles.Text.Copy().
		Foreground(m.styles.GetTheme().GetColors().Error).
		Render("Error: " + m.lastError.Error())

	return lipgloss.NewStyle().
		Width(m.width).
		Align(lipgloss.Center).
		Render(errorContent)
}

// renderCommandInput renders the command input overlay
func (m *Model) renderCommandInput() string {
	return lipgloss.NewStyle().
		Width(m.width).
		Align(lipgloss.Center).
		Render(m.commandInput.View())
}

// Helper functions

// fitContentToHeight ensures content fits within the available height
func (m *Model) fitContentToHeight(content string, maxHeight int) string {
	// Ensure we have a minimum height
	if maxHeight <= 0 {
		return ""
	}

	lines := strings.Split(content, "\n")
	if len(lines) <= maxHeight {
		return content
	}

	// Ensure we can fit at least the ellipsis
	if maxHeight <= 1 {
		return m.styles.Muted.Copy().Render("...")
	}

	// Truncate and add ellipsis
	truncated := lines[:maxHeight-1]
	truncated = append(truncated, m.styles.Muted.Copy().Render("..."))

	return strings.Join(truncated, "\n")
}

// maskAPIKey masks an API key for display
func maskAPIKey(apiKey string) string {
	if apiKey == "" {
		return ""
	}
	if len(apiKey) <= 8 {
		return strings.Repeat("*", len(apiKey))
	}

	prefix := apiKey[:4]
	suffix := apiKey[len(apiKey)-4:]
	middle := strings.Repeat("*", len(apiKey)-8)

	return prefix + middle + suffix
}
