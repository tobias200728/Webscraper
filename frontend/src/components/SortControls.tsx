"use client";

import { SortOption } from "@/types/vehicle";
import { ArrowUpDown } from "lucide-react";
import clsx from "clsx";

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "price_asc", label: "Preis ↑" },
  { value: "price_desc", label: "Preis ↓" },
  { value: "mileage_asc", label: "km ↑" },
  { value: "year_desc", label: "Neuste zuerst" },
  { value: "year_asc", label: "Älteste zuerst" },
];

interface SortControlsProps {
  current: SortOption;
  onChange: (sort: SortOption) => void;
  totalCount: number;
}

export default function SortControls({ current, onChange, totalCount }: SortControlsProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="text-sm text-gray-500 dark:text-gray-400">
        <span className="font-semibold text-gray-900 dark:text-gray-100">{totalCount}</span> Ergebnisse gefunden
      </p>
      <div className="flex items-center gap-2">
        <ArrowUpDown className="w-4 h-4 text-gray-400" />
        <div className="flex gap-1 flex-wrap">
          {SORT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onChange(opt.value)}
              className={clsx(
                "text-xs font-medium px-3 py-1.5 rounded-lg transition-all",
                current === opt.value
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700",
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
