# /app/services/external/pet_info_service.py
import time
import hmac
import hashlib
from fastapi import Depends, HTTPException
from loguru import logger

from app.core.config import Settings, get_settings
from app.models.pet import PetInfo
from app.utils.http_client import AsyncHttpClient

class PetInfoService:
    def __init__(
        self,
        settings: Settings = Depends(get_settings),
        http_client: AsyncHttpClient = Depends(),
    ):
        self.settings = settings
        self.http_client = http_client
        self.base_url = settings.PET_INFO_API_BASE_URL

    def _generate_pet_info_signature(self, timestamp: str) -> str:
        """
        Generates HMAC-SHA256 signature for the Pet Info API.
        The signature logic might be more complex in a real scenario
        (e.g., including method, path, body). This is based on the example.
        """
        message = f"{self.settings.PET_INFO_API_CLIENT_ID}{timestamp}".encode('utf-8')
        secret = self.settings.PET_INFO_API_SECRET_KEY.encode('utf-8')
        signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
        return signature

    async def get_pet_info(self, pet_id: str) -> PetInfo:
        """
        Retrieves pet information from the third-party service.
        Includes HMAC-SHA256 authentication and retry logic.
        """
        # In a real application, you would call the external API.
        # For this example, we'll return mock data to avoid actual network calls.
        logger.info(f"Fetching mock pet info for pet_id: {pet_id}")
        if pet_id == "PET_1234567":
            return PetInfo(
                pet_id="PET_1234567",
                name="Buddy",
                species="canine",
                breed="金毛寻回犬", # Using a name present in the breed map
                age=5,
                weight=28.5,
                vaccination_records=[{"vaccine": "Rabies", "date": "2023-01-15"}],
                medical_history=[{"date": "2022-08-10", "diagnosis": "Ear infection"}]
            )
        else:
            # Default mock data for any other pet_id
            return PetInfo(
                pet_id=pet_id,
                name="Unknown Pet",
                species="feline",
                breed="三花猫", # Using a name present in the breed map
                age=2,
                weight=4.5,
                vaccination_records=[],
                medical_history=[]
            )

        # --- REAL IMPLEMENTATION (commented out for demonstration) ---
        # url = f"{self.base_url}/pets/{pet_id}"
        # max_retries = 2
        # for attempt in range(max_retries + 1):
        #     try:
        #         timestamp = str(int(time.time()))
        #         signature = self._generate_pet_info_signature(timestamp)
        #         headers = {
        #             "Authorization": f"HMAC-SHA256 Credential={self.settings.PET_INFO_API_CLIENT_ID}",
        #             "X-Timestamp": timestamp,
        #             "X-Signature": signature,
        #             "Content-Type": "application/json"
        #         }
                
        #         logger.info(f"Calling Pet Info API: {url} (Attempt {attempt + 1})")
        #         response = await self.http_client.get(url, headers=headers, timeout=5.0)
        #         response.raise_for_status()
        #         data = response.json()
                
        #         logger.info(f"Successfully fetched pet info for {pet_id}")
        #         return PetInfo(**data['data'])

        #     except Exception as e:
        #         logger.error(f"Attempt {attempt + 1} failed to get pet info for {pet_id}: {e}")
        #         if attempt >= max_retries:
        #             raise HTTPException(status_code=503, detail=f"Failed to retrieve pet information after {max_retries + 1} attempts.")
        #         await asyncio.sleep(1) # Wait before retrying
        # -------------------------------------------------------------
