import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: 'AI Tutor',
    description: 'Your intelligent learning companion - powered by AI',
    icons: {
        icon: '/favicon.ico',
    },
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body>
                {children}
            </body>
        </html>
    );
}
