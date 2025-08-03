package api

import (
	"fmt"
	"log"
	"net/url"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/gorilla/websocket"
)

// WSClient handles WebSocket connections for real-time updates
type WSClient struct {
	serverURL string
	conn      *websocket.Conn
	connected bool
	messages  chan WSMessage
	errors    chan error
}

// WSMessage represents a WebSocket message
type WSMessage struct {
	Type      string                 `json:"type"`
	Data      map[string]interface{} `json:"data"`
	Timestamp time.Time              `json:"timestamp"`
}

// WSEventType defines the types of WebSocket events
type WSEventType string

const (
	WSEventEvaluationUpdate   WSEventType = "evaluation_update"
	WSEventEvaluationComplete WSEventType = "evaluation_complete"
	WSEventEvaluationProgress WSEventType = "evaluation_progress"
	WSEventChatMessage        WSEventType = "chat_message"
	WSEventAgentResponse      WSEventType = "agent_response"
	WSEventConnectionStatus   WSEventType = "connection_status"
	WSEventError              WSEventType = "error"
)

// Bubble Tea messages for WebSocket events
type (
	WSConnectedMsg    struct{}
	WSDisconnectedMsg struct{}
	WSMessageMsg      WSMessage
	WSErrorMsg        error
)

// NewWSClient creates a new WebSocket client
func NewWSClient(serverURL string) *WSClient {
	return &WSClient{
		serverURL: serverURL,
		messages:  make(chan WSMessage, 100),
		errors:    make(chan error, 10),
	}
}

// Connect establishes a WebSocket connection
func (ws *WSClient) Connect() tea.Cmd {
	return func() tea.Msg {
		// Parse server URL and create WebSocket URL
		u, err := url.Parse(ws.serverURL)
		if err != nil {
			return WSErrorMsg(fmt.Errorf("invalid server URL: %w", err))
		}

		// Convert HTTP/HTTPS to WS/WSS
		wsScheme := "ws"
		if u.Scheme == "https" {
			wsScheme = "wss"
		}

		wsURL := &url.URL{
			Scheme: wsScheme,
			Host:   u.Host,
			Path:   "/ws",
		}

		// Establish connection
		conn, _, err := websocket.DefaultDialer.Dial(wsURL.String(), nil)
		if err != nil {
			return WSErrorMsg(fmt.Errorf("failed to connect to WebSocket: %w", err))
		}

		ws.conn = conn
		ws.connected = true

		// Start listening for messages
		go ws.listen()

		return WSConnectedMsg{}
	}
}

// Disconnect closes the WebSocket connection
func (ws *WSClient) Disconnect() {
	if ws.conn != nil {
		ws.connected = false
		ws.conn.Close()
		ws.conn = nil
	}
}

// IsConnected returns true if the WebSocket is connected
func (ws *WSClient) IsConnected() bool {
	return ws.connected
}

// SendMessage sends a message to the server
func (ws *WSClient) SendMessage(msgType string, data map[string]interface{}) error {
	if !ws.connected || ws.conn == nil {
		return fmt.Errorf("WebSocket not connected")
	}

	message := WSMessage{
		Type:      msgType,
		Data:      data,
		Timestamp: time.Now(),
	}

	return ws.conn.WriteJSON(message)
}

// SubscribeToEvaluation subscribes to updates for a specific evaluation
func (ws *WSClient) SubscribeToEvaluation(evaluationID string) error {
	return ws.SendMessage("subscribe", map[string]interface{}{
		"type":          "evaluation",
		"evaluation_id": evaluationID,
	})
}

// SubscribeToInterview subscribes to interview session updates
func (ws *WSClient) SubscribeToInterview(sessionID string) error {
	return ws.SendMessage("subscribe", map[string]interface{}{
		"type":       "interview",
		"session_id": sessionID,
	})
}

// listen runs in a goroutine to handle incoming WebSocket messages
func (ws *WSClient) listen() {
	defer func() {
		ws.connected = false
		if ws.conn != nil {
			ws.conn.Close()
		}
	}()

	for ws.connected {
		var message WSMessage
		err := ws.conn.ReadJSON(&message)
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("WebSocket error: %v", err)
			}
			ws.errors <- err
			return
		}

		// Set timestamp if not provided
		if message.Timestamp.IsZero() {
			message.Timestamp = time.Now()
		}

		ws.messages <- message
	}
}

// WaitForMessage returns a Bubble Tea command that waits for the next WebSocket message
func (ws *WSClient) WaitForMessage() tea.Cmd {
	return func() tea.Msg {
		select {
		case msg := <-ws.messages:
			return WSMessageMsg(msg)
		case err := <-ws.errors:
			return WSErrorMsg(err)
		}
	}
}

// Ping sends a ping message to keep the connection alive
func (ws *WSClient) Ping() error {
	if !ws.connected || ws.conn == nil {
		return fmt.Errorf("WebSocket not connected")
	}

	return ws.conn.WriteMessage(websocket.PingMessage, []byte{})
}

// StartHeartbeat starts a heartbeat to keep the connection alive
func (ws *WSClient) StartHeartbeat(interval time.Duration) tea.Cmd {
	return tea.Every(interval, func(time.Time) tea.Msg {
		if ws.IsConnected() {
			if err := ws.Ping(); err != nil {
				return WSErrorMsg(err)
			}
		}
		return nil
	})
}

// HandleMessage processes WebSocket messages and returns appropriate Bubble Tea commands
func (ws *WSClient) HandleMessage(msg WSMessage) tea.Cmd {
	switch WSEventType(msg.Type) {
	case WSEventEvaluationUpdate:
		// Handle evaluation updates
		return func() tea.Msg {
			return EvaluationUpdateMsg{
				ID:   msg.Data["id"].(string),
				Data: msg.Data,
			}
		}

	case WSEventEvaluationProgress:
		// Handle progress updates
		return func() tea.Msg {
			return EvaluationProgressMsg{
				ID:       msg.Data["id"].(string),
				Progress: msg.Data["progress"].(float64),
			}
		}

	case WSEventChatMessage:
		// Handle chat messages
		return func() tea.Msg {
			return ChatMessageMsg{
				SessionID: msg.Data["session_id"].(string),
				Message:   msg.Data["message"].(string),
				Role:      msg.Data["role"].(string),
			}
		}

	case WSEventError:
		// Handle errors
		return func() tea.Msg {
			return WSErrorMsg(fmt.Errorf("server error: %v", msg.Data["error"]))
		}

	default:
		// Unknown message type
		return nil
	}
}

// Message types for Bubble Tea updates
type (
	EvaluationUpdateMsg struct {
		ID   string
		Data map[string]interface{}
	}

	EvaluationProgressMsg struct {
		ID       string
		Progress float64
	}

	ChatMessageMsg struct {
		SessionID string
		Message   string
		Role      string
	}
)
