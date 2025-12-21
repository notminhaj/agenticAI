/**
 * AI Tutor - Main Page
 * 
 * The main chat interface combining Sidebar and ChatPanel.
 * Uses the useChat hook for state management.
 */

'use client';

import { useEffect } from 'react';
import { Sidebar, ChatPanel } from '@/components';
import { useChat } from '@/hooks/useChat';
import styles from './page.module.css';

export default function Home() {
    const {
        sessions,
        activeSession,
        activeSessionId,
        isLoading,
        startNewChat,
        switchSession,
        deleteSession,
        sendMessage,
        startNewChatWithMessage,
    } = useChat();

    // Auto-start removed to allow Welcome Screen to show
    // and prevent double-initialization in React StrictMode
    // useEffect(() => {
    //     if (sessions.length === 0) {
    //         startNewChat();
    //     }
    // }, [sessions.length, startNewChat]);

    // Handler that ensures a chat exists before sending
    const handleSendMessage = async (message: string) => {
        if (!activeSession) {
            // Start new chat AND send message atomically
            await startNewChatWithMessage(message);
        } else {
            sendMessage(message);
        }
    };

    return (
        <main className={styles.main}>
            <Sidebar
                sessions={sessions}
                activeSessionId={activeSessionId}
                onNewChat={startNewChat}
                onSelectSession={switchSession}
                onDeleteSession={deleteSession}
            />
            <ChatPanel
                session={activeSession}
                isLoading={isLoading}
                onSendMessage={handleSendMessage}
            />
        </main>
    );
}
