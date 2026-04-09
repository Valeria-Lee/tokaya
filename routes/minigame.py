"""
Minigame endpoints — Tiki Toka session lifecycle.
"""

import uuid as uuid_pkg
from datetime import datetime, timezone

from robyn import Request

from database.database import get_session
from database.minigame import Minigame
from routes._helpers import json_response, parse_json_body, get_user_id


def _serialize(m: Minigame) -> dict:
    return {
        "uuid": str(m.uuid),
        "name": m.name,
        "exp_date": m.exp_date.isoformat() if m.exp_date else None,
        "completed": m.completed,
        "won": m.won,
        "score_goal": m.score_goal,
    }


def register(app):
    @app.get("/minigames/:uuid", openapi_tags=["Minigame"])
    async def get_minigame(request: Request, uuid: str):
        """
        Fetch a minigame session by its UUID.

        Returns the full session including completion state and target score.
        Requires `X-User-Id` header.
        """
        _, err = get_user_id(request)
        if err:
            return err

        try:
            mg_uuid = uuid_pkg.UUID(uuid)
        except ValueError:
            return json_response({"error": "invalid uuid"}, status=400)

        async with get_session() as session:
            minigame = await session.get(Minigame, mg_uuid)
            if not minigame:
                return json_response({"error": "not found"}, status=404)
            return json_response(_serialize(minigame))

    @app.post("/minigames", openapi_tags=["Minigame"])
    async def create_minigame(request: Request):
        """
        Create a new minigame session.

        The session starts as not completed and not won. The client must
        call `/minigames/:uuid/check-win` after the player finishes to
        validate the result.

        Body:
            {
                "name": "Tiki Toka Run",
                "exp_date": "2026-04-09T23:59:59+00:00",
                "score_goal": 100
            }
        """
        _, err = get_user_id(request)
        if err:
            return err

        data, err = parse_json_body(request)
        if err:
            return err

        name = data.get("name")
        exp_date_raw = data.get("exp_date")
        score_goal = data.get("score_goal")

        if not name or not exp_date_raw or score_goal is None:
            return json_response(
                {"error": "name, exp_date and score_goal are required"},
                status=400,
            )

        try:
            exp_date = datetime.fromisoformat(exp_date_raw)
        except ValueError:
            return json_response(
                {"error": "exp_date must be ISO 8601 (e.g. 2026-04-08T20:00:00+00:00)"},
                status=400,
            )

        if not isinstance(score_goal, int) or score_goal < 0:
            return json_response(
                {"error": "score_goal must be a non-negative integer"}, status=400
            )

        async with get_session() as session:
            minigame = Minigame(
                name=name,
                exp_date=exp_date,
                score_goal=score_goal,
                completed=False,
                won=False,
            )
            session.add(minigame)
            await session.flush()
            return json_response(_serialize(minigame), status=201)

    @app.post("/minigames/:uuid/check-win", openapi_tags=["Minigame"])
    async def check_minigame_win(request: Request, uuid: str):
        """
        Validate the result of a minigame session.

        The client reports the final score after the player finishes.
        The server compares it against `score_goal` and marks the session
        as completed. The session is marked as won only if
        `score >= score_goal`.

        IMPORTANT: finishing a minigame does NOT imply winning. A player
        can complete a session with an insufficient score, in which case
        the session is marked completed but not won.

        Sessions can only be checked once — a second call returns 409.
        Sessions past their `exp_date` return 410 and are marked
        completed but not won.

        Body:
            { "score": 120 }
        """
        _, err = get_user_id(request)
        if err:
            return err

        try:
            mg_uuid = uuid_pkg.UUID(uuid)
        except ValueError:
            return json_response({"error": "invalid uuid"}, status=400)

        data, err = parse_json_body(request)
        if err:
            return err

        score = data.get("score")
        if not isinstance(score, int) or score < 0:
            return json_response(
                {"error": "score must be a non-negative integer"}, status=400
            )

        async with get_session() as session:
            minigame = await session.get(Minigame, mg_uuid)
            if not minigame:
                return json_response({"error": "not found"}, status=404)

            if minigame.completed:
                return json_response(
                    {"error": "minigame already completed", "won": minigame.won},
                    status=409,
                )

            now = datetime.now(timezone.utc)
            if minigame.exp_date and now > minigame.exp_date:
                minigame.completed = True
                minigame.won = False
                return json_response(
                    {"won": False, "reason": "expired", **_serialize(minigame)},
                    status=410,
                )

            minigame.completed = True
            minigame.won = score >= minigame.score_goal

            return json_response(
                {
                    "won": minigame.won,
                    "score": score,
                    "score_goal": minigame.score_goal,
                    **_serialize(minigame),
                }
            )