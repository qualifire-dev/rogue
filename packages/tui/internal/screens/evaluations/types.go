package evaluations

// FormField represents the field indices for the evaluation form
// These constants mirror the EvalFormField constants in the tui package
// to avoid import cycles while maintaining consistency
type FormField int

const (
	FormFieldProtocol FormField = iota
	FormFieldAgentURL           // Also used for PythonEntrypointFile when protocol is Python
	FormFieldTransport
	FormFieldAuthType        // Skipped for Python protocol
	FormFieldAuthCredentials // Skipped for Python protocol; skipped when AuthType is no_auth
	FormFieldJudgeModel
	FormFieldDeepTest
	FormFieldEvaluationMode
	// Policy mode start button / Red Team mode scan type (both at index 8)
	FormFieldStartButtonPolicy
	FormFieldConfigureButton    // 9 - Red Team mode only
	FormFieldStartButtonRedTeam // 10 - Red Team mode only
)

// FormFieldScanType is an alias - in Red Team mode, index 8 is the scan type field
const FormFieldScanType = FormFieldStartButtonPolicy

// FormState contains all data needed to render the evaluation form
type FormState struct {
	// Dimensions
	Width  int
	Height int

	// Form fields
	AgentURL             string
	Protocol             string
	Transport            string
	AuthType             string // "no_auth", "api_key", "bearer_token", "basic"
	AuthCredentials      string // Credential value (API key, token, or base64 username:password)
	PythonEntrypointFile string // Path to Python file with call_agent function (for Python protocol)
	JudgeModel           string
	DeepTest             bool
	ServerURL            string
	ScenariosCount       int
	EvaluationMode       string
	ScanType             string // "basic", "full", or "custom" (only shown in Red Team mode)

	// Editing state
	// Policy mode: 0: Protocol, 1: AgentURL/PythonFile, 2: Transport, 3: AuthType, 4: AuthCredentials, 5: JudgeModel, 6: DeepTest, 7: EvaluationMode, 8: StartButton
	// Red Team mode: 0: Protocol, 1: AgentURL/PythonFile, 2: Transport, 3: AuthType, 4: AuthCredentials, 5: JudgeModel, 6: DeepTest, 7: EvaluationMode, 8: ScanType, 9: Configure, 10: StartButton
	// Note: Transport, AuthType, AuthCredentials fields are skipped for Python protocol
	// Note: AuthCredentials field is skipped when AuthType is no_auth
	CurrentField int
	CursorPos    int

	// UI state
	EvalSpinnerActive     bool
	HealthSpinnerActive   bool
	HealthSpinnerView     string
	RedTeamConfigSaved    bool   // Shows green banner when red team config is saved
	RedTeamConfigSavedMsg string // Custom message for the banner
}

// DetailState contains all data needed to render the evaluation detail screen
type DetailState struct {
	// Dimensions
	Width  int
	Height int

	// Status
	Status    string
	Progress  float64
	Completed bool

	// Evaluation mode
	EvaluationMode string

	// Focus state
	FocusedViewport int // 0: events, 1: summary

	// Spinner views (pre-rendered strings)
	EvalSpinnerActive    bool
	EvalSpinnerView      string
	SummarySpinnerActive bool
	SummarySpinnerView   string

	// Pre-rendered content from MessageHistoryView components
	EventsContent  string
	SummaryContent string
	HasSummary     bool
}
