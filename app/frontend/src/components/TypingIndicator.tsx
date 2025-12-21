/**
 * TypingIndicator - Animated loading indicator.
 * 
 * Displays while waiting for a response from the AI.
 */

'use client';

import styles from './TypingIndicator.module.css';

export function TypingIndicator() {
    return (
        <div className={styles.container}>
            <div className={styles.indicator}>
                <span className={styles.dot} style={{ animationDelay: '0ms' }} />
                <span className={styles.dot} style={{ animationDelay: '150ms' }} />
                <span className={styles.dot} style={{ animationDelay: '300ms' }} />
            </div>
            <span className={styles.text}>Thinking...</span>
        </div>
    );
}
