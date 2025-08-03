package config

import (
	"os"
	"path/filepath"

	"github.com/pelletier/go-toml/v2"
)

// Config represents the TUI configuration structure
type Config struct {
	Server   ServerConfig   `toml:"server"`
	Auth     AuthConfig     `toml:"auth"`
	Defaults DefaultsConfig `toml:"defaults"`
	Agent    AgentConfig    `toml:"agent"`
	UI       UIConfig       `toml:"ui"`
}

// ServerConfig contains server connection settings
type ServerConfig struct {
	URL     string `toml:"url"`
	Timeout string `toml:"timeout"`
}

// AuthConfig contains API keys for different LLM providers
type AuthConfig struct {
	OpenAIKey    string `toml:"openai_api_key"`
	AnthropicKey string `toml:"anthropic_api_key"`
	GoogleKey    string `toml:"google_api_key"`
}

// DefaultsConfig contains default settings
type DefaultsConfig struct {
	JudgeLLM     string `toml:"judge_llm"`
	DeepTestMode bool   `toml:"deep_test_mode"`
	Theme        string `toml:"theme"`
}

// AgentConfig contains agent-related settings
type AgentConfig struct {
	DefaultURL      string `toml:"default_url"`
	DefaultAuthType string `toml:"default_auth_type"`
}

// UIConfig contains UI-specific settings
type UIConfig struct {
	Theme        string `toml:"theme"`
	MouseEnabled bool   `toml:"mouse_enabled"`
	Animations   bool   `toml:"animations"`
}

// Load loads configuration from the default location or creates a new one with defaults
func Load() (*Config, error) {
	cfg := GetDefaults()

	// Try to load existing config
	configPath, err := GetConfigPath()
	if err != nil {
		return cfg, nil // Return defaults if can't determine config path
	}

	if data, err := os.ReadFile(configPath); err == nil {
		if err := toml.Unmarshal(data, cfg); err != nil {
			return cfg, err // Return error if config is malformed
		}
	}

	return cfg, nil
}

// Save saves the configuration to the default location
func (c *Config) Save() error {
	configPath, err := GetConfigPath()
	if err != nil {
		return err
	}

	// Create config directory if it doesn't exist
	configDir := filepath.Dir(configPath)
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return err
	}

	// Marshal and write config
	data, err := toml.Marshal(c)
	if err != nil {
		return err
	}

	return os.WriteFile(configPath, data, 0644)
}

// GetConfigPath returns the path to the configuration file
func GetConfigPath() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, ".rogue", "config.toml"), nil
}
