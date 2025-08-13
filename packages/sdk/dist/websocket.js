"use strict";
/**
 * WebSocket Client for Rogue Agent Evaluator real-time updates
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.RogueWebSocketClient = void 0;
const ws_1 = __importDefault(require("ws"));
class RogueWebSocketClient {
    constructor(baseUrl, jobId) {
        this.eventHandlers = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnecting = false;
        this.baseUrl = baseUrl.replace(/^http/, 'ws').replace(/\/$/, '');
        this.jobId = jobId;
    }
    /**
     * Connect to WebSocket
     */
    async connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === ws_1.default.OPEN)) {
            return;
        }
        this.isConnecting = true;
        return new Promise((resolve, reject) => {
            try {
                const wsUrl = this.jobId
                    ? `${this.baseUrl}/ws/${this.jobId}`
                    : `${this.baseUrl}/ws`;
                this.ws = new ws_1.default(wsUrl);
                this.ws.on('open', () => {
                    this.isConnecting = false;
                    this.reconnectAttempts = 0;
                    this.emit('connected', { url: wsUrl });
                    resolve();
                });
                this.ws.on('message', (data) => {
                    try {
                        const message = JSON.parse(data.toString());
                        this.handleMessage(message);
                    }
                    catch (error) {
                        console.error('Failed to parse WebSocket message:', error);
                    }
                });
                this.ws.on('close', (code, reason) => {
                    this.isConnecting = false;
                    this.emit('disconnected', { code, reason: reason.toString() });
                    if (code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.scheduleReconnect();
                    }
                });
                this.ws.on('error', (error) => {
                    this.isConnecting = false;
                    this.emit('error', { error: error.message });
                    reject(error);
                });
            }
            catch (error) {
                this.isConnecting = false;
                reject(error);
            }
        });
    }
    /**
     * Disconnect from WebSocket
     */
    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = undefined;
        }
    }
    /**
     * Add event handler
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }
    /**
     * Remove event handler
     */
    off(event, handler) {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }
    /**
     * Remove all event handlers
     */
    removeAllListeners(event) {
        if (event) {
            this.eventHandlers.delete(event);
        }
        else {
            this.eventHandlers.clear();
        }
    }
    /**
     * Check if connected
     */
    get isConnected() {
        return this.ws?.readyState === ws_1.default.OPEN;
    }
    /**
     * Handle incoming WebSocket message
     */
    handleMessage(message) {
        switch (message.type) {
            case 'job_update':
                this.emit('job_update', message.data);
                break;
            case 'chat_update':
                this.emit('chat_update', message.data);
                break;
            default:
                console.warn('Unknown WebSocket message type:', message.type);
        }
    }
    /**
     * Emit event to handlers
     */
    emit(event, data) {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(event, data);
                }
                catch (error) {
                    console.error('Error in WebSocket event handler:', error);
                }
            });
        }
    }
    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        setTimeout(() => {
            if (this.reconnectAttempts <= this.maxReconnectAttempts) {
                this.connect().catch(error => {
                    console.error('Reconnection failed:', error);
                });
            }
        }, delay);
    }
}
exports.RogueWebSocketClient = RogueWebSocketClient;
//# sourceMappingURL=websocket.js.map
