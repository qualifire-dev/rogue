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
	EvaluatedAgentURL          string                 `json:"evaluated_agent_url"`
	EvaluatedAgentProtocol     Protocol               `json:"protocol"`
	EvaluatedAgentTransport    Transport              `json:"transport"`
	EvaluatedAgentAuthType     AuthType               `json:"evaluated_agent_auth_type"`
	EvaluatedAgentCredentials  string                 `json:"evaluated_agent_credentials,omitempty"`
	JudgeLLMModel              string                 `json:"judge_llm"`
	JudgeLLMAPIKey             string                 `json:"judge_llm_api_key,omitempty"`
	JudgeLLMAWSAccessKeyID     string                 `json:"judge_llm_aws_access_key_id,omitempty"`
	JudgeLLMAWSSecretAccessKey string                 `json:"judge_llm_aws_secret_access_key,omitempty"`
	JudgeLLMAWSRegion          string                 `json:"judge_llm_aws_region,omitempty"`
	InterviewMode              bool                   `json:"interview_mode"`
	DeepTestMode               bool                   `json:"deep_test_mode"`
	ParallelRuns               int                    `json:"parallel_runs"`
	EvaluationMode             string                 `json:"evaluation_mode,omitempty"`
	RedTeamConfig              map[string]interface{} `json:"red_team_config,omitempty"`
	QualifireAPIKey            string                 `json:"qualifire_api_key,omitempty"`
	BusinessContext            string                 `json:"business_context,omitempty"`
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
	Results   any     `json:"results,omitempty"` // Can be []any for policy eval or map for red team
	CreatedAt string  `json:"created_at"`
	UpdatedAt string  `json:"updated_at"`
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
	Summary StructuredSummary `json:"summary"`
	Message string            `json:"message"`
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
	var body []byte
	var err error
	var endpoint string

	// Route to appropriate endpoint based on evaluation mode
	if request.AgentConfig.EvaluationMode == "red_team" {
		// Transform to RedTeamRequest format
		// Note: We manually map fields because the red team API expects different JSON keys
		// (e.g., "evaluated_agent_protocol" vs AgentConfig's "protocol")
		redTeamReq := map[string]interface{}{
			"red_team_config":                    request.AgentConfig.RedTeamConfig,
			"evaluated_agent_url":                request.AgentConfig.EvaluatedAgentURL,
			"evaluated_agent_protocol":           request.AgentConfig.EvaluatedAgentProtocol,
			"evaluated_agent_transport":          request.AgentConfig.EvaluatedAgentTransport,
			"evaluated_agent_auth_type":          request.AgentConfig.EvaluatedAgentAuthType,
			"evaluated_agent_auth_credentials":   request.AgentConfig.EvaluatedAgentCredentials,
			"judge_llm":                          request.AgentConfig.JudgeLLMModel,
			"judge_llm_api_key":                  request.AgentConfig.JudgeLLMAPIKey,
			"judge_llm_aws_access_key_id":        request.AgentConfig.JudgeLLMAWSAccessKeyID,
			"judge_llm_aws_secret_access_key":    request.AgentConfig.JudgeLLMAWSSecretAccessKey,
			"judge_llm_aws_region":               request.AgentConfig.JudgeLLMAWSRegion,
			"attacker_llm":                       request.AgentConfig.JudgeLLMModel, // Use same as judge for now
			"attacker_llm_api_key":               request.AgentConfig.JudgeLLMAPIKey,
			"attacker_llm_aws_access_key_id":     request.AgentConfig.JudgeLLMAWSAccessKeyID,
			"attacker_llm_aws_secret_access_key": request.AgentConfig.JudgeLLMAWSSecretAccessKey,
			"attacker_llm_aws_region":            request.AgentConfig.JudgeLLMAWSRegion,
			"business_context":                   request.AgentConfig.BusinessContext,
			"qualifire_api_key":                  request.AgentConfig.QualifireAPIKey,
			"max_retries":                        request.MaxRetries,
			"timeout_seconds":                    request.TimeoutSeconds,
		}
		body, err = json.Marshal(redTeamReq)
		endpoint = "/api/v1/red-team"
	} else {
		// Use standard EvaluationRequest format
		body, err = json.Marshal(request)
		endpoint = "/api/v1/evaluations"
	}

	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, "POST", sdk.baseURL+endpoint, bytes.NewReader(body))
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
// Tries both red-team and evaluations endpoints to support both job types
func (sdk *RogueSDK) GetEvaluation(ctx context.Context, jobID string) (*EvaluationJob, error) {
	// Try red-team endpoint first (newer jobs will likely be here)
	endpoints := []string{
		"/api/v1/red-team/" + url.PathEscape(jobID),
		"/api/v1/evaluations/" + url.PathEscape(jobID),
	}

	var lastErr error
	for _, endpoint := range endpoints {
		req, err := http.NewRequestWithContext(ctx, "GET", sdk.baseURL+endpoint, nil)
		if err != nil {
			lastErr = err
			continue
		}

		resp, err := sdk.httpClient.Do(req)
		if err != nil {
			lastErr = err
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode == http.StatusOK {
			var job EvaluationJob
			if err := json.NewDecoder(resp.Body).Decode(&job); err != nil {
				lastErr = err
				continue
			}
			return &job, nil
		} else if resp.StatusCode == http.StatusNotFound {
			// Try next endpoint
			continue
		} else {
			body, _ := io.ReadAll(resp.Body)
			lastErr = fmt.Errorf("get evaluation failed: %d %s", resp.StatusCode, string(body))
		}
	}

	if lastErr != nil {
		return nil, lastErr
	}
	return nil, fmt.Errorf("job not found: %s", jobID)
}

// WebSocket keepalive configuration
// These values should match or exceed the server's ping interval to prevent timeout errors
// during long-running operations like red team scans (which can last up to an hour or more)
const (
	wsPingInterval = 20 * time.Second  // How often to send pings (matches server)
	wsPongWait     = 120 * time.Second // Time to wait for pong response (2 minutes, generous for network hiccups)
	wsWriteWait    = 30 * time.Second  // Time to wait for write operations
)

// ConnectWebSocket establishes a WebSocket connection for real-time updates
func (sdk *RogueSDK) ConnectWebSocket(ctx context.Context, jobID string) error {
	// Convert http:// to ws:// or https:// to wss://
	wsURL := strings.Replace(sdk.baseURL, "http://", "ws://", 1)
	wsURL = strings.Replace(wsURL, "https://", "wss://", 1)
	wsURL += "/api/v1/ws/" + url.PathEscape(jobID)

	dialer := websocket.DefaultDialer
	// Set handshake timeout for initial connection
	dialer.HandshakeTimeout = 30 * time.Second

	conn, _, err := dialer.DialContext(ctx, wsURL, nil)
	if err != nil {
		return fmt.Errorf("websocket connection failed: %w", err)
	}

	// Configure keepalive settings to prevent timeout during long operations
	// Set read deadline - will be extended by pong handler
	conn.SetReadDeadline(time.Now().Add(wsPongWait))

	// Set pong handler to extend read deadline when pong received
	conn.SetPongHandler(func(string) error {
		conn.SetReadDeadline(time.Now().Add(wsPongWait))
		return nil
	})

	// Set ping handler to respond to server pings and extend deadline
	conn.SetPingHandler(func(appData string) error {
		conn.SetReadDeadline(time.Now().Add(wsPongWait))
		// Send pong response
		err := conn.WriteControl(websocket.PongMessage, []byte(appData), time.Now().Add(wsWriteWait))
		if err != nil {
			return err
		}
		return nil
	})

	sdk.ws = conn

	// Start a goroutine to send periodic pings to keep connection alive
	go sdk.wsKeepalive(ctx)

	return nil
}

// wsKeepalive sends periodic ping messages to keep the WebSocket connection alive
func (sdk *RogueSDK) wsKeepalive(ctx context.Context) {
	ticker := time.NewTicker(wsPingInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			if sdk.ws == nil {
				return
			}

			sdk.ws.SetWriteDeadline(time.Now().Add(wsWriteWait))
			if err := sdk.ws.WriteMessage(websocket.PingMessage, nil); err != nil {
				// Connection likely closed, exit goroutine
				return
			}
		}
	}
}

// ReadWebSocketMessage reads a message from the WebSocket connection
func (sdk *RogueSDK) ReadWebSocketMessage() (*EvaluationEvent, error) {
	if sdk.ws == nil {
		return nil, fmt.Errorf("websocket not connected")
	}

	for {
		// Extend read deadline before each read
		sdk.ws.SetReadDeadline(time.Now().Add(wsPongWait))

		messageType, data, err := sdk.ws.ReadMessage()
		if err != nil {
			return nil, err
		}

		// Handle binary messages (keepalive pings from server)
		if messageType == websocket.BinaryMessage {
			// Server sends binary "ping" as keepalive - just continue reading
			// The pong response is handled automatically by the ping/pong handlers
			continue
		}

		// Handle text messages (the actual job updates)
		if messageType != websocket.TextMessage {
			// Skip other message types
			continue
		}

		var msg WebSocketMessage
		if err := json.Unmarshal(data, &msg); err != nil {
			return nil, fmt.Errorf("failed to unmarshal websocket message: %w", err)
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
}

// CloseWebSocket closes the WebSocket connection gracefully
func (sdk *RogueSDK) CloseWebSocket() error {
	if sdk.ws != nil {
		// Send close message with normal closure
		sdk.ws.SetWriteDeadline(time.Now().Add(wsWriteWait))
		err := sdk.ws.WriteMessage(websocket.CloseMessage, websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""))
		if err != nil {
			// If we can't send close message, just close the connection
			sdk.ws.Close()
			sdk.ws = nil
			return err
		}
		err = sdk.ws.Close()
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
// Tries both red-team and evaluations endpoints to support both job types
func (sdk *RogueSDK) CancelEvaluation(ctx context.Context, jobID string) error {
	// Try red-team endpoint first (newer jobs will likely be here)
	endpoints := []string{
		"/api/v1/red-team/" + url.PathEscape(jobID),
		"/api/v1/evaluations/" + url.PathEscape(jobID),
	}

	var lastErr error
	for _, endpoint := range endpoints {
		req, err := http.NewRequestWithContext(ctx, "DELETE", sdk.baseURL+endpoint, nil)
		if err != nil {
			lastErr = err
			continue
		}

		resp, err := sdk.httpClient.Do(req)
		if err != nil {
			lastErr = err
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode == http.StatusOK || resp.StatusCode == http.StatusNoContent {
			return nil
		} else if resp.StatusCode == http.StatusNotFound {
			// Try next endpoint
			continue
		} else {
			body, _ := io.ReadAll(resp.Body)
			lastErr = fmt.Errorf("cancel evaluation failed: %d %s", resp.StatusCode, string(body))
		}
	}

	if lastErr != nil {
		return lastErr
	}
	return fmt.Errorf("job not found: %s", jobID)
}

// StartEvaluation is the main entry point used by the TUI
func (m *Model) StartEvaluation(
	ctx context.Context,
	serverURL string,
	agentURL string,
	agentProtocol Protocol,
	agentTransport Transport,
	scenarios []EvalScenario,
	judgeModel string,
	parallelRuns int,
	deepTest bool,
	evaluationMode string,
	redTeamConfig map[string]interface{},
	businessContext string,
) (<-chan EvaluationEvent, func() error, error) {
	sdk := NewRogueSDK(serverURL)

	// Validate URLs
	if _, err := url.Parse(serverURL); err != nil {
		return nil, nil, fmt.Errorf("invalid server url: %w", err)
	}
	if _, err := url.Parse(agentURL); err != nil {
		return nil, nil, fmt.Errorf("invalid agent url: %w", err)
	}

	// Extract API key and AWS credentials from config based on judge model provider
	var apiKey string
	var awsAccessKeyID, awsSecretAccessKey, awsRegion string

	// Extract provider from judge model (e.g. "openai/gpt-4" -> "openai" or "bedrock/anthropic.claude-..." -> "bedrock")
	if parts := strings.Split(judgeModel, "/"); len(parts) >= 2 {
		provider := parts[0]

		// For Bedrock, extract AWS credentials from config (don't use api_key)
		if provider == "bedrock" {
			if accessKey, ok := m.config.APIKeys["bedrock_access_key"]; ok {
				awsAccessKeyID = accessKey
			}
			if secretKey, ok := m.config.APIKeys["bedrock_secret_key"]; ok {
				awsSecretAccessKey = secretKey
			}
			if region, ok := m.config.APIKeys["bedrock_region"]; ok {
				awsRegion = region
			}
			// Don't set apiKey for Bedrock - use AWS credentials only
		} else {
			// For non-Bedrock providers, extract API key
			if key, ok := m.config.APIKeys[provider]; ok {
				apiKey = key
			}
		}
	}

	// Get Qualifire API key from config
	qualifireAPIKey := ""
	if m.config.QualifireEnabled && m.config.QualifireAPIKey != "" {
		qualifireAPIKey = m.config.QualifireAPIKey
	}

	// Build evaluation request
	request := EvaluationRequest{
		AgentConfig: AgentConfig{
			EvaluatedAgentURL:          agentURL,
			EvaluatedAgentProtocol:     agentProtocol,
			EvaluatedAgentTransport:    agentTransport,
			EvaluatedAgentAuthType:     AuthTypeNoAuth,
			JudgeLLMModel:              judgeModel,
			JudgeLLMAPIKey:             apiKey,
			JudgeLLMAWSAccessKeyID:     awsAccessKeyID,
			JudgeLLMAWSSecretAccessKey: awsSecretAccessKey,
			JudgeLLMAWSRegion:          awsRegion,
			InterviewMode:              true,
			DeepTestMode:               deepTest,
			ParallelRuns:               parallelRuns,
			EvaluationMode:             evaluationMode,
			RedTeamConfig:              redTeamConfig,
			QualifireAPIKey:            qualifireAPIKey,
			BusinessContext:            businessContext,
		},
		MaxRetries:     3,
		TimeoutSeconds: 600,
	}

	// Convert scenarios
	for _, s := range scenarios {
		request.Scenarios = append(request.Scenarios, EvalScenario{
			Scenario:        s.Scenario,
			ScenarioType:    s.ScenarioType,
			ExpectedOutcome: s.ExpectedOutcome,
		})
	}

	return sdk.RunEvaluationWithUpdates(ctx, request)
}

// GenerateSummary generates a markdown summary from evaluation results
// Routes to the appropriate endpoint based on job type (red team vs policy)
func (sdk *RogueSDK) GenerateSummary(
	ctx context.Context,
	jobID, model, apiKey string,
	qualifireAPIKey *string,
	deepTest bool,
	judgeModel string,
	awsAccessKeyID *string,
	awsSecretAccessKey *string,
	awsRegion *string,
) (*SummaryResp, error) {
	// First get the evaluation job to extract results
	job, err := sdk.GetEvaluation(ctx, jobID)
	if err != nil {
		return nil, fmt.Errorf("failed to get evaluation results: %w", err)
	}

	if job.Results == nil {
		return nil, fmt.Errorf("no results available for job %s", jobID)
	}

	// Detect if this is a red team job or policy evaluation job
	isRedTeamJob := false
	switch job.Results.(type) {
	case map[string]interface{}:
		// Red team results are objects
		isRedTeamJob = true
	case []interface{}:
		// Policy results are arrays
		isRedTeamJob = false
	}

	var endpoint string
	var summaryReq map[string]interface{}

	if isRedTeamJob {
		// Use dedicated red team summary endpoint (no request body needed)
		endpoint = fmt.Sprintf("/api/v1/red-team/%s/summary", url.PathEscape(jobID))
		summaryReq = nil // POST with no body
	} else {
		// Use standard policy evaluation summary endpoint
		endpoint = "/api/v1/llm/summary"
		summaryReq = map[string]interface{}{
			"model":   model,
			"api_key": apiKey,
			"results": map[string]interface{}{
				"results": job.Results,
			},
			"job_id": jobID,
			"qualifire_api_key": func() string {
				if qualifireAPIKey == nil {
					return ""
				}
				return *qualifireAPIKey
			}(),
			"deep_test":   deepTest,
			"judge_model": judgeModel,
		}
	}

	var req *http.Request

	if isRedTeamJob {
		// Red team endpoint doesn't need request body
		req, err = http.NewRequestWithContext(ctx, "POST", sdk.baseURL+endpoint, nil)
		if err != nil {
			return nil, err
		}
	} else {
		// Policy evaluation - add AWS credentials and marshal request
		if awsAccessKeyID != nil && *awsAccessKeyID != "" {
			summaryReq["aws_access_key_id"] = *awsAccessKeyID
		}
		if awsSecretAccessKey != nil && *awsSecretAccessKey != "" {
			summaryReq["aws_secret_access_key"] = *awsSecretAccessKey
		}
		if awsRegion != nil && *awsRegion != "" {
			summaryReq["aws_region"] = *awsRegion
		}

		body, err := json.Marshal(summaryReq)
		if err != nil {
			return nil, err
		}

		req, err = http.NewRequestWithContext(ctx, "POST", sdk.baseURL+endpoint, bytes.NewReader(body))
		if err != nil {
			return nil, err
		}
		req.Header.Set("Content-Type", "application/json")
	}

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

// ReportSummary reports a summary to Qualifire
func (sdk *RogueSDK) ReportSummary(
	ctx context.Context,
	jobID string,
	summary StructuredSummary,
	deepTest bool,
	judgeModel string,
	qualifireAPIKey string,
) error {
	reportReq := map[string]interface{}{
		"job_id":             jobID,
		"structured_summary": summary,
		"deep_test":          deepTest,
		"judge_model":        judgeModel,
		"qualifire_api_key":  qualifireAPIKey,
	}

	body, err := json.Marshal(reportReq)
	if err != nil {
		return err
	}

	req, err := http.NewRequestWithContext(ctx, "POST", sdk.baseURL+"/api/v1/llm/report_summary", bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := sdk.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("report summary failed: %d %s", resp.StatusCode, string(body))
	}

	return nil
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
