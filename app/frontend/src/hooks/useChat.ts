/**
 * useChat - Custom hook for chat state management.
 * 
 * Manages sessions, messages, and API communication.
 * Provides in-memory persistence (can be upgraded to DB later).
 */

'use client';

import { useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Message, ChatSession, ChatState } from '@/types/chat';
import { sendMessage as sendAPIMessage, createSession } from '@/lib/api';

const INITIAL_STATE: ChatState = {
    sessions: [],
    activeSessionId: null,
    isLoading: false,
    error: null,
};

export function useChat() {
    const [state, setState] = useState<ChatState>(INITIAL_STATE);

    // Get the active session
    const activeSession = state.sessions.find(
        (s) => s.id === state.activeSessionId
    );

    // Create a new chat session
    const startNewChat = useCallback(async () => {
        try {
            // Try to get session ID from API
            let sessionId: string;
            try {
                sessionId = await createSession();
            } catch {
                // Fallback to local UUID if API unavailable
                sessionId = uuidv4();
            }

            const newSession: ChatSession = {
                id: sessionId,
                title: 'New Chat',
                messages: [],
                createdAt: new Date(),
                updatedAt: new Date(),
            };

            setState((prev) => ({
                ...prev,
                sessions: [newSession, ...prev.sessions],
                activeSessionId: sessionId,
                error: null,
            }));

            return sessionId;
        } catch (error) {
            console.error('Failed to start new chat:', error);
            setState((prev) => ({
                ...prev,
                error: 'Failed to start new chat',
            }));
            return null;
        }
    }, []);

    // Switch to a different session
    const switchSession = useCallback((sessionId: string) => {
        setState((prev) => ({
            ...prev,
            activeSessionId: sessionId,
            error: null,
        }));
    }, []);

    // Delete a session
    const deleteSession = useCallback((sessionId: string) => {
        setState((prev) => {
            const filtered = prev.sessions.filter((s) => s.id !== sessionId);
            const newActiveId =
                prev.activeSessionId === sessionId
                    ? filtered[0]?.id ?? null
                    : prev.activeSessionId;

            return {
                ...prev,
                sessions: filtered,
                activeSessionId: newActiveId,
            };
        });
    }, []);

    // Send a message in the active session
    const sendMessage = useCallback(
        async (content: string) => {
            if (!state.activeSessionId || !content.trim()) return;

            const sessionId = state.activeSessionId;

            // Create user message
            const userMessage: Message = {
                id: uuidv4(),
                role: 'user',
                content: content.trim(),
                timestamp: new Date(),
            };

            // Add user message to state
            setState((prev) => ({
                ...prev,
                isLoading: true,
                error: null,
                sessions: prev.sessions.map((s) =>
                    s.id === sessionId
                        ? {
                            ...s,
                            messages: [...s.messages, userMessage],
                            updatedAt: new Date(),
                            // Update title from first message
                            title:
                                s.messages.length === 0
                                    ? content.slice(0, 30) + (content.length > 30 ? '...' : '')
                                    : s.title,
                        }
                        : s
                ),
            }));

            try {
                // Call the API
                const response = await sendAPIMessage(content, sessionId);

                // Create assistant message
                const assistantMessage: Message = {
                    id: uuidv4(),
                    role: 'assistant',
                    content: response.response,
                    timestamp: new Date(),
                    metadata: response.metadata,
                };

                // Add assistant message to state
                setState((prev) => ({
                    ...prev,
                    isLoading: false,
                    sessions: prev.sessions.map((s) =>
                        s.id === sessionId
                            ? {
                                ...s,
                                messages: [...s.messages, assistantMessage],
                                updatedAt: new Date(),
                            }
                            : s
                    ),
                }));
            } catch (error) {
                console.error('Failed to send message:', error);

                // Add error message
                const errorMessage: Message = {
                    id: uuidv4(),
                    role: 'assistant',
                    content:
                        'Sorry, I encountered an error connecting to the server. Please check that the backend is running.',
                    timestamp: new Date(),
                    metadata: { error: String(error) },
                };

                setState((prev) => ({
                    ...prev,
                    isLoading: false,
                    error: 'Failed to get response',
                    sessions: prev.sessions.map((s) =>
                        s.id === sessionId
                            ? {
                                ...s,
                                messages: [...s.messages, errorMessage],
                                updatedAt: new Date(),
                            }
                            : s
                    ),
                }));
            }
        },
        [state.activeSessionId]
    );
    // Start a new chat and immediately send a message (for welcome screen)
    const startNewChatWithMessage = useCallback(
        async (content: string) => {
            if (!content.trim()) return;

            try {
                // Create session
                let sessionId: string;
                try {
                    sessionId = await createSession();
                } catch {
                    sessionId = uuidv4();
                }

                // Create user message
                const userMessage: Message = {
                    id: uuidv4(),
                    role: 'user',
                    content: content.trim(),
                    timestamp: new Date(),
                };

                const newSession: ChatSession = {
                    id: sessionId,
                    title: content.slice(0, 30) + (content.length > 30 ? '...' : ''),
                    messages: [userMessage],
                    createdAt: new Date(),
                    updatedAt: new Date(),
                };

                // Add session with message and set loading
                setState((prev) => ({
                    ...prev,
                    sessions: [newSession, ...prev.sessions],
                    activeSessionId: sessionId,
                    isLoading: true,
                    error: null,
                }));

                // Call the API
                const response = await sendAPIMessage(content.trim(), sessionId);

                // Create assistant message
                const assistantMessage: Message = {
                    id: uuidv4(),
                    role: 'assistant',
                    content: response.response,
                    timestamp: new Date(),
                    metadata: response.metadata,
                };

                // Add assistant message
                setState((prev) => ({
                    ...prev,
                    isLoading: false,
                    sessions: prev.sessions.map((s) =>
                        s.id === sessionId
                            ? {
                                ...s,
                                messages: [...s.messages, assistantMessage],
                                updatedAt: new Date(),
                            }
                            : s
                    ),
                }));
            } catch (error) {
                console.error('Failed to start chat with message:', error);
                setState((prev) => ({
                    ...prev,
                    isLoading: false,
                    error: 'Failed to get response',
                }));
            }
        },
        []
    );

    return {
        sessions: state.sessions,
        activeSession,
        activeSessionId: state.activeSessionId,
        isLoading: state.isLoading,
        error: state.error,
        startNewChat,
        switchSession,
        deleteSession,
        sendMessage,
        startNewChatWithMessage,
    };
}
