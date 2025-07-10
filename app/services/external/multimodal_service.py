# /app/services/external/multimodal_service.py
import json
from fastapi import Depends, HTTPException
from loguru import logger

from app.core.config import Settings, get_settings
from app.models.chat import ImageType
from app.models.pet import PetInfo, PetBreed
from app.utils.http_client import AsyncHttpClient
from app.utils.signature import generate_signature

class MultiModalService:
    def __init__(
        self,
        settings: Settings = Depends(get_settings),
        http_client: AsyncHttpClient = Depends(),
    ):
        self.settings = settings
        self.http_client = http_client
        self.breed_map = self._load_breed_map()

    def _load_breed_map(self):
        try:
            # Assuming pet_breed_0dd7f7.json is in the root directory
            with open("D:/Prj/github/gemini-cli-deployment/pet_breed_0dd7f7.json", "r", encoding="utf-8") as f:
                breeds_data = json.load(f)
            # Create a mapping from breed name (str) to breed id (int)
            return {
                item["name"]: item["id"]
                for item in breeds_data
            }
        except FileNotFoundError:
            logger.error("pet_breed_0dd7f7.json not found. Breed mapping will be unavailable.")
            return {}
        except Exception as e:
            logger.error(f"Error loading breed map: {e}")
            return {}

    def _get_breed_id(self, breed_name: str) -> int:
        """
        Finds the breed ID from the loaded map.
        Defaults to a common ID (e.g., 1 for '阿富汗猎犬') if not found.
        """
        breed_id = self.breed_map.get(breed_name, 1)
        if breed_id == 1 and breed_name not in self.breed_map:
             logger.warning(f"Breed '{breed_name}' not found in breed map. Defaulting to ID 1.")
        return breed_id

    async def analyze_image(self, image_base64: str, image_type: ImageType, pet_info: PetInfo):
        """
        Calls the appropriate multimodal API endpoint to analyze an image.
        """
        api_path = f"/open/v1/{image_type.value}"
        url = f"{self.settings.MULTIMODAL_BASE_URL}{api_path}"

        # Base64 cleaning
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]

        body = {"image": image_base64}

        # Add pet-specific info for relevant endpoints
        if image_type in [
            ImageType.FECES, ImageType.SKIN, ImageType.URINE,
            ImageType.VOMITUS, ImageType.EAR_CANAL
        ]:
            # Assuming pet_info.age is in years, and API needs birth date
            # This is a simplification. A more robust solution would be needed.
            from datetime import date, timedelta
            birth_date = date.today() - timedelta(days=pet_info.age * 365)
            
            body.update({
                "breed": self._get_breed_id(pet_info.breed),
                "birth": birth_date.strftime("%Y-%m-%d"),
                "gender": 1, # Assuming 1 for male, 2 for female. Needs clarification.
                "fertility": 1 # Assuming 1 for not neutered, 2 for neutered. Needs clarification.
            })

        # Generate signature and headers
        headers, body_str = generate_signature(
            api_key=self.settings.MULTIMODAL_API_KEY,
            api_secret=self.settings.MULTIMODAL_API_SECRET,
            path=api_path,
            body=body
        )
        
        logger.info(f"Calling multimodal API: {url} with body: {body_str[:100]}...")
        
        try:
            response = await self.http_client.post(url, data=body_str, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                logger.error(f"Multimodal API returned an error: {result}")
                raise HTTPException(status_code=502, detail=f"Multimodal API Error: {result.get('message', 'Unknown error')}")

            logger.info(f"Multimodal API call successful for path: {api_path}")
            return result

        except Exception as e:
            logger.error(f"Error calling multimodal API at {url}: {e}")
            raise HTTPException(status_code=502, detail=f"Could not connect to Multimodal Service: {e}")
