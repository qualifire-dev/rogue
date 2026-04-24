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
