import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Satyendra Kumar – Software Developer",
  description:
    "Satyendra Kumar – Full-Stack Software Developer specialising in AI integration, microservices, React/Next.js, Node.js, and cloud deployments.",
  keywords: [
    "Satyendra Kumar",
    "Software Developer",
    "Full Stack Developer",
    "React Developer",
    "Next.js Developer",
    "Node.js Developer",
    "Portfolio",
    "AI Integration",
    "Microservices",
  ],
  authors: [{ name: "Satyendra Kumar" }],
  openGraph: {
    title: "Satyendra Kumar – Software Developer",
    description:
      "Satyendra Kumar – Full-Stack Software Developer specialising in AI integration, microservices, React/Next.js, Node.js, and cloud deployments..",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5" />
        <meta name="theme-color" content="#060810" />
      </head>
      <body
        suppressHydrationWarning
        style={{ fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" }}
      >
        {children}
      </body>
    </html>
  );
}
