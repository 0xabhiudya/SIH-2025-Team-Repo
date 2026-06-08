"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { cities } from "@/data/mockData";
import { X } from "lucide-react";
import { motion } from "framer-motion";

export default function AnalyticsPanel({ onClose }: { onClose: () => void }) {
  const topCities = cities.slice(0, 5).map(c => ({ name: c.name, GDP: 26 - c.gdpRank }));
  
  const regions = [
    { name: "Western UP", value: 12 },
    { name: "Central UP", value: 5 },
    { name: "Eastern UP", value: 6 },
    { name: "Bundelkhand", value: 2 },
  ];
  const COLORS = ['#2563EB', '#0EA5E9', '#14B8A6', '#F59E0B'];

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95, y: -20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: -20 }}
      transition={{ duration: 0.3 }}
      className="absolute right-4 top-20 w-96 bg-white shadow-xl rounded-lg p-4 z-[1000] border border-slate-100"
    >
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-bold text-slate-800">Analytics Dashboard</h3>
        <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded-full">
          <X className="w-5 h-5 text-slate-500" />
        </button>
      </div>

      <div className="mb-6">
        <h4 className="text-sm font-semibold text-slate-600 mb-2">Top 5 Economic Cities</h4>
        <div className="h-48 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topCities} layout="vertical" margin={{ left: 20 }}>
              <XAxis type="number" hide />
              <YAxis dataKey="name" type="category" width={80} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="GDP" fill="#2563EB" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div>
        <h4 className="text-sm font-semibold text-slate-600 mb-2">Regional Economic Distribution</h4>
        <div className="h-48 w-full flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={regions}
                innerRadius={40}
                outerRadius={60}
                paddingAngle={5}
                dataKey="value"
              >
                {regions.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </motion.div>
  );
}
