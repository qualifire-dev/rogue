package config

// ConfigField represents different configuration fields
type ConfigField int

const (
	ConfigFieldServerURL ConfigField = iota
	ConfigFieldTheme
	ConfigFieldQualifire
)

// ConfigState represents the configuration screen state
type ConfigState struct {
	ActiveField      ConfigField
	ServerURL        string
	CursorPos        int
	ThemeIndex       int
	IsEditing        bool
	HasChanges       bool
	QualifireEnabled bool
}

// Config represents application configuration
type Config struct {
	ServerURL               string            `toml:"server_url"`
	Theme                   string            `toml:"theme"`
	APIKeys                 map[string]string `toml:"api_keys"`
	SelectedModel           string            `toml:"selected_model"`
	SelectedProvider        string            `toml:"selected_provider"`
	InterviewModel          string            `toml:"interview_model"`
	InterviewProvider       string            `toml:"interview_provider"`
	QualifireAPIKey         string            `toml:"qualifire_api_key"`
	QualifireEnabled        bool              `toml:"qualifire_enabled"`
	DontShowQualifirePrompt bool              `toml:"dont_show_qualifire_prompt"`
}
