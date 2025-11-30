"""
Google Maps API Service for SegurifAI x PAQ
============================================

Provides location services including:
- Geocoding (address to coordinates)
- Reverse Geocoding (coordinates to address)
- Directions & Route calculation
- Distance Matrix (distance/time between points)
- ETA calculation with traffic

Required Google Cloud APIs:
1. Maps JavaScript API (frontend)
2. Directions API
3. Distance Matrix API
4. Geocoding API
5. Places API

Author: SegurifAI Development Team
"""

import requests
import logging
from typing import Optional, Dict, List, Tuple
from django.conf import settings
from math import radians, cos, sin, asin, sqrt

logger = logging.getLogger('segurifai.maps')

# Google Maps API Base URLs
GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
# Use Places API (New) - the legacy endpoint requires old Places API
PLACES_AUTOCOMPLETE_URL = "https://places.googleapis.com/v1/places:autocomplete"


def get_api_key() -> str:
    """Get the Google Maps API key from settings."""
    key = getattr(settings, 'GOOGLE_MAPS_SERVER_KEY', '') or getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
    if not key:
        logger.warning("Google Maps API key not configured")
    return key


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on earth (in km).

    This is a fallback when Google Maps API is not available.

    Args:
        lat1, lon1: Origin coordinates
        lat2, lon2: Destination coordinates

    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # Earth's radius in kilometers
    r = 6371

    return c * r


def geocode_address(address: str) -> Optional[Dict]:
    """
    Convert an address to coordinates using Google Geocoding API.

    Args:
        address: Human-readable address string

    Returns:
        Dict with lat, lng, formatted_address or None if failed
    """
    api_key = get_api_key()
    if not api_key:
        logger.error("Geocoding failed: No API key")
        return None

    try:
        response = requests.get(GEOCODING_URL, params={
            'address': address,
            'key': api_key,
            'region': 'gt',  # Guatemala bias
            'language': 'es'
        }, timeout=10)

        data = response.json()

        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            location = result['geometry']['location']
            return {
                'lat': location['lat'],
                'lng': location['lng'],
                'formatted_address': result['formatted_address'],
                'place_id': result.get('place_id')
            }
        else:
            logger.warning(f"Geocoding failed: {data['status']}")
            return None

    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return None


def reverse_geocode(lat: float, lng: float) -> Optional[Dict]:
    """
    Convert coordinates to an address using Google Geocoding API.

    Args:
        lat: Latitude
        lng: Longitude

    Returns:
        Dict with formatted_address and components or None if failed
    """
    api_key = get_api_key()
    if not api_key:
        return None

    try:
        response = requests.get(GEOCODING_URL, params={
            'latlng': f'{lat},{lng}',
            'key': api_key,
            'language': 'es'
        }, timeout=10)

        data = response.json()

        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            return {
                'formatted_address': result['formatted_address'],
                'place_id': result.get('place_id'),
                'components': {
                    comp['types'][0]: comp['long_name']
                    for comp in result.get('address_components', [])
                    if comp.get('types')
                }
            }
        return None

    except Exception as e:
        logger.error(f"Reverse geocoding error: {e}")
        return None


def get_directions(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    mode: str = 'driving'
) -> Optional[Dict]:
    """
    Get directions between two points using Google Directions API.

    Args:
        origin: (lat, lng) tuple
        destination: (lat, lng) tuple
        mode: 'driving', 'walking', 'bicycling', 'transit'

    Returns:
        Dict with route information including distance, duration, polyline
    """
    api_key = get_api_key()
    if not api_key:
        # Fallback to haversine
        distance_km = haversine_distance(origin[0], origin[1], destination[0], destination[1])
        avg_speed = 30  # km/h in Guatemala City traffic
        duration_minutes = int((distance_km / avg_speed) * 60)
        return {
            'distance_km': round(distance_km, 2),
            'distance_text': f'{round(distance_km, 1)} km',
            'duration_minutes': duration_minutes,
            'duration_text': f'{duration_minutes} min',
            'source': 'haversine_fallback'
        }

    try:
        response = requests.get(DIRECTIONS_URL, params={
            'origin': f'{origin[0]},{origin[1]}',
            'destination': f'{destination[0]},{destination[1]}',
            'mode': mode,
            'departure_time': 'now',  # For traffic-aware routing
            'traffic_model': 'best_guess',
            'key': api_key,
            'language': 'es'
        }, timeout=15)

        data = response.json()

        if data['status'] == 'OK' and data['routes']:
            route = data['routes'][0]
            leg = route['legs'][0]

            return {
                'distance_km': leg['distance']['value'] / 1000,
                'distance_text': leg['distance']['text'],
                'duration_minutes': leg['duration']['value'] // 60,
                'duration_text': leg['duration']['text'],
                'duration_in_traffic_minutes': leg.get('duration_in_traffic', {}).get('value', leg['duration']['value']) // 60,
                'duration_in_traffic_text': leg.get('duration_in_traffic', {}).get('text', leg['duration']['text']),
                'start_address': leg['start_address'],
                'end_address': leg['end_address'],
                'polyline': route['overview_polyline']['points'],
                'steps': [
                    {
                        'instruction': step['html_instructions'],
                        'distance': step['distance']['text'],
                        'duration': step['duration']['text']
                    }
                    for step in leg['steps']
                ],
                'source': 'google_directions'
            }
        else:
            logger.warning(f"Directions API failed: {data['status']}")
            # Fallback
            distance_km = haversine_distance(origin[0], origin[1], destination[0], destination[1])
            return {
                'distance_km': round(distance_km, 2),
                'distance_text': f'{round(distance_km, 1)} km',
                'duration_minutes': int((distance_km / 30) * 60),
                'duration_text': f'{int((distance_km / 30) * 60)} min',
                'source': 'haversine_fallback'
            }

    except Exception as e:
        logger.error(f"Directions API error: {e}")
        distance_km = haversine_distance(origin[0], origin[1], destination[0], destination[1])
        return {
            'distance_km': round(distance_km, 2),
            'duration_minutes': int((distance_km / 30) * 60),
            'source': 'haversine_fallback'
        }


def get_distance_matrix(
    origins: List[Tuple[float, float]],
    destinations: List[Tuple[float, float]],
    mode: str = 'driving'
) -> Optional[Dict]:
    """
    Get distance and duration matrix between multiple origins and destinations.

    Args:
        origins: List of (lat, lng) tuples
        destinations: List of (lat, lng) tuples
        mode: 'driving', 'walking', 'bicycling', 'transit'

    Returns:
        Dict with distance/duration matrix
    """
    api_key = get_api_key()
    if not api_key:
        return None

    try:
        origins_str = '|'.join([f'{lat},{lng}' for lat, lng in origins])
        destinations_str = '|'.join([f'{lat},{lng}' for lat, lng in destinations])

        response = requests.get(DISTANCE_MATRIX_URL, params={
            'origins': origins_str,
            'destinations': destinations_str,
            'mode': mode,
            'departure_time': 'now',
            'traffic_model': 'best_guess',
            'key': api_key,
            'language': 'es'
        }, timeout=15)

        data = response.json()

        if data['status'] == 'OK':
            return {
                'origin_addresses': data['origin_addresses'],
                'destination_addresses': data['destination_addresses'],
                'rows': [
                    {
                        'elements': [
                            {
                                'distance_km': elem['distance']['value'] / 1000 if elem['status'] == 'OK' else None,
                                'distance_text': elem['distance']['text'] if elem['status'] == 'OK' else None,
                                'duration_minutes': elem['duration']['value'] // 60 if elem['status'] == 'OK' else None,
                                'duration_text': elem['duration']['text'] if elem['status'] == 'OK' else None,
                                'status': elem['status']
                            }
                            for elem in row['elements']
                        ]
                    }
                    for row in data['rows']
                ]
            }
        return None

    except Exception as e:
        logger.error(f"Distance Matrix API error: {e}")
        return None


def calculate_eta(
    provider_location: Tuple[float, float],
    user_location: Tuple[float, float]
) -> Dict:
    """
    Calculate ETA from provider to user location.

    Args:
        provider_location: (lat, lng) of provider
        user_location: (lat, lng) of user

    Returns:
        Dict with ETA information
    """
    directions = get_directions(provider_location, user_location)

    if directions:
        return {
            'eta_minutes': directions.get('duration_in_traffic_minutes', directions['duration_minutes']),
            'eta_text': directions.get('duration_in_traffic_text', directions['duration_text']),
            'distance_km': directions['distance_km'],
            'distance_text': directions['distance_text'],
            'source': directions['source']
        }

    # Ultimate fallback
    distance_km = haversine_distance(
        provider_location[0], provider_location[1],
        user_location[0], user_location[1]
    )
    eta_minutes = int((distance_km / 30) * 60)  # 30 km/h average

    return {
        'eta_minutes': eta_minutes,
        'eta_text': f'{eta_minutes} min',
        'distance_km': round(distance_km, 2),
        'distance_text': f'{round(distance_km, 1)} km',
        'source': 'haversine_fallback'
    }


def autocomplete_address(query: str, session_token: str = None) -> List[Dict]:
    """
    Get address autocomplete suggestions using Google Places API (New).

    Args:
        query: Partial address string
        session_token: Optional session token for billing optimization

    Returns:
        List of suggestion dicts
    """
    api_key = get_api_key()
    if not api_key:
        return []

    try:
        # Places API (New) uses POST with JSON body
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': api_key,
            'X-Goog-FieldMask': 'suggestions.placePrediction.placeId,suggestions.placePrediction.text'
        }

        body = {
            'input': query,
            'includedRegionCodes': ['gt'],  # Guatemala only
            'languageCode': 'es'
        }

        if session_token:
            body['sessionToken'] = session_token

        response = requests.post(PLACES_AUTOCOMPLETE_URL, json=body, headers=headers, timeout=10)
        data = response.json()

        suggestions = data.get('suggestions', [])
        return [
            {
                'description': s.get('placePrediction', {}).get('text', {}).get('text', ''),
                'place_id': s.get('placePrediction', {}).get('placeId', ''),
            }
            for s in suggestions
            if s.get('placePrediction')
        ]

    except Exception as e:
        logger.error(f"Places Autocomplete error: {e}")
        return []
