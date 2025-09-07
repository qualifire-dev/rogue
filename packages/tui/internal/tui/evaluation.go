package tui

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/gorilla/websocket"
)

// SDK-like types to match the Python implementation

type AuthType string

const (
	AuthTypeNoAuth AuthType = "no_auth"
	AuthTypeBearer AuthType = "bearer"
	AuthTypeBasic  AuthType = "basic"
)

type ScenarioType string

const (
	ScenarioTypePolicy ScenarioType = "policy"
	ScenarioTypeCustom ScenarioType = "custom"
)

type AgentConfig struct {
	EvaluatedAgentURL         string   `json:"evaluated_agent_url"`
	EvaluatedAgentAuthType    AuthType `json:"evaluated_agent_auth_type"`
	EvaluatedAgentCredentials string   `json:"evaluated_agent_credentials,omitempty"`
	JudgeLLMModel             string   `json:"judge_llm"`
	InterviewMode             bool     `json:"interview_mode"`
	DeepTestMode              bool     `json:"deep_test_mode"`
	ParallelRuns              int      `json:"parallel_runs"`
}

type EvalScenario struct {
	Scenario     string       `json:"scenario"`
	ScenarioType ScenarioType `json:"scenario_type"`
}

type EvaluationRequest struct {
	AgentConfig    AgentConfig    `json:"agent_config"`
	Scenarios      []EvalScenario `json:"scenarios"`
	MaxRetries     int            `json:"max_retries,omitempty"`
	TimeoutSeconds int            `json:"timeout_seconds,omitempty"`
}

type EvaluationResponse struct {
	JobID   string `json:"job_id"`
	Message string `json:"message"`
}

type EvaluationJob struct {
	JobID     string  `json:"job_id"`
	Status    string  `json:"status"`
	Progress  float64 `json:"progress"`
	Error     string  `json:"error_message,omitempty"`
	Results   []any   `json:"results,omitempty"`
	CreatedAt string  `json:"created_at"`
	UpdatedAt string  `json:"updated_at"`
}

type EvaluationEvent struct {
	Type     string  `json:"type"`
	Status   string  `json:"status,omitempty"`
	Progress float64 `json:"progress,omitempty"`
	Role     string  `json:"role,omitempty"`
	Content  string  `json:"content,omitempty"`
	Message  string  `json:"message,omitempty"`
	JobID    string  `json:"job_id,omitempty"`
	Data     any     `json:"data,omitempty"`
}

type WebSocketMessage struct {
	Type  string `json:"type"`
	JobID string `json:"job_id"`
	Data  any    `json:"data"`
}

// RogueSDK is a simplified SDK for the TUI
type RogueSDK struct {
	baseURL    string
	httpClient *http.Client
	ws         *websocket.Conn
}

type SummaryResp struct {
	Summary struct {
		OverallSummary    string   `json:"overall_summary"`
		KeyFindings       []string `json:"key_findings"`
		Recommendations   []string `json:"recommendations"`
		DetailedBreakdown []struct {
			Scenario string `json:"scenario"`
			Status   string `json:"status"`
			Outcome  string `json:"outcome"`
		} `json:"detailed_breakdown"`
	} `json:"summary"`
	Message string `json:"message"`
}

// NewRogueSDK creates a new SDK instance
func NewRogueSDK(baseURL string) *RogueSDK {
	return &RogueSDK{
		baseURL: strings.TrimRight(baseURL, "/"),
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// Health checks the server health
func (sdk *RogueSDK) Health(ctx context.Context) (map[string]string, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", sdk.baseURL+"/api/v1/health", nil)
	if err != nil {
		return nil, err
	}

	resp, err := sdk.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("health check failed: %d %s", resp.StatusCode, string(body))
	}

	var health map[string]string
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
		return nil, err
	}

	return health, nil
}

// CreateEvaluation starts a new evaluation
func (sdk *RogueSDK) CreateEvaluation(ctx context.Context, request EvaluationRequest) (*EvaluationResponse, error) {
	body, err := json.Marshal(request)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, "POST", sdk.baseURL+"/api/v1/evaluations", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := sdk.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("create evaluation failed: %d %s", resp.StatusCode, string(body))
	}

	var evalResp EvaluationResponse
	if err := json.NewDecoder(resp.Body).Decode(&evalResp); err != nil {
		return nil, err
	}

	return &evalResp, nil
}

// GetEvaluation gets the current status of an evaluation
func (sdk *RogueSDK) GetEvaluation(ctx context.Context, jobID string) (*EvaluationJob, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", sdk.baseURL+"/api/v1/evaluations/"+url.PathEscape(jobID), nil)
	if err != nil {
		return nil, err
	}

	resp, err := sdk.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("get evaluation failed: %d %s", resp.StatusCode, string(body))
	}

	var job EvaluationJob
	if err := json.NewDecoder(resp.Body).Decode(&job); err != nil {
		return nil, err
	}

	return &job, nil
}

// ConnectWebSocket establishes a WebSocket connection for real-time updates
func (sdk *RogueSDK) ConnectWebSocket(ctx context.Context, jobID string) error {
	// Convert http:// to ws:// or https:// to wss://
	wsURL := strings.Replace(sdk.baseURL, "http://", "ws://", 1)
	wsURL = strings.Replace(wsURL, "https://", "wss://", 1)
	wsURL += "/api/v1/ws/" + url.PathEscape(jobID)

	dialer := websocket.DefaultDialer
	conn, _, err := dialer.DialContext(ctx, wsURL, nil)
	if err != nil {
		return fmt.Errorf("websocket connection failed: %w", err)
	}

	sdk.ws = conn
	return nil
}

// ReadWebSocketMessage reads a message from the WebSocket connection
func (sdk *RogueSDK) ReadWebSocketMessage() (*EvaluationEvent, error) {
	if sdk.ws == nil {
		return nil, fmt.Errorf("websocket not connected")
	}

	var msg WebSocketMessage
	if err := sdk.ws.ReadJSON(&msg); err != nil {
		return nil, err
	}

	// Convert the message to an EvaluationEvent
	event := &EvaluationEvent{
		Type: msg.Type,
	}

	// Handle different message types - server sends "job_update" and "chat_update"
	switch msg.Type {
	case "job_update":
		// Convert job_update to status event
		event.Type = "status"
		if data, ok := msg.Data.(map[string]interface{}); ok {
			if status, ok := data["status"].(string); ok {
				event.Status = status
			}
			if progress, ok := data["progress"].(float64); ok {
				event.Progress = progress
			}
			if errorMsg, ok := data["error_message"].(string); ok && errorMsg != "" {
				event.Message = errorMsg
			}
		}
		event.JobID = msg.JobID

	case "chat_update":
		// Convert chat_update to chat event
		event.Type = "chat"
		if data, ok := msg.Data.(map[string]interface{}); ok {
			if role, ok := data["role"].(string); ok {
				event.Role = role
			}
			if content, ok := data["content"].(string); ok {
				event.Content = content
			}
		}
		event.JobID = msg.JobID

	case "error":
		if data, ok := msg.Data.(map[string]interface{}); ok {
			if message, ok := data["message"].(string); ok {
				event.Message = message
			}
		}
		event.JobID = msg.JobID

	}

	return event, nil
}

// CloseWebSocket closes the WebSocket connection
func (sdk *RogueSDK) CloseWebSocket() error {
	if sdk.ws != nil {
		err := sdk.ws.Close()
		sdk.ws = nil
		return err
	}
	return nil
}

// RunEvaluationWithUpdates runs an evaluation with real-time WebSocket updates
func (sdk *RogueSDK) RunEvaluationWithUpdates(ctx context.Context, request EvaluationRequest) (<-chan EvaluationEvent, func() error, error) {
	events := make(chan EvaluationEvent, 64)

	// Start the evaluation
	resp, err := sdk.CreateEvaluation(ctx, request)
	if err != nil {
		close(events)
		return nil, nil, fmt.Errorf("failed to create evaluation: %w", err)
	}

	jobID := resp.JobID

	// Send initial status
	events <- EvaluationEvent{
		Type:   "status",
		Status: "starting",
		JobID:  jobID,
	}

	// Connect to WebSocket for real-time updates
	if err := sdk.ConnectWebSocket(ctx, jobID); err != nil {
		// Fall back to polling if WebSocket fails
		return sdk.pollEvaluationStatus(ctx, jobID, events)
	}

	// Start WebSocket message reader
	go func() {
		defer close(events)
		defer sdk.CloseWebSocket()

		for {
			select {
			case <-ctx.Done():
				return
			default:
				event, err := sdk.ReadWebSocketMessage()
				if err != nil {
					if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
						events <- EvaluationEvent{
							Type:    "error",
							Message: err.Error(),
						}
					}
					return
				}

				events <- *event

				// Check if evaluation is complete
				if event.Type == "status" && (event.Status == "completed" || event.Status == "failed" || event.Status == "cancelled") {
					return
				}
			}
		}
	}()

	cancel := func() error {
		return sdk.CancelEvaluation(context.Background(), jobID)
	}

	return events, cancel, nil
}

// pollEvaluationStatus falls back to HTTP polling when WebSocket fails
func (sdk *RogueSDK) pollEvaluationStatus(ctx context.Context, jobID string, events chan EvaluationEvent) (<-chan EvaluationEvent, func() error, error) {
	go func() {
		defer close(events)
		ticker := time.NewTicker(1 * time.Second)
		defer ticker.Stop()

		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				job, err := sdk.GetEvaluation(ctx, jobID)
				if err != nil {
					events <- EvaluationEvent{
						Type:    "error",
						Message: err.Error(),
					}
					return
				}

				events <- EvaluationEvent{
					Type:     "status",
					Status:   job.Status,
					Progress: job.Progress,
					JobID:    job.JobID,
				}

				if job.Status == "completed" || job.Status == "failed" || job.Status == "cancelled" {
					return
				}
			}
		}
	}()

	cancel := func() error {
		return sdk.CancelEvaluation(context.Background(), jobID)
	}

	return events, cancel, nil
}

// CancelEvaluation cancels a running evaluation
func (sdk *RogueSDK) CancelEvaluation(ctx context.Context, jobID string) error {
	req, err := http.NewRequestWithContext(ctx, "DELETE", sdk.baseURL+"/api/v1/evaluations/"+url.PathEscape(jobID), nil)
	if err != nil {
		return err
	}

	resp, err := sdk.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusNoContent {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("cancel evaluation failed: %d %s", resp.StatusCode, string(body))
	}

	return nil
}

// StartEvaluation is the main entry point used by the TUI
func (m *Model) StartEvaluation(ctx context.Context, serverURL, agentURL string, scenarios []string, judgeModel string, parallelRuns int, deepTest bool) (<-chan EvaluationEvent, func() error, error) {
	sdk := NewRogueSDK(serverURL)

	// Validate URLs
	if _, err := url.Parse(serverURL); err != nil {
		return nil, nil, fmt.Errorf("invalid server url: %w", err)
	}
	if _, err := url.Parse(agentURL); err != nil {
		return nil, nil, fmt.Errorf("invalid agent url: %w", err)
	}

	// Build evaluation request
	request := EvaluationRequest{
		AgentConfig: AgentConfig{
			EvaluatedAgentURL:      agentURL,
			EvaluatedAgentAuthType: AuthTypeNoAuth,
			JudgeLLMModel:          judgeModel,
			InterviewMode:          true,
			DeepTestMode:           deepTest,
			ParallelRuns:           parallelRuns,
		},
		MaxRetries:     3,
		TimeoutSeconds: 600,
	}

	// Convert scenarios
	for _, s := range scenarios {
		request.Scenarios = append(request.Scenarios, EvalScenario{
			Scenario:     s,
			ScenarioType: ScenarioTypePolicy,
		})
	}

	return sdk.RunEvaluationWithUpdates(ctx, request)
}

// GenerateSummary generates a markdown summary from evaluation results
func (sdk *RogueSDK) GenerateSummary(ctx context.Context, jobID, model, apiKey string) (*SummaryResp, error) {
	// First get the evaluation job to extract results
	job, err := sdk.GetEvaluation(ctx, jobID)
	if err != nil {
		return nil, fmt.Errorf("failed to get evaluation results: %w", err)
	}

	if job.Results == nil {
		return nil, fmt.Errorf("no results available for job %s", jobID)
	}

	// Prepare summary request - match server's SummaryGenerationRequest format
	summaryReq := map[string]interface{}{
		"model":   model,
		"api_key": apiKey,
		"results": map[string]interface{}{
			"results": job.Results,
		},
	}

	body, err := json.Marshal(summaryReq)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, "POST", sdk.baseURL+"/api/v1/llm/summary", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")

	// Use a longer timeout client for summary generation (LLM operations can be slow)
	longTimeoutClient := &http.Client{
		Timeout: 5 * time.Minute, // 5 minutes for LLM summary generation
	}

	resp, err := longTimeoutClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("summary generation failed: %d %s", resp.StatusCode, string(body))
	}

	var summaryResp SummaryResp

	if err := json.NewDecoder(resp.Body).Decode(&summaryResp); err != nil {
		return nil, err
	}

	return &summaryResp, nil
}

// CheckServerHealth calls GET /health and returns the status string
func (m *Model) CheckServerHealth(ctx context.Context, serverURL string) (string, error) {
	sdk := NewRogueSDK(serverURL)
	health, err := sdk.Health(ctx)
	if err != nil {
		return "", err
	}

	if status, ok := health["status"]; ok {
		return status, nil
	}
	return "unknown", nil
}
