"use client";

import { useState, useRef, useCallback } from "react";
import { Vehicle, SearchParams, SortOption } from "@/types/vehicle";
import { streamSearch } from "@/lib/api";
import Header from "@/components/Header";
import SearchForm from "@/components/SearchForm";
import SortControls from "@/components/SortControls";
import VehicleCard from "@/components/VehicleCard";
import LoadingBar from "@/components/LoadingBar";
import { AlertCircle, SearchX, Car } from "lucide-react";

function sortVehicles(vehicles: Vehicle[], sort: SortOption): Vehicle[] {
  return [...vehicles].sort((a, b) => {
    switch (sort) {
      case "price_asc":    return (a.price ?? Infinity) - (b.price ?? Infinity);
      case "price_desc":   return (b.price ?? -Infinity) - (a.price ?? -Infinity);
      case "mileage_asc":  return (a.mileage ?? Infinity) - (b.mileage ?? Infinity);
      case "year_desc":    return (b.year ?? 0) - (a.year ?? 0);
      case "year_asc":     return (a.year ?? 9999) - (b.year ?? 9999);
      default:             return 0;
    }
  });
}

export default function HomePage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortOption>("price_asc");
  const [hasSearched, setHasSearched] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const handleSearch = useCallback(async (params: SearchParams) => {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setVehicles([]);
    setError(null);
    setIsSearching(true);
    setHasSearched(true);

    try {
      for await (const vehicle of streamSearch(params, ctrl.signal)) {
        if (ctrl.signal.aborted) break;
        setVehicles((prev) =>
          prev.some((v) => v.id === vehicle.id) ? prev : [...prev, vehicle]
        );
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") return;
      const msg = err instanceof Error ? err.message : "Unbekannter Fehler";
      setError(`Suche fehlgeschlagen: ${msg} — Ist das Backend gestartet? (uvicorn app.main:app --reload)`);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
    setIsSearching(false);
  }, []);

  const sorted = sortVehicles(vehicles, sortBy);

  return (
    <div className="min-h-screen flex flex-col">
      <LoadingBar isVisible={isSearching} />
      <Header />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-8 space-y-8">

        {/* Hero — nur vor der ersten Suche */}
        {!hasSearched && (
          <div className="text-center py-6 space-y-3 animate-fade-in">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
              Gebrauchtwagen in <span className="text-blue-600">Österreich</span>
            </h1>
            <p className="text-gray-500 dark:text-gray-400 max-w-xl mx-auto">
              Alle großen österreichischen Fahrzeugportale gleichzeitig durchsuchen.
              Ergebnisse erscheinen live.
            </p>
            <div className="flex flex-wrap justify-center gap-3 text-sm text-gray-400 pt-2">
              {["willhaben.at", "AutoScout24", "mobile.de", "gebrauchtwagen.at", "autoinserat.at"].map((s) => (
                <span key={s} className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" />
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Suchformular */}
        <SearchForm onSearch={handleSearch} isSearching={isSearching} onStop={handleStop} />

        {/* Fehler */}
        {error && (
          <div className="flex items-start gap-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-xl p-4 text-red-700 dark:text-red-300 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <p>{error}</p>
          </div>
        )}

        {/* Live-Indikator */}
        {isSearching && vehicles.length > 0 && (
          <div className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
            <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            Suche läuft — {vehicles.length} Inserate gefunden...
          </div>
        )}

        {/* Ergebnisse */}
        {vehicles.length > 0 && (
          <div className="space-y-4">
            <SortControls current={sortBy} onChange={setSortBy} totalCount={vehicles.length} />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {sorted.map((vehicle) => (
                <VehicleCard key={vehicle.id} vehicle={vehicle} />
              ))}
            </div>
          </div>
        )}

        {/* Leer-Zustand */}
        {hasSearched && !isSearching && vehicles.length === 0 && !error && (
          <div className="text-center py-16 text-gray-400 dark:text-gray-600">
            <SearchX className="w-12 h-12 mx-auto mb-3" />
            <p className="text-lg font-medium">Keine Ergebnisse</p>
            <p className="text-sm mt-1">Versuche es mit anderen Suchbegriffen oder weiteren Filtern.</p>
          </div>
        )}
      </main>

      <footer className="text-center text-xs text-gray-400 dark:text-gray-600 py-6 border-t border-gray-100 dark:border-gray-800">
        CarFinder Austria — Ergebnisse werden direkt von den Portalen geladen und nicht gespeichert.
      </footer>
    </div>
  );
}
