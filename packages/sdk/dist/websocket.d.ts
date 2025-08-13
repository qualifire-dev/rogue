/**
 * WebSocket Client for Rogue Agent Evaluator real-time updates
 */
import { WebSocketEventType, WebSocketEventHandler } from './types';
export declare class RogueWebSocketClient {
    private ws?;
    private baseUrl;
    private jobId?;
    private eventHandlers;
    private reconnectAttempts;
    private maxReconnectAttempts;
    private reconnectDelay;
    private isConnecting;
    constructor(baseUrl: string, jobId?: string);
    /**
     * Connect to WebSocket
     */
    connect(): Promise<void>;
    /**
     * Disconnect from WebSocket
     */
    disconnect(): void;
    /**
     * Add event handler
     */
    on(event: WebSocketEventType, handler: WebSocketEventHandler): void;
    /**
     * Remove event handler
     */
    off(event: WebSocketEventType, handler: WebSocketEventHandler): void;
    /**
     * Remove all event handlers
     */
    removeAllListeners(event?: WebSocketEventType): void;
    /**
     * Check if connected
     */
    get isConnected(): boolean;
    /**
     * Handle incoming WebSocket message
     */
    private handleMessage;
    /**
     * Emit event to handlers
     */
    private emit;
    /**
     * Schedule reconnection attempt
     */
    private scheduleReconnect;
}
//# sourceMappingURL=websocket.d.ts.map
