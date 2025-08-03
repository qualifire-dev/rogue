package config

// GetDefaults returns the default configuration
func GetDefaults() *Config {
	return &Config{
		Server: ServerConfig{
			URL:     "http://localhost:8000",
			Timeout: "30s",
		},
		Auth: AuthConfig{
			OpenAIKey:    "",
			AnthropicKey: "",
			GoogleKey:    "",
		},
		Defaults: DefaultsConfig{
			JudgeLLM:     "openai/gpt-4o-mini",
			DeepTestMode: false,
			Theme:        "auto",
		},
		Agent: AgentConfig{
			DefaultURL:      "http://localhost:3000",
			DefaultAuthType: "no_auth",
		},
		UI: UIConfig{
			Theme:        "dark",
			MouseEnabled: true,
			Animations:   true,
		},
	}
}

// AuthTypes returns the available authentication types
func AuthTypes() []string {
	return []string{
		"no_auth",
		"api_key",
		"bearer_token",
		"basic_auth",
	}
}

// Themes returns the available UI themes
func Themes() []string {
	return []string{
		"dark",
		"light",
		"auto",
	}
}

// DefaultModels returns the available LLM models
func DefaultModels() []string {
	return []string{
		"openai/gpt-4o-mini",
		"openai/gpt-4o",
		"openai/gpt-3.5-turbo",
		"anthropic/claude-3-haiku",
		"anthropic/claude-3-sonnet",
		"anthropic/claude-3-opus",
		"google/gemini-pro",
		"google/gemini-pro-vision",
	}
}
