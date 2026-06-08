"use client";

import { CheckSquare, Square } from "lucide-react";
import { cities, rivers, districtsGeoJSON } from "@/data/mockData";

interface SidebarProps {
  layers: {
    boundary: boolean;
    districts: boolean;
    rivers: boolean;
    cities: boolean;
    heatmap: boolean;
  };
  setLayers: (layers: any) => void;
}

export default function Sidebar({ layers, setLayers }: SidebarProps) {
  const toggleLayer = (key: keyof typeof layers) => {
    setLayers({ ...layers, [key]: !layers[key] });
  };

  return (
    <div className="w-80 bg-white shadow-xl h-full flex flex-col p-4 z-10 overflow-y-auto">
      <h2 className="text-xl font-bold mb-6 text-slate-800">UP Atlas Controls</h2>

      <div className="mb-8">
        <h3 className="text-md font-semibold mb-3 text-slate-700">Map Layers</h3>
        <div className="space-y-3">
          {Object.entries(layers).map(([key, value]) => (
            <button
              key={key}
              onClick={() => toggleLayer(key as any)}
              className="flex items-center space-x-2 w-full text-left hover:bg-slate-50 p-2 rounded"
            >
              {value ? <CheckSquare className="text-blue-600" /> : <Square className="text-slate-400" />}
              <span className="capitalize text-slate-700">{key}</span>
            </button>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-md font-semibold mb-3 text-slate-700">Statistics</h3>
        <div className="bg-slate-50 p-4 rounded-lg space-y-2 text-sm text-slate-600">
          <div className="flex justify-between">
            <span>Total Rivers:</span>
            <span className="font-bold text-slate-800">{rivers.length}</span>
          </div>
          <div className="flex justify-between">
            <span>Total Cities:</span>
            <span className="font-bold text-slate-800">{cities.length}</span>
          </div>
          <div className="flex justify-between">
            <span>Districts:</span>
            <span className="font-bold text-slate-800">75 (Mocked: {districtsGeoJSON.features.length})</span>
          </div>
          <div className="flex justify-between">
            <span>Largest Economic Center:</span>
            <span className="font-bold text-slate-800">{cities[0].name}</span>
          </div>
          <div className="flex justify-between">
            <span>Longest River:</span>
            <span className="font-bold text-slate-800">Ganga (2525 km)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
