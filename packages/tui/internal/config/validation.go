package config

import (
	"fmt"
	"net/url"
	"time"
)

// ValidationError represents a configuration validation error
type ValidationError struct {
	Field   string
	Message string
}

func (e ValidationError) Error() string {
	return fmt.Sprintf("config validation error [%s]: %s", e.Field, e.Message)
}

// Validate validates the configuration and returns any errors
func (c *Config) Validate() []ValidationError {
	var errors []ValidationError

	// Validate server URL
	if c.Server.URL == "" {
		errors = append(errors, ValidationError{
			Field:   "server.url",
			Message: "server URL cannot be empty",
		})
	} else {
		if _, err := url.Parse(c.Server.URL); err != nil {
			errors = append(errors, ValidationError{
				Field:   "server.url",
				Message: fmt.Sprintf("invalid server URL: %v", err),
			})
		}
	}

	// Validate server timeout
	if c.Server.Timeout != "" {
		if _, err := time.ParseDuration(c.Server.Timeout); err != nil {
			errors = append(errors, ValidationError{
				Field:   "server.timeout",
				Message: fmt.Sprintf("invalid timeout duration: %v", err),
			})
		}
	}

	// Validate agent URL
	if c.Agent.DefaultURL != "" {
		if _, err := url.Parse(c.Agent.DefaultURL); err != nil {
			errors = append(errors, ValidationError{
				Field:   "agent.default_url",
				Message: fmt.Sprintf("invalid agent URL: %v", err),
			})
		}
	}

	// Validate auth type
	validAuthTypes := AuthTypes()
	isValidAuthType := false
	for _, authType := range validAuthTypes {
		if c.Agent.DefaultAuthType == authType {
			isValidAuthType = true
			break
		}
	}
	if !isValidAuthType {
		errors = append(errors, ValidationError{
			Field:   "agent.default_auth_type",
			Message: fmt.Sprintf("invalid auth type, must be one of: %v", validAuthTypes),
		})
	}

	// Validate theme
	validThemes := Themes()
	isValidTheme := false
	for _, theme := range validThemes {
		if c.UI.Theme == theme {
			isValidTheme = true
			break
		}
	}
	if !isValidTheme {
		errors = append(errors, ValidationError{
			Field:   "ui.theme",
			Message: fmt.Sprintf("invalid theme, must be one of: %v", validThemes),
		})
	}

	return errors
}

// IsValid returns true if the configuration is valid
func (c *Config) IsValid() bool {
	return len(c.Validate()) == 0
}
