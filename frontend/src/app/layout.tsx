import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TRISP — Радар рисков и сезонности для путешественников",
  description:
    "Анализ климатической истории за 10 лет, геополитических рисков, стихийных бедствий и генерация Плана Б для вашей поездки.",
};

const themeInit = `
(function() {
  try {
    var stored = localStorage.getItem('trisp-theme');
    var dark = stored ? stored === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (dark) document.documentElement.classList.add('dark');
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
