import React, { useEffect, useRef, useState } from 'react';
import { MapPin, Navigation, Clock } from 'lucide-react';

interface TrackingMapProps {
  userLocation: { lat: number; lng: number };
  techLocation: { lat: number; lng: number };
  techName?: string;
  eta?: number; // ETA in minutes
  autoRefresh?: boolean; // Auto-refresh location every 10 seconds
  onRefresh?: () => void;
}

export const TrackingMap: React.FC<TrackingMapProps> = ({
  userLocation,
  techLocation,
  techName = 'Tecnico',
  eta,
  autoRefresh = false,
  onRefresh
}) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [userMarker, setUserMarker] = useState<google.maps.Marker | null>(null);
  const [techMarker, setTechMarker] = useState<google.maps.Marker | null>(null);
  const [routeLine, setRouteLine] = useState<google.maps.Polyline | null>(null);
  const [directionsRenderer, setDirectionsRenderer] = useState<google.maps.DirectionsRenderer | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [mapError, setMapError] = useState<string | null>(null);

  // Initialize Google Maps
  useEffect(() => {
    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

    if (!apiKey) {
      console.warn('Google Maps API key not found. Add VITE_GOOGLE_MAPS_API_KEY to .env file');
      setMapError('Google Maps API key not configured');
      setIsLoading(false);
      return;
    }

    // Check if Google Maps is already loaded
    if (window.google && window.google.maps) {
      initializeMap();
      return;
    }

    // Load Google Maps script
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=geometry,places`;
    script.async = true;
    script.defer = true;
    script.onload = () => {
      initializeMap();
    };
    script.onerror = () => {
      setMapError('Failed to load Google Maps');
      setIsLoading(false);
    };
    document.head.appendChild(script);

    return () => {
      // Cleanup script if needed
      if (script.parentNode) {
        script.parentNode.removeChild(script);
      }
    };
  }, []);

  const initializeMap = () => {
    if (!mapRef.current) return;

    try {
      // Calculate center point between user and tech
      const centerLat = (userLocation.lat + techLocation.lat) / 2;
      const centerLng = (userLocation.lng + techLocation.lng) / 2;

      // Create map
      const newMap = new google.maps.Map(mapRef.current, {
        center: { lat: centerLat, lng: centerLng },
        zoom: 14,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: true,
        zoomControl: true,
        styles: [
          {
            featureType: 'poi',
            elementType: 'labels',
            stylers: [{ visibility: 'off' }]
          }
        ]
      });

      // Create user marker (blue pin)
      const newUserMarker = new google.maps.Marker({
        position: userLocation,
        map: newMap,
        title: 'Tu ubicacion',
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 10,
          fillColor: '#3B82F6',
          fillOpacity: 1,
          strokeColor: '#FFFFFF',
          strokeWeight: 3
        }
      });

      // Create tech marker (car icon)
      const newTechMarker = new google.maps.Marker({
        position: techLocation,
        map: newMap,
        title: techName,
        icon: {
          path: 'M17.402,0H5.643C2.526,0,0,3.467,0,6.584v34.804c0,3.116,2.526,5.644,5.643,5.644h11.759c3.116,0,5.644-2.527,5.644-5.644 V6.584C23.044,3.467,20.518,0,17.402,0z M22.057,14.188v11.665l-2.729,0.351v-4.806L22.057,14.188z M20.625,10.773 c-1.016,3.9-2.219,8.51-2.219,8.51H4.638l-2.222-8.51C2.417,10.773,11.3,7.755,20.625,10.773z M3.748,21.713v4.492l-2.73-0.349 V14.502L3.748,21.713z M1.018,37.938V27.579l2.73,0.343v8.196L1.018,37.938z M2.575,40.882l2.218-3.336h13.771l2.219,3.336H2.575z M19.328,35.805v-7.872l2.729-0.355v10.048L19.328,35.805z',
          fillColor: '#10B981',
          fillOpacity: 1,
          strokeColor: '#FFFFFF',
          strokeWeight: 2,
          scale: 0.7,
          anchor: new google.maps.Point(12, 24)
        }
      });

      // Create directions renderer
      const newDirectionsRenderer = new google.maps.DirectionsRenderer({
        map: newMap,
        suppressMarkers: true, // We use custom markers
        polylineOptions: {
          strokeColor: '#3B82F6',
          strokeWeight: 4,
          strokeOpacity: 0.7
        }
      });

      // Draw route
      const directionsService = new google.maps.DirectionsService();
      directionsService.route(
        {
          origin: techLocation,
          destination: userLocation,
          travelMode: google.maps.TravelMode.DRIVING
        },
        (result, status) => {
          if (status === google.maps.DirectionsStatus.OK && result) {
            newDirectionsRenderer.setDirections(result);
          }
        }
      );

      // Fit bounds to show both markers
      const bounds = new google.maps.LatLngBounds();
      bounds.extend(userLocation);
      bounds.extend(techLocation);
      newMap.fitBounds(bounds);

      // Add some padding
      const padding = { top: 50, right: 50, bottom: 50, left: 50 };
      newMap.fitBounds(bounds, padding);

      setMap(newMap);
      setUserMarker(newUserMarker);
      setTechMarker(newTechMarker);
      setDirectionsRenderer(newDirectionsRenderer);
      setIsLoading(false);
    } catch (error) {
      console.error('Error initializing map:', error);
      setMapError('Error initializing map');
      setIsLoading(false);
    }
  };

  // Update markers when locations change
  useEffect(() => {
    if (!map || !userMarker || !techMarker || !directionsRenderer) return;

    // Update user marker position
    userMarker.setPosition(userLocation);

    // Animate tech marker position
    techMarker.setPosition(techLocation);

    // Update route
    const directionsService = new google.maps.DirectionsService();
    directionsService.route(
      {
        origin: techLocation,
        destination: userLocation,
        travelMode: google.maps.TravelMode.DRIVING
      },
      (result, status) => {
        if (status === google.maps.DirectionsStatus.OK && result) {
          directionsRenderer.setDirections(result);
        }
      }
    );

    // Adjust bounds
    const bounds = new google.maps.LatLngBounds();
    bounds.extend(userLocation);
    bounds.extend(techLocation);
    map.fitBounds(bounds);
  }, [userLocation, techLocation, map, userMarker, techMarker, directionsRenderer]);

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh || !onRefresh) return;

    const interval = setInterval(() => {
      onRefresh();
    }, 10000); // Every 10 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, onRefresh]);

  if (mapError) {
    return (
      <div className="w-full h-96 bg-gradient-to-br from-blue-100 to-purple-100 rounded-xl flex items-center justify-center border-2 border-dashed border-blue-300">
        <div className="text-center text-blue-700">
          <MapPin size={48} className="mx-auto mb-4 opacity-50" />
          <p className="font-medium">{mapError}</p>
          <p className="text-sm text-blue-600 mt-2">
            Mostrando informacion de ubicacion sin mapa
          </p>
          <div className="mt-4 space-y-2 text-left max-w-xs mx-auto">
            <div className="p-3 bg-white rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span className="font-medium">Tu ubicacion</span>
              </div>
              <p className="text-xs text-gray-600">
                {userLocation.lat.toFixed(6)}, {userLocation.lng.toFixed(6)}
              </p>
            </div>
            <div className="p-3 bg-white rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Navigation className="text-green-500" size={16} />
                <span className="font-medium">{techName}</span>
              </div>
              <p className="text-xs text-gray-600">
                {techLocation.lat.toFixed(6)}, {techLocation.lng.toFixed(6)}
              </p>
              {eta && (
                <p className="text-sm font-bold text-green-700 mt-1">
                  <Clock className="inline mr-1" size={14} />
                  Llegada en {eta} min
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-96 rounded-xl overflow-hidden shadow-lg">
      {isLoading && (
        <div className="absolute inset-0 bg-gray-100 flex items-center justify-center z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-gray-600">Cargando mapa...</p>
          </div>
        </div>
      )}
      <div ref={mapRef} className="w-full h-full" />

      {/* ETA Badge */}
      {eta && !isLoading && (
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg px-4 py-2 flex items-center gap-2 z-10">
          <Clock className="text-blue-600" size={20} />
          <div>
            <p className="text-xs text-gray-600">Llegada estimada</p>
            <p className="text-lg font-bold text-blue-900">{eta} min</p>
          </div>
        </div>
      )}

      {/* Tech Info Badge */}
      {!isLoading && (
        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg px-4 py-2 z-10">
          <div className="flex items-center gap-2">
            <Navigation className="text-green-500" size={20} />
            <div>
              <p className="text-xs text-gray-600">Tecnico en camino</p>
              <p className="font-bold text-gray-900">{techName}</p>
            </div>
          </div>
        </div>
      )}

      {/* Auto-refresh indicator */}
      {autoRefresh && !isLoading && (
        <div className="absolute top-4 right-4 bg-green-500 text-white text-xs px-2 py-1 rounded-full shadow-lg z-10 flex items-center gap-1">
          <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
          Live
        </div>
      )}
    </div>
  );
};
