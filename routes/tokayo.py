"""
Tokayo endpoints — manage the user's tokayito stats.
"""

from sqlalchemy import select
from robyn import Request

from database.database import get_session
from database.tokayo import Tokayo
from routes._helpers import json_response, parse_json_body, get_user_id


EDITABLE_STATS = {
    "kindness",
    "strength",
    "happiness",
    "luck",
    "destroyed_bases",
    "tokayos_helped",
}


def _serialize(t: Tokayo) -> dict:
    return {
        "uuid": str(t.uuid),
        "name": t.name,
        "owned_by_user": t.owned_by_user,
        "kindness": t.kindness,
        "strength": t.strength,
        "happiness": t.happiness,
        "luck": t.luck,
        "destroyed_bases": t.destroyed_bases,
        "tokayos_helped": t.tokayos_helped,
    }


async def _get_by_user(session, user_id: str) -> Tokayo | None:
    result = await session.execute(
        select(Tokayo).where(Tokayo.owned_by_user == user_id)
    )
    return result.scalar_one_or_none()


def register(app):
    @app.get("/tokayo/stats", openapi_tags=["Tokayo"])
    async def get_tokayo_stats(request: Request):
        """
        Get the authenticated user's tokayito stats.

        Requires the `X-User-Id` header injected by the super app after
        token validation. Returns the full tokayito record including
        growth stats (kindness, strength, happiness, luck) and arena
        stats (destroyed_bases, tokayos_helped).

        Returns 404 if the user has no tokayito yet.
        """
        user_id, err = get_user_id(request)
        if err:
            return err

        async with get_session() as session:
            tokayo = await _get_by_user(session, user_id)
            if not tokayo:
                return json_response(
                    {"error": "tokayo not found for user"}, status=404
                )
            return json_response(_serialize(tokayo))

    @app.patch("/tokayo/stats", openapi_tags=["Tokayo"])
    async def update_tokayo_stats(request: Request):
        """
        Update the authenticated user's tokayito stats.

        Only the stat fields can be modified: kindness, strength,
        happiness, luck, destroyed_bases, tokayos_helped. Any other
        field in the body is silently ignored. The tokayito's name,
        uuid and owner cannot be changed through this endpoint.

        Body example:
            { "kindness": 10, "happiness": 8 }

        All values must be integers. Returns 400 if no valid fields
        are provided or if any value has the wrong type.
        """
        user_id, err = get_user_id(request)
        if err:
            return err

        data, err = parse_json_body(request)
        if err:
            return err

        updates = {}
        for key, value in data.items():
            if key not in EDITABLE_STATS:
                continue
            if not isinstance(value, int):
                return json_response(
                    {"error": f"field '{key}' must be an integer"}, status=400
                )
            updates[key] = value

        if not updates:
            return json_response(
                {"error": "no valid fields to update"}, status=400
            )

        async with get_session() as session:
            tokayo = await _get_by_user(session, user_id)
            if not tokayo:
                return json_response(
                    {"error": "tokayo not found for user"}, status=404
                )

            for key, value in updates.items():
                setattr(tokayo, key, value)

            return json_response(_serialize(tokayo))