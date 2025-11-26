import logging
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class CognitiveService:
    """
    Thin wrapper around Azure AI Vision (Cognitive Services) Analyze API.
    """

    def __init__(self):
        self.endpoint = (
            settings.azure_ai_endpoint.rstrip("/")
            if getattr(settings, "azure_ai_endpoint", None)
            else None
        )
        self.api_key = getattr(settings, "azure_ai_key", None)
        self.enabled = bool(self.endpoint and self.api_key)

    async def analyze_image(self, image_url: str) -> Optional[Dict[str, Any]]:
        """
        Calls Azure AI Vision Analyze API and returns the raw JSON response.
        """
        if not self.enabled:
            logger.debug("CognitiveService disabled - missing endpoint or API key.")
            return None

        analyze_url = f"{self.endpoint}/vision/v3.2/analyze"
        params = {
            "visualFeatures": "Description,Tags,Categories,Objects,Color,Adult",
            "language": "en",
        }
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {"url": image_url}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    analyze_url, params=params, json=payload, headers=headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Azure Vision request failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )
        except httpx.RequestError as exc:
            logger.error("Azure Vision request error: %s", str(exc))
        except Exception as exc:
            logger.exception("Unexpected Azure Vision error: %s", str(exc))

        return None

    def build_insights(self, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalizes the Azure response into PhotoAIInsights shape.
        """
        if not analysis:
            return None

        description = analysis.get("description", {})
        captions = description.get("captions") or []
        caption = captions[0] if captions else {}

        tags = {tag.get("name") for tag in analysis.get("tags", []) if tag.get("name")}
        description_tags = description.get("tags") or []
        tags.update(filter(None, description_tags))

        insights = {
            "tags": sorted(tags),
            "objects": [
                obj.get("object")
                for obj in analysis.get("objects", [])
                if obj.get("object")
            ],
            "categories": [
                cat.get("name")
                for cat in analysis.get("categories", [])
                if cat.get("name")
            ],
            "dominant_colors": analysis.get("color", {}).get("dominantColors", []),
            "caption": caption.get("text"),
            "caption_confidence": caption.get("confidence"),
            "moderation": {
                "is_adult_content": analysis.get("adult", {}).get("isAdultContent"),
                "is_racy_content": analysis.get("adult", {}).get("isRacyContent"),
                "is_gory_content": analysis.get("adult", {}).get("isGoryContent"),
                "adult_score": analysis.get("adult", {}).get("adultScore"),
                "racy_score": analysis.get("adult", {}).get("racyScore"),
                "gore_score": analysis.get("adult", {}).get("goreScore"),
            },
            "model_version": analysis.get("modelVersion"),
            "analyzed_at": datetime.utcnow(),
        }

        # Remove moderation block if all values are None to keep payload concise.
        moderation = insights["moderation"]
        if all(value is None for value in moderation.values()):
            insights["moderation"] = None

        return insights


cognitive_service = CognitiveService()
