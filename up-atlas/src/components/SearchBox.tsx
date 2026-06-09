"use client";

import { useState } from "react";
import { Search } from "lucide-react";

interface SearchBoxProps {
  onSearch: (query: string) => void;
}

export default function SearchBox({ onSearch }: SearchBoxProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <form 
      onSubmit={handleSubmit}
      className="absolute top-4 left-1/2 -translate-x-1/2 w-96 bg-white rounded-full shadow-lg z-[1000] flex items-center px-4 py-2 border border-slate-200"
    >
      <Search className="w-5 h-5 text-slate-400 mr-2" />
      <input
        type="text"
        placeholder="Search cities, districts, rivers..."
        className="flex-1 outline-none text-slate-700 bg-transparent"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
    </form>
  );
}
