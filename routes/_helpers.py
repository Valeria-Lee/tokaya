import json
from robyn import Response


def json_response(payload, status: int = 200) -> Response:
    return Response(
        status_code=status,
        headers={"Content-Type": "application/json"},
        description=json.dumps(payload, default=str),
    )


def parse_json_body(request):
    """Devuelve (data, error_response). Si error_response no es None, devuélvelo."""
    try:
        return json.loads(request.body), None
    except (json.JSONDecodeError, TypeError):
        return None, json_response({"error": "invalid json body"}, status=400)


def get_user_id(request):
    """
    Extrae el user_id del header X-User-Id inyectado por la super app
    después de validar el token. Devuelve (user_id, error_response).
    """
    # Robyn normaliza headers a lowercase
    user_id = request.headers.get("x-user-id")
    if not user_id:
        return None, json_response(
            {"error": "missing user identity"}, status=401
        )
    return user_id, None