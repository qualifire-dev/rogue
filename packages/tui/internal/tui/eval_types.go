package tui

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
)

type Protocol string

const (
	ProtocolA2A Protocol = "a2a"
	ProtocolMCP Protocol = "mcp"
)

type Transport string

const (
	// mcp transports
	TransportSSE            Transport = "sse"
	TransportStreamableHTTP Transport = "streamable_http"

	// a2a transports
	TransportHTTP Transport = "http"
)

type EvaluationMode string

const (
	EvaluationModePolicy  EvaluationMode = "policy"
	EvaluationModeRedTeam EvaluationMode = "red_team"
)

// EvaluationViewState is defined in tui package to avoid import cycles
type EvaluationViewState struct {
	ServerURL      string // Used from config, not editable in form
	AgentURL       string
	AgentProtocol  Protocol
	AgentTransport Transport
	JudgeModel     string
	ParallelRuns   int
	DeepTest       bool
	Scenarios      []EvalScenario

	// Red teaming mode
	EvaluationMode     EvaluationMode
	OWASPCategories    []string // e.g., ["LLM_01", "LLM_06", "LLM_07"]
	AttacksPerCategory int

	// Runtime
	Running  bool
	Progress float64
	Status   string
	Events   []EvaluationEvent
	cancelFn func() error

	// Report generation
	Summary           string // Generated markdown summary
	JobID             string // For tracking the evaluation job
	Completed         bool   // Whether evaluation finished successfully
	SummaryGenerated  bool   // Whether summary generation was already attempted
	StructuredSummary StructuredSummary

	// Editing state for New Evaluation
	currentField int // 0: AgentURL, 1: Protocol, 2: Transport, 3: JudgeModel, 4: DeepTest, 5: EvaluationMode, 6: StartButton
	cursorPos    int // rune index in current text field
}

// loadScenariosFromWorkdir reads .rogue/scenarios.json upward from CWD
func loadScenariosFromWorkdir() []EvalScenario {
	wd, _ := os.Getwd()
	dir := wd
	for {
		p := filepath.Join(dir, ".rogue", "scenarios.json")
		if b, err := os.ReadFile(p); err == nil {
			var v struct {
				Scenarios []struct {
					Scenario        string `json:"scenario"`
					ScenarioType    string `json:"scenario_type"`
					ExpectedOutcome string `json:"expected_outcome"`
				} `json:"scenarios"`
			}
			if json.Unmarshal(b, &v) == nil {
				out := make([]EvalScenario, 0, len(v.Scenarios))
				for _, s := range v.Scenarios {
					if s.Scenario != "" {
						out = append(out, EvalScenario{
							Scenario:        s.Scenario,
							ScenarioType:    s.ScenarioType,
							ExpectedOutcome: s.ExpectedOutcome,
						})
					}
				}
				return out
			}
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	return nil
}

// startEval kicks off evaluation and consumes events into state
func (m *Model) startEval(ctx context.Context, st *EvaluationViewState) {
	ch, cancel, err := m.StartEvaluation(
		ctx,
		st.ServerURL,
		st.AgentURL,
		st.AgentProtocol,
		st.AgentTransport,
		st.Scenarios,
		st.JudgeModel,
		st.ParallelRuns,
		st.DeepTest,
		string(st.EvaluationMode),
		st.OWASPCategories,
		st.AttacksPerCategory,
	)
	if err != nil {
		st.Running = false
		st.Status = "error"
		st.Events = append(st.Events, EvaluationEvent{Type: "error", Message: err.Error()})
		return
	}
	st.Running = true
	st.cancelFn = cancel
	go func() {
		defer cancel()
		for ev := range ch {
			st.Events = append(st.Events, ev)
			if ev.Type == "status" {
				st.Status = ev.Status
				st.Progress = ev.Progress

				// Store job ID from first event
				if st.JobID == "" && ev.JobID != "" {
					st.JobID = ev.JobID
				}

				// Check if evaluation completed
				if ev.Status == "completed" {
					st.Completed = true
					// TODO: Auto-generate summary and show in evaluation view
				}
			}
			// TODO: trigger repaint via program.Send in future
			// For now, this will update the state but UI won't refresh until next user input
		}
		st.Running = false
	}()
}

// triggerSummaryGeneration triggers automatic summary generation for completed evaluation
func (m *Model) triggerSummaryGeneration() {
	if m.evalState == nil || m.evalState.JobID == "" || !m.evalState.Completed {
		return
	}

	// Don't regenerate if we already have a summary
	if m.evalState.Summary != "" {
		return
	}

	// Start spinner for automatic summary generation
	m.summarySpinner.SetActive(true)
}

// getAllProtocols returns all available protocol options
func getAllProtocols() []Protocol {
	return []Protocol{ProtocolA2A, ProtocolMCP}
}

// getTransportsForProtocol returns valid transport options for a given protocol
func getTransportsForProtocol(protocol Protocol) []Transport {
	switch protocol {
	case ProtocolMCP:
		return []Transport{TransportStreamableHTTP, TransportSSE}
	case ProtocolA2A:
		return []Transport{TransportHTTP}
	default:
		return []Transport{}
	}
}

// cycleProtocol cycles to the next protocol option
func (st *EvaluationViewState) cycleProtocol(reverse bool) {
	protocols := getAllProtocols()
	currentIdx := -1
	for i, p := range protocols {
		if p == st.AgentProtocol {
			currentIdx = i
			break
		}
	}

	if reverse {
		currentIdx--
		if currentIdx < 0 {
			currentIdx = len(protocols) - 1
		}
	} else {
		currentIdx++
		if currentIdx >= len(protocols) {
			currentIdx = 0
		}
	}

	st.AgentProtocol = protocols[currentIdx]
	// Reset transport to first valid option for new protocol
	validTransports := getTransportsForProtocol(st.AgentProtocol)
	if len(validTransports) > 0 {
		st.AgentTransport = validTransports[0]
	}
}

// cycleTransport cycles to the next transport option for the current protocol
func (st *EvaluationViewState) cycleTransport(reverse bool) {
	transports := getTransportsForProtocol(st.AgentProtocol)
	if len(transports) == 0 {
		return
	}

	currentIdx := -1
	for i, t := range transports {
		if t == st.AgentTransport {
			currentIdx = i
			break
		}
	}

	if reverse {
		currentIdx--
		if currentIdx < 0 {
			currentIdx = len(transports) - 1
		}
	} else {
		currentIdx++
		if currentIdx >= len(transports) {
			currentIdx = 0
		}
	}

	st.AgentTransport = transports[currentIdx]
}

// cycleEvaluationMode cycles between Policy and Red Team modes
func (st *EvaluationViewState) cycleEvaluationMode(reverse bool) {
	if reverse {
		if st.EvaluationMode == EvaluationModeRedTeam {
			st.EvaluationMode = EvaluationModePolicy
		} else {
			st.EvaluationMode = EvaluationModeRedTeam
			// Default OWASP categories if none set
			if len(st.OWASPCategories) == 0 {
				st.OWASPCategories = []string{"LLM_01", "LLM_06", "LLM_07"}
			}
		}
	} else {
		if st.EvaluationMode == EvaluationModePolicy {
			st.EvaluationMode = EvaluationModeRedTeam
			// Default OWASP categories if none set
			if len(st.OWASPCategories) == 0 {
				st.OWASPCategories = []string{"LLM_01", "LLM_06", "LLM_07"}
			}
		} else {
			st.EvaluationMode = EvaluationModePolicy
		}
	}
}
