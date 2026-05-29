import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Doc2LLM",
  description: "Convert files into clean, LLM-friendly Markdown.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
