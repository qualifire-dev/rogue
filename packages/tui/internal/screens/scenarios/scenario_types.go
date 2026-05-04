package scenarios

// ScenarioData represents a single scenario aligned with Python schema
type ScenarioData struct {
	Scenario          string  `json:"scenario"`
	ScenarioType      string  `json:"scenario_type"`
	Dataset           *string `json:"dataset,omitempty"`
	ExpectedOutcome   *string `json:"expected_outcome,omitempty"`
	DatasetSampleSize *int    `json:"dataset_sample_size,omitempty"`
	// MultiTurn (nullable to distinguish "missing in old JSON" from "explicit false").
	// Callers that read a ScenarioData should use MultiTurnEnabled() / MaxTurnsValue()
	// to apply defaults (multi_turn=true, max_turns=10).
	MultiTurn *bool `json:"multi_turn,omitempty"`
	MaxTurns  *int  `json:"max_turns,omitempty"`
	// AvailableKwargs is the pool of side-data keys/values the multi-turn driver
	// may attach per turn. Forwarded only to PYTHON-protocol targets; ignored
	// elsewhere. Empty/nil means no kwargs available.
	AvailableKwargs map[string]any `json:"available_kwargs,omitempty"`
	// FilePath is a convenience top-level path (e.g. an artifact to upload).
	// When set, the driver always sees ``file_path`` as an available kwarg.
	// An explicit ``file_path`` entry in AvailableKwargs takes precedence.
	FilePath *string `json:"file_path,omitempty"`
	// Attempts is the number of independent conversations to run for this
	// scenario. Variation between attempts comes from stochastic sampling
	// in the multi-turn driver. The scenario passes only if EVERY attempt
	// passes — see ``EvaluationResults.add_result`` on the server side.
	// Nullable to distinguish "missing in old JSON" from "explicit 1";
	// callers should use AttemptsValue().
	Attempts *int `json:"attempts,omitempty"`
	// Temperature is an optional driver-LLM sampling temperature override.
	// nil (omitted) means use the driver default (0.7). The TUI editor
	// doesn't expose this knob (no float-text widget) but the field
	// roundtrips on disk so a value set via the SPA isn't lost when the
	// TUI rewrites scenarios.json.
	Temperature *float64 `json:"temperature,omitempty"`
}

// MultiTurnDefault is the default for new / legacy scenarios (multi-turn on).
const MultiTurnDefault = true

// MaxTurnsDefault is the default stop condition when not specified.
const MaxTurnsDefault = 10

// MaxTurnsMin / MaxTurnsMax bracket the allowed range (matches Python Pydantic bounds).
const (
	MaxTurnsMin = 1
	MaxTurnsMax = 100
)

// AttemptsDefault is the default scenario attempt count (single conversation).
const AttemptsDefault = 1

// AttemptsMin / AttemptsMax bracket the allowed range (matches Python Pydantic bounds).
const (
	AttemptsMin = 1
	AttemptsMax = 20
)

// MultiTurnEnabled returns the effective multi-turn flag, applying the default
// when the field was absent in the source JSON.
func (s ScenarioData) MultiTurnEnabled() bool {
	if s.MultiTurn == nil {
		return MultiTurnDefault
	}
	return *s.MultiTurn
}

// MaxTurnsValue returns the effective max-turns value, applying the default
// when the field was absent in the source JSON.
func (s ScenarioData) MaxTurnsValue() int {
	if s.MaxTurns == nil {
		return MaxTurnsDefault
	}
	return *s.MaxTurns
}

// AttemptsValue returns the effective attempt count, applying the default
// when the field was absent in the source JSON.
func (s ScenarioData) AttemptsValue() int {
	if s.Attempts == nil {
		return AttemptsDefault
	}
	return *s.Attempts
}

// ScenariosFile represents the JSON file structure
type ScenariosFile struct {
	BusinessContext *string        `json:"business_context"`
	Scenarios       []ScenarioData `json:"scenarios"`
}

// ScenarioEditorMode represents the current mode of the editor
type ScenarioEditorMode int

const (
	ListMode ScenarioEditorMode = iota
	EditMode
	AddMode
	BusinessContextMode
	InterviewMode
)

// ScenarioEditorMsg represents messages from the scenario editor
type ScenarioEditorMsg struct {
	Action string
	Data   any
}

// InterviewMessage represents a message in the interview conversation

// Interview-related message types
type StartInterviewMsg struct{}

type InterviewStartedMsg struct {
	SessionID      string
	InitialMessage string
	Error          error
}

type InterviewResponseMsg struct {
	Response     string
	IsComplete   bool
	MessageCount int
	Error        error
}

type ScenariosGeneratedMsg struct {
	Scenarios       []ScenarioData
	BusinessContext string
	Error           error
}

type SendInterviewMessageMsg struct {
	SessionID string
	Message   string
}

type GenerateScenariosMsg struct {
	BusinessContext string
}
