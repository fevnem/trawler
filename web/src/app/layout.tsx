import type { Metadata } from "next";
import { Archivo, Geist_Mono } from "next/font/google";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

const archivo = Archivo({
  subsets: ["latin"],
  axes: ["wdth"],
  variable: "--font-archivo",
  display: "swap",
});

const mono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono-code",
  display: "swap",
});

export const metadata: Metadata = {
  title: "trawler",
  description: "Paste a link, take the file. Video, audio, GIF and trimmed clips from 1,751 sites.",
  openGraph: {
    title: "trawler",
    description: "Paste a link, take the file.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${archivo.variable} ${mono.variable}`}>
      <body className="min-h-[100dvh]">
        <div className="mx-auto flex min-h-[100dvh] w-full max-w-[1400px] flex-col px-5 sm:px-8">
          <SiteHeader />
          <div className="flex flex-1 flex-col">{children}</div>
          <SiteFooter />
        </div>
      </body>
    </html>
  );
}
