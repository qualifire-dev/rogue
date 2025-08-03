package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Client wraps HTTP client functionality for the Rogue API
type Client struct {
	baseURL    string
	httpClient *http.Client
	headers    map[string]string
}

// Evaluation represents an evaluation from the API
type Evaluation struct {
	ID              string                 `json:"id"`
	Title           string                 `json:"title"`
	Status          string                 `json:"status"`
	Progress        float64                `json:"progress"`
	AgentURL        string                 `json:"agent_url"`
	Scenarios       []Scenario             `json:"scenarios"`
	CreatedAt       time.Time              `json:"created_at"`
	UpdatedAt       time.Time              `json:"updated_at"`
	CompletedAt     *time.Time             `json:"completed_at,omitempty"`
	Results         map[string]interface{} `json:"results,omitempty"`
	BusinessContext string                 `json:"business_context,omitempty"`
}

// Scenario represents a test scenario
type Scenario struct {
	ID          string `json:"id"`
	Title       string `json:"title"`
	Description string `json:"description"`
	Category    string `json:"category"`
	Difficulty  string `json:"difficulty"`
}

// ChatMessage represents a chat message in interview mode
type ChatMessage struct {
	ID        string    `json:"id"`
	Role      string    `json:"role"` // "user", "agent", "evaluator"
	Content   string    `json:"content"`
	Timestamp time.Time `json:"timestamp"`
}

// HealthResponse represents the health check response
type HealthResponse struct {
	Status  string `json:"status"`
	Version string `json:"version"`
}

// NewClient creates a new API client
func NewClient(baseURL string) *Client {
	return &Client{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		headers: map[string]string{
			"Content-Type": "application/json",
			"Accept":       "application/json",
		},
	}
}

// SetTimeout sets the HTTP client timeout
func (c *Client) SetTimeout(timeout time.Duration) {
	c.httpClient.Timeout = timeout
}

// SetHeaders sets custom headers for requests
func (c *Client) SetHeaders(headers map[string]string) {
	for k, v := range headers {
		c.headers[k] = v
	}
}

// Health checks the health of the Rogue server
func (c *Client) Health() (*HealthResponse, error) {
	var health HealthResponse
	err := c.get("/api/v1/health", &health)
	return &health, err
}

// GetEvaluations retrieves all evaluations
func (c *Client) GetEvaluations() ([]Evaluation, error) {
	var evaluations []Evaluation
	err := c.get("/api/v1/evaluations", &evaluations)
	return evaluations, err
}

// GetEvaluation retrieves a specific evaluation by ID
func (c *Client) GetEvaluation(id string) (*Evaluation, error) {
	var evaluation Evaluation
	err := c.get(fmt.Sprintf("/api/v1/evaluations/%s", id), &evaluation)
	return &evaluation, err
}

// CreateEvaluation creates a new evaluation
func (c *Client) CreateEvaluation(request map[string]interface{}) (*Evaluation, error) {
	var evaluation Evaluation
	err := c.post("/api/v1/evaluations", request, &evaluation)
	return &evaluation, err
}

// CancelEvaluation cancels a running evaluation
func (c *Client) CancelEvaluation(id string) error {
	return c.post(fmt.Sprintf("/api/v1/evaluations/%s/cancel", id), nil, nil)
}

// GetScenarios retrieves all scenarios
func (c *Client) GetScenarios() ([]Scenario, error) {
	var scenarios []Scenario
	err := c.get("/api/v1/scenarios", &scenarios)
	return scenarios, err
}

// GenerateScenarios generates new scenarios based on business context
func (c *Client) GenerateScenarios(request map[string]interface{}) ([]Scenario, error) {
	var scenarios []Scenario
	err := c.post("/api/v1/scenarios/generate", request, &scenarios)
	return scenarios, err
}

// TestAgentConnection tests connection to an agent
func (c *Client) TestAgentConnection(agentURL string, authType string, credentials map[string]string) (bool, error) {
	request := map[string]interface{}{
		"agent_url":   agentURL,
		"auth_type":   authType,
		"credentials": credentials,
	}

	response := make(map[string]interface{})
	err := c.post("/api/v1/agents/test", request, &response)
	if err != nil {
		return false, err
	}

	success, ok := response["success"].(bool)
	return ok && success, nil
}

// SendInterviewMessage sends a message in interview mode
func (c *Client) SendInterviewMessage(sessionID, message string) (*ChatMessage, error) {
	request := map[string]interface{}{
		"session_id": sessionID,
		"message":    message,
	}

	var response ChatMessage
	err := c.post("/api/v1/interview/message", request, &response)
	return &response, err
}

// StartInterviewSession starts a new interview session
func (c *Client) StartInterviewSession(agentURL string) (string, error) {
	request := map[string]interface{}{
		"agent_url": agentURL,
	}

	response := make(map[string]interface{})
	err := c.post("/api/v1/interview/start", request, &response)
	if err != nil {
		return "", err
	}

	sessionID, ok := response["session_id"].(string)
	if !ok {
		return "", fmt.Errorf("invalid session_id in response")
	}

	return sessionID, nil
}

// get performs a GET request
func (c *Client) get(endpoint string, result interface{}) error {
	return c.request("GET", endpoint, nil, result)
}

// post performs a POST request
func (c *Client) post(endpoint string, body interface{}, result interface{}) error {
	return c.request("POST", endpoint, body, result)
}

// request performs an HTTP request
func (c *Client) request(method, endpoint string, body interface{}, result interface{}) error {
	url := c.baseURL + endpoint

	var bodyReader io.Reader
	if body != nil {
		jsonData, err := json.Marshal(body)
		if err != nil {
			return fmt.Errorf("failed to marshal request body: %w", err)
		}
		bodyReader = bytes.NewReader(jsonData)
	}

	req, err := http.NewRequest(method, url, bodyReader)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	// Set headers
	for k, v := range c.headers {
		req.Header.Set(k, v)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("API error %d: %s", resp.StatusCode, string(body))
	}

	if result != nil {
		if err := json.NewDecoder(resp.Body).Decode(result); err != nil {
			return fmt.Errorf("failed to decode response: %w", err)
		}
	}

	return nil
}
