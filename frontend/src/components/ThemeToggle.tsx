"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

export default function ThemeToggle() {
  const [dark, setDark] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setDark(document.documentElement.classList.contains("dark"));
  }, []);

  function toggle() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("trisp-theme", next ? "dark" : "light");
    } catch {}
  }

  if (!mounted) return <div className="h-9 w-9" />;
  return (
    <button
      onClick={toggle}
      aria-label="Переключить тему"
      className="inline-flex h-9 w-9 items-center justify-center rounded-xl border transition hover:scale-105"
      style={{ borderColor: "var(--border)" }}
    >
      {dark ? <Sun size={16} className="text-amber-400" /> : <Moon size={16} />}
    </button>
  );
}
