"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, GeoJSON, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { cities, rivers, upBoundaryGeoJSON, districtsGeoJSON } from "@/data/mockData";

// Fix for default leaflet icons in Next.js
const iconRetinaUrl = 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png';
const iconUrl = 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png';
const shadowUrl = 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png';

const getIcon = (tier: number) => {
  const size = tier === 1 ? 35 : tier === 2 ? 25 : 18;
  return new L.Icon({
    iconUrl,
    iconRetinaUrl,
    shadowUrl,
    iconSize: [size, size * 1.5],
    iconAnchor: [size / 2, size * 1.5],
    popupAnchor: [0, -size * 1.5],
  });
};

interface MapProps {
  layers: {
    boundary: boolean;
    districts: boolean;
    rivers: boolean;
    cities: boolean;
    heatmap: boolean;
  };
  searchQuery: string;
  selectedRiver: number | null;
  setSelectedRiver: (id: number | null) => void;
}

const MapController = ({ center, zoom }: { center: [number, number]; zoom: number }) => {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, zoom);
  }, [center, zoom, map]);
  return null;
};

export default function UPMap({ layers, searchQuery, selectedRiver, setSelectedRiver }: MapProps) {
  const [center, setCenter] = useState<[number, number]>([27.0, 80.0]);
  const [zoom, setZoom] = useState(6);

  useEffect(() => {
    if (searchQuery) {
      const city = cities.find((c) => c.name.toLowerCase() === searchQuery.toLowerCase());
      if (city) {
        setCenter([city.lat, city.lng]);
        setZoom(10);
      }
    }
  }, [searchQuery]);

  return (
    <div className="h-full w-full z-0">
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: "100%", width: "100%" }}
        zoomControl={false}
      >
        <MapController center={center} zoom={zoom} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />

        {layers.boundary && (
          <GeoJSON
            data={upBoundaryGeoJSON as any}
            style={{ color: "#000", weight: 3, fillOpacity: 0 }}
          />
        )}

        {layers.districts && (
          <GeoJSON
            data={districtsGeoJSON as any}
            style={{ color: "#888", weight: 1, fillOpacity: 0.1 }}
            onEachFeature={(feature, layer) => {
              layer.bindTooltip(feature.properties.name);
            }}
          />
        )}

        {layers.rivers &&
          rivers.map((river) => {
            const isSelected = selectedRiver === river.id;
            const opacity = selectedRiver === null || isSelected ? 1 : 0.2;
            const weight = isSelected ? 5 : 3;

            return (
              <Polyline
                key={river.id}
                positions={river.latlngs as [number, number][]}
                pathOptions={{ color: "#2563EB", weight, opacity }}
                eventHandlers={{
                  click: () => setSelectedRiver(isSelected ? null : river.id),
                }}
              >
                <Popup>
                  <div className="font-bold">{river.name}</div>
                  <div>Length: {river.length} km</div>
                  <div>Tributaries: {river.tributaries}</div>
                </Popup>
              </Polyline>
            );
          })}

        {layers.cities &&
          cities.map((city) => (
            <Marker
              key={city.id}
              position={[city.lat, city.lng]}
              icon={getIcon(city.tier)}
            >
              <Popup>
                <div className="min-w-[200px]">
                  <h3 className="font-bold text-lg mb-1">{city.name}</h3>
                  <div className="text-sm space-y-1">
                    <p><span className="font-semibold">District:</span> {city.district}</p>
                    <p><span className="font-semibold">Population:</span> {city.pop.toLocaleString()}</p>
                    <p><span className="font-semibold">Profile:</span> {city.profile}</p>
                    <p><span className="font-semibold">Industries:</span> {city.industries}</p>
                    <p><span className="font-semibold">GDP Rank:</span> {city.gdpRank}</p>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
      </MapContainer>
    </div>
  );
}
