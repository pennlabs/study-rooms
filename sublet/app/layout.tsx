import type { Metadata } from "next";

import localFont from "next/font/local";
//import { Inter } from "next/font/google";
import "./globals.css";

//const inter = Inter({ subsets: ["latin"] });

import { Toaster } from "@/components/ui/toaster"

const satoshi = localFont({
  src: '../fonts/satoshi/Satoshi-Variable.woff2',
  display: 'swap',
})

export const metadata: Metadata = {
  title: "Sublet@Portal",
  description: "Welcome to Sublet@Portal. The best place to sublet your room to other students!",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={satoshi.className}>
        <div className="">
          {children}
        </div>
        <Toaster />
      </body>
    </html>
  );
}
