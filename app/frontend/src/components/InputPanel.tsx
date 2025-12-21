/**
 * InputPanel - Message input area.
 * 
 * Auto-growing textarea with send button.
 * Supports Ctrl/Cmd+Enter to send.
 */

'use client';

import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import styles from './InputPanel.module.css';

interface InputPanelProps {
    onSend: (message: string) => void;
    disabled?: boolean;
    placeholder?: string;
}

export function InputPanel({
    onSend,
    disabled = false,
    placeholder = 'Ask me anything...',
}: InputPanelProps) {
    const [value, setValue] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize textarea
    useEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = 'auto';
            const newHeight = Math.min(textarea.scrollHeight, 150);
            textarea.style.height = `${newHeight}px`;
        }
    }, [value]);

    const handleSubmit = () => {
        if (value.trim() && !disabled) {
            onSend(value.trim());
            setValue('');

            // Reset height
            if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
            }
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        // Submit on Enter (without shift)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.inputWrapper}>
                <textarea
                    ref={textareaRef}
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    disabled={disabled}
                    rows={1}
                    className={styles.textarea}
                />

                <button
                    onClick={handleSubmit}
                    disabled={disabled || !value.trim()}
                    className={styles.sendButton}
                    aria-label="Send message"
                >
                    <svg
                        viewBox="0 0 24 24"
                        fill="currentColor"
                        className={styles.sendIcon}
                    >
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                    </svg>
                </button>
            </div>

            <p className={styles.hint}>
                Press <kbd>Enter</kbd> to send, <kbd>Shift + Enter</kbd> for new line
            </p>
        </div>
    );
}
