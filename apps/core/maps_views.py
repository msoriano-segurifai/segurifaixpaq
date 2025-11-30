"""
Google Maps API Views for SegurifAI x PAQ
==========================================

REST API endpoints for location services testing via Postman.

Author: SegurifAI Development Team
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .maps_service import (
    geocode_address,
    reverse_geocode,
    get_directions,
    calculate_eta,
    autocomplete_address,
    haversine_distance
)


@api_view(['GET'])
@permission_classes([AllowAny])
def geocode(request):
    """
    Convert address to coordinates.

    GET /api/maps/geocode/?address=Zona 10, Guatemala

    Returns:
    {
        "lat": 14.5959,
        "lng": -90.5065,
        "formatted_address": "Zone 10, Guatemala City, Guatemala"
    }
    """
    address = request.query_params.get('address')
    if not address:
        return Response(
            {'error': 'address parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    result = geocode_address(address)
    if result:
        return Response(result)
    return Response(
        {'error': 'Could not geocode address'},
        status=status.HTTP_404_NOT_FOUND
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def reverse_geocode_view(request):
    """
    Convert coordinates to address.

    GET /api/maps/reverse-geocode/?lat=14.6349&lng=-90.5069

    Returns:
    {
        "formatted_address": "6a Avenida, Guatemala City, Guatemala",
        "place_id": "ChIJ..."
    }
    """
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')

    if not lat or not lng:
        return Response(
            {'error': 'lat and lng parameters are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        return Response(
            {'error': 'lat and lng must be valid numbers'},
            status=status.HTTP_400_BAD_REQUEST
        )

    result = reverse_geocode(lat, lng)
    if result:
        return Response(result)
    return Response(
        {'error': 'Could not reverse geocode coordinates'},
        status=status.HTTP_404_NOT_FOUND
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def directions(request):
    """
    Get directions between two points.

    GET /api/maps/directions/?origin_lat=14.62&origin_lng=-90.51&dest_lat=14.63&dest_lng=-90.50

    Returns:
    {
        "distance_km": 2.5,
        "duration_minutes": 8,
        "polyline": "encoded_polyline_string",
        "steps": [...]
    }
    """
    origin_lat = request.query_params.get('origin_lat')
    origin_lng = request.query_params.get('origin_lng')
    dest_lat = request.query_params.get('dest_lat')
    dest_lng = request.query_params.get('dest_lng')

    if not all([origin_lat, origin_lng, dest_lat, dest_lng]):
        return Response(
            {'error': 'origin_lat, origin_lng, dest_lat, dest_lng are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        origin = (float(origin_lat), float(origin_lng))
        destination = (float(dest_lat), float(dest_lng))
    except ValueError:
        return Response(
            {'error': 'Coordinates must be valid numbers'},
            status=status.HTTP_400_BAD_REQUEST
        )

    result = get_directions(origin, destination)
    if result:
        return Response(result)
    return Response(
        {'error': 'Could not get directions'},
        status=status.HTTP_404_NOT_FOUND
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def eta(request):
    """
    Calculate ETA between provider and user.

    GET /api/maps/eta/?provider_lat=14.62&provider_lng=-90.51&user_lat=14.63&user_lng=-90.50

    Returns:
    {
        "eta_minutes": 8,
        "eta_text": "8 mins",
        "distance_km": 2.5,
        "distance_text": "2.5 km"
    }
    """
    provider_lat = request.query_params.get('provider_lat')
    provider_lng = request.query_params.get('provider_lng')
    user_lat = request.query_params.get('user_lat')
    user_lng = request.query_params.get('user_lng')

    if not all([provider_lat, provider_lng, user_lat, user_lng]):
        return Response(
            {'error': 'provider_lat, provider_lng, user_lat, user_lng are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        provider = (float(provider_lat), float(provider_lng))
        user = (float(user_lat), float(user_lng))
    except ValueError:
        return Response(
            {'error': 'Coordinates must be valid numbers'},
            status=status.HTTP_400_BAD_REQUEST
        )

    result = calculate_eta(provider, user)
    return Response(result)


@api_view(['GET'])
@permission_classes([AllowAny])
def autocomplete(request):
    """
    Get address autocomplete suggestions.

    GET /api/maps/autocomplete/?query=zona 10

    Returns:
    {
        "suggestions": [
            {"description": "Zona 10, Guatemala City", "place_id": "ChIJ..."},
            ...
        ]
    }
    """
    query = request.query_params.get('query')
    if not query:
        return Response(
            {'error': 'query parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    suggestions = autocomplete_address(query)
    return Response({'suggestions': suggestions})


@api_view(['GET'])
@permission_classes([AllowAny])
def distance(request):
    """
    Calculate straight-line distance between two points (Haversine).

    GET /api/maps/distance/?lat1=14.62&lng1=-90.51&lat2=14.63&lng2=-90.50

    Returns:
    {
        "distance_km": 1.8,
        "method": "haversine"
    }
    """
    lat1 = request.query_params.get('lat1')
    lng1 = request.query_params.get('lng1')
    lat2 = request.query_params.get('lat2')
    lng2 = request.query_params.get('lng2')

    if not all([lat1, lng1, lat2, lng2]):
        return Response(
            {'error': 'lat1, lng1, lat2, lng2 are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        distance_km = haversine_distance(
            float(lat1), float(lng1),
            float(lat2), float(lng2)
        )
    except ValueError:
        return Response(
            {'error': 'Coordinates must be valid numbers'},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({
        'distance_km': round(distance_km, 3),
        'method': 'haversine'
    })
