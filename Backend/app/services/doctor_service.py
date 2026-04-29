"""
CareSlot — Doctor Recommendation Service
Integrates with Google Maps Places API for nearby doctor/hospital search.
"""

import httpx
from app.config import get_settings
from typing import Dict, Any, Optional, List
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
        # Build search keyword
        search_keyword = "hospital doctor clinic"
        if specialty and specialty in SPECIALTY_KEYWORDS:
            search_keyword = SPECIALTY_KEYWORDS[specialty]
        if keyword:
            search_keyword += f" {keyword}"

        params = {
            "location": f"{latitude},{longitude}",
            "radius": radius,
            "type": "hospital|doctor|health",
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

    async def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get detailed info about a specific place."""
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
        }

    def get_specialties(self) -> List[Dict[str, Any]]:
        """Return list of available specialties."""
        return [
            {"key": key, "label": key.replace("_", " ").title(), "keywords": val.split()}
            for key, val in SPECIALTY_KEYWORDS.items()
        ]
