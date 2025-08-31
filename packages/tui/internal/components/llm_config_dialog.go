package components

import (
	"fmt"
	"math"
	"os/exec"
	"runtime"
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// buildSelectableItems creates a flattened list of providers and their models
func (d LLMConfigDialog) buildSelectableItems() []SelectableItem {
	var items []SelectableItem

	for i, provider := range d.Providers {
		// Add provider item
		items = append(items, SelectableItem{
			Type:         "provider",
			ProviderIdx:  i,
			ModelIdx:     -1,
			DisplayText:  provider.DisplayName,
			IsConfigured: provider.Configured,
			IsSelectable: true, // Only unconfigured providers are selectable for setup
		})

		// Add model items if provider is configured
		if provider.Configured {
			for j, model := range provider.Models {
				items = append(items, SelectableItem{
					Type:         "model",
					ProviderIdx:  i,
					ModelIdx:     j,
					DisplayText:  model,
					IsConfigured: true,
					IsSelectable: true,
				})
			}
		}
	}

	return items
}

// getSelectedItem returns the currently selected item
func (d LLMConfigDialog) getSelectedItem() SelectableItem {
	items := d.buildSelectableItems()
	if d.SelectedModelIdx >= 0 && d.SelectedModelIdx < len(items) {
		return items[d.SelectedModelIdx]
	}
	return SelectableItem{}
}

// getButtonText returns the appropriate button text based on current selection
func (d LLMConfigDialog) getButtonText() string {
	if d.CurrentStep != ProviderSelectionStep {
		return "Next"
	}

	selectedItem := d.getSelectedItem()

	if selectedItem.Type == "model" {
		return "Use Model"
	} else if selectedItem.Type == "provider" {
		return "Configure"
	}
	return "Select"
}

// updateScroll adjusts the scroll offset to keep the selected item visible
func (d *LLMConfigDialog) updateScroll() {
	if d.CurrentStep != ProviderSelectionStep {
		return
	}

	// Ensure selected item is visible
	if d.SelectedModelIdx < d.ScrollOffset {
		// Selected item is above visible area - scroll up
		d.ScrollOffset = d.SelectedModelIdx
	} else if d.SelectedModelIdx >= d.ScrollOffset+d.VisibleItems {
		// Selected item is below visible area - scroll down
		d.ScrollOffset = d.SelectedModelIdx - d.VisibleItems + 1
	}

	// Ensure scroll offset is not negative
	if d.ScrollOffset < 0 {
		d.ScrollOffset = 0
	}
}

// getVisibleItems returns the items that should be displayed based on scroll position
func (d LLMConfigDialog) getVisibleItems() []SelectableItem {
	items := d.buildSelectableItems()

	start := d.ScrollOffset
	end := start + d.VisibleItems

	if start >= len(items) {
		return []SelectableItem{}
	}

	if end > len(items) {
		end = len(items)
	}

	return items[start:end]
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
	CurrentStep        LLMConfigStep
	Providers          []LLMProvider
	SelectedProvider   int
	SelectedModelIdx   int // Index within the flattened provider+model list
	ScrollOffset       int // Current scroll position
	VisibleItems       int // Number of items that can be displayed
	APIKeyInput        string
	APIKeyCursor       int
	AvailableModels    []string
	SelectedModel      int
	ConfiguredKeys     map[string]string
	ConfiguredProvider string // Currently configured provider
	ConfiguredModel    string // Currently configured model
	Loading            bool
	ErrorMessage       string
	ExpandedProviders  map[int]bool // Track which providers are expanded
	loadingSpinner     Spinner      // Spinner for loading states
	ButtonsFocused     bool         // Track whether focus is on buttons (vs input field)
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

// APIValidationCompleteMsg is sent when API validation is complete
type APIValidationCompleteMsg struct {
	Success  bool
	Models   []string
	ErrorMsg string
}

// SelectableItem represents an item in the provider/model list
type SelectableItem struct {
	Type         string // "provider" or "model"
	ProviderIdx  int
	ModelIdx     int
	DisplayText  string
	IsConfigured bool
	IsSelectable bool
}

// NewLLMConfigDialog creates a new LLM configuration dialog
func NewLLMConfigDialog(configuredKeys map[string]string, selectedProvider, selectedModel string) LLMConfigDialog {
	providers := []LLMProvider{
		{
			Name:        "openai",
			DisplayName: "OpenAI",
			APIKeyName:  "OPENAI_API_KEY",
			Models:      []string{"gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-5", "gpt-5-mini"},
			Configured:  configuredKeys["openai"] != "",
		},
		{
			Name:        "anthropic",
			DisplayName: "Anthropic",
			APIKeyName:  "ANTHROPIC_API_KEY",
			Models:      []string{"claude-3-5-sonnet", "claude-3-7-opus", "claude-3-7-sonnet", "claude-4-sonnet", "claude-4-opus"},
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

	dialog := LLMConfigDialog{
		Dialog: Dialog{
			Type:    CustomDialog,
			Title:   "LLM Provider Configuration",
			Width:   85,
			Height:  25, // Reduced height to fit better in terminals
			Focused: true,
			Buttons: []DialogButton{
				{Label: "Cancel", Action: "cancel", Style: SecondaryButton},
				{Label: "Select", Action: "select", Style: PrimaryButton},
			},
			SelectedBtn: 1,
		},
		CurrentStep:        ProviderSelectionStep,
		Providers:          providers,
		SelectedProvider:   0,
		SelectedModelIdx:   0,
		ScrollOffset:       0,
		VisibleItems:       10, // Show up to 10 items at once
		ConfiguredKeys:     configuredKeys,
		ConfiguredProvider: selectedProvider,
		ConfiguredModel:    selectedModel,
		AvailableModels:    []string{},
		ExpandedProviders:  make(map[int]bool),
		ButtonsFocused:     false, // Start with input field focused
	}

	// Find the previously selected model or first selectable item
	items := dialog.buildSelectableItems()
	selectedIdx := 0

	// Look for previously selected model first
	if selectedProvider != "" && selectedModel != "" {
		for i, item := range items {
			if item.Type == "model" &&
				dialog.Providers[item.ProviderIdx].Name == selectedProvider &&
				dialog.Providers[item.ProviderIdx].Models[item.ModelIdx] == selectedModel {
				selectedIdx = i
				break
			}
		}
	}

	// If not found or no previous selection, find first selectable item
	if selectedIdx == 0 {
		for i, item := range items {
			if item.IsSelectable {
				selectedIdx = i
				break
			}
		}
	}

	dialog.SelectedModelIdx = selectedIdx

	// Initialize spinner
	dialog.loadingSpinner = NewSpinner(4) // ID 4 for LLM config spinner

	// Initialize scroll position
	dialog.updateScroll()

	return dialog
}

// Update handles LLM config dialog input
func (d LLMConfigDialog) Update(msg tea.Msg) (LLMConfigDialog, tea.Cmd) {
	if !d.Focused {
		return d, nil
	}
	switch msg := msg.(type) {
	case SpinnerTickMsg:
		// Update spinner if loading
		if d.Loading {
			var cmd tea.Cmd
			d.loadingSpinner, cmd = d.loadingSpinner.Update(msg)
			return d, cmd
		}
		return d, nil
	case APIValidationCompleteMsg:
		// Stop loading and process validation result
		d.Loading = false
		d.loadingSpinner.SetActive(false)
		if msg.Success {
			d.AvailableModels = msg.Models
			d.CurrentStep = ModelSelectionStep
			d.Buttons = []DialogButton{
				{Label: "Back", Action: "back", Style: SecondaryButton},
				{Label: "Configure", Action: "configure", Style: PrimaryButton},
			}
			d.SelectedBtn = 1
			d.ButtonsFocused = false // Reset focus state when transitioning
		} else {
			d.ErrorMessage = msg.ErrorMsg
		}
		return d, nil
	case tea.PasteMsg:
		if d.CurrentStep == APIKeyInputStep {
			return d.handlePaste()
		}
		return d, nil
	case tea.KeyMsg:
		switch msg.String() {
		case "esc":
			return d, func() tea.Msg {
				return LLMDialogClosedMsg{Action: "cancel"}
			}

		case "enter":
			return d.handleEnter()

		case "right":
			// Navigate buttons if buttons are focused, otherwise move cursor in API key input
			if d.CurrentStep == APIKeyInputStep && d.ButtonsFocused {
				if len(d.Buttons) > 1 {
					d.SelectedBtn = (d.SelectedBtn + 1) % len(d.Buttons)
				}
			} else if d.CurrentStep == APIKeyInputStep {
				if d.APIKeyCursor < len(d.APIKeyInput) {
					d.APIKeyCursor++
				}
			} else if len(d.Buttons) > 1 {
				d.SelectedBtn = (d.SelectedBtn + 1) % len(d.Buttons)
			}
			return d, nil

		case "left":
			// Navigate buttons if buttons are focused, otherwise move cursor in API key input
			if d.CurrentStep == APIKeyInputStep && d.ButtonsFocused {
				if len(d.Buttons) > 1 {
					d.SelectedBtn = (d.SelectedBtn - 1 + len(d.Buttons)) % len(d.Buttons)
				}
			} else if d.CurrentStep == APIKeyInputStep {
				if d.APIKeyCursor > 0 {
					d.APIKeyCursor--
				}
			} else if len(d.Buttons) > 1 {
				d.SelectedBtn = (d.SelectedBtn - 1 + len(d.Buttons)) % len(d.Buttons)
			}
			return d, nil

		case "up":
			switch d.CurrentStep {
			case ProviderSelectionStep:
				items := d.buildSelectableItems()
				// Find previous selectable item
				for i := d.SelectedModelIdx - 1; i >= 0; i-- {
					if items[i].IsSelectable {
						d.SelectedModelIdx = i
						d.updateScroll()
						break
					}
				}
			case APIKeyInputStep:
				// Move focus from buttons back to input field
				if d.ButtonsFocused {
					d.ButtonsFocused = false
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
				items := d.buildSelectableItems()
				// Find next selectable item
				for i := d.SelectedModelIdx + 1; i < len(items); i++ {
					if items[i].IsSelectable {
						d.SelectedModelIdx = i
						d.updateScroll()
						break
					}
				}
			case APIKeyInputStep:
				// Move focus from input field to buttons
				if !d.ButtonsFocused {
					d.ButtonsFocused = true
				}
			case ModelSelectionStep:
				if d.SelectedModel < len(d.AvailableModels)-1 {
					d.SelectedModel++
				}
			}
			return d, nil
		case "backspace":
			if d.CurrentStep == APIKeyInputStep && !d.ButtonsFocused && d.APIKeyCursor > 0 && len(d.APIKeyInput) > 0 {
				d.APIKeyInput = d.APIKeyInput[:d.APIKeyCursor-1] + d.APIKeyInput[d.APIKeyCursor:]
				d.APIKeyCursor--
			}
			return d, nil

		case "delete":
			if d.CurrentStep == APIKeyInputStep && !d.ButtonsFocused && d.APIKeyCursor < len(d.APIKeyInput) {
				d.APIKeyInput = d.APIKeyInput[:d.APIKeyCursor] + d.APIKeyInput[d.APIKeyCursor+1:]
			}
			return d, nil

		default:
			// Handle regular character input for API key (only when input field is focused)
			if d.CurrentStep == APIKeyInputStep && !d.ButtonsFocused {
				keyStr := msg.String()

				// Special handling for space key since it might have special representation
				if keyStr == " " || keyStr == "space" {
					d.APIKeyInput = d.APIKeyInput[:d.APIKeyCursor] + " " + d.APIKeyInput[d.APIKeyCursor:]
					d.APIKeyCursor++
				} else if len(keyStr) == 1 {
					char := keyStr
					d.APIKeyInput = d.APIKeyInput[:d.APIKeyCursor] + char + d.APIKeyInput[d.APIKeyCursor:]
					d.APIKeyCursor++
				}
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

		selectedItem := d.getSelectedItem()

		if selectedItem.Type == "model" {
			// User selected a model directly - configure it
			provider := d.Providers[selectedItem.ProviderIdx]
			selectedModel := provider.Models[selectedItem.ModelIdx]

			return d, func() tea.Msg {
				return LLMConfigResultMsg{
					Provider: provider.Name,
					APIKey:   d.ConfiguredKeys[provider.Name], // Use existing API key
					Model:    selectedModel,
					Action:   "configure",
				}
			}
		} else if selectedItem.Type == "provider" {
			// User selected an unconfigured provider - go to API key input
			d.SelectedProvider = selectedItem.ProviderIdx
			d.CurrentStep = APIKeyInputStep
			d.Buttons = []DialogButton{
				{Label: "Back", Action: "back", Style: SecondaryButton},
				{Label: "Validate", Action: "validate", Style: PrimaryButton},
			}
			d.SelectedBtn = 1
			d.ButtonsFocused = false // Focus on input field when entering this step

			d.APIKeyInput = ""
			d.APIKeyCursor = 0

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
			d.ButtonsFocused = false // Reset focus state when going back
			return d, nil
		}

		// Validate API key and fetch models
		if d.APIKeyInput == "" {
			d.ErrorMessage = "API key cannot be empty"
			return d, nil
		}

		d.Loading = true
		d.ErrorMessage = ""
		d.loadingSpinner.SetActive(true)

		provider := d.Providers[d.SelectedProvider]
		selectedModel := ""
		if d.SelectedModel < len(d.AvailableModels) {
			selectedModel = d.AvailableModels[d.SelectedModel]
		}
		// Return command to start spinner and simulate API validation TODO implement the api validation
		return d, func() tea.Msg {
			return LLMConfigResultMsg{
				Provider: provider.Name,
				APIKey:   d.APIKeyInput,
				Model:    selectedModel,
				Action:   "configure",
			}
		}

	case ModelSelectionStep:
		if d.SelectedBtn == 0 { // Back
			d.CurrentStep = APIKeyInputStep
			d.Buttons = []DialogButton{
				{Label: "Back", Action: "back", Style: SecondaryButton},
				{Label: "Validate", Action: "validate", Style: PrimaryButton},
			}
			d.SelectedBtn = 1
			d.ButtonsFocused = false // Reset focus state when going back
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

// handlePaste handles clipboard paste operation for API key input
func (d LLMConfigDialog) handlePaste() (LLMConfigDialog, tea.Cmd) {
	// Get clipboard content based on the operating system
	clipboardText, err := getClipboardContent()
	if err != nil {
		// If clipboard reading fails, just return without error
		return d, nil
	}

	// Clean the clipboard text (remove newlines and trim whitespace)
	cleanText := strings.TrimSpace(strings.ReplaceAll(clipboardText, "\n", ""))

	if cleanText == "" {
		return d, nil
	}

	// Insert the clipboard content at the current cursor position
	d.APIKeyInput = d.APIKeyInput[:d.APIKeyCursor] + cleanText + d.APIKeyInput[d.APIKeyCursor:]
	d.APIKeyCursor += len(cleanText)

	return d, nil
}

// getClipboardContent reads content from the system clipboard
func getClipboardContent() (string, error) {
	var cmd *exec.Cmd

	switch runtime.GOOS {
	case "darwin": // macOS
		cmd = exec.Command("pbpaste")
	case "linux", "freebsd", "openbsd", "netbsd":
		// Try xclip first, then xsel as fallback
		if _, err := exec.LookPath("xclip"); err == nil {
			cmd = exec.Command("xclip", "-selection", "clipboard", "-o")
		} else if _, err := exec.LookPath("xsel"); err == nil {
			cmd = exec.Command("xsel", "--clipboard", "--output")
		} else {
			return "", fmt.Errorf("no clipboard utility found (xclip or xsel required)")
		}
	case "windows":
		cmd = exec.Command("powershell", "-command", "Get-Clipboard")
	default:
		return "", fmt.Errorf("unsupported operating system: %s", runtime.GOOS)
	}

	output, err := cmd.Output()
	if err != nil {
		return "", err
	}

	return string(output), nil
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
		Background(t.BackgroundPanel()).
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
		content = append(content, loadingStyle.Render(fmt.Sprintf("%s Validating API key and fetching models...", d.loadingSpinner.View())))
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

	content = append(content, instructionStyle.Render("Select a provider to configure or choose a model from configured providers:"))
	content = append(content, instructionStyle.Render("✓ = configured provider, ● = currently selected model"))

	// Show scroll indicators if needed
	allItems := d.buildSelectableItems()
	if len(allItems) > d.VisibleItems {
		scrollInfo := fmt.Sprintf("Showing %d-%d of %d items",
			d.ScrollOffset+1,
			math.Min(float64(d.ScrollOffset+d.VisibleItems), float64(len(allItems))),
			len(allItems))

		scrollStyle := lipgloss.NewStyle().
			Foreground(t.TextMuted()).
			Italic(true).
			Width(d.Width - 4).
			Align(lipgloss.Right)

		content = append(content, scrollStyle.Render(scrollInfo))
	} else {
		content = append(content, "")
	}

	visibleItems := d.getVisibleItems()

	for i, item := range visibleItems {
		actualIndex := d.ScrollOffset + i
		var line string
		var isSelected = (actualIndex == d.SelectedModelIdx)

		switch item.Type {
		case "provider":
			// Render provider
			var providerLine string

			if isSelected {
				// Selected unconfigured provider
				nameStyle := lipgloss.NewStyle().
					Foreground(t.Primary()).
					Background(t.BackgroundPanel()).
					Bold(true)
				providerLine = nameStyle.Render("▶ " + item.DisplayText)
			} else {
				// Unselected or configured provider
				nameStyle := lipgloss.NewStyle().
					Foreground(t.Text()).
					Background(t.BackgroundPanel())
				providerLine = nameStyle.Render("  " + item.DisplayText)
			}

			// Add configured status
			if item.IsConfigured {
				statusStyle := lipgloss.NewStyle().
					Foreground(t.Success()).
					Background(t.BackgroundPanel()).
					Italic(true)
				providerLine += statusStyle.Render(" ✓")
			}

			line = providerLine

		case "model":
			// Render model
			var modelLine string
			provider := d.Providers[item.ProviderIdx]
			modelName := provider.Models[item.ModelIdx]

			// Check if this is the currently configured model
			isConfiguredModel := (provider.Name == d.ConfiguredProvider && modelName == d.ConfiguredModel)

			if isSelected {
				// Selected model
				modelStyle := lipgloss.NewStyle().
					Foreground(t.Primary()).
					Bold(true)
				modelLine = modelStyle.Render("    ▶ " + item.DisplayText)
			} else {
				// Unselected model
				modelStyle := lipgloss.NewStyle().
					Foreground(t.TextMuted()).
					Background(t.BackgroundPanel())
				modelLine = modelStyle.Render("      " + item.DisplayText)
			}

			// Add indicator for currently configured model
			if isConfiguredModel {
				configIndicatorStyle := lipgloss.NewStyle().
					Foreground(t.Success()).
					Background(t.BackgroundPanel()).
					Bold(true)
				modelLine += configIndicatorStyle.Render(" ●")
			}

			line = modelLine
		}
		content = append(content, line)
	}

	// Add scroll indicators at the bottom
	if len(allItems) > d.VisibleItems {
		var scrollIndicators []string

		if d.ScrollOffset > 0 {
			scrollIndicators = append(scrollIndicators, "↑ More above")
		}

		if d.ScrollOffset+d.VisibleItems < len(allItems) {
			scrollIndicators = append(scrollIndicators, "↓ More below")
		}

		if len(scrollIndicators) > 0 {
			content = append(content, "")
			indicatorStyle := lipgloss.NewStyle().
				Foreground(t.Accent()).
				Width(d.Width - 4).
				Align(lipgloss.Center)

			content = append(content, indicatorStyle.Render(strings.Join(scrollIndicators, "  •  ")))
		}
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

	// Add focus indicator for input field
	var inputFieldLine string
	if !d.ButtonsFocused {
		// Input field is focused - show triangle indicator
		focusIndicator := lipgloss.NewStyle().
			Foreground(t.Primary()).
			Background(t.BackgroundPanel()).
			Bold(true)
		inputFieldLine = focusIndicator.Render("▶ API Key:")
	} else {
		// Input field not focused
		inputFieldLine = "  API Key:"
	}

	labelStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.BackgroundPanel()).
		Width(d.Width - 4).
		Align(lipgloss.Left)
	content = append(content, labelStyle.Render(inputFieldLine))

	// API key input field
	inputStyle := lipgloss.NewStyle().
		Width(d.Width-6).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Primary()).
		Background(t.BackgroundPanel()).
		Padding(0, 1)

	// Render input with cursor (similar to textarea approach)
	var inputText string

	// Define text style for normal characters
	textStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.BackgroundPanel())

	if d.APIKeyCursor >= len(d.APIKeyInput) {
		// Cursor at end of input
		cursorStyle := lipgloss.NewStyle().
			Background(t.Primary()).
			Foreground(t.BackgroundPanel())
		inputText = textStyle.Render(d.APIKeyInput) + cursorStyle.Render(" ")
	} else if d.APIKeyCursor >= 0 && d.APIKeyCursor < len(d.APIKeyInput) {
		// Cursor in middle of input - highlight the character at cursor position
		before := d.APIKeyInput[:d.APIKeyCursor]
		atCursor := string(d.APIKeyInput[d.APIKeyCursor])
		after := ""
		if d.APIKeyCursor+1 < len(d.APIKeyInput) {
			after = d.APIKeyInput[d.APIKeyCursor+1:]
		}

		// Render with cursor highlighting the character
		cursorStyle := lipgloss.NewStyle().
			Background(t.Primary()).
			Foreground(t.BackgroundPanel())
		inputText = textStyle.Render(before) + cursorStyle.Render(atCursor) + textStyle.Render(after)
	} else {
		// Fallback for invalid cursor position
		inputText = textStyle.Render(d.APIKeyInput)
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
	content = append(content, "")

	// Add navigation hints
	navHintStyle := lipgloss.NewStyle().
		Foreground(t.Accent()).
		Width(d.Width - 4).
		Align(lipgloss.Center).
		Italic(true)

	if d.ButtonsFocused {
		content = append(content, navHintStyle.Render("↑ Input field • ←→ Navigate buttons • Enter: Execute"))
	} else {
		content = append(content, navHintStyle.Render("↓ Buttons • ←→ Move cursor • Enter: Execute"))
	}

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
		// Use dynamic button text for the primary button
		buttonText := btn.Label
		if i == 1 && d.CurrentStep == ProviderSelectionStep {
			buttonText = d.getButtonText()
		}

		// Add focus indicator for buttons when they're focused
		if d.CurrentStep == APIKeyInputStep && d.ButtonsFocused && i == d.SelectedBtn {
			buttonText = "▶ " + buttonText
		}
		buttonStyle := lipgloss.NewStyle().
			Padding(0, 2).
			Background(t.BackgroundPanel()).
			Border(lipgloss.RoundedBorder()).
			BorderBackground(t.BackgroundPanel()).
			Align(lipgloss.Center)

		// Apply button styling based on type and selection
		switch btn.Style {
		case PrimaryButton:
			if i == d.SelectedBtn {
				buttonStyle = buttonStyle.
					Background(t.Primary()).
					Foreground(t.Background()).
					BorderForeground(t.Primary()).
					BorderBackground(t.BackgroundPanel()).
					Bold(true)
			} else {
				buttonStyle = buttonStyle.
					Background(t.BackgroundElement()).
					Foreground(t.Primary()).
					BorderForeground(t.Primary()).
					BorderBackground(t.BackgroundPanel())
			}

		case SecondaryButton:
			if i == d.SelectedBtn {
				buttonStyle = buttonStyle.
					Background(t.Border()).
					Foreground(t.Text()).
					BorderForeground(t.Border()).
					BorderBackground(t.BackgroundPanel()).
					Bold(true)
			} else {
				buttonStyle = buttonStyle.
					Background(t.BackgroundElement()).
					Foreground(t.Text()).
					BorderForeground(t.Border()).
					BorderBackground(t.BackgroundPanel())
			}

		case DangerButton:
			if i == d.SelectedBtn {
				buttonStyle = buttonStyle.
					Background(t.Error()).
					Foreground(t.Background()).
					BorderForeground(t.Error()).
					BorderBackground(t.Background()).
					Bold(true)
			} else {
				buttonStyle = buttonStyle.
					Background(t.BackgroundElement()).
					Foreground(t.Error()).
					BorderForeground(t.Error()).
					BorderBackground(t.Background())
			}
		}

		buttons = append(buttons, buttonStyle.Render(buttonText))
	}

	// Join buttons horizontally with spacing
	var buttonParts []string
	for i, button := range buttons {
		buttonParts = append(buttonParts, button)
		if i < len(buttons)-1 {
			buttonParts = append(buttonParts, lipgloss.NewStyle().Height(3).Background(t.BackgroundPanel()).Render("  ")) // Add spacing between buttons
		}
	}
	buttonRow := lipgloss.JoinHorizontal(lipgloss.Left, buttonParts...)

	return lipgloss.Place(
		d.Width-8,
		4,
		lipgloss.Center,
		lipgloss.Center,
		buttonRow,
		lipgloss.WithWhitespaceChars(" "),
		lipgloss.WithWhitespaceStyle(lipgloss.NewStyle().Background(t.BackgroundPanel())),
	)

}
