/**
 * API client for communicating with the FastAPI backend.
 */

import { ChatRequest, ChatResponse } from '@/types/chat';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * Send a chat message and receive a response.
 */
export async function sendMessage(
    message: string,
    sessionId: string
): Promise<ChatResponse> {
    const request: ChatRequest = {
        message,
        session_id: sessionId,
    };

    const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
}

/**
 * Create a new chat session.
 */
export async function createSession(): Promise<string> {
    const response = await fetch(`${API_BASE}/api/chat/new`, {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data.session_id;
}

/**
 * Get available modes and active mode.
 */
export async function getModes(): Promise<{
    active: string;
    available: string[];
}> {
    const response = await fetch(`${API_BASE}/api/modes`);

    if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
}
