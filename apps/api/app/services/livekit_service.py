import time
import jwt
from typing import Optional
from apps.api.app.core.config import settings


class LiveKitService:
    @staticmethod
    def generate_token(
        room_name: str,
        identity: str,
        name: Optional[str] = None,
        can_publish: bool = True,
        can_subscribe: bool = True,
        valid_seconds: int = 86400
    ) -> str:
        """
        Generate a valid LiveKit Access Token JWT.
        """
        api_key = settings.LIVEKIT_API_KEY
        api_secret = settings.LIVEKIT_API_SECRET

        now = int(time.time())
        exp = now + valid_seconds

        grant = {
            "identity": identity,
            "name": name or identity,
            "video": {
                "room": room_name,
                "roomJoin": True,
                "canPublish": can_publish,
                "canSubscribe": can_subscribe,
                "canPublishData": True,
            }
        }

        payload = {
            "iss": api_key,
            "sub": identity,
            "exp": exp,
            "nbf": now - 5,
            "video": grant["video"],
            "name": name or identity,
        }

        token = jwt.encode(payload, api_secret, algorithm="HS256")
        return token
