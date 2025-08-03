package util

import (
	"fmt"
	"net/url"
	"regexp"
	"strings"
	"unicode"
)

// ValidationResult represents the result of a validation
type ValidationResult struct {
	IsValid bool
	Errors  []string
}

// NewValidationResult creates a new validation result
func NewValidationResult() *ValidationResult {
	return &ValidationResult{
		IsValid: true,
		Errors:  []string{},
	}
}

// AddError adds an error to the validation result
func (vr *ValidationResult) AddError(err string) {
	vr.IsValid = false
	vr.Errors = append(vr.Errors, err)
}

// GetFirstError returns the first error or empty string if no errors
func (vr *ValidationResult) GetFirstError() string {
	if len(vr.Errors) > 0 {
		return vr.Errors[0]
	}
	return ""
}

// ValidateURL validates a URL string
func ValidateURL(urlStr string) *ValidationResult {
	result := NewValidationResult()

	if urlStr == "" {
		result.AddError("URL cannot be empty")
		return result
	}

	parsedURL, err := url.Parse(urlStr)
	if err != nil {
		result.AddError(fmt.Sprintf("Invalid URL format: %v", err))
		return result
	}

	if parsedURL.Scheme == "" {
		result.AddError("URL must include a scheme (http:// or https://)")
		return result
	}

	if parsedURL.Scheme != "http" && parsedURL.Scheme != "https" {
		result.AddError("URL scheme must be http or https")
		return result
	}

	if parsedURL.Host == "" {
		result.AddError("URL must include a host")
		return result
	}

	return result
}

// ValidateNonEmpty validates that a string is not empty
func ValidateNonEmpty(value, fieldName string) *ValidationResult {
	result := NewValidationResult()

	if strings.TrimSpace(value) == "" {
		result.AddError(fmt.Sprintf("%s cannot be empty", fieldName))
	}

	return result
}

// ValidateLength validates string length
func ValidateLength(value, fieldName string, min, max int) *ValidationResult {
	result := NewValidationResult()

	length := len(strings.TrimSpace(value))

	if length < min {
		result.AddError(fmt.Sprintf("%s must be at least %d characters long", fieldName, min))
	}

	if max > 0 && length > max {
		result.AddError(fmt.Sprintf("%s must be no more than %d characters long", fieldName, max))
	}

	return result
}

// ValidateEmail validates an email address format
func ValidateEmail(email string) *ValidationResult {
	result := NewValidationResult()

	if email == "" {
		result.AddError("Email cannot be empty")
		return result
	}

	// Simple email validation regex
	emailRegex := regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
	if !emailRegex.MatchString(email) {
		result.AddError("Invalid email format")
	}

	return result
}

// ValidatePort validates a port number
func ValidatePort(port string) *ValidationResult {
	result := NewValidationResult()

	if port == "" {
		result.AddError("Port cannot be empty")
		return result
	}

	// Check if it's a valid number
	portRegex := regexp.MustCompile(`^\d+$`)
	if !portRegex.MatchString(port) {
		result.AddError("Port must be a number")
		return result
	}

	// Convert to int and check range
	var portNum int
	if _, err := fmt.Sscanf(port, "%d", &portNum); err != nil {
		result.AddError("Invalid port number")
		return result
	}

	if portNum < 1 || portNum > 65535 {
		result.AddError("Port must be between 1 and 65535")
	}

	return result
}

// ValidateAPIKey validates an API key format
func ValidateAPIKey(apiKey, provider string) *ValidationResult {
	result := NewValidationResult()

	if apiKey == "" {
		return result // Empty API keys are allowed
	}

	switch strings.ToLower(provider) {
	case "openai":
		if !strings.HasPrefix(apiKey, "sk-") {
			result.AddError("OpenAI API key must start with 'sk-'")
		}
		if len(apiKey) < 10 {
			result.AddError("OpenAI API key appears to be too short")
		}

	case "anthropic":
		if !strings.HasPrefix(apiKey, "sk-ant-") {
			result.AddError("Anthropic API key must start with 'sk-ant-'")
		}
		if len(apiKey) < 15 {
			result.AddError("Anthropic API key appears to be too short")
		}

	case "google":
		// Google API keys can have various formats
		if len(apiKey) < 10 {
			result.AddError("Google API key appears to be too short")
		}

	default:
		// Generic validation for unknown providers
		if len(apiKey) < 5 {
			result.AddError("API key appears to be too short")
		}
	}

	// Check for suspicious characters
	if strings.Contains(apiKey, " ") {
		result.AddError("API key should not contain spaces")
	}

	return result
}

// ValidateJSON validates that a string is valid JSON
func ValidateJSON(jsonStr string) *ValidationResult {
	result := NewValidationResult()

	if jsonStr == "" {
		result.AddError("JSON cannot be empty")
		return result
	}

	// TODO: Add JSON parsing validation if needed
	// For now, just check basic structure
	jsonStr = strings.TrimSpace(jsonStr)
	if !strings.HasPrefix(jsonStr, "{") && !strings.HasPrefix(jsonStr, "[") {
		result.AddError("JSON must start with '{' or '['")
	}

	return result
}

// ValidateAlphanumeric validates that a string contains only alphanumeric characters
func ValidateAlphanumeric(value, fieldName string) *ValidationResult {
	result := NewValidationResult()

	for _, r := range value {
		if !unicode.IsLetter(r) && !unicode.IsDigit(r) {
			result.AddError(fmt.Sprintf("%s must contain only letters and numbers", fieldName))
			break
		}
	}

	return result
}

// ValidateOneOf validates that a value is one of the allowed options
func ValidateOneOf(value string, options []string, fieldName string) *ValidationResult {
	result := NewValidationResult()

	for _, option := range options {
		if value == option {
			return result
		}
	}

	result.AddError(fmt.Sprintf("%s must be one of: %s", fieldName, strings.Join(options, ", ")))
	return result
}

// ValidateRegex validates that a string matches a regular expression
func ValidateRegex(value, pattern, fieldName string) *ValidationResult {
	result := NewValidationResult()

	regex, err := regexp.Compile(pattern)
	if err != nil {
		result.AddError(fmt.Sprintf("Invalid validation pattern for %s", fieldName))
		return result
	}

	if !regex.MatchString(value) {
		result.AddError(fmt.Sprintf("%s format is invalid", fieldName))
	}

	return result
}

// CombineValidationResults combines multiple validation results
func CombineValidationResults(results ...*ValidationResult) *ValidationResult {
	combined := NewValidationResult()

	for _, result := range results {
		if !result.IsValid {
			combined.IsValid = false
			combined.Errors = append(combined.Errors, result.Errors...)
		}
	}

	return combined
}

// ValidateRequired validates that a value is not empty (wrapper for ValidateNonEmpty)
func ValidateRequired(value, fieldName string) *ValidationResult {
	return ValidateNonEmpty(value, fieldName)
}

// IsValidURL is a helper function that returns true if the URL is valid
func IsValidURL(urlStr string) bool {
	return ValidateURL(urlStr).IsValid
}

// IsValidEmail is a helper function that returns true if the email is valid
func IsValidEmail(email string) bool {
	return ValidateEmail(email).IsValid
}

// IsValidPort is a helper function that returns true if the port is valid
func IsValidPort(port string) bool {
	return ValidatePort(port).IsValid
}
