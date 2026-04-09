"""
Inventory and shop endpoints — manage the user's tokayito's blocks.

Inventory only tracks blocks (other items like hammers and accessories
are simulated client-side and not persisted).

The shop endpoint currently does NOT validate or deduct user points —
points are not yet modeled in the database. When a user wallet is
implemented, plug the validation into `buy_block` where marked TODO.
"""

import uuid as uuid_pkg

from sqlalchemy import select
from robyn import Request

from database.database import get_session
from database.tokayo import Tokayo
from database.block import Block
from database.inventory_item import InventoryItem
from routes._helpers import json_response, parse_json_body, get_user_id


def _serialize_block(b: Block) -> dict:
    return {
        "uuid": str(b.uuid),
        "name": b.name,
        "x_pos": b.x_pos,
        "y_pos": b.y_pos,
        "durability": b.durability,
        "price": b.price,
    }


def _serialize_inventory_entry(entry: InventoryItem) -> dict:
    """
    Serializes an inventory row including the joined block details.
    Thanks to lazy='joined' on the relationship, entry.block is already
    loaded — no extra query.
    """
    return {
        "uuid": str(entry.uuid),
        "tokayo_id": str(entry.tokayo_id),
        "block_id": str(entry.block_id),
        "quantity": entry.quantity,
        "equipped": entry.equipped,
        "block": _serialize_block(entry.block) if entry.block else None,
    }


async def _get_tokayo_by_user(session, user_id: str) -> Tokayo | None:
    result = await session.execute(
        select(Tokayo).where(Tokayo.owned_by_user == user_id)
    )
    return result.scalar_one_or_none()


def register(app):

    # ─── Catálogo / tienda ────────────────────────────────────────────

    @app.get("/catalog/blocks", openapi_tags=["Shop"])
    async def list_blocks(request: Request):
        """
        List all blocks available in the shop catalog.

        Returns every block defined in the catalog, regardless of
        whether the user owns any. Used by the client to render the
        shop screen. Does not require ownership of a tokayito — any
        authenticated user can browse the catalog.
        """
        _, err = get_user_id(request)
        if err:
            return err

        async with get_session() as session:
            result = await session.execute(select(Block))
            blocks = result.scalars().all()
            return json_response([_serialize_block(b) for b in blocks])

    @app.get("/catalog/blocks/:uuid", openapi_tags=["Shop"])
    async def get_block(request: Request, uuid: str):
        """
        Fetch a single block from the catalog by its UUID.

        Returns 400 if the UUID is malformed and 404 if the block
        does not exist.
        """
        _, err = get_user_id(request)
        if err:
            return err

        try:
            block_uuid = uuid_pkg.UUID(uuid)
        except ValueError:
            return json_response({"error": "invalid uuid"}, status=400)

        async with get_session() as session:
            block = await session.get(Block, block_uuid)
            if not block:
                return json_response({"error": "block not found"}, status=404)
            return json_response(_serialize_block(block))

    # ─── Inventario ───────────────────────────────────────────────────

    @app.get("/inventory", openapi_tags=["Inventory"])
    async def get_inventory(request: Request):
        """
        Get the authenticated user's tokayito inventory.

        Returns every inventory entry for the user's tokayito, each
        including the full block details (name, durability, price)
        joined from the catalog. Returns an empty list if the
        tokayito has no items.

        Returns 404 if the user doesn't have a tokayito yet.
        """
        user_id, err = get_user_id(request)
        if err:
            return err

        async with get_session() as session:
            tokayo = await _get_tokayo_by_user(session, user_id)
            if not tokayo:
                return json_response(
                    {"error": "tokayo not found for user"}, status=404
                )

            result = await session.execute(
                select(InventoryItem).where(
                    InventoryItem.tokayo_id == tokayo.uuid
                )
            )
            entries = result.scalars().all()
            return json_response([_serialize_inventory_entry(e) for e in entries])

    # ─── Compra (incremento) ──────────────────────────────────────────

    @app.post("/shop/buy", openapi_tags=["Shop"])
    async def buy_block(request: Request):
        """
        Buy one or more blocks for the user's tokayito.

        Body:
            { "block_id": "<uuid>", "quantity": 5 }

        If the tokayito already owns this block, increments the quantity.
        Otherwise, creates a new inventory row.
        """
        user_id, err = get_user_id(request)
        if err:
            return err

        data, err = parse_json_body(request)
        if err:
            return err

        block_id_raw = data.get("block_id")
        quantity = data.get("quantity", 1)

        if not block_id_raw:
            return json_response({"error": "block_id is required"}, status=400)
        if not isinstance(quantity, int) or quantity < 1:
            return json_response(
                {"error": "quantity must be a positive integer"}, status=400
            )

        try:
            block_uuid = uuid_pkg.UUID(block_id_raw)
        except ValueError:
            return json_response({"error": "invalid block_id"}, status=400)

        async with get_session() as session:
            tokayo = await _get_tokayo_by_user(session, user_id)
            if not tokayo:
                return json_response(
                    {"error": "tokayo not found for user"}, status=404
                )

            block = await session.get(Block, block_uuid)
            if not block:
                return json_response({"error": "block not found"}, status=404)

            # TODO: validate user has enough points to buy `quantity * block.price`

            result = await session.execute(
                select(InventoryItem).where(
                    InventoryItem.tokayo_id == tokayo.uuid,
                    InventoryItem.block_id == block.uuid,
                )
            )
            entry = result.scalar_one_or_none()

            if entry:
                entry.quantity += quantity
            else:
                entry = InventoryItem(
                    user_id=user_id,
                    tokayo_id=tokayo.uuid,
                    block_id=block.uuid,
                    quantity=quantity,
                    equipped=False,
                )
                session.add(entry)
                
            # Aplicamos commit para guardar en base de datos
            await session.commit()
            # Refrescamos para tener el objeto `block` anidado listo para serializar
            await session.refresh(entry, attribute_names=["block"])
            
            # Serializamos la respuesta ANTES de cerrar la sesión
            response_data = _serialize_inventory_entry(entry)

        # Devolvemos la respuesta fuera del `async with`
        return json_response(response_data, status=201)

    # ─── Uso (decremento) ─────────────────────────────────────────────

    @app.post("/inventory/use", openapi_tags=["Inventory"])
    async def use_block(request: Request):
        """
        Use one or more blocks from the inventory.

        Body:
            { "block_id": "<uuid>", "quantity": 1 }

        Decrements the inventory quantity by the requested amount.
        If the resulting quantity is 0, the inventory row is deleted
        entirely.
        """
        user_id, err = get_user_id(request)
        if err:
            return err

        data, err = parse_json_body(request)
        if err:
            return err

        block_id_raw = data.get("block_id")
        quantity = data.get("quantity", 1)

        if not block_id_raw:
            return json_response({"error": "block_id is required"}, status=400)
        if not isinstance(quantity, int) or quantity < 1:
            return json_response(
                {"error": "quantity must be a positive integer"}, status=400
            )

        try:
            block_uuid = uuid_pkg.UUID(block_id_raw)
        except ValueError:
            return json_response({"error": "invalid block_id"}, status=400)

        async with get_session() as session:
            tokayo = await _get_tokayo_by_user(session, user_id)
            if not tokayo:
                return json_response(
                    {"error": "tokayo not found for user"}, status=404
                )

            result = await session.execute(
                select(InventoryItem).where(
                    InventoryItem.tokayo_id == tokayo.uuid,
                    InventoryItem.block_id == block_uuid,
                )
            )
            entry = result.scalar_one_or_none()

            if not entry:
                return json_response(
                    {"error": "block not in inventory"}, status=404
                )

            if entry.quantity < quantity:
                return json_response(
                    {
                        "error": "not enough quantity in inventory",
                        "available": entry.quantity,
                        "requested": quantity,
                    },
                    status=400,
                )

            entry.quantity -= quantity

            if entry.quantity == 0:
                await session.delete(entry)
                await session.commit() # ¡Faltaba el commit aquí también!
                return json_response(
                    {"deleted": True, "block_id": str(block_uuid)}
                )

            # Guardamos los cambios de la resta
            await session.commit()
            await session.refresh(entry, attribute_names=["block"])
            
            # Serializamos antes de cerrar la sesión
            response_data = _serialize_inventory_entry(entry)

        # Retornamos fuera del bloque async with
        return json_response(response_data)