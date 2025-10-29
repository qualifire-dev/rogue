package scenarios

// ScenarioData represents a single scenario aligned with Python schema
type ScenarioData struct {
	Scenario          string  `json:"scenario"`
	ScenarioType      string  `json:"scenario_type"`
	Dataset           *string `json:"dataset"`
	ExpectedOutcome   *string `json:"expected_outcome"`
	DatasetSampleSize *int    `json:"dataset_sample_size"`
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
