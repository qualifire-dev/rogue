package tui

import (
	"fmt"

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
			case 0:
				m.evalState.cursorPos = len([]rune(m.evalState.AgentURL))
			case 3:
				m.evalState.cursorPos = len([]rune(m.evalState.JudgeModel))
			default:
				m.evalState.cursorPos = 0
			}
		}
		return m, nil

	case "down":
		if m.evalState.currentField < 6 { // 0-6 fields (AgentURL, Protocol, Transport, JudgeModel, DeepTest, Mode, StartButton)
			m.evalState.currentField++
			// Set cursor to end of field content when switching fields
			switch m.evalState.currentField {
			case 0:
				m.evalState.cursorPos = len([]rune(m.evalState.AgentURL))
			case 3:
				m.evalState.cursorPos = len([]rune(m.evalState.JudgeModel))
			default:
				m.evalState.cursorPos = 0
			}
		}
		return m, nil

	case "left":
		switch m.evalState.currentField {
		case 0, 3: // Text fields: AgentURL, JudgeModel
			if m.evalState.cursorPos > 0 {
				m.evalState.cursorPos--
			}
		case 1: // Protocol dropdown
			m.evalState.cycleProtocol(true) // cycle backwards
		case 2: // Transport dropdown
			m.evalState.cycleTransport(true) // cycle backwards
		case 5: // EvaluationMode dropdown
			m.evalState.cycleEvaluationMode(true) // cycle backwards
		}
		return m, nil

	case "right":
		switch m.evalState.currentField {
		case 0: // AgentURL text field
			fieldLen := len(m.evalState.AgentURL)
			if m.evalState.cursorPos < fieldLen {
				m.evalState.cursorPos++
			}
		case 1: // Protocol dropdown
			m.evalState.cycleProtocol(false) // cycle forwards
		case 2: // Transport dropdown
			m.evalState.cycleTransport(false) // cycle forwards
		case 3: // JudgeModel text field
			fieldLen := len(m.evalState.JudgeModel)
			if m.evalState.cursorPos < fieldLen {
				m.evalState.cursorPos++
			}
		case 5: // EvaluationMode dropdown
			m.evalState.cycleEvaluationMode(false) // cycle forwards
		}
		return m, nil

	case "space":
		if m.evalState.currentField == 4 { // DeepTest field is now index 2
			m.evalState.DeepTest = !m.evalState.DeepTest
			return m, nil
		}

	case "tab":
		// Open LLM config dialog when on Judge Model field
		if m.evalState.currentField == 3 { // JudgeModel field
			llmDialog := components.NewLLMConfigDialog(m.config.APIKeys, m.config.SelectedProvider, m.config.SelectedModel)
			m.llmDialog = &llmDialog
			return m, nil
		}

	case "backspace":
		// Handle backspace for text fields
		if m.evalState.currentField >= 0 {
			switch m.evalState.currentField {
			case 0: // AgentURL
				runes := []rune(m.evalState.AgentURL)
				if m.evalState.cursorPos > 0 && m.evalState.cursorPos <= len(runes) && len(runes) > 0 {
					m.evalState.AgentURL = string(runes[:m.evalState.cursorPos-1]) + string(runes[m.evalState.cursorPos:])
					m.evalState.cursorPos--
				}
			case 3: // JudgeModel
				runes := []rune(m.evalState.JudgeModel)
				if m.evalState.cursorPos > 0 && m.evalState.cursorPos <= len(runes) && len(runes) > 0 {
					m.evalState.JudgeModel = string(runes[:m.evalState.cursorPos-1]) + string(runes[m.evalState.cursorPos:])
					m.evalState.cursorPos--
				}
			case 6: // ParallelRuns (special handling for numbers)
				if m.evalState.ParallelRuns >= 10 {
					m.evalState.ParallelRuns /= 10
					m.evalState.cursorPos--
				} else if m.evalState.ParallelRuns > 0 {
					m.evalState.ParallelRuns = 1 // Don't allow 0
					m.evalState.cursorPos = 0
				}
			}
			return m, nil
		}

	default:
		// insert character into text fields
		s := msg.String()
		if len(s) == 1 {
			switch m.evalState.currentField {
			case 0: // AgentURL
				runes := []rune(m.evalState.AgentURL)
				m.evalState.AgentURL = string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
				m.evalState.cursorPos++
			case 3: // JudgeModel
				runes := []rune(m.evalState.JudgeModel)
				m.evalState.JudgeModel = string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
				m.evalState.cursorPos++
			case 6: // ParallelRuns (numeric only)
				if s[0] >= '0' && s[0] <= '9' {
					numStr := fmt.Sprintf("%d", m.evalState.ParallelRuns)
					runes := []rune(numStr)
					newNumStr := string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
					m.evalState.ParallelRuns = clampToInt(newNumStr)
					m.evalState.cursorPos++
				}
			}
			return m, nil
		}
	}

	return m, nil
}
