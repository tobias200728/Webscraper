"use client";

import { useState, useEffect } from "react";
import { Car, Moon, Sun } from "lucide-react";

export default function Header() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    setIsDark(document.documentElement.classList.contains("dark"));
  }, []);

  const toggleTheme = () => {
    const next = !isDark;
    setIsDark(next);
    document.documentElement.classList.toggle("dark", next);
    try { localStorage.setItem("theme", next ? "dark" : "light"); } catch {}
  };

  return (
    <header className="sticky top-0 z-40 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md border-b border-gray-100 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center">
            <Car className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg">
            CarFinder <span className="text-blue-600">Austria</span>
          </span>
          <span className="hidden sm:block text-xs text-gray-400 dark:text-gray-500 border-l border-gray-200 dark:border-gray-700 pl-3 ml-1">
            Gebrauchtwagen-Aggregator
          </span>
        </div>
        <button
          onClick={toggleTheme}
          className="btn-secondary p-2"
          title="Dunkelmodus umschalten"
        >
          {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </header>
  );
}
