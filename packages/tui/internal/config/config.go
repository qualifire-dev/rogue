package config

import (
	"os"
	"path/filepath"

	"github.com/pelletier/go-toml/v2"
)

// Config represents the application configuration
type Config struct {
	Server   ServerConfig   `toml:"server"`
	Auth     AuthConfig     `toml:"auth"`
	Defaults DefaultsConfig `toml:"defaults"`
	Agent    AgentConfig    `toml:"agent"`
	UI       UIConfig       `toml:"ui"`
}

// ServerConfig represents server configuration
type ServerConfig struct {
	URL     string `toml:"url"`
	Timeout string `toml:"timeout"`
}

// AuthConfig represents authentication configuration
type AuthConfig struct {
	OpenAIAPIKey    string `toml:"openai_api_key"`
	AnthropicAPIKey string `toml:"anthropic_api_key"`
	GoogleAPIKey    string `toml:"google_api_key"`
}

// DefaultsConfig represents default settings
type DefaultsConfig struct {
	JudgeLLM     string `toml:"judge_llm"`
	DeepTestMode bool   `toml:"deep_test_mode"`
	Theme        string `toml:"theme"`
}

// AgentConfig represents agent configuration
type AgentConfig struct {
	DefaultURL      string `toml:"default_url"`
	DefaultAuthType string `toml:"default_auth_type"`
}

// UIConfig represents UI configuration
type UIConfig struct {
	Theme        string `toml:"theme"`
	MouseEnabled bool   `toml:"mouse_enabled"`
	Animations   bool   `toml:"animations"`
}

// DefaultConfig returns a default configuration
func DefaultConfig() *Config {
	return &Config{
		Server: ServerConfig{
			URL:     "http://localhost:8000",
			Timeout: "30s",
		},
		Auth: AuthConfig{},
		Defaults: DefaultsConfig{
			JudgeLLM:     "openai/gpt-4o-mini",
			DeepTestMode: false,
			Theme:        "auto",
		},
		Agent: AgentConfig{
			DefaultURL:      "http://localhost:10001",
			DefaultAuthType: "no_auth",
		},
		UI: UIConfig{
			Theme:        "dark",
			MouseEnabled: true,
			Animations:   true,
		},
	}
}

// Load loads configuration from file
func Load(configPath string) (*Config, error) {
	if configPath == "" {
		configPath = DefaultConfigPath()
	}

	// Create default config
	config := DefaultConfig()

	// Check if config file exists
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		// Create config directory if it doesn't exist
		configDir := filepath.Dir(configPath)
		if err := os.MkdirAll(configDir, 0755); err != nil {
			return nil, err
		}

		// Save default config
		if err := Save(config, configPath); err != nil {
			return nil, err
		}

		return config, nil
	}

	// Read config file
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, err
	}

	// Parse TOML
	if err := toml.Unmarshal(data, config); err != nil {
		return nil, err
	}

	return config, nil
}

// Save saves configuration to file
func Save(config *Config, configPath string) error {
	if configPath == "" {
		configPath = DefaultConfigPath()
	}

	// Create config directory if it doesn't exist
	configDir := filepath.Dir(configPath)
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return err
	}

	// Marshal to TOML
	data, err := toml.Marshal(config)
	if err != nil {
		return err
	}

	// Write to file
	return os.WriteFile(configPath, data, 0644)
}

// DefaultConfigPath returns the default configuration file path
func DefaultConfigPath() string {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return ".rogue/config.toml"
	}
	return filepath.Join(homeDir, ".rogue", "config.toml")
}
