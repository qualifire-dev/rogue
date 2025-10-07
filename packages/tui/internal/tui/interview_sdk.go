package tui

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
)

// Interview API types matching server's rogue_sdk.types

// InterviewMessage represents a single message in the interview conversation
type InterviewMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// StartInterviewRequest is the request to start a new interview session
type StartInterviewRequest struct {
	Model  string `json:"model"`
	APIKey string `json:"api_key"`
}

// StartInterviewResponse is the response from starting an interview
type StartInterviewResponse struct {
	SessionID      string `json:"session_id"`
	InitialMessage string `json:"initial_message"`
	Message        string `json:"message"`
}

// SendMessageRequest is the request to send a message in an interview
type SendMessageRequest struct {
	SessionID string `json:"session_id"`
	Message   string `json:"message"`
}

// SendMessageResponse is the response from sending a message
type SendMessageResponse struct {
	SessionID    string `json:"session_id"`
	Response     string `json:"response"`
	IsComplete   bool   `json:"is_complete"`
	MessageCount int    `json:"message_count"`
}

// GetConversationResponse is the response from getting conversation history
type GetConversationResponse struct {
	SessionID    string             `json:"session_id"`
	Messages     []InterviewMessage `json:"messages"`
	IsComplete   bool               `json:"is_complete"`
	MessageCount int                `json:"message_count"`
}

// StartInterview starts a new interview session
func (sdk *RogueSDK) StartInterview(ctx context.Context, model, apiKey string) (*StartInterviewResponse, error) {
	request := StartInterviewRequest{
		Model:  model,
		APIKey: apiKey,
	}

	body, err := json.Marshal(request)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, "POST", sdk.baseURL+"/api/v1/interview/start", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := sdk.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("start interview failed: %d %s", resp.StatusCode, string(body))
	}

	var startResp StartInterviewResponse
	if err := json.NewDecoder(resp.Body).Decode(&startResp); err != nil {
		return nil, err
	}

	return &startResp, nil
}

// SendInterviewMessage sends a message in an interview session
func (sdk *RogueSDK) SendInterviewMessage(ctx context.Context, sessionID, message string) (*SendMessageResponse, error) {
	request := SendMessageRequest{
		SessionID: sessionID,
		Message:   message,
	}

	body, err := json.Marshal(request)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, "POST", sdk.baseURL+"/api/v1/interview/message", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := sdk.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("send message failed: %d %s", resp.StatusCode, string(body))
	}

	var msgResp SendMessageResponse
	if err := json.NewDecoder(resp.Body).Decode(&msgResp); err != nil {
		return nil, err
	}

	return &msgResp, nil
}

// GetConversation gets the full conversation for an interview session
func (sdk *RogueSDK) GetConversation(ctx context.Context, sessionID string) (*GetConversationResponse, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", sdk.baseURL+"/api/v1/interview/conversation/"+url.PathEscape(sessionID), nil)
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
		return nil, fmt.Errorf("get conversation failed: %d %s", resp.StatusCode, string(body))
	}

	var convResp GetConversationResponse
	if err := json.NewDecoder(resp.Body).Decode(&convResp); err != nil {
		return nil, err
	}

	return &convResp, nil
}

// EndInterview ends an interview session and cleans up resources
func (sdk *RogueSDK) EndInterview(ctx context.Context, sessionID string) error {
	req, err := http.NewRequestWithContext(ctx, "DELETE", sdk.baseURL+"/api/v1/interview/session/"+url.PathEscape(sessionID), nil)
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
		return fmt.Errorf("end interview failed: %d %s", resp.StatusCode, string(body))
	}

	return nil
}
