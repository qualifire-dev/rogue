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
			case 1:
				m.evalState.cursorPos = len([]rune(m.evalState.JudgeModel))
			default:
				m.evalState.cursorPos = 0
			}
		}
		return m, nil

	case "down":
		if m.evalState.currentField < 3 { // Now includes start button (0-3)
			m.evalState.currentField++
			// Set cursor to end of field content when switching fields
			switch m.evalState.currentField {
			case 0:
				m.evalState.cursorPos = len([]rune(m.evalState.AgentURL))
			case 1:
				m.evalState.cursorPos = len([]rune(m.evalState.JudgeModel))
			default:
				m.evalState.cursorPos = 0
			}
		}
		return m, nil

	case "left":
		if m.evalState.currentField <= 1 && m.evalState.cursorPos > 0 { // Text fields 0-2
			m.evalState.cursorPos--
		}
		return m, nil

	case "right":
		if m.evalState.currentField <= 1 { // Text fields 0-1
			// Get current field length to limit cursor
			var fieldLen int
			switch m.evalState.currentField {
			case 0:
				fieldLen = len(m.evalState.AgentURL)
			case 1:
				fieldLen = len(m.evalState.JudgeModel)
			case 2:
				fieldLen = len(fmt.Sprintf("%d", m.evalState.ParallelRuns))
			}
			if m.evalState.cursorPos < fieldLen {
				m.evalState.cursorPos++
			}
		}
		return m, nil

	case "space":
		if m.evalState.currentField == 2 { // DeepTest field is now index 2
			m.evalState.DeepTest = !m.evalState.DeepTest
			return m, nil
		}

	case "tab":
		// Open LLM config dialog when on Judge Model field
		if m.evalState.currentField == 1 { // JudgeModel field
			llmDialog := components.NewLLMConfigDialog(m.config.APIKeys, m.config.SelectedProvider, m.config.SelectedModel)
			m.llmDialog = &llmDialog
			return m, nil
		}

	case "backspace":
		// Handle backspace for text fields
		if m.evalState.currentField <= 1 && m.evalState.cursorPos > 0 {
			switch m.evalState.currentField {
			case 0: // AgentURL
				runes := []rune(m.evalState.AgentURL)
				if m.evalState.cursorPos <= len(runes) {
					m.evalState.AgentURL = string(runes[:m.evalState.cursorPos-1]) + string(runes[m.evalState.cursorPos:])
					m.evalState.cursorPos--
				}
			case 1: // JudgeModel
				runes := []rune(m.evalState.JudgeModel)
				if m.evalState.cursorPos <= len(runes) {
					m.evalState.JudgeModel = string(runes[:m.evalState.cursorPos-1]) + string(runes[m.evalState.cursorPos:])
					m.evalState.cursorPos--
				}
			case 2: // ParallelRuns (special handling for numbers)
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
		if len(s) == 1 && m.evalState.currentField <= 2 { // Text fields 0-2
			switch m.evalState.currentField {
			case 0: // AgentURL
				runes := []rune(m.evalState.AgentURL)
				m.evalState.AgentURL = string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
				m.evalState.cursorPos++
			case 1: // JudgeModel
				runes := []rune(m.evalState.JudgeModel)
				m.evalState.JudgeModel = string(runes[:m.evalState.cursorPos]) + s + string(runes[m.evalState.cursorPos:])
				m.evalState.cursorPos++
			case 2: // ParallelRuns (numeric only)
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
