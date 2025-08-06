package components

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// min returns the minimum of two integers
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

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
			Models:      []string{"gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"},
			Configured:  configuredKeys["openai"] != "",
		},
		{
			Name:        "anthropic",
			DisplayName: "Anthropic",
			APIKeyName:  "ANTHROPIC_API_KEY",
			Models:      []string{"claude-3-5-sonnet", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"},
			Configured:  configuredKeys["anthropic"] != "",
		},
		{
			Name:        "google",
			DisplayName: "Google AI",
			APIKeyName:  "GOOGLE_API_KEY",
			Models:      []string{"gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro", "gemini-pro-vision"},
			Configured:  configuredKeys["google"] != "",
		},
		{
			Name:        "cohere",
			DisplayName: "Cohere",
			APIKeyName:  "COHERE_API_KEY",
			Models:      []string{"command-r-plus", "command-r", "command", "command-light", "command-nightly"},
			Configured:  configuredKeys["cohere"] != "",
		},
	}

	return LLMConfigDialog{
		Dialog: Dialog{
			Type:    CustomDialog,
			Title:   "LLM Provider Configuration",
			Width:   85,
			Height:  25,
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
		provider := d.Providers[d.SelectedProvider]

		// If provider is already configured, skip to model selection
		if provider.Configured {
			d.CurrentStep = ModelSelectionStep
			d.AvailableModels = provider.Models
			d.Buttons = []DialogButton{
				{Label: "Back", Action: "back", Style: SecondaryButton},
				{Label: "Configure", Action: "configure", Style: PrimaryButton},
			}
			d.SelectedBtn = 1
		} else {
			// Move to API key input step for unconfigured providers
			d.CurrentStep = APIKeyInputStep
			d.Buttons = []DialogButton{
				{Label: "Back", Action: "back", Style: SecondaryButton},
				{Label: "Validate", Action: "validate", Style: PrimaryButton},
			}
			d.SelectedBtn = 1

			// Pre-fill API key if already configured
			if existingKey, exists := d.ConfiguredKeys[provider.Name]; exists {
				d.APIKeyInput = existingKey
				d.APIKeyCursor = len(existingKey)
			}
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
	content = append(content, instructionStyle.Render("Providers with ✓ are already configured and show available models."))
	content = append(content, "")

	// Render provider list with sleek design
	for i, provider := range d.Providers {
		var providerLine string
		var modelsLine string

		// Provider name styling
		if i == d.SelectedProvider {
			// Selected provider - highlight in primary color
			nameStyle := lipgloss.NewStyle().
				Foreground(t.Primary()).
				Bold(true)
			providerLine = nameStyle.Render("▶ " + provider.DisplayName)
		} else {
			// Unselected provider - normal text
			nameStyle := lipgloss.NewStyle().
				Foreground(t.Text())
			providerLine = nameStyle.Render("  " + provider.DisplayName)
		}

		// Add configured status
		if provider.Configured {
			statusStyle := lipgloss.NewStyle().
				Foreground(t.Success()).
				Italic(true)
			providerLine += statusStyle.Render(" ✓")

			// Show available models for configured providers
			modelStyle := lipgloss.NewStyle().
				Foreground(t.TextMuted()).
				Italic(true)

			modelList := strings.Join(provider.Models[:min(3, len(provider.Models))], ", ")
			if len(provider.Models) > 3 {
				modelList += fmt.Sprintf(" (+%d more)", len(provider.Models)-3)
			}
			modelsLine = modelStyle.Render("    " + modelList)
		}

		content = append(content, providerLine)
		if modelsLine != "" {
			content = append(content, modelsLine)
		}
		content = append(content, "") // Add spacing between providers
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

	// Render model list with sleek design
	for i, model := range d.AvailableModels {
		var modelLine string

		if i == d.SelectedModel {
			// Selected model - highlight in primary color
			modelStyle := lipgloss.NewStyle().
				Foreground(t.Primary()).
				Bold(true)
			modelLine = modelStyle.Render("▶ " + model)
		} else {
			// Unselected model - normal text
			modelStyle := lipgloss.NewStyle().
				Foreground(t.Text())
			modelLine = modelStyle.Render("  " + model)
		}

		content = append(content, modelLine)
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
