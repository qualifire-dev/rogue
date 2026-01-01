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

// EvalField constants for form field indices
// Policy mode: AgentURL(0), Protocol(1), Transport(2), JudgeModel(3), DeepTest(4), EvaluationMode(5), StartButton(6)
// Red Team mode adds: ScanType(6), ConfigureButton(7), StartButton(8)
const (
	EvalFieldAgentURL       = 0
	EvalFieldProtocol       = 1
	EvalFieldTransport      = 2
	EvalFieldJudgeModel     = 3
	EvalFieldDeepTest       = 4
	EvalFieldEvaluationMode = 5
	// Policy mode
	EvalFieldStartButtonPolicy = 6
	// Red Team mode additional fields
	EvalFieldScanType           = 6
	EvalFieldConfigureButton    = 7
	EvalFieldStartButtonRedTeam = 8
)

// ScanType represents the type of red team scan
type ScanType string

const (
	ScanTypeBasic  ScanType = "basic"
	ScanTypeFull   ScanType = "full"
	ScanTypeCustom ScanType = "custom"
)

// RedTeamConfig holds the new vulnerability-centric red team configuration
type RedTeamConfig struct {
	ScanType                ScanType
	Vulnerabilities         []string // Vulnerability IDs to test
	Attacks                 []string // Attack IDs to use
	AttacksPerVulnerability int
	Frameworks              []string // Framework IDs for report mapping
	RandomSeed              *int     // For reproducible tests
}

// EvaluationViewState is defined in tui package to avoid import cycles
type EvaluationViewState struct {
	ServerURL       string // Used from config, not editable in form
	AgentURL        string
	AgentProtocol   Protocol
	AgentTransport  Transport
	JudgeModel      string
	ParallelRuns    int
	DeepTest        bool
	Scenarios       []EvalScenario
	BusinessContext string // Business context for red team attacks

	// Evaluation mode
	EvaluationMode EvaluationMode

	// Red team configuration (new vulnerability-centric approach)
	RedTeamConfig *RedTeamConfig

	// Red team config save notification
	RedTeamConfigSaved    bool
	RedTeamConfigSavedMsg string

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
	// Policy mode: 0: AgentURL, 1: Protocol, 2: Transport, 3: JudgeModel, 4: DeepTest, 5: EvaluationMode, 6: StartButton
	// Red Team mode: 0: AgentURL, 1: Protocol, 2: Transport, 3: JudgeModel, 4: DeepTest, 5: EvaluationMode, 6: ScanType, 7: ConfigureButton, 8: StartButton
	currentField int
	cursorPos    int // rune index in current text field
}

// ScenariosWithContext holds scenarios and business context loaded from file
type ScenariosWithContext struct {
	Scenarios       []EvalScenario
	BusinessContext string
}

// loadScenariosFromWorkdir reads .rogue/scenarios.json upward from CWD
func loadScenariosFromWorkdir() []EvalScenario {
	result := loadScenariosWithContextFromWorkdir()
	return result.Scenarios
}

// loadScenariosWithContextFromWorkdir reads .rogue/scenarios.json and returns both scenarios and business context
func loadScenariosWithContextFromWorkdir() ScenariosWithContext {
	wd, _ := os.Getwd()
	dir := wd
	for {
		p := filepath.Join(dir, ".rogue", "scenarios.json")
		if b, err := os.ReadFile(p); err == nil {
			var v struct {
				BusinessContext *string `json:"business_context"`
				Scenarios       []struct {
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
				businessContext := ""
				if v.BusinessContext != nil {
					businessContext = *v.BusinessContext
				}
				return ScenariosWithContext{
					Scenarios:       out,
					BusinessContext: businessContext,
				}
			}
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	return ScenariosWithContext{}
}

// startEval kicks off evaluation and consumes events into state
func (m *Model) startEval(ctx context.Context, st *EvaluationViewState) {
	// Prepare red team config if in red team mode
	var redTeamConfigMap map[string]interface{}
	if st.EvaluationMode == EvaluationModeRedTeam && st.RedTeamConfig != nil {
		redTeamConfigMap = map[string]interface{}{
			"scan_type":                 string(st.RedTeamConfig.ScanType),
			"vulnerabilities":           st.RedTeamConfig.Vulnerabilities,
			"attacks":                   st.RedTeamConfig.Attacks,
			"attacks_per_vulnerability": st.RedTeamConfig.AttacksPerVulnerability,
			"frameworks":                st.RedTeamConfig.Frameworks,
		}
	}

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
		redTeamConfigMap,
		st.BusinessContext,
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
			// Initialize RedTeamConfig if not set
			if st.RedTeamConfig == nil {
				st.RedTeamConfig = &RedTeamConfig{
					ScanType:                ScanTypeBasic,
					AttacksPerVulnerability: 3,
				}
			}
		}
	} else {
		if st.EvaluationMode == EvaluationModePolicy {
			st.EvaluationMode = EvaluationModeRedTeam
			// Initialize RedTeamConfig if not set
			if st.RedTeamConfig == nil {
				st.RedTeamConfig = &RedTeamConfig{
					ScanType:                ScanTypeBasic,
					AttacksPerVulnerability: 3,
				}
			}
		} else {
			st.EvaluationMode = EvaluationModePolicy
		}
	}
}

// cycleScanType cycles between Basic, Full, and Custom scan types
func (st *EvaluationViewState) cycleScanType(reverse bool) {
	if st.RedTeamConfig == nil {
		st.RedTeamConfig = &RedTeamConfig{
			ScanType:                ScanTypeBasic,
			AttacksPerVulnerability: 3,
		}
	}

	scanTypes := []ScanType{ScanTypeBasic, ScanTypeFull, ScanTypeCustom}
	currentIdx := 0
	for i, s := range scanTypes {
		if s == st.RedTeamConfig.ScanType {
			currentIdx = i
			break
		}
	}

	if reverse {
		currentIdx--
		if currentIdx < 0 {
			currentIdx = len(scanTypes) - 1
		}
	} else {
		currentIdx++
		if currentIdx >= len(scanTypes) {
			currentIdx = 0
		}
	}

	st.RedTeamConfig.ScanType = scanTypes[currentIdx]
}

// getMaxFieldIndex returns the maximum field index based on the current evaluation mode
// Policy mode: 6 (StartButton)
// Red Team mode: 8 (StartButton after ScanType and Configure)
func (st *EvaluationViewState) getMaxFieldIndex() int {
	if st.EvaluationMode == EvaluationModeRedTeam {
		return 8 // ScanType at 6, Configure at 7, StartButton at 8
	}
	return 6 // StartButton at 6
}

// getStartButtonIndex returns the index of the start button based on evaluation mode
func (st *EvaluationViewState) getStartButtonIndex() int {
	if st.EvaluationMode == EvaluationModeRedTeam {
		return 8
	}
	return 6
}

// getConfigureButtonIndex returns the index of the configure button (only for red team mode)
func (st *EvaluationViewState) getConfigureButtonIndex() int {
	return 7 // Only valid in red team mode
}
