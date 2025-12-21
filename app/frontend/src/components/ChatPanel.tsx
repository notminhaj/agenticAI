/**
 * ChatPanel - Main chat interface container.
 * 
 * Contains message list and input panel.
 */

'use client';

import { useRef, useEffect } from 'react';
import { ChatSession } from '@/types/chat';
import { MessageBubble } from './MessageBubble';
import { InputPanel } from './InputPanel';
import { TypingIndicator } from './TypingIndicator';
import styles from './ChatPanel.module.css';

interface ChatPanelProps {
    session: ChatSession | undefined;
    isLoading: boolean;
    onSendMessage: (message: string) => void;
}

export function ChatPanel({ session, isLoading, onSendMessage }: ChatPanelProps) {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [session?.messages, isLoading]);

    if (!session) {
        return (
            <div className={styles.container}>
                <div className={styles.emptyState}>
                    <div className={styles.emptyIcon}>
                        <svg viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
                        </svg>
                    </div>
                    <h2 className={styles.emptyTitle}>Welcome to AI Tutor</h2>
                    <p className={styles.emptyDescription}>
                        Start a new conversation to begin your learning journey.
                        <br />
                        Ask questions, explore concepts, and learn at your own pace.
                    </p>
                    <div className={styles.suggestionsList}>
                        <p className={styles.suggestionsTitle}>Try asking:</p>
                        <div className={styles.suggestions}>
                            <button className={styles.suggestionChip} onClick={() => onSendMessage("What is cell biology?")}>
                                What is cell biology?
                            </button>
                            <button className={styles.suggestionChip} onClick={() => onSendMessage("Teach me the basics of linear algebra")}>
                                Teach me the basics of linear algebra
                            </button>
                            <button className={styles.suggestionChip} onClick={() => onSendMessage("What are the basics of quantum mechanics?")}>
                                What are the basics of quantum mechanics?
                            </button>
                        </div>
                    </div>
                </div>
                {/* Input Area for Welcome Screen */}
                <InputPanel
                    onSend={onSendMessage}
                    disabled={isLoading}
                    placeholder="Ask me anything..."
                />
            </div>
        );
    }

    return (
        <div className={styles.container}>
            {/* Messages Area */}
            <div className={styles.messagesArea}>
                <div className={styles.messagesList}>
                    {session.messages.length === 0 ? (
                        <div className={styles.emptyChat}>
                            <p>What would you like to learn today?</p>
                        </div>
                    ) : (
                        session.messages.map((message) => (
                            <MessageBubble key={message.id} message={message} />
                        ))
                    )}

                    {isLoading && <TypingIndicator />}

                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <InputPanel
                onSend={onSendMessage}
                disabled={isLoading}
                placeholder="Ask anything about any topic..."
            />
        </div>
    );
}
