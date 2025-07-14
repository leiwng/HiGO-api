from fastapi import APIRouter, Depends, HTTPException, status
from app.models.api_key import APIKeyCreate, APIKeyResponse
from app.models.user import User
from app.services.api_key_service import APIKeyService
from app.core.security import get_current_user

router = APIRouter()

@router.post("/api-keys", response_model=APIKeyResponse, summary="创建API Key")
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user)
):
    """创建新的API Key"""
    api_key_service = APIKeyService()

    try:
        # 确保用户有账户
        account = await api_key_service.get_account_by_user_id(current_user.id)
        if not account:
            account = await api_key_service.create_account(current_user.id)

        # 创建API Key
        api_key, api_key_str = await api_key_service.create_api_key(current_user.id, key_data)

        # 返回响应（包含完整的key，只在创建时返回一次）
        response = APIKeyResponse(**api_key.model_dump())
        response.key = api_key_str

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )

@router.get("/api-keys", response_model=list[APIKeyResponse], summary="获取API Key列表")
async def list_api_keys(
    current_user: User = Depends(get_current_user)
):
    """获取用户的所有API Key"""
    api_key_service = APIKeyService()

    api_keys = await api_key_service.get_user_api_keys(current_user.id)

    return [
        APIKeyResponse(**key.model_dump())
        for key in api_keys
    ]

@router.delete("/api-keys/{api_key_id}", summary="撤销API Key")
async def revoke_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_user)
):
    """撤销指定的API Key"""
    api_key_service = APIKeyService()

    success = await api_key_service.revoke_api_key(api_key_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    return {"message": "API key revoked successfully"}

@router.get("/account", response_model=dict, summary="获取账户信息")
async def get_account_info(
    current_user: User = Depends(get_current_user)
):
    """获取用户账户信息"""
    api_key_service = APIKeyService()

    account = await api_key_service.get_account_by_user_id(current_user.id)
    if not account:
        account = await api_key_service.create_account(current_user.id)

    return {
        "account_type": account.account_type,
        "balance": account.balance_cents / 100,  # 转换为美元
        "credit": account.credit_cents / 100,
        "total_spent": account.total_spent_cents / 100,
        "monthly_spent": account.monthly_spent_cents / 100,
        "daily_spent": account.daily_spent_cents / 100
    }