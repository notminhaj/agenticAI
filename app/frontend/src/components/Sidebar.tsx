/**
 * Sidebar - Chat history navigation.
 * 
 * Displays list of chat sessions with new chat button.
 */

'use client';

import { ChatSession } from '@/types/chat';
import styles from './Sidebar.module.css';

interface SidebarProps {
    sessions: ChatSession[];
    activeSessionId: string | null;
    onNewChat: () => void;
    onSelectSession: (id: string) => void;
    onDeleteSession: (id: string) => void;
}

export function Sidebar({
    sessions,
    activeSessionId,
    onNewChat,
    onSelectSession,
    onDeleteSession,
}: SidebarProps) {
    return (
        <aside className={styles.sidebar}>
            {/* Header */}
            <div className={styles.header}>
                <div className={styles.logo}>
                    <svg
                        viewBox="0 0 24 24"
                        fill="currentColor"
                        className={styles.logoIcon}
                    >
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
                    </svg>
                    <span className={styles.logoText}>AI Tutor</span>
                </div>
            </div>

            {/* New Chat Button */}
            <button onClick={onNewChat} className={styles.newChatBtn}>
                <svg viewBox="0 0 24 24" fill="currentColor" className={styles.plusIcon}>
                    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
                </svg>
                New Chat
            </button>

            {/* Sessions List */}
            <div className={styles.sessionsList}>
                {sessions.length === 0 ? (
                    <p className={styles.emptyState}>
                        No conversations yet.
                        <br />
                        Start a new chat to begin learning!
                    </p>
                ) : (
                    sessions.map((session) => (
                        <div
                            key={session.id}
                            className={`${styles.sessionItem} ${session.id === activeSessionId ? styles.active : ''
                                }`}
                            onClick={() => onSelectSession(session.id)}
                        >
                            <svg
                                viewBox="0 0 24 24"
                                fill="currentColor"
                                className={styles.chatIcon}
                            >
                                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z" />
                            </svg>
                            <span className={styles.sessionTitle}>{session.title}</span>
                            <button
                                className={styles.deleteBtn}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onDeleteSession(session.id);
                                }}
                                aria-label="Delete chat"
                            >
                                <svg viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
                                </svg>
                            </button>
                        </div>
                    ))
                )}
            </div>

            {/* Footer */}
            <div className={styles.footer}>
                <p className={styles.modeBadge}>Mode-Agnostic UI</p>
            </div>
        </aside>
    );
}
