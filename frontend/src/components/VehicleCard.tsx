"use client";

import { useState } from "react";
import { Vehicle } from "@/types/vehicle";
import {
  MapPin, Gauge, Calendar, Zap, Fuel,
  ExternalLink, ChevronLeft, ChevronRight, Tag,
} from "lucide-react";
import clsx from "clsx";

const SOURCE_LABELS: Record<string, { label: string; color: string }> = {
  willhaben:       { label: "willhaben",       color: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" },
  autoscout24:     { label: "AutoScout24 AT",  color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200" },
  autoscout24_de:  { label: "AutoScout24 DE",  color: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200" },
};

const RATING: Record<string, { style: string; label: string }> = {
  cheap:     { style: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300", label: "Günstig" },
  average:   { style: "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400",             label: "Durchschnitt" },
  expensive: { style: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",                 label: "Teuer" },
};

export default function VehicleCard({ vehicle }: { vehicle: Vehicle }) {
  const [imgIdx, setImgIdx] = useState(0);
  const [imgError, setImgError] = useState(false);

  const images = vehicle.image_urls ?? [];
  const hasImg = images.length > 0 && !imgError;
  const source = SOURCE_LABELS[vehicle.source] ?? { label: vehicle.source, color: "bg-gray-100 text-gray-700" };
  const rating = vehicle.price_rating ? RATING[vehicle.price_rating] : null;

  return (
    <article className="card overflow-hidden flex flex-col group hover:shadow-md hover:border-blue-200 dark:hover:border-blue-800 transition-all duration-200 animate-slide-up">

      {/* Bild */}
      <div className="relative bg-gray-100 dark:bg-gray-800 aspect-[16/10] overflow-hidden">
        {hasImg ? (
          <>
            <img
              src={images[imgIdx]}
              alt={vehicle.title}
              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              onError={() => setImgError(true)}
            />
            {images.length > 1 && (
              <>
                <button
                  onClick={(e) => { e.preventDefault(); setImgIdx((i) => (i - 1 + images.length) % images.length); }}
                  className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => { e.preventDefault(); setImgIdx((i) => (i + 1) % images.length); }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
                <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                  {images.slice(0, 6).map((_, i) => (
                    <button
                      key={i}
                      onClick={(e) => { e.preventDefault(); setImgIdx(i); }}
                      className={clsx("w-1.5 h-1.5 rounded-full transition-colors", i === imgIdx ? "bg-white" : "bg-white/50")}
                    />
                  ))}
                </div>
              </>
            )}
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300 dark:text-gray-600">
            <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )}
        <div className="absolute top-2 left-2">
          <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full", source.color)}>
            {source.label}
          </span>
        </div>
      </div>

      {/* Inhalt */}
      <div className="p-4 flex flex-col gap-3 flex-1">
        <h3 className="font-semibold text-base leading-tight line-clamp-2">{vehicle.title}</h3>

        <div className="flex items-center gap-2 flex-wrap">
          {vehicle.price ? (
            <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {vehicle.price.toLocaleString("de-AT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })}
            </span>
          ) : (
            <span className="text-gray-400 italic text-sm">Preis auf Anfrage</span>
          )}
          {rating && (
            <span className={clsx("flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full", rating.style)}>
              <Tag className="w-3 h-3" />
              {rating.label}
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-2 text-sm">
          {vehicle.mileage != null && (
            <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
              <Gauge className="w-3.5 h-3.5 shrink-0" />
              {vehicle.mileage.toLocaleString("de-AT")} km
            </div>
          )}
          {vehicle.year && (
            <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
              <Calendar className="w-3.5 h-3.5 shrink-0" />
              {vehicle.year}
            </div>
          )}
          {vehicle.power_kw && (
            <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
              <Zap className="w-3.5 h-3.5 shrink-0" />
              {vehicle.power_kw} kW ({Math.round(vehicle.power_kw * 1.36)} PS)
            </div>
          )}
          {vehicle.fuel && (
            <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
              <Fuel className="w-3.5 h-3.5 shrink-0" />
              {vehicle.fuel}
            </div>
          )}
          {vehicle.location && (
            <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400 col-span-2">
              <MapPin className="w-3.5 h-3.5 shrink-0" />
              <span className="truncate">{vehicle.location}</span>
            </div>
          )}
        </div>

        <a
          href={vehicle.listing_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-auto btn-primary text-sm flex items-center justify-center gap-2 py-2.5"
        >
          Inserat öffnen
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>
    </article>
  );
}
