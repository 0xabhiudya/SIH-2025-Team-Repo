# Uttar Pradesh Rivers & Economic Cities Atlas

A complete production-ready web application built with Next.js, TailwindCSS, React Leaflet, and Recharts. 
It visualizes the state and district boundaries, rivers, and the top 25 economic cities of Uttar Pradesh.

## Project Structure
```
up-atlas/
├── public/                 # Static assets
├── src/
│   ├── app/                # Next.js App Router layout, pages, and global styles
│   ├── components/         # Reusable React components (Sidebar, Map, Analytics Panel, etc.)
│   ├── data/               # Mock data (GeoJSON schemas, Cities, Rivers JSON)
│   └── lib/                # Utility functions
├── tailwind.config.ts      # Tailwind CSS configuration
├── tsconfig.json           # TypeScript configuration
└── package.json            # Project dependencies and scripts
```

## Setup & Installation

Ensure you have Node.js (v18+) installed.

```bash
# Navigate to the project directory
cd up-atlas

# Install dependencies
npm install
```

## Running the Application

To run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to see the result.

## Deployment to Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new).

1. Push your code to a GitHub repository.
2. Log in to Vercel and click "New Project".
3. Import your GitHub repository.
4. Vercel will automatically detect that it is a Next.js app and configure the build settings.
5. Click **Deploy**.

## Updating GIS Data

Currently, the application uses realistic placeholder GeoJSON structures for `upBoundaryGeoJSON` and `districtsGeoJSON`.
To update the maps with actual GIS data:
1. Obtain the authentic `.geojson` files for the UP boundary and districts.
2. Open `src/data/mockData.ts`.
3. Replace the `upBoundaryGeoJSON` and `districtsGeoJSON` constants with your actual data, ensuring it matches the expected GeoJSON FeatureCollection structure.

## Features

- **Interactive Map:** Pan, zoom, and explore UP.
- **Layers Toggle:** Toggle state boundary, districts, rivers, and cities.
- **City Visualizations:** Markers scaled by tier/economic importance with detailed popups.
- **River Visualizations:** Clickable rivers with length and tributary info.
- **Search:** Quickly navigate to a specific city.
- **Analytics:** View top 5 cities GDP and regional distribution in a floating panel.
