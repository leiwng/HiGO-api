# /app/services/external/multimodal_service.py
import json
import os
from pathlib import Path
from datetime import date, timedelta
from fastapi import HTTPException

from app.core.config import Settings, get_settings
from app.models.chat import ImageType
from app.models.pet import PetInfo
from app.utils.http_client import AsyncHttpClient
from app.utils.signature import generate_signature
from app.core.logging import get_logger

logger = get_logger(__name__)

class MultiModalService:
    def __init__(
        self,
        settings: Settings | None = None,
        http_client: AsyncHttpClient | None = None
    ):
        # 如果没有传入 settings，则获取默认配置
        self.settings = settings or get_settings()

        # 如果没有传入 http_client，则创建默认实例
        self.http_client = http_client or AsyncHttpClient()

        self.breed_map = self._load_breed_map()

    def _load_breed_map(self) -> dict[str, int]:
        """加载品种映射表"""
        try:
            # 使用配置中的文件路径
            breed_file_path = self.settings.BREED_MAP_FILE

            # 如果是相对路径，则相对于项目根目录
            if not os.path.isabs(breed_file_path):
                project_root = Path(__file__).parent.parent.parent.parent
                breed_file_path = project_root / breed_file_path

            with open(breed_file_path, "r", encoding="utf-8") as f:
                breeds_data = json.load(f)

            # 创建从品种名称到ID的映射
            breed_map = {
                item["name"]: item["id"]
                for item in breeds_data
                if isinstance(item, dict) and "name" in item and "id" in item
            }

            logger.info(f"Loaded {len(breed_map)} breed mappings from {breed_file_path}")
            return breed_map

        except FileNotFoundError:
            logger.error(f"Breed mapping file not found: {self.settings.BREED_MAP_FILE}. Breed mapping will be unavailable.")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in breed mapping file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading breed map: {e}")
            return {}

    def _get_breed_id(self, breed_name: str) -> int:
        """
        从加载的映射表中查找品种ID
        如果未找到，默认返回ID 1
        """
        breed_id = self.breed_map.get(breed_name, 1)
        if breed_id == 1 and breed_name not in self.breed_map:
            logger.warning(f"Breed '{breed_name}' not found in breed map. Defaulting to ID 1.")
        return breed_id

    def _get_pet_gender_code(self, gender: str) -> int:
        """将性别字符串转换为API需要的代码"""
        gender_map = {
            "male": 1,
            "female": 2,
            "公": 1,
            "母": 2,
            "雄": 1,
            "雌": 2
        }
        return gender_map.get(gender.lower(), 1)  # 默认为雄性

    def _get_fertility_code(self, is_neutered: bool) -> int:
        """将绝育状态转换为API需要的代码"""
        return 2 if is_neutered else 1  # 2=已绝育, 1=未绝育

    async def analyze_image(self, image_base64: str, image_type: ImageType, pet_info: PetInfo) -> dict:
        """
        调用相应的多模态API端点分析图像
        """
        api_path = f"/open/v1/{image_type.value}"
        url = f"{self.settings.MULTIMODAL_BASE_URL}{api_path}"

        # 清理Base64字符串
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]

        body = {"image": image_base64}

        # 为相关端点添加宠物特定信息
        if image_type in [
            ImageType.FECES, ImageType.SKIN, ImageType.URINE,
            ImageType.VOMITUS, ImageType.EAR_CANAL
        ]:
            # 计算生日（假设pet_info.age是年龄）
            birth_date = date.today() - timedelta(days=int(pet_info.age * 365))

            body.update({
                "breed": self._get_breed_id(pet_info.breed),
                "birth": birth_date.strftime("%Y-%m-%d"),
                "gender": self._get_pet_gender_code(getattr(pet_info, 'gender', 'male')),
                "fertility": self._get_fertility_code(getattr(pet_info, 'is_neutered', False))
            })

        # 生成签名和请求头
        headers, body_str = generate_signature(
            api_key=self.settings.MULTIMODAL_API_KEY,
            api_secret=self.settings.MULTIMODAL_API_SECRET,
            path=api_path,
            body=body
        )

        logger.info(f"Calling multimodal API: {url} with body: {body_str[:100]}...")

        try:
            response = await self.http_client.post(
                url,
                data=body_str,
                headers=headers,
                timeout=self.settings.MULTIMODAL_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()

            if result.get("code") != 0:
                logger.error(f"Multimodal API returned an error: {result}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Multimodal API Error: {result.get('message', 'Unknown error')}"
                )

            logger.info(f"Multimodal API call successful for path: {api_path}")
            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error calling multimodal API at {url}: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Could not connect to Multimodal Service: {e}"
            )


# 创建依赖注入函数，用于FastAPI路由
def get_multimodal_service() -> MultiModalService:
    """获取多模态服务实例（用于FastAPI依赖注入）"""
    return MultiModalService()
