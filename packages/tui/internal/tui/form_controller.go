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
		if m.evalState.currentField < EvalFieldStartButton {
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
		switch m.evalState.currentField {
		case EvalFieldAgentURL, EvalFieldJudgeModel: // Text fields
			if m.evalState.cursorPos > 0 {
				m.evalState.cursorPos--
			}
		case EvalFieldProtocol: // Protocol dropdown
			m.evalState.cycleProtocol(true) // cycle backwards
		case EvalFieldTransport: // Transport dropdown
			m.evalState.cycleTransport(true) // cycle backwards
		}
		return m, nil

	case "right":
		switch m.evalState.currentField {
		case EvalFieldAgentURL: // AgentURL text field
			fieldLen := len(m.evalState.AgentURL)
			if m.evalState.cursorPos < fieldLen {
				m.evalState.cursorPos++
			}
		case EvalFieldProtocol: // Protocol dropdown
			m.evalState.cycleProtocol(false) // cycle forwards
		case EvalFieldTransport: // Transport dropdown
			m.evalState.cycleTransport(false) // cycle forwards
		case EvalFieldJudgeModel: // JudgeModel text field
			fieldLen := len(m.evalState.JudgeModel)
			if m.evalState.cursorPos < fieldLen {
				m.evalState.cursorPos++
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
