package components

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// LLMProvider represents an LLM provider
type LLMProvider struct {
	Name        string
	DisplayName string
	APIKeyName  string
	Models      []string
	Configured  bool
}

// LLMConfigStep represents the current step in the configuration process
type LLMConfigStep int

const (
	ProviderSelectionStep LLMConfigStep = iota
	APIKeyInputStep
	ModelSelectionStep
	ConfigurationCompleteStep
)

// LLMConfigDialog represents the LLM configuration dialog
type LLMConfigDialog struct {
	Dialog
	CurrentStep      LLMConfigStep
	Providers        []LLMProvider
	SelectedProvider int
	APIKeyInput      string
	APIKeyCursor     int
	AvailableModels  []string
	SelectedModel    int
	ConfiguredKeys   map[string]string
	Loading          bool
	ErrorMessage     string
}

// LLMConfigResultMsg is sent when LLM configuration is complete
type LLMConfigResultMsg struct {
	Provider string
	APIKey   string
	Model    string
	Action   string
}

// LLMDialogClosedMsg is sent when LLM dialog is closed
type LLMDialogClosedMsg struct {
	Action string
}

// NewLLMConfigDialog creates a new LLM configuration dialog
func NewLLMConfigDialog(configuredKeys map[string]string) LLMConfigDialog {
	providers := []LLMProvider{
		{
			Name:        "openai",
			DisplayName: "OpenAI",
			APIKeyName:  "OPENAI_API_KEY",
			Models:      []string{"gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"},
			Configured:  configuredKeys["openai"] != "",
		},
		{
			Name:        "anthropic",
			DisplayName: "Anthropic",
			APIKeyName:  "ANTHROPIC_API_KEY",
			Models:      []string{"claude-3-opus", "claude-3-sonnet", "claude-3-haiku"},
			Configured:  configuredKeys["anthropic"] != "",
		},
		{
			Name:        "google",
			DisplayName: "Google AI",
			APIKeyName:  "GOOGLE_API_KEY",
			Models:      []string{"gemini-pro", "gemini-pro-vision"},
			Configured:  configuredKeys["google"] != "",
		},
		{
			Name:        "cohere",
			DisplayName: "Cohere",
			APIKeyName:  "COHERE_API_KEY",
			Models:      []string{"command", "command-light", "command-nightly"},
			Configured:  configuredKeys["cohere"] != "",
		},
	}

	return LLMConfigDialog{
		Dialog: Dialog{
			Type:    CustomDialog,
			Title:   "LLM Provider Configuration",
			Width:   80,
			Height:  20,
			Focused: true,
			Buttons: []DialogButton{
				{Label: "Cancel", Action: "cancel", Style: SecondaryButton},
				{Label: "Next", Action: "next", Style: PrimaryButton},
			},
			SelectedBtn: 1,
		},
		CurrentStep:      ProviderSelectionStep,
		Providers:        providers,
		SelectedProvider: 0,
		ConfiguredKeys:   configuredKeys,
		AvailableModels:  []string{},
	}
}

// Update handles LLM config dialog input
func (d LLMConfigDialog) Update(msg tea.Msg) (LLMConfigDialog, tea.Cmd) {
	if !d.Focused {
		return d, nil
	}

	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c":
			return d, tea.Quit

		case "escape":
			return d, func() tea.Msg {
				return LLMDialogClosedMsg{Action: "cancel"}
			}

		case "enter":
			return d.handleEnter()

		case "tab", "right":
			// Navigate buttons for all steps
			if len(d.Buttons) > 1 {
				d.SelectedBtn = (d.SelectedBtn + 1) % len(d.Buttons)
			}
			return d, nil

		case "shift+tab", "left":
			// Navigate buttons for all steps
			if len(d.Buttons) > 1 {
				d.SelectedBtn = (d.SelectedBtn - 1 + len(d.Buttons)) % len(d.Buttons)
			}
			return d, nil

		case "up":
			switch d.CurrentStep {
			case ProviderSelectionStep:
				if d.SelectedProvider > 0 {
					d.SelectedProvider--
				}
			case ModelSelectionStep:
				if d.SelectedModel > 0 {
					d.SelectedModel--
				}
			}
			return d, nil

		case "down":
			switch d.CurrentStep {
			case ProviderSelectionStep:
				if d.SelectedProvider < len(d.Providers)-1 {
					d.SelectedProvider++
				}
			case ModelSelectionStep:
				if d.SelectedModel < len(d.AvailableModels)-1 {
					d.SelectedModel++
				}
			}
			return d, nil

		case "backspace":
			if d.CurrentStep == APIKeyInputStep && d.APIKeyCursor > 0 && len(d.APIKeyInput) > 0 {
				d.APIKeyInput = d.APIKeyInput[:d.APIKeyCursor-1] + d.APIKeyInput[d.APIKeyCursor:]
				d.APIKeyCursor--
			}
			return d, nil

		case "delete":
			if d.CurrentStep == APIKeyInputStep && d.APIKeyCursor < len(d.APIKeyInput) {
				d.APIKeyInput = d.APIKeyInput[:d.APIKeyCursor] + d.APIKeyInput[d.APIKeyCursor+1:]
			}
			return d, nil

		case "ctrl+a":
			if d.CurrentStep == APIKeyInputStep {
				d.APIKeyCursor = 0
			}
			return d, nil

		case "ctrl+e":
			if d.CurrentStep == APIKeyInputStep {
				d.APIKeyCursor = len(d.APIKeyInput)
			}
			return d, nil

		default:
			// Handle regular character input for API key
			if d.CurrentStep == APIKeyInputStep && len(msg.String()) == 1 {
				char := msg.String()
				d.APIKeyInput = d.APIKeyInput[:d.APIKeyCursor] + char + d.APIKeyInput[d.APIKeyCursor:]
				d.APIKeyCursor++
			}
			return d, nil
		}
	}

	return d, nil
}

// handleEnter processes the enter key based on current step
func (d LLMConfigDialog) handleEnter() (LLMConfigDialog, tea.Cmd) {
	switch d.CurrentStep {
	case ProviderSelectionStep:
		if d.SelectedBtn == 0 { // Cancel
			return d, func() tea.Msg {
				return LLMDialogClosedMsg{Action: "cancel"}
			}
		}
		// Move to API key input step
		d.CurrentStep = APIKeyInputStep
		d.Buttons = []DialogButton{
			{Label: "Back", Action: "back", Style: SecondaryButton},
			{Label: "Validate", Action: "validate", Style: PrimaryButton},
		}
		d.SelectedBtn = 1

		// Pre-fill API key if already configured
		provider := d.Providers[d.SelectedProvider]
		if existingKey, exists := d.ConfiguredKeys[provider.Name]; exists {
			d.APIKeyInput = existingKey
			d.APIKeyCursor = len(existingKey)
		}

		return d, nil

	case APIKeyInputStep:
		if d.SelectedBtn == 0 { // Back
			d.CurrentStep = ProviderSelectionStep
			d.Buttons = []DialogButton{
				{Label: "Cancel", Action: "cancel", Style: SecondaryButton},
				{Label: "Next", Action: "next", Style: PrimaryButton},
			}
			d.SelectedBtn = 1
			return d, nil
		}

		// Validate API key and fetch models
		if d.APIKeyInput == "" {
			d.ErrorMessage = "API key cannot be empty"
			return d, nil
		}

		d.Loading = true
		d.ErrorMessage = ""

		// Simulate API key validation and model fetching
		provider := d.Providers[d.SelectedProvider]
		d.AvailableModels = provider.Models // In real implementation, fetch from API
		d.CurrentStep = ModelSelectionStep
		d.Loading = false

		d.Buttons = []DialogButton{
			{Label: "Back", Action: "back", Style: SecondaryButton},
			{Label: "Configure", Action: "configure", Style: PrimaryButton},
		}
		d.SelectedBtn = 1

		return d, nil

	case ModelSelectionStep:
		if d.SelectedBtn == 0 { // Back
			d.CurrentStep = APIKeyInputStep
			d.Buttons = []DialogButton{
				{Label: "Back", Action: "back", Style: SecondaryButton},
				{Label: "Validate", Action: "validate", Style: PrimaryButton},
			}
			d.SelectedBtn = 1
			return d, nil
		}

		// Complete configuration
		provider := d.Providers[d.SelectedProvider]
		selectedModel := ""
		if d.SelectedModel < len(d.AvailableModels) {
			selectedModel = d.AvailableModels[d.SelectedModel]
		}

		return d, func() tea.Msg {
			return LLMConfigResultMsg{
				Provider: provider.Name,
				APIKey:   d.APIKeyInput,
				Model:    selectedModel,
				Action:   "configure",
			}
		}

	case ConfigurationCompleteStep:
		return d, func() tea.Msg {
			return LLMDialogClosedMsg{Action: "ok"}
		}
	}

	return d, nil
}

// View renders the LLM configuration dialog
func (d LLMConfigDialog) View() string {
	t := theme.CurrentTheme()

	// Create dialog container style
	dialogStyle := lipgloss.NewStyle().
		Width(d.Width).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Primary()).
		Background(t.BackgroundPanel()).
		Padding(1, 2)

	// Create title style
	titleStyle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Bold(true).
		Align(lipgloss.Center).
		Width(d.Width - 4)

	var content []string
	content = append(content, titleStyle.Render(d.Title))
	content = append(content, "")

	// Render content based on current step
	switch d.CurrentStep {
	case ProviderSelectionStep:
		content = append(content, d.renderProviderSelection(t)...)
	case APIKeyInputStep:
		content = append(content, d.renderAPIKeyInput(t)...)
	case ModelSelectionStep:
		content = append(content, d.renderModelSelection(t)...)
	case ConfigurationCompleteStep:
		content = append(content, d.renderComplete(t)...)
	}

	// Add error message if present
	if d.ErrorMessage != "" {
		errorStyle := lipgloss.NewStyle().
			Foreground(t.Error()).
			Width(d.Width - 4).
			Align(lipgloss.Center)
		content = append(content, "")
		content = append(content, errorStyle.Render("⚠ "+d.ErrorMessage))
	}

	// Add loading indicator if loading
	if d.Loading {
		loadingStyle := lipgloss.NewStyle().
			Foreground(t.Accent()).
			Width(d.Width - 4).
			Align(lipgloss.Center)
		content = append(content, "")
		content = append(content, loadingStyle.Render("⏳ Validating API key and fetching models..."))
	}

	// Add spacing before buttons
	content = append(content, "")

	// Add buttons
	if len(d.Buttons) > 0 {
		buttonRow := d.renderButtons(t)
		content = append(content, buttonRow)
	}

	// Join all content
	dialogContent := strings.Join(content, "\n")

	return dialogStyle.Render(dialogContent)
}

// ViewWithBackdrop renders the LLM config dialog with a backdrop overlay
func (d LLMConfigDialog) ViewWithBackdrop(screenWidth, screenHeight int) string {
	t := theme.CurrentTheme()
	dialogView := d.View()

	// Create backdrop character with theme background
	backdropChar := " "

	// Position dialog in center of screen with backdrop using theme background
	return lipgloss.Place(
		screenWidth,
		screenHeight,
		lipgloss.Center,
		lipgloss.Center,
		dialogView,
		lipgloss.WithWhitespaceChars(backdropChar),
		lipgloss.WithWhitespaceStyle(lipgloss.NewStyle().Background(t.Background())),
	)
}

// renderProviderSelection renders the provider selection step
func (d LLMConfigDialog) renderProviderSelection(t theme.Theme) []string {
	var content []string

	instructionStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Width(d.Width - 4).
		Align(lipgloss.Left)

	content = append(content, instructionStyle.Render("Select an LLM provider to configure:"))
	content = append(content, "")

	// Render provider list
	for i, provider := range d.Providers {
		itemStyle := lipgloss.NewStyle().
			Width(d.Width-6).
			Padding(0, 1).
			Border(lipgloss.RoundedBorder())

		statusIcon := "○"
		statusColor := t.TextMuted()

		if provider.Configured {
			statusIcon = "●"
			statusColor = t.Success()
		}

		if i == d.SelectedProvider {
			itemStyle = itemStyle.
				Background(t.Primary()).
				Foreground(t.Background()).
				BorderForeground(t.Primary()).
				Bold(true)
			statusColor = t.Background()
		} else {
			itemStyle = itemStyle.
				Background(t.BackgroundElement()).
				Foreground(t.Text()).
				BorderForeground(t.Border())
		}

		statusStyle := lipgloss.NewStyle().Foreground(statusColor)
		nameStyle := lipgloss.NewStyle().Foreground(itemStyle.GetForeground())

		line := lipgloss.JoinHorizontal(lipgloss.Left,
			statusStyle.Render(statusIcon+" "),
			nameStyle.Render(provider.DisplayName),
		)

		if provider.Configured {
			configuredStyle := lipgloss.NewStyle().
				Foreground(itemStyle.GetForeground()).
				Italic(true)
			line += configuredStyle.Render(" (configured)")
		}

		content = append(content, itemStyle.Render(line))
	}

	return content
}

// renderAPIKeyInput renders the API key input step
func (d LLMConfigDialog) renderAPIKeyInput(t theme.Theme) []string {
	var content []string

	provider := d.Providers[d.SelectedProvider]

	instructionStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Width(d.Width - 4).
		Align(lipgloss.Left)

	content = append(content, instructionStyle.Render(fmt.Sprintf("Enter your %s API key:", provider.DisplayName)))
	content = append(content, "")

	// API key input field
	inputStyle := lipgloss.NewStyle().
		Width(d.Width-6).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Primary()).
		Background(t.Background()).
		Padding(0, 1)

	// Render input with cursor (mask the API key for security)
	var inputText string
	maskedInput := strings.Repeat("*", len(d.APIKeyInput))

	if d.APIKeyCursor == len(d.APIKeyInput) {
		inputText = maskedInput + "█"
	} else {
		inputText = maskedInput[:d.APIKeyCursor] + "█" + maskedInput[d.APIKeyCursor:]
	}

	content = append(content, inputStyle.Render(inputText))
	content = append(content, "")

	// Add help text
	helpStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Width(d.Width - 4).
		Align(lipgloss.Left).
		Italic(true)

	content = append(content, helpStyle.Render(fmt.Sprintf("Environment variable: %s", provider.APIKeyName)))

	return content
}

// renderModelSelection renders the model selection step
func (d LLMConfigDialog) renderModelSelection(t theme.Theme) []string {
	var content []string

	provider := d.Providers[d.SelectedProvider]

	instructionStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Width(d.Width - 4).
		Align(lipgloss.Left)

	content = append(content, instructionStyle.Render(fmt.Sprintf("Select a %s model:", provider.DisplayName)))
	content = append(content, "")

	// Render model list
	for i, model := range d.AvailableModels {
		itemStyle := lipgloss.NewStyle().
			Width(d.Width-6).
			Padding(0, 1).
			Border(lipgloss.RoundedBorder())

		if i == d.SelectedModel {
			itemStyle = itemStyle.
				Background(t.Primary()).
				Foreground(t.Background()).
				BorderForeground(t.Primary()).
				Bold(true)
		} else {
			itemStyle = itemStyle.
				Background(t.BackgroundElement()).
				Foreground(t.Text()).
				BorderForeground(t.Border())
		}

		content = append(content, itemStyle.Render("○ "+model))
	}

	return content
}

// renderComplete renders the configuration complete step
func (d LLMConfigDialog) renderComplete(t theme.Theme) []string {
	var content []string

	successStyle := lipgloss.NewStyle().
		Foreground(t.Success()).
		Width(d.Width - 4).
		Align(lipgloss.Center).
		Bold(true)

	content = append(content, successStyle.Render("✓ Configuration Complete!"))
	content = append(content, "")

	provider := d.Providers[d.SelectedProvider]
	selectedModel := ""
	if d.SelectedModel < len(d.AvailableModels) {
		selectedModel = d.AvailableModels[d.SelectedModel]
	}

	infoStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Width(d.Width - 4).
		Align(lipgloss.Left)

	content = append(content, infoStyle.Render(fmt.Sprintf("Provider: %s", provider.DisplayName)))
	content = append(content, infoStyle.Render(fmt.Sprintf("Model: %s", selectedModel)))

	return content
}

// renderButtons renders the button row for LLM config dialog
func (d LLMConfigDialog) renderButtons(t theme.Theme) string {
	if len(d.Buttons) == 0 {
		return ""
	}

	var buttons []string
	for i, btn := range d.Buttons {
		buttonStyle := lipgloss.NewStyle().
			Padding(0, 2).
			Border(lipgloss.RoundedBorder()).
			Align(lipgloss.Center)

		// Apply button styling based on type and selection
		switch btn.Style {
		case PrimaryButton:
			if i == d.SelectedBtn {
				buttonStyle = buttonStyle.
					Background(t.Primary()).
					Foreground(t.Background()).
					BorderForeground(t.Primary()).
					Bold(true)
			} else {
				buttonStyle = buttonStyle.
					Background(t.BackgroundElement()).
					Foreground(t.Primary()).
					BorderForeground(t.Primary())
			}

		case SecondaryButton:
			if i == d.SelectedBtn {
				buttonStyle = buttonStyle.
					Background(t.Border()).
					Foreground(t.Background()).
					BorderForeground(t.Border()).
					Bold(true)
			} else {
				buttonStyle = buttonStyle.
					Background(t.BackgroundElement()).
					Foreground(t.Text()).
					BorderForeground(t.Border())
			}

		case DangerButton:
			if i == d.SelectedBtn {
				buttonStyle = buttonStyle.
					Background(t.Error()).
					Foreground(t.Background()).
					BorderForeground(t.Error()).
					Bold(true)
			} else {
				buttonStyle = buttonStyle.
					Background(t.BackgroundElement()).
					Foreground(t.Error()).
					BorderForeground(t.Error())
			}
		}

		buttons = append(buttons, buttonStyle.Render(btn.Label))
	}

	// Join buttons horizontally with spacing
	var buttonParts []string
	for i, button := range buttons {
		buttonParts = append(buttonParts, button)
		if i < len(buttons)-1 {
			buttonParts = append(buttonParts, "  ") // Add spacing between buttons
		}
	}
	buttonRow := lipgloss.JoinHorizontal(lipgloss.Left, buttonParts...)

	// Center the button row
	return lipgloss.NewStyle().
		Width(d.Width - 4).
		Align(lipgloss.Center).
		Render(buttonRow)
}
