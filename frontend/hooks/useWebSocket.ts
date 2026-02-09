/**
 * React hook for WebSocket connection with automatic reconnection.
 *
 * Manages WebSocket lifecycle and provides connection state and messages.
 */
import { useEffect, useState, useRef, useCallback } from 'react';
import {
  TaskWebSocketClient,
  TaskUpdateEvent,
  ConnectionState,
} from '@/services/websocket';

export interface UseWebSocketReturn {
  lastMessage: TaskUpdateEvent | null;
  isConnected: boolean;
  connectionState: ConnectionState;
  sendMessage: (data: string) => void;
}

/**
 * Hook to manage WebSocket connection for real-time task updates.
 *
 * @param token - JWT authentication token
 * @param url - WebSocket server URL (default: ws://localhost:8003/ws/tasks)
 * @returns WebSocket state and utilities
 *
 * @example
 * ```tsx
 * const { lastMessage, isConnected, connectionState } = useWebSocket(token);
 *
 * useEffect(() => {
 *   if (lastMessage) {
 *     console.log('Task update:', lastMessage);
 *   }
 * }, [lastMessage]);
 * ```
 */
export function useWebSocket(
  token: string,
  url: string = 'ws://localhost:8003/ws/tasks'
): UseWebSocketReturn {
  const [lastMessage, setLastMessage] = useState<TaskUpdateEvent | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const clientRef = useRef<TaskWebSocketClient | null>(null);

  // Initialize WebSocket client
  useEffect(() => {
    if (!token) {
      console.warn('useWebSocket: No token provided, skipping connection');
      return;
    }

    // Create client if not already created
    if (!clientRef.current) {
      clientRef.current = new TaskWebSocketClient({
        initialReconnectDelay: 1000,
        maxReconnectDelay: 30000,
      });

      // Setup message handler
      clientRef.current.onMessage((event: TaskUpdateEvent) => {
        setLastMessage(event);
      });

      // Setup state change handler
      clientRef.current.onStateChange((state: ConnectionState) => {
        setConnectionState(state);
      });
    }

    // Connect
    clientRef.current.connect(url, token);

    // Cleanup on unmount
    return () => {
      if (clientRef.current) {
        clientRef.current.disconnect();
        clientRef.current = null;
      }
    };
  }, [token, url]);

  // Send message function
  const sendMessage = useCallback((data: string) => {
    if (clientRef.current) {
      clientRef.current.send(data);
    }
  }, []);

  return {
    lastMessage,
    isConnected: connectionState === 'connected',
    connectionState,
    sendMessage,
  };
}
