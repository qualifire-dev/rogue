package config

// ConfigField represents different configuration fields
type ConfigField int

const (
	ConfigFieldServerURL ConfigField = iota
	ConfigFieldTheme
	ConfigFieldRogueSecurity
)

// ConfigState represents the configuration screen state
type ConfigState struct {
	ActiveField          ConfigField
	ServerURL            string
	CursorPos            int
	ThemeIndex           int
	IsEditing            bool
	HasChanges           bool
	RogueSecurityEnabled bool
}

// Config represents application configuration
type Config struct {
	ServerURL                   string            `toml:"server_url"`
	Theme                       string            `toml:"theme"`
	APIKeys                     map[string]string `toml:"api_keys"`
	SelectedModel               string            `toml:"selected_model"`
	SelectedProvider            string            `toml:"selected_provider"`
	InterviewModel              string            `toml:"interview_model"`
	InterviewProvider           string            `toml:"interview_provider"`
	RogueSecurityAPIKey         string            `toml:"rogue_security_api_key"`
	RogueSecurityEnabled        bool              `toml:"rogue_security_enabled"`
	DontShowRogueSecurityPrompt bool              `toml:"dont_show_rogue_security_prompt"`
}
