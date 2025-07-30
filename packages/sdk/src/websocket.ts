/**
 * WebSocket Client for Rogue Agent Evaluator real-time updates
 */

import WebSocket from 'ws';
import {
  WebSocketMessage,
  WebSocketEventType,
  WebSocketEventHandler
} from './types';

export class RogueWebSocketClient {
  private ws?: WebSocket;
  private baseUrl: string;
  private jobId?: string;
  private eventHandlers: Map<WebSocketEventType, WebSocketEventHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;

  constructor(baseUrl: string, jobId?: string) {
    this.baseUrl = baseUrl.replace(/^http/, 'ws').replace(/\/$/, '');
    this.jobId = jobId;
  }

  /**
   * Connect to WebSocket
   */
  async connect(): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.isConnecting = true;

    return new Promise((resolve, reject) => {
      try {
        const wsUrl = this.jobId 
          ? `${this.baseUrl}/ws/${this.jobId}`
          : `${this.baseUrl}/ws`;

        this.ws = new WebSocket(wsUrl);

        this.ws.on('open', () => {
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.emit('connected', { url: wsUrl });
          resolve();
        });

        this.ws.on('message', (data: WebSocket.Data) => {
          try {
            const message: WebSocketMessage = JSON.parse(data.toString());
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        });

        this.ws.on('close', (code: number, reason: Buffer) => {
          this.isConnecting = false;
          this.emit('disconnected', { code, reason: reason.toString() });
          
          if (code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        });

        this.ws.on('error', (error: Error) => {
          this.isConnecting = false;
          this.emit('error', { error: error.message });
          reject(error);
        });

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = undefined;
    }
  }

  /**
   * Add event handler
   */
  on(event: WebSocketEventType, handler: WebSocketEventHandler): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event)!.push(handler);
  }

  /**
   * Remove event handler
   */
  off(event: WebSocketEventType, handler: WebSocketEventHandler): void {
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
  removeAllListeners(event?: WebSocketEventType): void {
    if (event) {
      this.eventHandlers.delete(event);
    } else {
      this.eventHandlers.clear();
    }
  }

  /**
   * Check if connected
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(message: WebSocketMessage): void {
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
  private emit(event: WebSocketEventType, data: any): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(event, data);
        } catch (error) {
          console.error('Error in WebSocket event handler:', error);
        }
      });
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
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
