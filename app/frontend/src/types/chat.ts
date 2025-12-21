/**
 * Chat-related TypeScript types.
 * 
 * These types define the data structures used throughout
 * the chat interface and API communication.
 */

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    metadata?: MessageMetadata;
}

export interface MessageMetadata {
    mode?: string;
    tools_used?: string[];
    error?: string;
}

export interface ChatSession {
    id: string;
    title: string;
    messages: Message[];
    createdAt: Date;
    updatedAt: Date;
}

export interface ChatRequest {
    message: string;
    session_id: string;
    context?: {
        history_summary?: string;
    };
}

export interface ChatResponse {
    response: string;
    session_id: string;
    metadata?: MessageMetadata;
}

export interface ChatState {
    sessions: ChatSession[];
    activeSessionId: string | null;
    isLoading: boolean;
    error: string | null;
}
