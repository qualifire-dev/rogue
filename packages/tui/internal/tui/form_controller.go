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
			// Set cursor to end of field content when switching fields
			switch m.evalState.currentField {
			case EvalFieldAgentURL:
				m.evalState.cursorPos = len([]rune(m.evalState.AgentURL))
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
			// Set cursor to end of field content when switching fields
			switch m.evalState.currentField {
			case EvalFieldAgentURL:
				m.evalState.cursorPos = len([]rune(m.evalState.AgentURL))
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
		case EvalFieldTransport:
			m.evalState.cycleTransport(true) // cycle backwards
		case EvalFieldEvaluationMode:
			m.evalState.cycleEvaluationMode(true) // cycle backwards
		case EvalFieldScanType: // ScanType dropdown (only in Red Team mode)
			if m.evalState.EvaluationMode == EvaluationModeRedTeam {
				m.evalState.cycleScanType(true) // cycle backwards
			}
		}
		return m, nil

	case "right":
		// Clear the red team config saved banner when user starts interacting
		m.evalState.RedTeamConfigSaved = false
		switch m.evalState.currentField {
		case EvalFieldAgentURL:
			fieldLen := len(m.evalState.AgentURL)
			if m.evalState.cursorPos < fieldLen {
				m.evalState.cursorPos++
			}
		case EvalFieldProtocol:
			m.evalState.cycleProtocol(false) // cycle forwards
		case EvalFieldTransport:
			m.evalState.cycleTransport(false) // cycle forwards
		case EvalFieldJudgeModel:
			fieldLen := len(m.evalState.JudgeModel)
			if m.evalState.cursorPos < fieldLen {
				m.evalState.cursorPos++
			}
		case EvalFieldEvaluationMode:
			m.evalState.cycleEvaluationMode(false) // cycle forwards
		case EvalFieldScanType: // ScanType dropdown (only in Red Team mode)
			if m.evalState.EvaluationMode == EvaluationModeRedTeam {
				m.evalState.cycleScanType(false) // cycle forwards
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
				runes := []rune(m.evalState.AgentURL)
				if m.evalState.cursorPos > 0 && m.evalState.cursorPos <= len(runes) && len(runes) > 0 {
					m.evalState.AgentURL = string(runes[:m.evalState.cursorPos-1]) + string(runes[m.evalState.cursorPos:])
					m.evalState.cursorPos--
				}
			case EvalFieldJudgeModel:
				runes := []rune(m.evalState.JudgeModel)
				if m.evalState.cursorPos > 0 && m.evalState.cursorPos <= len(runes) && len(runes) > 0 {
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
				runes := []rune(m.evalState.AgentURL)
				m.evalState.AgentURL = string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
				m.evalState.cursorPos++
			case EvalFieldJudgeModel:
				runes := []rune(m.evalState.JudgeModel)
				m.evalState.JudgeModel = string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
				m.evalState.cursorPos++
			}
			return m, nil
		}
	}

	return m, nil
}
