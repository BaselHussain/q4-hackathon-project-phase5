'use client';

import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { useTheme } from 'next-themes';
import { isAuthenticated, getToken } from '@/lib/auth';

interface ChatKitWidgetProps {
  prePopulatedText?: string | undefined;
  onClearPrePopulatedText?: (() => void) | undefined;
}

export function ChatKitWidget({ prePopulatedText, onClearPrePopulatedText }: ChatKitWidgetProps = {}) {
  const [isClient, setIsClient] = useState(false);
  const [ChatKitComponents, setChatKitComponents] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [isMinimized, setIsMinimized] = useState(true);

  // Re-check auth on every route change (e.g. after login redirects to /dashboard)
  const [authed, setAuthed] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    setIsClient(true);

    import('@openai/chatkit-react')
      .then((module) => {
        console.log('ChatKit module loaded:', Object.keys(module));
        setChatKitComponents(module);
      })
      .catch((err) => {
        console.error('Failed to load ChatKit:', err);
        setError(`Failed to load ChatKit: ${err.message}`);
      });
  }, []);

  // Re-check auth state on route changes
  useEffect(() => {
    setAuthed(isAuthenticated());
  }, [pathname]);

  // Auto-open widget when pre-populated text arrives
  useEffect(() => {
    if (prePopulatedText) {
      setIsMinimized(false);
    }
  }, [prePopulatedText]);

  // Don't render for unauthenticated users
  if (!isClient || !authed) {
    return null;
  }

  if (error) {
    return (
      <div style={{ position: 'fixed', bottom: '20px', right: '20px', zIndex: 9999, backgroundColor: '#ef4444', color: 'white', padding: '16px', borderRadius: '8px', maxWidth: '400px', fontSize: '14px' }}>
        <strong>ChatKit Error:</strong> {error}
      </div>
    );
  }

  if (!ChatKitComponents) {
    return null;
  }

  return (
    <ChatKitInner
      ChatKit={ChatKitComponents.ChatKit}
      useChatKit={ChatKitComponents.useChatKit}
      isMinimized={isMinimized}
      onToggleMinimize={() => setIsMinimized(!isMinimized)}
      prePopulatedText={prePopulatedText}
      onClearPrePopulatedText={onClearPrePopulatedText}
    />
  );
}

interface ChatKitInnerProps {
  ChatKit: any;
  useChatKit: any;
  isMinimized: boolean;
  onToggleMinimize: () => void;
  prePopulatedText?: string | undefined;
  onClearPrePopulatedText?: (() => void) | undefined;
}

function ChatKitInner({
  ChatKit,
  useChatKit,
  isMinimized,
  onToggleMinimize,
  prePopulatedText,
  onClearPrePopulatedText,
}: ChatKitInnerProps) {
  const [error, setError] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const { resolvedTheme } = useTheme();

  // Handle Escape key to close widget
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isMinimized) {
        onToggleMinimize();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isMinimized, onToggleMinimize]);

  // Use environment variable for API URL
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8002';

  // Custom fetch function that includes JWT token in Authorization header
  const authenticatedFetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const token = getToken();
    const headers = new Headers(init?.headers);

    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    return fetch(input, {
      ...init,
      headers,
    });
  };

  const { control, setThreadId, setComposerValue } = useChatKit({
    api: {
      url: `${apiBaseUrl}/chatkit`,
      domainKey: 'domain_pk_69880ff7bb688190b20fba4a75b722e4001d97f86d6c4216',
      fetch: authenticatedFetch,
    },
    theme: {
      colorScheme: resolvedTheme === 'dark' ? 'dark' : 'light',
      color: { accent: { primary: '#6366f1', level: 2 } },
      radius: 'round',
      density: 'compact',
    },
    onReady: () => {
      console.log('ChatKit is ready!');
      setIsReady(true);
    },
    onThreadChange: ({ threadId }: any) => {
      console.log('Thread changed:', threadId);
      if (threadId) {
        localStorage.setItem('chatkit_thread_id', threadId);
      } else {
        localStorage.removeItem('chatkit_thread_id');
      }
    },
    onError: ({ error }: any) => {
      console.error('ChatKit onError:', error);
      setError(error?.message || 'ChatKit failed to initialize');
    },
    onLog: ({ name, data }: any) => {
      console.log('ChatKit log:', name, data);
    },
  });

  // Restore thread from localStorage when ChatKit is ready
  useEffect(() => {
    if (isReady && setThreadId) {
      const savedThreadId = localStorage.getItem('chatkit_thread_id');
      if (savedThreadId) {
        setThreadId(savedThreadId).catch((err: any) => {
          console.error('Failed to restore thread:', err);
        });
      }
    }
  }, [isReady, setThreadId]);

  // Handle pre-populated text from TextSelectionMenu
  useEffect(() => {
    if (prePopulatedText && isReady && setComposerValue) {
      setComposerValue({ text: prePopulatedText })
        .then(() => {
          if (onClearPrePopulatedText) {
            onClearPrePopulatedText();
          }
        })
        .catch((err: any) => {
          console.error('Failed to set composer value:', err);
        });
    }
  }, [prePopulatedText, isReady, setComposerValue, onClearPrePopulatedText]);

  if (error) {
    return (
      <div style={{ position: 'fixed', bottom: '20px', right: '20px', zIndex: 9999, backgroundColor: 'white', border: '2px solid #ef4444', padding: '16px', borderRadius: '8px', maxWidth: '400px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
        <h3 style={{ color: '#ef4444', margin: '0 0 8px 0', fontSize: '16px' }}>ChatKit Error</h3>
        <p style={{ margin: 0, fontSize: '14px', color: '#333' }}>{error}</p>
      </div>
    );
  }

  // Only mount ChatKit when widget is open - web component needs to be visible at mount time
  if (isMinimized) {
    return (
      <div
        onClick={onToggleMinimize}
        role="button"
        aria-label="Open chat assistant"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onToggleMinimize();
          }
        }}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          zIndex: 9999,
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          backgroundColor: '#6366f1',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)',
          transition: 'all 0.3s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.1)';
          e.currentTarget.style.boxShadow = '0 6px 16px rgba(99, 102, 241, 0.5)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(99, 102, 241, 0.4)';
        }}
        title="Open Chat"
      >
        <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      </div>
    );
  }

  return (
    <div
      role="dialog"
      aria-label="Chat assistant"
      aria-modal="false"
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        zIndex: 9999,
      }}
    >
      {/* Minimize button */}
      <button
        onClick={onToggleMinimize}
        aria-label="Minimize chat assistant"
        style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          zIndex: 10000,
          backgroundColor: 'rgba(0, 0, 0, 0.1)',
          border: 'none',
          borderRadius: '50%',
          width: '32px',
          height: '32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          transition: 'background-color 0.2s',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = 'rgba(0, 0, 0, 0.2)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'rgba(0, 0, 0, 0.1)';
        }}
        title="Minimize Chat"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* ChatKit wrapper with explicit dimensions */}
      <div style={{
        height: '600px',
        width: '400px',
        overscrollBehavior: 'contain',
      }}>
        <ChatKit control={control} />
      </div>
    </div>
  );
}
