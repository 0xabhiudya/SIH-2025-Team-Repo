import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Uttar Pradesh Rivers & Economic Cities Atlas",
  description: "Interactive atlas of Uttar Pradesh rivers, cities, and economic data.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}

