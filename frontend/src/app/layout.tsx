import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Indian Compliance RAG - Legal Assistant",
  description:
    "Multi-agent RAG system for Indian legal compliance (DPDPA 2023, IT Act 2000, Companies Act 2013)",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className={inter.className}>
        <div className="h-full">{children}</div>
      </body>
    </html>
  );
}