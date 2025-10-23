package tui

import (
	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/rogue/tui/internal/components"
	"github.com/rogue/tui/internal/theme"
)

// HandleConfigEnter handles Enter key in configuration screen
func HandleConfigEnter(m Model) (Model, tea.Cmd) {
	if m.configState == nil {
		return m, nil
	}

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

// HandleConfigInput handles keyboard input for the configuration screen
func HandleConfigInput(m Model, msg tea.KeyMsg) (Model, tea.Cmd) {
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
