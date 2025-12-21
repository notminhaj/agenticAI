/**
 * MessageBubble - Individual chat message display.
 * 
 * Renders user and assistant messages with markdown support.
 */

'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message } from '@/types/chat';
import styles from './MessageBubble.module.css';

interface MessageBubbleProps {
    message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
    const isUser = message.role === 'user';

    return (
        <div
            className={`${styles.container} ${isUser ? styles.user : styles.assistant}`}
        >
            <div className={styles.avatar}>
                {isUser ? (
                    <svg
                        viewBox="0 0 24 24"
                        fill="currentColor"
                        className={styles.icon}
                    >
                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                    </svg>
                ) : (
                    <svg
                        viewBox="0 0 24 24"
                        fill="currentColor"
                        className={styles.icon}
                    >
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
                    </svg>
                )}
            </div>

            <div className={styles.bubble}>
                <div className={styles.content}>
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            // Custom code block rendering
                            code(props) {
                                const { children, className, ...rest } = props;
                                const match = /language-(\w+)/.exec(className || '');
                                const isInline = !match;

                                return isInline ? (
                                    <code className={styles.inlineCode} {...rest}>
                                        {children}
                                    </code>
                                ) : (
                                    <pre className={styles.codeBlock}>
                                        <code className={className} {...rest}>
                                            {children}
                                        </code>
                                    </pre>
                                );
                            },
                            // Style links
                            a(props) {
                                return (
                                    <a {...props} target="_blank" rel="noopener noreferrer" />
                                );
                            },
                        }}
                    >
                        {message.content}
                    </ReactMarkdown>
                </div>

                {message.metadata?.mode && !isUser && (
                    <div className={styles.metadata}>
                        <span className={styles.modeBadge}>{message.metadata.mode}</span>
                    </div>
                )}
            </div>
        </div>
    );
}
