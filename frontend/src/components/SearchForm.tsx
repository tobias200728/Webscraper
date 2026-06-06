"use client";

import { useState } from "react";
import { SearchParams } from "@/types/vehicle";
import { Search, SlidersHorizontal, X } from "lucide-react";
import clsx from "clsx";

const POPULAR_BRANDS = [
  "Audi", "BMW", "Fiat", "Ford", "Honda", "Hyundai", "Kia", "Mazda",
  "Mercedes-Benz", "Nissan", "Opel", "Peugeot", "Renault", "SEAT",
  "Skoda", "Toyota", "Volkswagen", "Volvo",
];

const MODELS_BY_BRAND: Record<string, string[]> = {
  Audi: ["A1", "A3", "A4", "A5", "A6", "A7", "A8", "Q2", "Q3", "Q5", "Q7", "Q8", "TT", "R8", "e-tron", "e-tron GT", "RS3", "RS4", "RS6", "S3", "S4", "S5"],
  BMW: ["1er", "2er", "3er", "4er", "5er", "6er", "7er", "8er", "X1", "X2", "X3", "X4", "X5", "X6", "X7", "Z4", "M2", "M3", "M4", "M5", "iX", "i3", "i4"],
  "Mercedes-Benz": ["A-Klasse", "B-Klasse", "C-Klasse", "E-Klasse", "S-Klasse", "CLA", "CLS", "GLA", "GLB", "GLC", "GLE", "GLS", "EQA", "EQB", "EQC", "EQE", "EQS", "SL", "AMG GT"],
  Volkswagen: ["Golf", "Polo", "Passat", "Tiguan", "T-Roc", "T-Cross", "Touareg", "Sharan", "Touran", "Caddy", "Arteon", "ID.3", "ID.4", "ID.5", "ID.6", "Up", "Scirocco"],
  Opel: ["Astra", "Corsa", "Insignia", "Mokka", "Crossland", "Grandland", "Zafira", "Meriva", "Adam", "Cascada", "Combo"],
  Ford: ["Fiesta", "Focus", "Mondeo", "Kuga", "Puma", "EcoSport", "Edge", "Explorer", "Mustang", "Ranger", "Transit", "Galaxy", "S-Max"],
  Skoda: ["Octavia", "Fabia", "Superb", "Kodiaq", "Karoq", "Kamiq", "Scala", "Enyaq", "Citigo", "Rapid"],
  Toyota: ["Yaris", "Corolla", "Camry", "RAV4", "C-HR", "Land Cruiser", "Prius", "Aygo", "GR86", "Supra", "Hilux", "Proace"],
  Renault: ["Clio", "Megane", "Laguna", "Twingo", "Captur", "Kadjar", "Koleos", "Scenic", "Talisman", "Zoe", "Kangoo"],
  Peugeot: ["108", "208", "308", "508", "2008", "3008", "5008", "Rifter", "Partner", "Traveller"],
  SEAT: ["Ibiza", "Leon", "Ateca", "Arona", "Tarraco", "Alhambra", "Toledo", "Mii", "Cupra Formentor"],
  Honda: ["Civic", "Jazz", "HR-V", "CR-V", "ZR-V", "e:Ny1", "Accord", "NSX", "Legend"],
  Hyundai: ["i10", "i20", "i30", "i40", "Tucson", "Santa Fe", "Kona", "IONIQ", "IONIQ 5", "IONIQ 6", "Nexo"],
  Kia: ["Picanto", "Rio", "Ceed", "Sportage", "Sorento", "Stinger", "Niro", "EV6", "Soul"],
  Mazda: ["Mazda2", "Mazda3", "Mazda6", "CX-3", "CX-30", "CX-5", "CX-60", "MX-5", "MX-30"],
  Nissan: ["Micra", "Juke", "Qashqai", "X-Trail", "Leaf", "Ariya", "Navara", "Note", "Pulsar"],
  Fiat: ["500", "Panda", "Tipo", "Bravo", "Punto", "500X", "500L", "Doblo", "Ducato"],
  Volvo: ["XC40", "XC60", "XC90", "S60", "S90", "V40", "V60", "V90", "C40", "EX30", "EX90"],
};

const COLORS = [
  "Schwarz", "Weiß", "Silber", "Grau", "Blau", "Rot",
  "Grün", "Braun", "Beige", "Orange", "Gelb", "Violett",
];

// Parst "20.000" oder "20,000" oder "20000" zuverlässig als 20000
function parseNumber(val: string): number | undefined {
  if (!val.trim()) return undefined;
  // Entferne Tausendertrennzeichen (Punkt oder Komma wenn danach 3 Stellen folgen)
  const cleaned = val.replace(/[.,](?=\d{3})/g, "").replace(",", ".");
  const num = parseFloat(cleaned);
  return isNaN(num) ? undefined : Math.round(num);
}

interface SearchFormProps {
  onSearch: (params: SearchParams) => void;
  isSearching: boolean;
  onStop: () => void;
}

export default function SearchForm({ onSearch, isSearching, onStop }: SearchFormProps) {
  const [brand, setBrand] = useState("");
  const [model, setModel] = useState("");
  const [color, setColor] = useState("");
  const [maxMileage, setMaxMileage] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!brand.trim() || !model.trim()) return;
    const params: SearchParams = {
      brand: brand.trim(),
      model: model.trim(),
      color: color || undefined,
      max_mileage: parseNumber(maxMileage),
      min_price: parseNumber(minPrice),
      max_price: parseNumber(maxPrice),
    };
    onSearch(params);
  };

  return (
    <form onSubmit={handleSubmit} className="card p-6 space-y-5">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
          <Search className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="font-bold text-lg">Fahrzeugsuche</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">Alle österreichischen Portale auf einmal</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Marke *</label>
          <input
            list="brands-list"
            className="input"
            placeholder="z.B. Volkswagen"
            value={brand}
            onChange={(e) => { setBrand(e.target.value); setModel(""); }}
            required
          />
          <datalist id="brands-list">
            {POPULAR_BRANDS.map((b) => <option key={b} value={b} />)}
          </datalist>
        </div>
        <div>
          <label className="label">Modell *</label>
          <input
            list="models-list"
            className="input"
            placeholder={brand && MODELS_BY_BRAND[brand] ? `z.B. ${MODELS_BY_BRAND[brand][0]}` : "z.B. Golf"}
            value={model}
            onChange={(e) => setModel(e.target.value)}
            required
          />
          <datalist id="models-list">
            {(MODELS_BY_BRAND[brand] ?? []).map((m) => <option key={m} value={m} />)}
          </datalist>
        </div>
      </div>

      {/* Preis — als Text-Input damit "20000" oder "20.000" beide funktionieren */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Preis von (€)</label>
          <input
            type="text"
            inputMode="numeric"
            className="input"
            placeholder="z.B. 5000"
            value={minPrice}
            onChange={(e) => setMinPrice(e.target.value)}
          />
        </div>
        <div>
          <label className="label">Preis bis (€)</label>
          <input
            type="text"
            inputMode="numeric"
            className="input"
            placeholder="z.B. 20000"
            value={maxPrice}
            onChange={(e) => setMaxPrice(e.target.value)}
          />
        </div>
      </div>

      <button
        type="button"
        className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 transition-colors"
        onClick={() => setShowAdvanced(!showAdvanced)}
      >
        <SlidersHorizontal className="w-4 h-4" />
        {showAdvanced ? "Weniger Filter" : "Weitere Filter"}
      </button>

      {showAdvanced && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-fade-in">
          <div>
            <label className="label">Farbe</label>
            <select className="input" value={color} onChange={(e) => setColor(e.target.value)}>
              <option value="">Alle Farben</option>
              {COLORS.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Max. Kilometerstand</label>
            <input
              type="text"
              inputMode="numeric"
              className="input"
              placeholder="z.B. 150000"
              value={maxMileage}
              onChange={(e) => setMaxMileage(e.target.value)}
            />
          </div>
        </div>
      )}

      <div className="flex gap-3 pt-1">
        <button
          type="submit"
          disabled={isSearching || !brand || !model}
          className={clsx("btn-primary flex-1 flex items-center justify-center gap-2", isSearching && "opacity-70")}
        >
          {isSearching ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Suche läuft...
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Jetzt suchen
            </>
          )}
        </button>
        {isSearching && (
          <button type="button" onClick={onStop} className="btn-secondary flex items-center gap-2">
            <X className="w-4 h-4" />
            Stop
          </button>
        )}
      </div>
    </form>
  );
}
