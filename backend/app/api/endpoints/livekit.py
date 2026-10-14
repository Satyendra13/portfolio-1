from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.livekit import LiveKitTokenRequest, LiveKitTokenResponse
from backend.app.services.livekit_service import create_livekit_token
from backend.app.core.config import settings

router = APIRouter(prefix="/livekit", tags=["LiveKit"])

@router.post("/token", response_model=LiveKitTokenResponse)
async def generate_token(payload: LiveKitTokenRequest):
    if not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LiveKit API Key or Secret not configured in environment.",
        )

    try:
        jwt_token = create_livekit_token(
            room_name=payload.room_name,
            participant_identity=payload.participant_identity,
            participant_name=payload.participant_name or payload.participant_identity,
            role=payload.role,
        )
        return LiveKitTokenResponse(
            token=jwt_token,
            server_url=settings.LIVEKIT_URL,
            room_name=payload.room_name,
            participant_identity=payload.participant_identity,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate LiveKit token: {str(e)}",
        )
