"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import Sidebar from "@/components/Sidebar";
import SearchBox from "@/components/SearchBox";
import AnalyticsPanel from "@/components/AnalyticsPanel";
import { BarChart3 } from "lucide-react";

// Dynamically import map to avoid SSR issues with leaflet
const UPMap = dynamic(() => import("@/components/Map"), { ssr: false });

export default function Home() {
  const [layers, setLayers] = useState({
    boundary: true,
    districts: true,
    rivers: true,
    cities: true,
    heatmap: false,
  });

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRiver, setSelectedRiver] = useState<number | null>(null);
  const [showAnalytics, setShowAnalytics] = useState(false);

  return (
    <main className="flex h-screen w-screen overflow-hidden bg-[#F8FAFC]">
      {/* Sidebar */}
      <Sidebar layers={layers} setLayers={setLayers} />

      {/* Main Map Area */}
      <div className="flex-1 relative">
        <SearchBox onSearch={setSearchQuery} />
        
        <button
          onClick={() => setShowAnalytics(!showAnalytics)}
          className="absolute top-4 right-4 bg-white p-3 rounded-full shadow-lg z-[1000] border border-slate-200 hover:bg-slate-50 transition-colors"
          title="Toggle Analytics"
        >
          <BarChart3 className="w-6 h-6 text-[#2563EB]" />
        </button>

        {showAnalytics && <AnalyticsPanel onClose={() => setShowAnalytics(false)} />}

        <div className="absolute inset-0 z-0">
          <UPMap 
            layers={layers} 
            searchQuery={searchQuery} 
            selectedRiver={selectedRiver}
            setSelectedRiver={setSelectedRiver}
          />
        </div>
      </div>
    </main>
  );
}
