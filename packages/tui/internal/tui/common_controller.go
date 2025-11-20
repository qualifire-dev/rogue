package tui

import (
	"context"
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/rogue/tui/internal/components"
	"github.com/rogue/tui/internal/screens/config"
	"github.com/rogue/tui/internal/screens/scenarios"
)

// handlePasteMsg handles clipboard paste messages
func (m Model) handlePasteMsg(msg tea.PasteMsg) (Model, tea.Cmd) {
	var cmd tea.Cmd
	var cmds []tea.Cmd

	if m.llmDialog != nil {
		*m.llmDialog, cmd = m.llmDialog.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		return m, tea.Batch(cmds...)
	}

	if m.dialog != nil {
		// Clean the clipboard text (remove newlines and trim whitespace)
		cleanText := strings.TrimSpace(strings.ReplaceAll(string(msg), "\n", ""))

		if cleanText == "" {
			return m, nil
		}

		m.dialog.Input += cleanText
		m.dialog.InputCursor = len(m.dialog.Input)
		return m, nil
	}

	// Handle paste for new evaluation screen (Agent URL, Judge Model fields)
	if m.currentScreen == NewEvaluationScreen && m.evalState != nil {
		// Clean the clipboard text (remove newlines and trim whitespace)
		cleanText := strings.TrimSpace(strings.ReplaceAll(string(msg), "\n", ""))

		if cleanText == "" {
			return m, nil
		}

		// Only paste into text fields (Agent URL and Judge Model)
		switch m.evalState.currentField {
		case 0: // Agent URL
			// Insert at cursor position
			runes := []rune(m.evalState.AgentURL)
			m.evalState.AgentURL = string(runes[:m.evalState.cursorPos]) + cleanText + string(runes[m.evalState.cursorPos:])
			m.evalState.cursorPos += len([]rune(cleanText))
		case 3: // Judge Model
			// Insert at cursor position
			runes := []rune(m.evalState.JudgeModel)
			m.evalState.JudgeModel = string(runes[:m.evalState.cursorPos]) + cleanText + string(runes[m.evalState.cursorPos:])
			m.evalState.cursorPos += len([]rune(cleanText))
		}
		return m, nil
	}

	// Forward paste to scenario editor if on scenarios screen
	if m.currentScreen == ScenariosScreen {
		m.scenarioEditor, cmd = m.scenarioEditor.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		return m, tea.Batch(cmds...)
	}

	return m, nil
}

// handleSpinnerTickMsg handles spinner animation updates
func (m Model) handleSpinnerTickMsg(msg components.SpinnerTickMsg) (Model, tea.Cmd) {
	var cmd tea.Cmd
	var cmds []tea.Cmd

	// Update spinners
	m.healthSpinner, cmd = m.healthSpinner.Update(msg)
	cmds = append(cmds, cmd)
	m.summarySpinner, cmd = m.summarySpinner.Update(msg)
	cmds = append(cmds, cmd)
	m.evalSpinner, cmd = m.evalSpinner.Update(msg)
	cmds = append(cmds, cmd)

	// Forward to scenario editor for interview spinner
	if m.currentScreen == ScenariosScreen {
		m.scenarioEditor, cmd = m.scenarioEditor.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
	}

	return m, tea.Batch(cmds...)
}

// handleWindowSizeMsg handles terminal window resize
func (m Model) handleWindowSizeMsg(msg tea.WindowSizeMsg) (Model, tea.Cmd) {
	m.width = msg.Width
	m.height = msg.Height
	// Update command input width
	m.commandInput.SetWidth(msg.Width - 8) // Leave some margin
	// Update scenario editor size
	m.scenarioEditor.SetSize(msg.Width, msg.Height)
	// Update viewport sizes
	viewportWidth := msg.Width - 4
	viewportHeight := msg.Height - 8
	if m.eventsHistory != nil {
		m.eventsHistory.SetSize(viewportWidth, viewportHeight)
	}
	if m.summaryHistory != nil {
		m.summaryHistory.SetSize(viewportWidth, viewportHeight)
	}
	if m.reportHistory != nil {
		m.reportHistory.SetSize(viewportWidth, viewportHeight)
	}
	m.helpViewport.SetSize(viewportWidth, viewportHeight)
	return m, nil
}

// handleAutoRefreshMsg handles periodic screen refresh for running evaluations
func (m Model) handleAutoRefreshMsg(msg AutoRefreshMsg) (Model, tea.Cmd) {
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
				return m, tea.Batch(m.summarySpinner.Start(), m.summaryGenerationCmd())
			}
		}
	}
	return m, nil
}

// handleHealthCheckResultMsg handles the result of a server health check
func (m Model) handleHealthCheckResultMsg(msg HealthCheckResultMsg) (Model, tea.Cmd) {
	// Stop health spinner and show result
	m.healthSpinner.SetActive(false)
	if msg.Err != nil {
		d := components.ShowErrorDialog("Server Health", fmt.Sprintf("%v", msg.Err))
		m.dialog = &d
	} else {
		d := components.NewInfoDialog("Server Health", msg.Status)
		m.dialog = &d
	}
	return m, nil
}

// handleStartEvaluationMsg handles starting a new evaluation
func (m Model) handleStartEvaluationMsg(msg StartEvaluationMsg) (Model, tea.Cmd) {
	// Actually start the evaluation (keep spinner running during evaluation)
	if m.evalState != nil && !m.evalState.Running {
		ctx := context.Background()
		m.startEval(ctx, m.evalState)
		// move to detail screen
		m.currentScreen = EvaluationDetailScreen
		// Reset viewport focus to events when entering detail screen
		m.focusedViewport = 0
		// Blur events history to enable auto-scroll for new evaluation
		if m.eventsHistory != nil {
			m.eventsHistory.Blur()
		}
		return m, autoRefreshCmd()
	}
	return m, nil
}

// handleSummaryGeneratedMsg handles the completion of summary generation
func (m Model) handleSummaryGeneratedMsg(msg SummaryGeneratedMsg) (Model, tea.Cmd) {
	// Stop summary spinner and update summary
	m.summarySpinner.SetActive(false)
	if msg.Err != nil {
		if m.evalState != nil {
			m.evalState.Summary = fmt.Sprintf("# Summary Generation Failed\n\nError: %v", msg.Err)
		}
	} else {
		if m.evalState != nil {
			m.evalState.Summary = msg.Summary
		}
	}
	return m, nil
}

// handleCommandSelectedMsg handles command selection from the command palette
func (m Model) handleCommandSelectedMsg(msg components.CommandSelectedMsg) (Model, tea.Cmd) {
	switch msg.Command.Action {
	case "new_evaluation":
		m.currentScreen = NewEvaluationScreen
		// initialize eval state with values from config
		judgeModel := "openai/gpt-4.1" // fallback default
		if m.config.SelectedModel != "" && m.config.SelectedProvider != "" {
			// Use the configured model in provider/model format
			// Check if model already has provider prefix (e.g., "bedrock/anthropic.claude-...")
			// If it does, use it as-is; otherwise, add the provider prefix
			if strings.Contains(m.config.SelectedModel, "/") {
				judgeModel = m.config.SelectedModel
			} else {
				judgeModel = m.config.SelectedProvider + "/" + m.config.SelectedModel
			}
		}
		// TODO read agent url and protocol .rogue/user_config.json
		m.evalState = &EvaluationViewState{
			ServerURL:          m.config.ServerURL,
			AgentURL:           "http://localhost:10001",
			AgentProtocol:      ProtocolA2A,
			AgentTransport:     TransportHTTP,
			JudgeModel:         judgeModel,
			ParallelRuns:       1,
			DeepTest:           false,
			Scenarios:          loadScenariosFromWorkdir(),
			EvaluationMode:     EvaluationModePolicy,
			OWASPCategories:    []string{},
			AttacksPerCategory: 5,
			cursorPos:          len([]rune("http://localhost:10001")), // Set cursor to end of Agent URL
		}
	case "configure_models":
		// Open LLM configuration dialog
		llmDialog := components.NewLLMConfigDialog(m.config.APIKeys, m.config.SelectedProvider, m.config.SelectedModel)
		m.llmDialog = &llmDialog
		return m, nil
	case "open_editor":
		m.currentScreen = ScenariosScreen
		// Unfocus command input when entering scenarios screen
		m.commandInput.SetFocus(false)
		m.commandInput.SetValue("")
		// Configure scenario editor with interview model settings
		m.configureScenarioEditorWithInterviewModel()
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
		// Initialize help viewport content if not already set
		m.initializeHelpViewport()
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
}

// handleDialogOpenMsg handles opening a new dialog
func (m Model) handleDialogOpenMsg(msg components.DialogOpenMsg) (Model, tea.Cmd) {
	m.dialog = &msg.Dialog
	return m, nil
}

// handleLLMConfigResultMsg handles LLM configuration completion
func (m Model) handleLLMConfigResultMsg(msg components.LLMConfigResultMsg) (Model, tea.Cmd) {
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

			// For Bedrock, also save AWS credentials separately
			if msg.Provider == "bedrock" {
				if msg.AWSAccessKeyID != "" {
					m.config.APIKeys["bedrock_access_key"] = msg.AWSAccessKeyID
				}
				if msg.AWSSecretAccessKey != "" {
					m.config.APIKeys["bedrock_secret_key"] = msg.AWSSecretAccessKey
				}
				if msg.AWSRegion != "" {
					m.config.APIKeys["bedrock_region"] = msg.AWSRegion
				}
			}

			// If we're on the evaluation screen, update the judge model
			if m.currentScreen == NewEvaluationScreen && m.evalState != nil {
				// Check if model already has provider prefix (e.g., "bedrock/anthropic.claude-...")
				// If it does, use it as-is; otherwise, add the provider prefix
				if strings.Contains(msg.Model, "/") {
					m.evalState.JudgeModel = msg.Model
				} else {
					m.evalState.JudgeModel = msg.Provider + "/" + msg.Model
				}
			}

			// Save config to file
			err := config.Save(&m.config)
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
}

// handleLLMDialogClosedMsg handles LLM dialog closure
func (m Model) handleLLMDialogClosedMsg(msg components.LLMDialogClosedMsg) (Model, tea.Cmd) {
	if m.llmDialog != nil {
		m.llmDialog = nil
	}
	return m, nil
}

// handleDialogClosedMsg handles dialog closure with action
func (m Model) handleDialogClosedMsg(msg components.DialogClosedMsg) (Model, tea.Cmd) {
	var cmd tea.Cmd

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
					if !m.config.QualifireEnabled {
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

					err = config.Save(&m.config)
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
				err := config.Save(&m.config)
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
				config.Save(&m.config)
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

		// Forward DialogClosedMsg to scenario editor if on scenarios screen
		// This allows the editor to handle its own dialog-specific logic (e.g., exiting interview mode)
		if m.currentScreen == ScenariosScreen {
			m.scenarioEditor, cmd = m.scenarioEditor.Update(msg)
		}

		m.dialog = nil
	}

	// Handle LLM dialog closure - this should close the LLM dialog
	if m.llmDialog != nil {
		m.llmDialog = nil
	}

	return m, cmd
}

// handleStartInterviewMsg handles starting an interview session
func (m Model) handleStartInterviewMsg(msg scenarios.StartInterviewMsg) (Model, tea.Cmd) {
	return m, m.startInterviewCmd()
}

// handleSendInterviewMessageMsg handles sending an interview message
func (m Model) handleSendInterviewMessageMsg(msg scenarios.SendInterviewMessageMsg) (Model, tea.Cmd) {
	return m, m.sendInterviewMessageCmd(msg.SessionID, msg.Message)
}

// handleInterviewStartedMsg forwards interview started events to scenario editor
func (m Model) handleInterviewStartedMsg(msg scenarios.InterviewStartedMsg) (Model, tea.Cmd) {
	var cmd tea.Cmd
	m.scenarioEditor, cmd = m.scenarioEditor.Update(msg)
	return m, cmd
}

// handleInterviewResponseMsg forwards interview response events to scenario editor
func (m Model) handleInterviewResponseMsg(msg scenarios.InterviewResponseMsg) (Model, tea.Cmd) {
	var cmd tea.Cmd
	m.scenarioEditor, cmd = m.scenarioEditor.Update(msg)
	return m, cmd
}

// handleGenerateScenariosMsg handles scenario generation requests
func (m Model) handleGenerateScenariosMsg(msg scenarios.GenerateScenariosMsg) (Model, tea.Cmd) {
	return m, m.generateScenariosCmd(msg.BusinessContext)
}

// handleScenariosGeneratedMsg forwards generated scenarios to scenario editor
func (m Model) handleScenariosGeneratedMsg(msg scenarios.ScenariosGeneratedMsg) (Model, tea.Cmd) {
	var cmd tea.Cmd
	m.scenarioEditor, cmd = m.scenarioEditor.Update(msg)
	return m, cmd
}

// handleScenarioEditorMsg handles messages from the scenario editor
func (m Model) handleScenarioEditorMsg(msg scenarios.ScenarioEditorMsg) (Model, tea.Cmd) {
	switch msg.Action {
	case "saved":
		// Show success message
		dialog := components.NewInfoDialog(
			"Scenarios Saved",
			"Scenarios have been successfully saved to scenarios.json",
		)
		m.dialog = &dialog
	case "scenarios_generated":
		// Show success message for generated scenarios
		dialog := components.NewInfoDialog(
			"Scenarios Generated",
			"AI has successfully generated scenarios from the interview!",
		)
		m.dialog = &dialog
	case "exit":
		// Exit scenarios screen back to dashboard
		m.currentScreen = DashboardScreen
		m.commandInput.SetFocus(true)
		m.commandInput.SetValue("")
	}
	return m, nil
}
