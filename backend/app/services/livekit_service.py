from typing import Optional
from livekit.api import AccessToken, VideoGrants
from backend.app.core.config import settings

def create_livekit_token(
    room_name: str,
    participant_identity: str,
    participant_name: Optional[str] = None,
    role: str = "customer",
) -> str:
    """
    Generate a LiveKit JWT token for customer, human agent, or AI worker.
    """
    grants = VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )

    if role == "agent":
        grants.room_admin = True

    token = (
        AccessToken(
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET
        )
        .with_identity(participant_identity)
        .with_name(participant_name or participant_identity)
        .with_grants(grants)
    )

    return token.to_jwt()
