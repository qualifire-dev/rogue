package tui

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Minimal state for eval screens
type EvaluationViewState struct {
	ServerURL    string // Used from config, not editable in form
	AgentURL     string
	JudgeModel   string
	ParallelRuns int
	DeepTest     bool
	Scenarios    []string

	// Runtime
	Running  bool
	Progress float64
	Status   string
	Events   []EvaluationEvent
	cancelFn func() error

	// Report generation
	Summary   string // Generated markdown summary
	JobID     string // For tracking the evaluation job
	Completed bool   // Whether evaluation finished successfully

	// Editing state for New Evaluation
	currentField int // 0: AgentURL, 1: JudgeModel, 2: ParallelRuns, 3: DeepTest, 4: StartButton
	cursorPos    int // rune index in current text field
}

// loadScenariosFromWorkdir reads .rogue/scenarios.json upward from CWD
func loadScenariosFromWorkdir() []string {
	wd, _ := os.Getwd()
	dir := wd
	for {
		p := filepath.Join(dir, ".rogue", "scenarios.json")
		if b, err := os.ReadFile(p); err == nil {
			var v struct {
				Scenarios []struct {
					Scenario string `json:"scenario"`
				} `json:"scenarios"`
			}
			if json.Unmarshal(b, &v) == nil {
				out := make([]string, 0, len(v.Scenarios))
				for _, s := range v.Scenarios {
					if s.Scenario != "" {
						out = append(out, s.Scenario)
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
	ch, cancel, err := m.StartEvaluation(ctx, st.ServerURL, st.AgentURL, st.Scenarios, st.JudgeModel, st.ParallelRuns, st.DeepTest)
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

// triggerSummaryGeneration generates summary for completed evaluation
func (m *Model) triggerSummaryGeneration() {
	if m.evalState == nil || m.evalState.JobID == "" || !m.evalState.Completed {
		return
	}

	// Don't regenerate if we already have a summary
	if m.evalState.Summary != "" {
		return
	}

	go func() {
		sdk := NewRogueSDK(m.config.ServerURL)

		// Use the judge model and API key from config
		judgeModel := m.evalState.JudgeModel
		var apiKey string

		// Extract provider from judge model (e.g. "openai/gpt-4" -> "openai")
		if parts := strings.Split(judgeModel, "/"); len(parts) >= 2 {
			provider := parts[0]
			if key, ok := m.config.APIKeys[provider]; ok {
				apiKey = key
			}
		}

		// Create a context with longer timeout for summary generation
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
		defer cancel()

		summary, err := sdk.GenerateSummary(ctx, m.evalState.JobID, judgeModel, apiKey)
		if err != nil {
			// Set error message as summary
			m.evalState.Summary = fmt.Sprintf("# Summary Generation Failed\n\nError: %v", err)
		} else {
			m.evalState.Summary = summary
		}
	}()
}

// placeholder tick for periodic UI updates while running
// Note: actual Bubble Tea cmds will be wired in the TUI update loop where tea is imported
func (m *Model) evalTick() {
	time.Sleep(300 * time.Millisecond)
}
