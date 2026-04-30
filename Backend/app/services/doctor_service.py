"""
CareSlot — Doctor Recommendation Service
Integrates with Google Maps Places API for nearby doctor/hospital search.
"""

import httpx
from app.config import get_settings
from typing import Dict, Any, Optional, List
from math import radians, sin, cos, sqrt, atan2
import logging

logger = logging.getLogger(__name__)

SPECIALTY_KEYWORDS = {
    "cardiologist": "cardiologist cardiology heart specialist",
    "dermatologist": "dermatologist dermatology skin clinic",
    "gynecologist": "gynecologist obstetrics women health OB-GYN",
    "endocrinologist": "endocrinologist endocrinology hormone diabetes",
    "pulmonologist": "pulmonologist pulmonology lung respiratory",
    "neurologist": "neurologist neurology brain nerve",
    "orthopedist": "orthopedic bone joint specialist",
    "psychiatrist": "psychiatrist mental health counseling",
    "gastroenterologist": "gastroenterologist digestive GI",
    "general_physician": "general physician family doctor clinic",
    "emergency": "emergency hospital ER urgent care",
}


class DoctorService:
    """Service for finding nearby doctors and hospitals via Google Maps."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://maps.googleapis.com/maps/api/place"

    async def find_nearby(
        self,
        latitude: float,
        longitude: float,
        specialty: Optional[str] = None,
        radius: int = 5000,
        keyword: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Find nearby hospitals/doctors using Google Maps Places API."""
        if not self.settings.GOOGLE_MAPS_API_KEY:
            return self._development_fallback(latitude, longitude, specialty, radius, keyword)

        # Build search keyword
        search_keyword = "hospital doctor clinic"
        if specialty and specialty in SPECIALTY_KEYWORDS:
            search_keyword = SPECIALTY_KEYWORDS[specialty]
        if keyword:
            search_keyword += f" {keyword}"

        params = {
            "location": f"{latitude},{longitude}",
            "radius": radius,
            "type": "hospital" if specialty == "emergency" else "doctor",
            "keyword": search_keyword,
            "key": self.settings.GOOGLE_MAPS_API_KEY,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/nearbysearch/json",
                    params=params,
                )
                data = response.json()

            if data.get("status") != "OK":
                logger.warning(f"Google Maps API status: {data.get('status')}")
                return {
                    "results": [],
                    "total": 0,
                    "search_location": {"latitude": latitude, "longitude": longitude},
                    "search_radius": radius,
                    "specialty_searched": specialty,
                }

            # Parse results
            results = []
            for place in data.get("results", []):
                location = place.get("geometry", {}).get("location", {})
                distance_text = self._distance_text(
                    latitude,
                    longitude,
                    location.get("lat", 0),
                    location.get("lng", 0),
                )
                result = {
                    "place_id": place.get("place_id", ""),
                    "name": place.get("name", ""),
                    "address": place.get("vicinity", ""),
                    "location": {
                        "latitude": location.get("lat", 0),
                        "longitude": location.get("lng", 0),
                    },
                    "rating": place.get("rating"),
                    "total_ratings": place.get("user_ratings_total"),
                    "is_open_now": place.get("opening_hours", {}).get("open_now"),
                    "specialty_match": specialty,
                    "distance_text": distance_text,
                    "types": place.get("types", []),
                    "photos": [
                        {
                            "photo_reference": p.get("photo_reference", ""),
                            "width": p.get("width", 0),
                            "height": p.get("height", 0),
                        }
                        for p in place.get("photos", [])[:1]
                    ],
                }
                results.append(result)

            return {
                "results": results,
                "total": len(results),
                "search_location": {"latitude": latitude, "longitude": longitude},
                "search_radius": radius,
                "specialty_searched": specialty,
            }

        except Exception as e:
            logger.error(f"Google Maps API error: {e}")
            raise

    async def find_nearby_hospitals(
        self,
        latitude: float,
        longitude: float,
        specialty: Optional[str] = None,
        radius: int = 5000,
        keyword: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Find nearby hospitals/clinics with department-aware search keywords."""
        if not self.settings.GOOGLE_MAPS_API_KEY:
            return self._development_fallback(latitude, longitude, specialty, radius, keyword, hospitals=True)

        search_keyword = "hospital clinic medical center"
        if specialty and specialty in SPECIALTY_KEYWORDS:
            search_keyword = f"{SPECIALTY_KEYWORDS[specialty]} hospital clinic"
        if keyword:
            search_keyword += f" {keyword}"

        params = {
            "location": f"{latitude},{longitude}",
            "radius": radius,
            "type": "hospital",
            "keyword": search_keyword,
            "key": self.settings.GOOGLE_MAPS_API_KEY,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{self.base_url}/nearbysearch/json", params=params)
                data = response.json()

            if data.get("status") not in {"OK", "ZERO_RESULTS"}:
                logger.warning(f"Google Maps API status: {data.get('status')}")
                return {
                    "results": [],
                    "total": 0,
                    "search_location": {"latitude": latitude, "longitude": longitude},
                    "search_radius": radius,
                    "specialty_searched": specialty,
                }

            results = []
            for place in data.get("results", []):
                location = place.get("geometry", {}).get("location", {})
                photos = [
                    {
                        "photo_reference": p.get("photo_reference", ""),
                        "width": p.get("width", 0),
                        "height": p.get("height", 0),
                    }
                    for p in place.get("photos", [])[:1]
                ]
                results.append(
                    {
                        "place_id": place.get("place_id", ""),
                        "name": place.get("name", ""),
                        "address": place.get("vicinity", ""),
                        "location": {
                            "latitude": location.get("lat", 0),
                            "longitude": location.get("lng", 0),
                        },
                        "rating": place.get("rating"),
                        "total_ratings": place.get("user_ratings_total"),
                        "is_open_now": place.get("opening_hours", {}).get("open_now"),
                        "specialty_match": specialty,
                        "distance_text": self._distance_text(
                            latitude,
                            longitude,
                            location.get("lat", 0),
                            location.get("lng", 0),
                        ),
                        "types": place.get("types", []),
                        "photos": photos,
                    }
                )

            return {
                "results": results,
                "total": len(results),
                "search_location": {"latitude": latitude, "longitude": longitude},
                "search_radius": radius,
                "specialty_searched": specialty,
            }
        except Exception as e:
            logger.error(f"Google Maps hospital search error: {e}")
            raise

    async def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get detailed info about a specific place."""
        if not self.settings.GOOGLE_MAPS_API_KEY:
            return {}

        params = {
            "place_id": place_id,
            "fields": "name,formatted_address,formatted_phone_number,website,rating,opening_hours,geometry,photos,reviews",
            "key": self.settings.GOOGLE_MAPS_API_KEY,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{self.base_url}/details/json", params=params)
            data = response.json()

        if data.get("status") != "OK":
            return {}

        result = data.get("result", {})
        location = result.get("geometry", {}).get("location", {})

        return {
            "place_id": place_id,
            "name": result.get("name", ""),
            "address": result.get("formatted_address", ""),
            "phone_number": result.get("formatted_phone_number"),
            "website": result.get("website"),
            "rating": result.get("rating"),
            "location": {
                "latitude": location.get("lat", 0),
                "longitude": location.get("lng", 0),
            },
            "opening_hours": result.get("opening_hours", {}).get("weekday_text", []),
            "is_open_now": result.get("opening_hours", {}).get("open_now"),
            "photos": [
                {
                    "photo_reference": p.get("photo_reference", ""),
                    "width": p.get("width", 0),
                    "height": p.get("height", 0),
                }
                for p in result.get("photos", [])[:3]
            ],
        }

    async def fetch_photo(self, photo_reference: str, max_width: int = 900) -> tuple[bytes, str]:
        """Fetch a Google Places photo through the backend so API keys stay server-side."""
        if not self.settings.GOOGLE_MAPS_API_KEY:
            return b"", "image/jpeg"

        params = {
            "photo_reference": photo_reference,
            "maxwidth": max_width,
            "key": self.settings.GOOGLE_MAPS_API_KEY,
        }
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(f"{self.base_url}/photo", params=params)
            response.raise_for_status()
            return response.content, response.headers.get("content-type", "image/jpeg")

    def get_specialties(self) -> List[Dict[str, Any]]:
        """Return list of available specialties."""
        return [
            {"key": key, "label": key.replace("_", " ").title(), "keywords": val.split()}
            for key, val in SPECIALTY_KEYWORDS.items()
        ]

    def _distance_text(self, lat1: float, lon1: float, lat2: float, lon2: float) -> str:
        km = self._haversine_km(lat1, lon1, lat2, lon2)
        if km < 1:
            return f"{max(100, round(km * 1000 / 50) * 50)} m"
        return f"{km:.1f} km"

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius_km = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        return radius_km * 2 * atan2(sqrt(a), sqrt(1 - a))

    def _development_fallback(
        self,
        latitude: float,
        longitude: float,
        specialty: Optional[str],
        radius: int,
        keyword: Optional[str],
        hospitals: bool = False,
    ) -> Dict[str, Any]:
        """Local development data when Google Maps credentials are not configured."""
        base_names = [
            "CareSlot Partner Hospital",
            "Aster Health Clinic",
            "BlueCare Medical Centre",
            "Nova Specialty Hospital",
        ]
        results = []
        for idx, name in enumerate(base_names):
            lat = latitude + (idx + 1) * 0.006
            lng = longitude + (idx + 1) * 0.004
            results.append(
                {
                    "place_id": f"dev-{idx + 1}-{(specialty or 'general').replace('_', '-')}",
                    "name": name,
                    "address": f"{idx + 2} Health Avenue, Demo District",
                    "location": {"latitude": lat, "longitude": lng},
                    "rating": round(4.8 - idx * 0.2, 1),
                    "total_ratings": 120 + idx * 37,
                    "is_open_now": idx != 2,
                    "specialty_match": specialty,
                    "distance_text": self._distance_text(latitude, longitude, lat, lng),
                    "types": ["hospital" if hospitals else "doctor", "health"],
                    "photos": [],
                }
            )

        return {
            "results": results,
            "total": len(results),
            "search_location": {"latitude": latitude, "longitude": longitude},
            "search_radius": radius,
            "specialty_searched": specialty,
            "keyword": keyword,
        }
