"""APP-039: GameBridge.use_item and orchestrator dispatch + mode gates."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest


CAMPAIGN_SLUG = "use-item-test"


def _bootstrap_delver_with_rations(bridge, *, uses: int = 3) -> tuple[str, str]:
    """Return (character_id, instance_id) with rations in pack."""
    from tomb_gm.domain.character import create_character
    from tomb_gm.domain.inventory import new_instance
    from tomb_gm.services.content import ContentService

    bridge.campaign_new(CAMPAIGN_SLUG, "Use Item Test")
    bridge.session_start(CAMPAIGN_SLUG)
    lookup = ContentService(bridge.ctx.config.content_root).items_lookup()
    pack = [
        new_instance(
            "rations",
            kind="consumable",
            uses=uses,
            catalog=lookup.get("rations"),
        )
    ]
    create_character(
        bridge.ctx.conn,
        campaign_slug=CAMPAIGN_SLUG,
        display_name="Delver",
        base_class="novice",
        character_id="delver",
        inventory={"pack": pack, "equipped": {}},
    )
    bridge.ctx.conn.execute(
        "UPDATE characters SET slot = 1 WHERE id = 'delver' AND campaign_slug = ?",
        (CAMPAIGN_SLUG,),
    )
    bridge.ctx.conn.commit()
    return "delver", pack[0]["instanceId"]


def _load_pack(bridge, char_id: str) -> list:
    row = bridge.ctx.conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (char_id, CAMPAIGN_SLUG),
    ).fetchone()
    return json.loads(row["sheet_json"])["inventory"]["pack"]


# --- T1: bridge decrements uses ---


def test_bridge_use_consumable_decrements_uses(bridge):
    char_id, instance_id = _bootstrap_delver_with_rations(bridge, uses=3)

    result = bridge.use_item(instance_id, character_id=char_id)

    assert result["ok"] is True
    assert result.get("remaining") == 2
    pack = _load_pack(bridge, char_id)
    row = next(i for i in pack if i["instanceId"] == instance_id)
    assert row["uses"] == 2


# --- T2: bridge depletes row ---


def test_bridge_use_consumable_depletes_row(bridge):
    char_id, instance_id = _bootstrap_delver_with_rations(bridge, uses=1)

    result = bridge.use_item(instance_id, character_id=char_id)

    assert result["ok"] is True
    assert result.get("depleted") is True
    assert len(_load_pack(bridge, char_id)) == 0


# --- T3: equipped item rejected ---


def test_bridge_use_equipped_item_rejected(bridge):
    char_id, instance_id = _bootstrap_delver_with_rations(bridge, uses=3)
    row = bridge.ctx.conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (char_id, CAMPAIGN_SLUG),
    ).fetchone()
    sheet = json.loads(row["sheet_json"])
    target = next(i for i in sheet["inventory"]["pack"] if i["instanceId"] == instance_id)
    target["equipped"] = True
    bridge.ctx.conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), char_id, CAMPAIGN_SLUG),
    )
    bridge.ctx.conn.commit()

    result = bridge.use_item(instance_id, character_id=char_id)

    assert result["ok"] is False
    assert "equipped" in result.get("error", "").lower()
    pack = _load_pack(bridge, char_id)
    row = next(i for i in pack if i["instanceId"] == instance_id)
    assert row["uses"] == 3


# --- T4: combat gate ---


def test_execute_tool_use_item_combat_gate(orchestrator, monkeypatch):
    orchestrator.creation.active = False
    orchestrator.combat.active = True
    monkeypatch.setattr(orchestrator, "_combat_active_in_db", lambda: False)
    use_item_mock = MagicMock(return_value={"ok": True})
    monkeypatch.setattr(orchestrator.bridge, "use_item", use_item_mock)

    result = orchestrator._execute_tool("use_item", {"instance_id": "it-x"})

    assert result == {
        "ok": False,
        "error": (
            "During combat only combat_action and fortune_spend are available. "
            "Got: use_item"
        ),
    }
    use_item_mock.assert_not_called()


# --- T5: happy path dispatch ---


def test_execute_tool_use_item_happy_path(orchestrator, monkeypatch):
    orchestrator.creation.active = False
    orchestrator.combat.active = False
    monkeypatch.setattr(orchestrator, "_combat_active_in_db", lambda: False)
    expected = {
        "ok": True,
        "character_id": "delver",
        "instanceId": "it-1",
        "itemId": "rations",
        "used": 1,
        "remaining": 2,
    }
    use_item_mock = MagicMock(return_value=expected)
    monkeypatch.setattr(orchestrator.bridge, "use_item", use_item_mock)

    result = orchestrator._execute_tool(
        "use_item",
        {"instance_id": "it-1", "quantity": 1, "character_id": "delver"},
    )

    assert result == expected
    use_item_mock.assert_called_once_with(
        instance_id="it-1",
        quantity=1,
        character_id="delver",
    )


# --- T6: creation gate ---


def test_execute_tool_use_item_creation_gate(orchestrator, monkeypatch):
    orchestrator.creation.active = True
    orchestrator.combat.active = False
    monkeypatch.setattr(orchestrator, "_combat_active_in_db", lambda: False)
    use_item_mock = MagicMock(return_value={"ok": True})
    monkeypatch.setattr(orchestrator.bridge, "use_item", use_item_mock)

    result = orchestrator._execute_tool("use_item", {"instance_id": "it-x"})

    assert result == {
        "ok": False,
        "error": "During character creation, only set_creation_choice is available. Got: use_item",
    }
    use_item_mock.assert_not_called()
