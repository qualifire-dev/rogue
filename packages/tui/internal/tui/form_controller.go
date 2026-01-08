package tui

import (
	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/rogue/tui/internal/components"
)

// HandleEvalFormInput handles keyboard input for the new evaluation form
func HandleEvalFormInput(m Model, msg tea.KeyMsg) (Model, tea.Cmd) {
	if m.evalState == nil {
		return m, nil
	}

	switch msg.String() {
	case "t":
		// Start health check spinner and background health check
		m.healthSpinner.SetActive(true)
		return m, tea.Batch(m.healthSpinner.Start(), m.healthCheckCmd())

	case "up":
		// Clear the red team config saved banner when navigating
		m.evalState.RedTeamConfigSaved = false
		if m.evalState.currentField > 0 {
			m.evalState.currentField--
			// Skip Transport field for Python protocol
			if m.evalState.AgentProtocol == ProtocolPython && m.evalState.currentField == EvalFieldTransport {
				m.evalState.currentField--
			}
			// Set cursor to end of field content when switching fields
			switch m.evalState.currentField {
			case EvalFieldAgentURL:
				if m.evalState.AgentProtocol == ProtocolPython {
					m.evalState.cursorPos = len([]rune(m.evalState.PythonEntrypointFile))
				} else {
					m.evalState.cursorPos = len([]rune(m.evalState.AgentURL))
				}
			case EvalFieldJudgeModel:
				m.evalState.cursorPos = len([]rune(m.evalState.JudgeModel))
			default:
				m.evalState.cursorPos = 0
			}
		}
		return m, nil

	case "down":
		// Clear the red team config saved banner when navigating
		m.evalState.RedTeamConfigSaved = false
		// Use dynamic max field index based on evaluation mode
		maxFieldIndex := m.evalState.getMaxFieldIndex()
		if m.evalState.currentField < maxFieldIndex {
			m.evalState.currentField++
			// Skip Transport field for Python protocol
			if m.evalState.AgentProtocol == ProtocolPython && m.evalState.currentField == EvalFieldTransport {
				m.evalState.currentField++
			}
			// Set cursor to end of field content when switching fields
			switch m.evalState.currentField {
			case EvalFieldAgentURL:
				if m.evalState.AgentProtocol == ProtocolPython {
					m.evalState.cursorPos = len([]rune(m.evalState.PythonEntrypointFile))
				} else {
					m.evalState.cursorPos = len([]rune(m.evalState.AgentURL))
				}
			case EvalFieldJudgeModel:
				m.evalState.cursorPos = len([]rune(m.evalState.JudgeModel))
			default:
				m.evalState.cursorPos = 0
			}
		}
		return m, nil

	case "left":
		// Clear the red team config saved banner when user starts interacting
		m.evalState.RedTeamConfigSaved = false
		switch m.evalState.currentField {
		case EvalFieldAgentURL, EvalFieldJudgeModel: // Text fields
			if m.evalState.cursorPos > 0 {
				m.evalState.cursorPos--
			}
		case EvalFieldProtocol:
			m.evalState.cycleProtocol(true) // cycle backwards
			// Save config after protocol change
			go saveUserConfig(
				m.evalState.AgentProtocol,
				m.evalState.AgentTransport,
				m.evalState.AgentURL,
				m.evalState.PythonEntrypointFile,
				m.evalState.EvaluationMode,
				m.getScanType(),
			)
		case EvalFieldTransport:
			m.evalState.cycleTransport(true) // cycle backwards
			// Save config after transport change
			go saveUserConfig(
				m.evalState.AgentProtocol,
				m.evalState.AgentTransport,
				m.evalState.AgentURL,
				m.evalState.PythonEntrypointFile,
				m.evalState.EvaluationMode,
				m.getScanType(),
			)
		case EvalFieldEvaluationMode:
			m.evalState.cycleEvaluationMode(true) // cycle backwards
			// Save config after evaluation mode change
			go saveUserConfig(
				m.evalState.AgentProtocol,
				m.evalState.AgentTransport,
				m.evalState.AgentURL,
				m.evalState.PythonEntrypointFile,
				m.evalState.EvaluationMode,
				m.getScanType(),
			)
		case EvalFieldScanType: // ScanType dropdown (only in Red Team mode)
			if m.evalState.EvaluationMode == EvaluationModeRedTeam {
				m.evalState.cycleScanType(true) // cycle backwards
				// Apply preset for the new scan type
				m.applyPresetForScanType()
				// Save config after scan type change
				go saveUserConfig(
					m.evalState.AgentProtocol,
					m.evalState.AgentTransport,
					m.evalState.AgentURL,
					m.evalState.PythonEntrypointFile,
					m.evalState.EvaluationMode,
					m.getScanType(),
				)
			}
		}
		return m, nil

	case "right":
		// Clear the red team config saved banner when user starts interacting
		m.evalState.RedTeamConfigSaved = false
		switch m.evalState.currentField {
		case EvalFieldAgentURL:
			var fieldLen int
			if m.evalState.AgentProtocol == ProtocolPython {
				fieldLen = len(m.evalState.PythonEntrypointFile)
			} else {
				fieldLen = len(m.evalState.AgentURL)
			}
			if m.evalState.cursorPos < fieldLen {
				m.evalState.cursorPos++
			}
		case EvalFieldProtocol:
			m.evalState.cycleProtocol(false) // cycle forwards
			// Save config after protocol change
			go saveUserConfig(
				m.evalState.AgentProtocol,
				m.evalState.AgentTransport,
				m.evalState.AgentURL,
				m.evalState.PythonEntrypointFile,
				m.evalState.EvaluationMode,
				m.getScanType(),
			)
		case EvalFieldTransport:
			m.evalState.cycleTransport(false) // cycle forwards
			// Save config after transport change
			go saveUserConfig(
				m.evalState.AgentProtocol,
				m.evalState.AgentTransport,
				m.evalState.AgentURL,
				m.evalState.PythonEntrypointFile,
				m.evalState.EvaluationMode,
				m.getScanType(),
			)
		case EvalFieldJudgeModel:
			fieldLen := len(m.evalState.JudgeModel)
			if m.evalState.cursorPos < fieldLen {
				m.evalState.cursorPos++
			}
		case EvalFieldEvaluationMode:
			m.evalState.cycleEvaluationMode(false) // cycle forwards
			// Save config after evaluation mode change
			go saveUserConfig(
				m.evalState.AgentProtocol,
				m.evalState.AgentTransport,
				m.evalState.AgentURL,
				m.evalState.PythonEntrypointFile,
				m.evalState.EvaluationMode,
				m.getScanType(),
			)
		case EvalFieldScanType: // ScanType dropdown (only in Red Team mode)
			if m.evalState.EvaluationMode == EvaluationModeRedTeam {
				m.evalState.cycleScanType(false) // cycle forwards
				// Apply preset for the new scan type
				m.applyPresetForScanType()
				// Save config after scan type change
				go saveUserConfig(
					m.evalState.AgentProtocol,
					m.evalState.AgentTransport,
					m.evalState.AgentURL,
					m.evalState.PythonEntrypointFile,
					m.evalState.EvaluationMode,
					m.getScanType(),
				)
			}
		}
		return m, nil

	case "space":
		if m.evalState.currentField == EvalFieldDeepTest {
			m.evalState.DeepTest = !m.evalState.DeepTest
			return m, nil
		}

	case "tab":
		// Open LLM config dialog when on Judge Model field
		if m.evalState.currentField == EvalFieldJudgeModel {
			llmDialog := components.NewLLMConfigDialog(m.config.APIKeys, m.config.SelectedProvider, m.config.SelectedModel)
			m.llmDialog = &llmDialog
			return m, nil
		}

	case "backspace":
		// Handle backspace for text fields
		if m.evalState.currentField >= 0 {
			switch m.evalState.currentField {
			case EvalFieldAgentURL:
				if m.evalState.AgentProtocol == ProtocolPython {
					runes := []rune(m.evalState.PythonEntrypointFile)
					// Clamp cursor position to valid range
					if m.evalState.cursorPos > len(runes) {
						m.evalState.cursorPos = len(runes)
					}
					if m.evalState.cursorPos > 0 && len(runes) > 0 {
						m.evalState.PythonEntrypointFile = string(runes[:m.evalState.cursorPos-1]) + string(runes[m.evalState.cursorPos:])
						m.evalState.cursorPos--
						// Save config after text change
						go saveUserConfig(
							m.evalState.AgentProtocol,
							m.evalState.AgentTransport,
							m.evalState.AgentURL,
							m.evalState.PythonEntrypointFile,
							m.evalState.EvaluationMode,
							m.getScanType(),
						)
					}
				} else {
					runes := []rune(m.evalState.AgentURL)
					// Clamp cursor position to valid range
					if m.evalState.cursorPos > len(runes) {
						m.evalState.cursorPos = len(runes)
					}
					if m.evalState.cursorPos > 0 && len(runes) > 0 {
						m.evalState.AgentURL = string(runes[:m.evalState.cursorPos-1]) + string(runes[m.evalState.cursorPos:])
						m.evalState.cursorPos--
						// Save config after text change
						go saveUserConfig(
							m.evalState.AgentProtocol,
							m.evalState.AgentTransport,
							m.evalState.AgentURL,
							m.evalState.PythonEntrypointFile,
							m.evalState.EvaluationMode,
							m.getScanType(),
						)
					}
				}
			case EvalFieldJudgeModel:
				runes := []rune(m.evalState.JudgeModel)
				// Clamp cursor position to valid range
				if m.evalState.cursorPos > len(runes) {
					m.evalState.cursorPos = len(runes)
				}
				if m.evalState.cursorPos > 0 && len(runes) > 0 {
					m.evalState.JudgeModel = string(runes[:m.evalState.cursorPos-1]) + string(runes[m.evalState.cursorPos:])
					m.evalState.cursorPos--
				}
			}
			return m, nil
		}

	default:
		// insert character into text fields
		s := msg.String()
		if len(s) == 1 {
			switch m.evalState.currentField {
			case EvalFieldAgentURL:
				if m.evalState.AgentProtocol == ProtocolPython {
					runes := []rune(m.evalState.PythonEntrypointFile)
					// Clamp cursor position to valid range
					if m.evalState.cursorPos > len(runes) {
						m.evalState.cursorPos = len(runes)
					}
					m.evalState.PythonEntrypointFile = string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
				} else {
					runes := []rune(m.evalState.AgentURL)
					// Clamp cursor position to valid range
					if m.evalState.cursorPos > len(runes) {
						m.evalState.cursorPos = len(runes)
					}
					m.evalState.AgentURL = string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
				}
				m.evalState.cursorPos++
				// Save config after text change
				go saveUserConfig(
					m.evalState.AgentProtocol,
					m.evalState.AgentTransport,
					m.evalState.AgentURL,
					m.evalState.PythonEntrypointFile,
					m.evalState.EvaluationMode,
					m.getScanType(),
				)
			case EvalFieldJudgeModel:
				runes := []rune(m.evalState.JudgeModel)
				// Clamp cursor position to valid range
				if m.evalState.cursorPos > len(runes) {
					m.evalState.cursorPos = len(runes)
				}
				m.evalState.JudgeModel = string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
				m.evalState.cursorPos++
			}
			return m, nil
		}
	}

	return m, nil
}
