import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CarFinder Austria – Gebrauchtwagen Suche",
  description: "Durchsuche alle großen österreichischen Gebrauchtwagenportale auf einmal.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                  document.documentElement.classList.add('dark');
                }
              } catch(_) {}
            `,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
