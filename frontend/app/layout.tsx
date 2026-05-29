import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://markitdoc.vercel.app"),
  title: "MarkIt — Prepare Documents for AI",
  description: "Get more from Claude & ChatGPT with clean Markdown.",
  openGraph: {
    title: "MarkIt — Prepare Documents for AI",
    description: "Get more from Claude & ChatGPT with clean Markdown.",
    url: "https://doc2md-one.vercel.app",
    siteName: "MarkIt",
    images: [
      {
        url: "/bg1.png",
        width: 1200,
        height: 630,
        alt: "MarkIt — AI-Ready Markdown",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "MarkIt — Prepare Documents for AI",
    description: "Get more from Claude & ChatGPT with clean Markdown.",
    images: ["/bg1.png"],
  },
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport = {
  themeColor: "#2563EB",
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
