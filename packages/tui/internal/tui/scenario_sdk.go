package tui

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Scenario generation API types matching server's rogue_sdk.types

// ScenarioData represents a single scenario aligned with Python schema
type ScenarioData struct {
	Scenario          string  `json:"scenario"`
	ScenarioType      string  `json:"scenario_type"`
	Dataset           *string `json:"dataset"`
	ExpectedOutcome   *string `json:"expected_outcome"`
	DatasetSampleSize *int    `json:"dataset_sample_size"`
}

// ScenariosList represents the collection of scenarios with business context
type ScenariosList struct {
	BusinessContext *string        `json:"business_context"`
	Scenarios       []ScenarioData `json:"scenarios"`
}

// ScenarioGenerationRequest is the request to generate scenarios from business context
type ScenarioGenerationRequest struct {
	BusinessContext string `json:"business_context"`
	Model           string `json:"model"`
	APIKey          string `json:"api_key"`
	Count           int    `json:"count,omitempty"`
}

// ScenarioGenerationResponse is the response from scenario generation
type ScenarioGenerationResponse struct {
	Scenarios ScenariosList `json:"scenarios"`
	Message   string        `json:"message"`
}

// GenerateScenarios generates test scenarios based on business context
func (sdk *RogueSDK) GenerateScenarios(ctx context.Context, request ScenarioGenerationRequest) (*ScenarioGenerationResponse, error) {
	// Set default count if not specified
	if request.Count == 0 {
		request.Count = 10
	}

	body, err := json.Marshal(request)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, "POST", sdk.baseURL+"/api/v1/llm/scenarios", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")

	// Use longer timeout for LLM operations
	longTimeoutClient := &http.Client{
		Timeout: 5 * time.Minute,
	}

	resp, err := longTimeoutClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("generate scenarios failed: %d %s", resp.StatusCode, string(body))
	}

	var scenResp ScenarioGenerationResponse
	if err := json.NewDecoder(resp.Body).Decode(&scenResp); err != nil {
		return nil, err
	}

	return &scenResp, nil
}
