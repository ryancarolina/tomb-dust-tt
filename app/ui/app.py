"""Main PyGame application — window, event loop, layout, thread-safe UI updates."""

from __future__ import annotations

import json
import queue
import threading
import time
import pygame
from pathlib import Path

from ui.theme import BG_DARK, TEXT_MUTED, TEXT_ACCENT, FONT_SIZE_SMALL, FONT_SIZE
from ui.panels.narration import NarrationPanel
from ui.panels.input_box import InputBox
from ui.panels.sidebar import Sidebar

UI_EVENT = pygame.USEREVENT + 1
SAVE_PATH = Path(__file__).resolve().parents[1] / "session_state.json"


class App:
    def __init__(self, config: dict):
        self.config = config
        ui_cfg = config.get("ui", {})
        self.width = ui_cfg.get("window_width", 1280)
        self.height = ui_cfg.get("window_height", 800)
        self.narration_ratio = ui_cfg.get("narration_width_ratio", 0.7)

        self._orchestrator = None
        self._tts_config = config.get("tts", {})
        self._processing = False
        self._status_text = "Initializing..."
        self._ui_queue: queue.Queue = queue.Queue()
        self._scroll_velocity = 0.0
        self._target_scroll = None
        self._shutdown = False
        self._last_save_time = 0
        self._autosave_interval = 60.0

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
                    if self.narration.rect.collidepoint(pygame.mouse.get_pos()):
                        self._scroll_velocity = -event.y * 300
                elif event.type == pygame.MOUSEMOTION:
                    self.sidebar.handle_hover(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    map_addr = self.sidebar.handle_map_click(event.pos)
                    if map_addr and not self._processing:
                        self._submit(f"travel to {map_addr}")
                    else:
                        result = self.input_box.handle_click(event.pos)
                        if result and not self._processing:
                            self._submit(result)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._save_session()
                        running = False
                    else:
                        result = self.input_box.handle_event(event)
                        if result and not self._processing:
                            self._submit(result)

            self._process_ui_queue()
            self._update_scroll(dt)
            self._autosave()

            screen.fill(BG_DARK)
            self.narration.draw(screen)
            self.input_box.draw(screen)
            self.sidebar.draw(screen)
            self._draw_status(screen)

            pygame.display.flip()

        pygame.quit()

    def _layout(self, w: int, h: int):
        sidebar_w = int(w * (1 - self.narration_ratio))
        narr_w = w - sidebar_w
        input_h = 50
        narr_h = h - input_h

        narr_rect = pygame.Rect(0, 0, narr_w, narr_h)
        input_rect = pygame.Rect(0, narr_h, narr_w, input_h)
        sidebar_rect = pygame.Rect(narr_w, 0, sidebar_w, h)

        content_root = Path(__file__).resolve().parents[2] / "build"

        if hasattr(self, "narration"):
            self.narration.resize(narr_rect)
            self.input_box.resize(input_rect)
            self.sidebar.resize(sidebar_rect)
        else:
            self.narration = NarrationPanel(narr_rect)
            self.input_box = InputBox(input_rect)
            self.sidebar = Sidebar(sidebar_rect, content_root=content_root)

    def _init_orchestrator(self):
        def _init():
            try:
                from gm.orchestrator import Orchestrator
                self._orchestrator = Orchestrator(self.config)
                status = self._orchestrator.get_status()
                self._ui_queue.put(("status", status))

                awaiting = status.get("awaiting", "SETUP")
                if awaiting == "SETUP":
                    self._ui_queue.put(("narration", [
                        {"text": "Welcome to Tomb Dust.", "voice": "narrator"},
                        {"text": "No active session found. Type 'new game' to begin, or 'continue' to resume.", "voice": "narrator"},
                    ]))
                    self._ui_queue.put(("suggestions", ["new game", "continue"]))
                elif awaiting == "PLAYER_ACTIONS":
                    self._ui_queue.put(("narration", [
                        {"text": "Session resumed. The world awaits your next move.", "voice": "narrator"},
                    ]))
                elif awaiting == "SESSION_ENDED":
                    self._ui_queue.put(("narration", [
                        {"text": "Your last session has ended. Type 'continue' to start a new one.", "voice": "narrator"},
                    ]))
                    self._ui_queue.put(("suggestions", ["continue"]))

                self._ui_queue.put(("load_session", None))
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
            elif msg_type == "status":
                self.sidebar.update_from_status(data)
            elif msg_type == "speaker":
                voice, speaking = data
                self.sidebar.set_speaker(voice, speaking)
            elif msg_type == "suggestions":
                self.input_box.set_suggestions(data)
            elif msg_type == "ready":
                self._processing = False
                self._status_text = "Ready"
                self.sidebar.set_speaker("narrator", False)
            elif msg_type == "load_session":
                self._load_session()
            elif msg_type == "error":
                self.narration.add_line(f"[Error: {data}]", "narrator")
                self._processing = False
                self._status_text = "Error — try again"
            elif msg_type == "processing":
                self._processing = True
                self._status_text = data or "GM is thinking..."

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
        self.narration.scroll_to_bottom()

    def _draw_status(self, screen: pygame.Surface):
        font = pygame.font.SysFont("Consolas", FONT_SIZE_SMALL)
        if self._processing:
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
        self._ui_queue.put(("processing", "GM is thinking"))
        self._ui_queue.put(("player", text))
        thread = threading.Thread(target=self._process_turn, args=(text,), daemon=True)
        thread.start()

    def _process_turn(self, text: str):
        try:
            if not self._orchestrator:
                self._ui_queue.put(("error", "Orchestrator not initialized"))
                return

            narration = self._orchestrator.process_turn(text)

            from tomb_gm.services.tts.scene import parse_scene
            lines = parse_scene(narration)

            if lines:
                self._ui_queue.put(("narration", lines))
            else:
                self._ui_queue.put(("narration_text", narration))

            status = self._orchestrator.get_status()
            self._ui_queue.put(("status", status))

            suggestions = self._extract_suggestions(narration)
            if suggestions:
                self._ui_queue.put(("suggestions", suggestions))

            self._speak_narration(narration, lines)

        except Exception as exc:
            self._ui_queue.put(("error", str(exc)))
        finally:
            self._ui_queue.put(("ready", None))

    def _extract_suggestions(self, narration: str) -> list[str]:
        import re
        match = re.search(r"\[.*?Awaiting:\s*(.+?)\]", narration)
        if match:
            raw = match.group(1).strip()
            parts = [p.strip() for p in raw.split("|") if p.strip()]
            if not parts:
                parts = [p.strip() for p in raw.split(",") if p.strip()]
            return parts[:4]
        return []

    def _speak_narration(self, text: str, lines: list[dict] | None):
        if self._tts_config.get("mode") == "text_only":
            return
        try:
            from tomb_gm.services.tts import speak_scene
            from tomb_gm.services.tts.scene import filter_for_mode
            from tomb_gm.services.tts.voices import resolve_voice

            cache_dir = Path(__file__).resolve().parents[2] / "play" / "workspace" / ".local" / "tts-cache"
            cache_dir.mkdir(parents=True, exist_ok=True)

            mode = self._tts_config.get("mode", "speak_dialogue")
            speak_lines = lines if lines else None

            if speak_lines:
                filtered = filter_for_mode(speak_lines, mode)
                for line in filtered:
                    voice = line.get("voice", "narrator")
                    self._ui_queue.put(("speaker", (voice, True)))

            speak_scene(text, tts=self._tts_config, cache_dir=cache_dir, lines=speak_lines)

            self._ui_queue.put(("speaker", ("narrator", False)))
        except ImportError:
            pass
        except Exception:
            self._ui_queue.put(("speaker", ("narrator", False)))

    def _save_session(self):
        """Persist narration history and visited map cells."""
        data = {
            "narration_lines": self.narration.lines[-200:],
            "input_history": self.input_box.history[-50:],
            "visited_cells": list(self.sidebar.map.visited),
            "current_address": self.sidebar.map.current_address,
            "orchestrator_history": (
                self._orchestrator.history[-40:] if self._orchestrator else []
            ),
        }
        try:
            SAVE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_session(self):
        """Restore UI state from last save."""
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
        except Exception:
            pass
