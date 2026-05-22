"""Main PyGame application — window, event loop, layout, thread-safe UI updates."""

from __future__ import annotations

import json
import queue
import threading
import time
from copy import deepcopy
import pygame
from pathlib import Path

from tomb_gm.services.content import ContentService
from ui.theme import BG_DARK, TEXT_MUTED, TEXT_ACCENT, FONT_SIZE_SMALL, FONT_SIZE
from gm.image_resolver import ImageResolver
from gm.image_service import ImageService
from ui.panels.illustration import IllustrationPanel
from ui.panels.narration import NarrationPanel
from ui.panels.input_box import InputBox
from ui.panels.character_panel import CharacterPanel
from ui.panels.sidebar import Sidebar

UI_EVENT = pygame.USEREVENT + 1
SAVE_PATH = Path(__file__).resolve().parents[1] / "session_state.json"
MAP_TRAVEL_BLOCKED_HINT = "Finish Registry intake first"


class App:
    def __init__(self, config: dict):
        self.config = config
        ui_cfg = config.get("ui", {})
        self.width = ui_cfg.get("window_width", 1280)
        self.height = ui_cfg.get("window_height", 800)
        self.narration_ratio = ui_cfg.get("narration_width_ratio", 0.7)
        self.character_panel_ratio = ui_cfg.get("character_panel_width_ratio", 0.22)
        self.sidebar_ratio = ui_cfg.get(
            "sidebar_width_ratio",
            max(0.2, 1.0 - self.narration_ratio),
        )
        self.illustration_ratio = float(ui_cfg.get("illustration_height_ratio", 0.35))

        self._orchestrator = None
        self._tts_config = config.get("tts", {})
        self._tts_enabled = self._tts_config.get("mode") != "text_only"
        self._images_config = config.get("images", {}) or {}
        self._images_enabled = bool(self._images_config.get("enabled", False))
        self._image_service: ImageService | None = None
        self._content_root = Path(__file__).resolve().parents[2] / "build"
        self._content_service: ContentService | None = None
        self._image_resolver = ImageResolver()
        self._turn_state = "idle"  # idle | thinking | speaking
        self._current_turn_id = 0
        self._turn_lock = threading.Lock()
        self._status_text = "Initializing..."
        self._ui_queue: queue.Queue = queue.Queue()
        self._scroll_velocity = 0.0
        self._target_scroll = None
        self._shutdown = False
        self._last_save_time = 0
        self._autosave_interval = 60.0
        self._map_travel_blocked_flag = False
        self._selected_character_item_instance_id: str | None = None
        self._selected_character_catalog_item_id: str | None = None
        self._selected_npc_id: str | None = None
        self._prev_engine_status: dict | None = None

    def run(self):
        pygame.init()
        pygame.display.set_caption("Tomb Dust")
        screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        clock = pygame.time.Clock()

        self._layout(self.width, self.height)
        self._init_orchestrator()

        running = True
        while running:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._save_session()
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.w, event.h
                    screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self._layout(self.width, self.height)
                elif event.type == pygame.MOUSEWHEEL:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.character_panel.rect.collidepoint(mouse_pos):
                        self.character_panel.handle_wheel(event.y)
                    elif self.narration.rect.collidepoint(mouse_pos):
                        self._scroll_velocity = -event.y * 300
                elif event.type == pygame.MOUSEMOTION:
                    self.sidebar.handle_hover(event.pos)
                    self.illustration.handle_images_hover(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.sidebar.handle_voice_toggle_click(event.pos):
                        self._toggle_tts_enabled()
                    elif self.character_panel.handle_click(event.pos):
                        pass
                    elif self.illustration.handle_images_toggle_click(event.pos):
                        self._toggle_images_enabled()
                    else:
                        map_addr = self.sidebar.handle_map_click(event.pos)
                        if map_addr and self._can_submit() and not self._map_travel_blocked():
                            self._submit(f"travel to {map_addr}")
                        else:
                            result = self.input_box.handle_click(event.pos)
                            if result and self._can_submit():
                                self._submit(result)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._save_session()
                        running = False
                    else:
                        result = self.input_box.handle_event(event)
                        if result and self._can_submit():
                            self._submit(result)

            self._process_ui_queue()
            self._update_scroll(dt)
            self._autosave()

            screen.fill(BG_DARK)
            self.character_panel.draw(screen)
            self.illustration.draw(screen)
            self.narration.draw(screen)
            self.input_box.draw(screen)
            self.sidebar.draw(screen)
            self._draw_status(screen)

            pygame.display.flip()

        pygame.quit()

    def _layout(self, w: int, h: int):
        character_w = int(w * self.character_panel_ratio)
        sidebar_w = int(w * self.sidebar_ratio)
        center_w = w - character_w - sidebar_w
        if center_w < 240:
            center_w = 240
            if character_w + sidebar_w > w - center_w:
                overage = character_w + sidebar_w - (w - center_w)
                shrink_left = min(character_w - 120, overage // 2) if character_w > 120 else 0
                character_w -= max(0, shrink_left)
                overage = character_w + sidebar_w - (w - center_w)
                if overage > 0 and sidebar_w > 180:
                    sidebar_w -= min(sidebar_w - 180, overage)
        center_w = max(1, w - character_w - sidebar_w)
        input_h = 50
        center_h = h - input_h
        min_illustration_h = 160
        min_narration_h = 120
        requested_illustration_h = int(center_h * self.illustration_ratio)
        illustration_h = max(min_illustration_h, requested_illustration_h)
        if center_h - illustration_h < min_narration_h:
            illustration_h = max(80, center_h - min_narration_h)
        illustration_h = max(80, min(center_h - 40, illustration_h))
        narr_h = max(40, center_h - illustration_h)

        character_rect = pygame.Rect(0, 0, character_w, h)
        illustration_rect = pygame.Rect(character_w, 0, center_w, illustration_h)
        narr_rect = pygame.Rect(character_w, illustration_h, center_w, narr_h)
        input_rect = pygame.Rect(character_w, illustration_h + narr_h, center_w, input_h)
        sidebar_rect = pygame.Rect(character_w + center_w, 0, sidebar_w, h)

        if hasattr(self, "narration"):
            self.character_panel.resize(character_rect)
            self.illustration.resize(illustration_rect)
            self.narration.resize(narr_rect)
            self.input_box.resize(input_rect)
            self.sidebar.resize(sidebar_rect)
        else:
            self.character_panel = CharacterPanel(
                character_rect,
                on_item_selected=self._on_character_item_selected,
            )
            default_title_path = self._content_root / "data" / "illustrations" / "tomb-dust-title.png"
            self.illustration = IllustrationPanel(
                illustration_rect,
                default_image_path=default_title_path if default_title_path.is_file() else None,
            )
            self.narration = NarrationPanel(narr_rect)
            self.input_box = InputBox(input_rect)
            self.sidebar = Sidebar(sidebar_rect, content_root=self._content_root)

        mode = self._tts_config.get("mode", "speak_dialogue")
        self.sidebar.set_tts_chip_visible(mode != "text_only")
        self.sidebar.set_tts_enabled(self._tts_enabled)
        self.illustration.set_images_chip_visible(True)
        self.illustration.set_images_enabled(self._images_enabled)

    def _init_orchestrator(self):
        def _init():
            try:
                from gm.orchestrator import Orchestrator
                self._orchestrator = Orchestrator(self.config)
                raw_status = self._orchestrator.get_status()
                self._prev_engine_status = deepcopy(raw_status)
                status = self._enrich_status_for_ui(raw_status)
                self._ui_queue.put(("status", status))

                has_save = self._orchestrator.bridge.has_save()

                self._ui_queue.put(("narration", [
                    {"text": "TOMB DUST", "voice": "narrator"},
                    {"text": "A hardcore extraction-fantasy TTRPG.", "voice": "narrator"},
                    {"text": "Death is frequent. The world is hostile. Even small victories are meaningful.", "voice": "narrator"},
                    {"text": "", "voice": "narrator"},
                ]))

                if has_save:
                    self._ui_queue.put(("narration", [
                        {"text": "You have a saved game.", "voice": "narrator"},
                    ]))
                    self._ui_queue.put(("suggestions", ["load game", "new game"]))
                else:
                    self._ui_queue.put(("narration", [
                        {"text": "Type 'new game' to create a character and enter the world.", "voice": "narrator"},
                    ]))
                    self._ui_queue.put(("suggestions", ["new game"]))

                self._ui_queue.put(("ready", None))
            except Exception as exc:
                self._ui_queue.put(("error", f"Init failed: {exc}"))

        threading.Thread(target=_init, daemon=True).start()

    def _process_ui_queue(self):
        while not self._ui_queue.empty():
            try:
                msg_type, data = self._ui_queue.get_nowait()
            except queue.Empty:
                break

            if msg_type == "narration":
                self.narration.add_lines(data)
                self._smooth_scroll_to_bottom()
            elif msg_type == "narration_text":
                self.narration.add_line(data, "narrator")
                self._smooth_scroll_to_bottom()
            elif msg_type == "player":
                self.narration.add_line(data, "player")
                self._smooth_scroll_to_bottom()
            elif msg_type == "clear_narration":
                self.narration.clear()
            elif msg_type == "status":
                self._map_travel_blocked_flag = bool(data.get("map_travel_blocked"))
                self.sidebar.update_from_status(data)
                self._refresh_character_panel_data(data)
            elif msg_type == "map_update":
                if isinstance(data, dict):
                    self.sidebar.map.update_position(
                        address=data.get("address", ""),
                        scene_index=data.get("scene_index", 1),
                        scene_max=data.get("scene_max", 3),
                        heading=data.get("heading", "N"),
                        mode=data.get("mode", "surface"),
                        dungeon_room=data.get("dungeon_room"),
                        dungeon_exits=data.get("dungeon_exits"),
                    )
                else:
                    self.sidebar.map.update_position(address=data)
            elif msg_type == "speaker":
                voice, speaking = data
                self.sidebar.set_speaker(voice, speaking)
            elif msg_type == "suggestions":
                self.input_box.set_suggestions(data)
            elif msg_type == "ready":
                self._set_turn_idle()
            elif msg_type == "turn_idle":
                if data == self._current_turn_id:
                    self._set_turn_idle()
            elif msg_type == "load_session":
                self._load_session()
            elif msg_type == "error":
                self.narration.add_line(f"[Error: {data}]", "narrator")
                self._smooth_scroll_to_bottom()
                self._set_turn_idle("Error — try again")
            elif msg_type == "processing":
                self._turn_state = "thinking"
                self._status_text = data or "GM is thinking..."
            elif msg_type == "speaking":
                self._turn_state = "speaking"
                self._status_text = "GM is speaking (Enter to interrupt)"
            elif msg_type == "illustration":
                if isinstance(data, dict):
                    self.illustration.set_illustration(
                        path=data.get("path"),
                        title=data.get("title", ""),
                        loading=bool(data.get("loading", False)),
                    )
            elif msg_type == "illustration_clear":
                self.illustration.clear_to_default()
            elif msg_type == "character_item_selected":
                if isinstance(data, dict):
                    self._selected_character_item_instance_id = data.get("instance_id")
                    self._selected_character_catalog_item_id = data.get("item_id")
                else:
                    self._selected_character_item_instance_id = None
                    self._selected_character_catalog_item_id = data

                if self._selected_character_catalog_item_id:
                    catalog_item_id = self._selected_character_catalog_item_id
                    self._request_illustration(
                        "item",
                        catalog_item_id,
                        self._item_display_name(catalog_item_id),
                    )
                elif self._selected_npc_id:
                    self._request_illustration(
                        "npc",
                        self._selected_npc_id,
                        self._entity_display_name(self._selected_npc_id),
                    )
                else:
                    self._ui_queue.put(("illustration_clear", None))

    def _update_scroll(self, dt: float):
        if abs(self._scroll_velocity) > 1:
            self.narration.scroll(int(self._scroll_velocity * dt))
            self._scroll_velocity *= 0.85
        else:
            self._scroll_velocity = 0

    def _autosave(self):
        now = time.time()
        if now - self._last_save_time > self._autosave_interval:
            self._last_save_time = now
            self._save_session()

    def _smooth_scroll_to_bottom(self):
        self.narration.request_follow_tail()

    def _can_submit(self) -> bool:
        return self._turn_state != "thinking"

    def _set_turn_idle(self, status_text: str = "Ready") -> None:
        self._turn_state = "idle"
        self._status_text = status_text
        self.sidebar.set_speaker("narrator", False)

    def _toggle_tts_enabled(self) -> None:
        self._tts_enabled = not self._tts_enabled
        self.sidebar.set_tts_enabled(self._tts_enabled)
        if not self._tts_enabled and self._turn_state == "speaking":
            from tomb_gm.services.tts.queue import request_stop
            request_stop()
            self._set_turn_idle()

    def _toggle_images_enabled(self) -> None:
        self._images_enabled = not self._images_enabled
        self.illustration.set_images_enabled(self._images_enabled)
        if not self._images_enabled:
            service = self._image_service
            if service:
                service.cancel_generation()

    def _draw_status(self, screen: pygame.Surface):
        font = pygame.font.SysFont("Consolas", FONT_SIZE_SMALL)
        if self._turn_state == "thinking":
            dots = "." * ((pygame.time.get_ticks() // 400) % 4)
            text = f"{self._status_text}{dots}"
            color = TEXT_ACCENT
        else:
            text = self._status_text
            color = TEXT_MUTED

        surf = font.render(text, True, color)
        screen.blit(surf, (self.input_box.rect.left + 10, self.input_box.rect.top - 18))

        model_name = self.config.get("llm", {}).get("model", "unknown")
        model_surf = font.render(f"Model: {model_name}", True, TEXT_MUTED)
        screen.blit(model_surf, (self.input_box.rect.right - model_surf.get_width() - 10, self.input_box.rect.top - 18))

    def _submit(self, text: str):
        if not self._can_submit():
            return

        if self._turn_state == "speaking":
            from tomb_gm.services.tts.queue import request_stop
            request_stop()

        self._current_turn_id += 1
        turn_id = self._current_turn_id

        self._ui_queue.put(("processing", "GM is thinking"))
        self._ui_queue.put(("player", text))
        thread = threading.Thread(
            target=self._process_turn,
            args=(text, turn_id),
            daemon=True,
        )
        thread.start()

    def _process_turn(self, text: str, turn_id: int):
        narration = None
        lines = None
        try:
            if turn_id != self._current_turn_id:
                return

            if not self._orchestrator:
                self._ui_queue.put(("error", "Orchestrator not initialized"))
                return

            if text.lower().strip() in ("load game", "load", "continue", "resume"):
                self._ui_queue.put(("load_session", None))
            elif text.lower().strip() in ("new game", "new", "start"):
                self._ui_queue.put(("clear_narration", None))

            with self._turn_lock:
                if turn_id != self._current_turn_id:
                    return
                narration = self._orchestrator.process_turn(text)

            if turn_id != self._current_turn_id:
                return

            from tomb_gm.services.tts.scene import parse_scene
            lines = parse_scene(narration)
            if not self._selected_character_catalog_item_id:
                npc_id = self._image_resolver.primary_key_npc_from_lines(lines)
                if npc_id:
                    self._selected_npc_id = npc_id
                    self._request_illustration("npc", npc_id, self._entity_display_name(npc_id))

            self._ui_queue.put(("narration_text", narration))

            status = self._orchestrator.get_status()
            party = status.get("party")
            if party and party.get("address"):
                map_data = {
                    "address": party["address"],
                    "scene_index": party.get("scene_index", 1),
                    "scene_max": party.get("scene_max", 3),
                    "heading": party.get("heading", "N"),
                    "mode": party.get("mode", "surface"),
                    "dungeon_room": party.get("dungeon_room_id"),
                    "dungeon_exits": party.get("dungeon_exits", []),
                }
                self._ui_queue.put(("map_update", map_data))

        except Exception as exc:
            if turn_id == self._current_turn_id:
                self._ui_queue.put(("error", str(exc)))
            return
        finally:
            self._queue_turn_suggestions(turn_id)
            self._queue_turn_status(turn_id)
            if self._orchestrator and narration is not None and turn_id == self._current_turn_id:
                self._save_session()

        if turn_id != self._current_turn_id:
            return

        if (
            narration
            and self._tts_enabled
            and self._tts_config.get("mode") != "text_only"
        ):
            threading.Thread(
                target=self._speak_narration,
                args=(narration, lines, turn_id),
                daemon=True,
            ).start()
        else:
            self._ui_queue.put(("turn_idle", turn_id))

    def _map_travel_blocked(self) -> bool:
        return self._map_travel_blocked_flag

    def _enrich_status_for_ui(self, status: dict) -> dict:
        if not self._orchestrator:
            return status
        out = dict(status)
        blocked = self._orchestrator.is_map_travel_blocked()
        out["map_travel_blocked"] = blocked
        if blocked:
            out["map_travel_blocked_hint"] = MAP_TRAVEL_BLOCKED_HINT
        badge = self._orchestrator.get_creation_step_badge()
        if badge:
            out["creation_step"] = badge["step"]
            out["creation_step_display"] = badge["display_label"]
        else:
            out["creation_step"] = None
            out["creation_step_display"] = None
        return out

    def _queue_turn_status(self, turn_id: int) -> None:
        if turn_id != self._current_turn_id or not self._orchestrator:
            return
        try:
            raw_status = self._orchestrator.get_status()
        except Exception:
            return
        status = self._enrich_status_for_ui(raw_status)
        self._ui_queue.put(("status", status))

        winner = self._image_resolver.pick_winner(
            self._image_resolver.detect_entities(self._prev_engine_status, raw_status),
            item_selected=bool(self._selected_character_catalog_item_id),
            npc_id=None,
        )
        if winner:
            entity_type = str(winner.get("entity_type") or "").strip()
            entity_id = str(winner.get("entity_id") or "").strip()
            if entity_type and entity_id:
                self._request_illustration(
                    entity_type,
                    entity_id,
                    self._entity_display_name(entity_id),
                )
        self._prev_engine_status = deepcopy(raw_status)

    def _queue_turn_suggestions(self, turn_id: int) -> None:
        """Unconditional chip refresh after every turn (success or error)."""
        if turn_id != self._current_turn_id or not self._orchestrator:
            return
        self._ui_queue.put(
            ("suggestions", self._orchestrator.get_player_suggestions())
        )

    def _on_character_item_selected(self, item: dict | str | None) -> None:
        if isinstance(item, dict):
            payload = {
                "instance_id": item.get("instance_id"),
                "item_id": item.get("item_id"),
            }
        elif isinstance(item, str):
            payload = {"instance_id": None, "item_id": item}
        else:
            payload = {"instance_id": None, "item_id": None}
        self._ui_queue.put(("character_item_selected", payload))

    def _entity_display_name(self, entity_id: str) -> str:
        return str(entity_id).replace("-", " ").replace("_", " ").title()

    def _resolve_campaign_slug(self) -> str:
        if not self._orchestrator:
            return "default"
        try:
            status = self._orchestrator.get_status()
        except Exception:
            return "default"
        active = status.get("active") if isinstance(status, dict) else None
        if isinstance(active, dict):
            slug = active.get("campaign_slug")
            if slug:
                return str(slug)
        return "default"

    def _get_content_service(self) -> ContentService:
        if self._content_service is None:
            self._content_service = ContentService(self._content_root)
        return self._content_service

    def _item_display_name(self, item_id: str) -> str:
        try:
            item = self._get_content_service().load_item(item_id) or {}
        except Exception:
            item = {}
        return str(item.get("displayName") or self._entity_display_name(item_id))

    def _get_image_service(self) -> ImageService:
        if self._image_service is None:
            repo_root = Path(__file__).resolve().parents[2]
            self._image_service = ImageService(
                workspace=repo_root / "play" / "workspace",
                content_root=self._content_root,
                async_generation=True,
            )
        return self._image_service

    def _request_illustration(self, entity_type: str, entity_id: str, title: str) -> None:
        if not self._orchestrator:
            return
        campaign_slug = self._resolve_campaign_slug()
        service = self._get_image_service()
        images_cfg = self._images_config
        should_show_loading = bool(images_cfg.get("enabled", False) and self._images_enabled)
        if should_show_loading:
            self._ui_queue.put(
                (
                    "illustration",
                    {
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "title": title,
                        "loading": True,
                    },
                )
            )

        def _on_complete(path: str | None) -> None:
            if path:
                self._ui_queue.put(
                    (
                        "illustration",
                        {
                            "entity_type": entity_type,
                            "entity_id": entity_id,
                            "title": title,
                            "path": path,
                            "loading": False,
                        },
                    )
                )
            elif should_show_loading:
                self._ui_queue.put(("illustration_clear", None))

        def _resolve() -> None:
            resolved = service.resolve(
                campaign_slug,
                entity_type,
                entity_id,
                images_enabled=self._images_enabled,
                config=self.config,
                on_complete=_on_complete,
            )
            if resolved:
                _on_complete(resolved)

        threading.Thread(target=_resolve, daemon=True).start()

    def _refresh_character_panel_data(self, status: dict | None = None) -> None:
        if not self._orchestrator or not hasattr(self, "character_panel"):
            return
        bridge = getattr(self._orchestrator, "bridge", None)
        if not bridge:
            self.character_panel.update_inventory(None)
            self.character_panel.update_spells(None)
            return

        character_id = None
        roster = (status or {}).get("roster") if isinstance(status, dict) else None
        if roster:
            top = roster[0]
            character_id = top.get("character_id") or top.get("id")

        inventory_payload = None
        try:
            inventory_payload = bridge.list_inventory(character_id=character_id)
        except TypeError:
            inventory_payload = bridge.list_inventory()
        except Exception:
            inventory_payload = None

        if inventory_payload and inventory_payload.get("ok"):
            character_id = inventory_payload.get("character_id") or character_id
        self.character_panel.update_inventory(inventory_payload)

        spells_payload = None
        if character_id:
            try:
                spells_payload = bridge.list_known_spells(character_id)
            except Exception:
                spells_payload = None
        self.character_panel.update_spells(spells_payload)

    def _speak_narration(self, text: str, lines: list[dict] | None, turn_id: int):
        if turn_id != self._current_turn_id:
            return
        if not self._tts_enabled or self._tts_config.get("mode") == "text_only":
            if turn_id == self._current_turn_id:
                self._ui_queue.put(("turn_idle", turn_id))
            return

        self._ui_queue.put(("speaking", None))
        try:
            from tomb_gm.services.tts import speak_scene
            from tomb_gm.services.tts.scene import filter_for_mode

            cache_dir = Path(__file__).resolve().parents[2] / "play" / "workspace" / ".local" / "tts-cache"
            cache_dir.mkdir(parents=True, exist_ok=True)

            mode = self._tts_config.get("mode", "speak_dialogue")
            speak_lines = lines if lines else None

            if turn_id != self._current_turn_id:
                return

            if speak_lines:
                filtered = filter_for_mode(speak_lines, mode)
                for line in filtered:
                    if turn_id != self._current_turn_id:
                        return
                    voice = line.get("voice", "narrator")
                    self._ui_queue.put(("speaker", (voice, True)))

            if turn_id != self._current_turn_id:
                return

            speak_scene(text, tts=self._tts_config, cache_dir=cache_dir, lines=speak_lines)

        except ImportError:
            pass
        except Exception:
            pass
        finally:
            if turn_id == self._current_turn_id:
                self._ui_queue.put(("turn_idle", turn_id))
            else:
                self._ui_queue.put(("speaker", ("narrator", False)))

    def _save_session(self):
        """Persist narration history and visited map cells.

        Snapshots full ``get_status()`` under ``engine_status`` for APP-017/018
        reconcile on load; read path is out of scope for APP-016.
        """
        session_id = None
        campaign_slug = None
        engine_status: dict | None = None
        if self._orchestrator:
            try:
                status = self._orchestrator.get_status()
                active = status.get("active") or {}
                session_id = active.get("session_id")
                campaign_slug = active.get("campaign_slug")
                if status.get("ok") is not False and "_error" not in status:
                    engine_status = status
            except Exception:
                pass
        data = {
            "session_id": session_id,
            "campaign_slug": campaign_slug,
            "narration_lines": self.narration.lines[-200:],
            "input_history": self.input_box.history[-50:],
            "visited_cells": list(self.sidebar.map.visited),
            "current_address": self.sidebar.map.current_address,
            "orchestrator_history": (
                self._orchestrator.history[-40:] if self._orchestrator else []
            ),
            "creation_state": (
                self._orchestrator.export_creation_state() if self._orchestrator else None
            ),
            "combat_state": (
                self._orchestrator.export_combat_state() if self._orchestrator else None
            ),
        }
        if engine_status is not None:
            data["engine_status"] = engine_status
        try:
            SAVE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_session(self):
        """Restore UI state from last save, then sync with DB state."""
        if not SAVE_PATH.exists():
            return
        try:
            data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
            for line in data.get("narration_lines", []):
                self.narration.lines.append(line)
            self.narration._dirty = True

            self.input_box.history = data.get("input_history", [])
            self.sidebar.map.visited = set(data.get("visited_cells", []))
            addr = data.get("current_address")
            if addr:
                self.sidebar.map.current_address = addr

            if self._orchestrator:
                self._orchestrator.history = data.get("orchestrator_history", [])
                # Creation state from UI file is only valid when DB has no roster yet.
                self._orchestrator.import_creation_state(data.get("creation_state"))
                self._orchestrator.import_combat_state(data.get("combat_state"))
                self._orchestrator._sync_creation_from_status()
                self._orchestrator._sync_combat_from_status()
        except Exception:
            pass

        if self._orchestrator:
            synced_status = None
            try:
                synced_status = self._orchestrator.get_status()
                party = synced_status.get("party")
                if party:
                    real_addr = party.get("address")
                    if real_addr:
                        self.sidebar.map.current_address = real_addr
                        self.sidebar.map.visited.add(real_addr)
            except Exception:
                pass
            if synced_status is not None:
                try:
                    self._prev_engine_status = deepcopy(synced_status)
                    self._ui_queue.put(("status", self._enrich_status_for_ui(synced_status)))
                except Exception:
                    pass

        self._tts_enabled = self._tts_config.get("mode") != "text_only"
        self.sidebar.set_tts_enabled(self._tts_enabled)
