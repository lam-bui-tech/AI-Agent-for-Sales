import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "DemoTech Sales Copilot",
  description: "AI Sales Copilot Dashboard & Simulator - Linear & Intercom style",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-[#f8fafc] text-slate-900 selection:bg-blue-100 selection:text-blue-900">
        {children}
      </body>
    </html>
  );
}
