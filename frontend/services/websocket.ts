/**
 * WebSocket client for real-time task updates.
 *
 * Provides automatic reconnection with exponential backoff and
 * event sequence tracking for gap detection.
 */

export interface TaskUpdateEvent {
  user_id: string;
  task_id: string;
  action: 'created' | 'updated' | 'deleted' | 'completed';
  task?: any;
  sequence?: number;
}

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface WebSocketConfig {
  maxReconnectDelay?: number; // Max delay in ms (default: 30000)
  initialReconnectDelay?: number; // Initial delay in ms (default: 1000)
}

export class TaskWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string = '';
  private token: string = '';
  private reconnectAttempt: number = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private expectedSequence: number = 0;
  private connectionState: ConnectionState = 'disconnected';
  private onMessageCallback: ((event: TaskUpdateEvent) => void) | null = null;
  private onStateChangeCallback: ((state: ConnectionState) => void) | null = null;

  // Configuration
  private maxReconnectDelay: number;
  private initialReconnectDelay: number;

  constructor(config: WebSocketConfig = {}) {
    this.maxReconnectDelay = config.maxReconnectDelay ?? 30000;
    this.initialReconnectDelay = config.initialReconnectDelay ?? 1000;
  }

  /**
   * Connect to WebSocket server with JWT authentication.
   *
   * @param url - WebSocket server URL (e.g., ws://localhost:8003/ws/tasks)
   * @param token - JWT authentication token
   */
  connect(url: string, token: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    this.url = url;
    this.token = token;
    this.setConnectionState('connecting');

    const wsUrl = `${url}?token=${encodeURIComponent(token)}`;

    try {
      this.ws = new WebSocket(wsUrl);
      this.setupEventHandlers();
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.setConnectionState('error');
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server.
   */
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'Client initiated disconnect');
      this.ws = null;
    }

    this.setConnectionState('disconnected');
    this.reconnectAttempt = 0;
  }

  /**
   * Send data to server (e.g., ping/pong).
   *
   * @param data - Data to send
   */
  send(data: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    } else {
      console.warn('WebSocket not connected, cannot send data');
    }
  }

  /**
   * Register callback for incoming messages.
   *
   * @param callback - Function to call when message is received
   */
  onMessage(callback: (event: TaskUpdateEvent) => void): void {
    this.onMessageCallback = callback;
  }

  /**
   * Register callback for connection state changes.
   *
   * @param callback - Function to call when connection state changes
   */
  onStateChange(callback: (state: ConnectionState) => void): void {
    this.onStateChangeCallback = callback;
  }

  /**
   * Get current connection status.
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get current connection state.
   */
  get state(): ConnectionState {
    return this.connectionState;
  }

  /**
   * Setup WebSocket event handlers.
   */
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.setConnectionState('connected');
      this.reconnectAttempt = 0;
      this.expectedSequence = 0;

      // Send ping to keep connection alive
      this.startPingInterval();
    };

    this.ws.onmessage = (event) => {
      try {
        const data: TaskUpdateEvent = JSON.parse(event.data);

        // Check for sequence gaps
        if (data.sequence !== undefined) {
          if (this.expectedSequence > 0 && data.sequence !== this.expectedSequence) {
            console.warn(
              `Sequence gap detected: expected ${this.expectedSequence}, got ${data.sequence}`
            );
          }
          this.expectedSequence = data.sequence + 1;
        }

        // Call message callback
        if (this.onMessageCallback) {
          this.onMessageCallback(data);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.setConnectionState('error');
    };

    this.ws.onclose = (event) => {
      console.log(`WebSocket closed: code=${event.code}, reason=${event.reason}`);
      this.setConnectionState('disconnected');

      // Reconnect unless client initiated close (code 1000)
      if (event.code !== 1000) {
        this.scheduleReconnect();
      }
    };
  }

  /**
   * Schedule reconnection with exponential backoff.
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    // Calculate delay with exponential backoff: 1s, 2s, 4s, 8s, max 30s
    const delay = Math.min(
      this.initialReconnectDelay * Math.pow(2, this.reconnectAttempt),
      this.maxReconnectDelay
    );

    console.log(
      `Scheduling reconnect in ${delay}ms (attempt ${this.reconnectAttempt + 1})`
    );

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectAttempt++;
      this.connect(this.url, this.token);
    }, delay);
  }

  /**
   * Send periodic pings to keep connection alive.
   */
  private startPingInterval(): void {
    const pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send('ping');
      } else {
        clearInterval(pingInterval);
      }
    }, 30000); // Ping every 30 seconds
  }

  /**
   * Update connection state and notify callback.
   */
  private setConnectionState(state: ConnectionState): void {
    this.connectionState = state;
    if (this.onStateChangeCallback) {
      this.onStateChangeCallback(state);
    }
  }
}
