import glob
import json
import os

import decky

# Crosshair glyphs written into MangoHud's custom_text lines.
STYLES = {
    "box": ("-----", "| + |", "-----"),
    "dot": (" ", "+", " "),
}

# How far the top-left of MangoHud's text block sits from the visual centre
# of the "+" glyph at MangoHud's default font size. These values come from the
# original 800p/1080p presets (e.g. 1280x800 box: 640-22=618, 400-20=380).
GLYPH_OFFSETS = {
    "box": (22, 20),
    "dot": (9, 20),
}

# Fallback if the screen resolution can't be read.
DEFAULT_RESOLUTION = (1280, 800)


class Plugin:
    def __init__(self):
        self.current_offset_x = None
        self.current_offset_y = None
        self.current_style = "box"  # "box" or "dot"
        self.resolution_mode = "auto"  # "auto" or "WIDTHxHEIGHT"
        self.active = False

    # ------------------------------------------------------------------ #
    # Settings persistence (so nudged positions survive a reboot)
    # ------------------------------------------------------------------ #
    def _settings_path(self):
        settings_dir = getattr(decky, "DECKY_PLUGIN_SETTINGS_DIR", None) or "/tmp"
        return os.path.join(settings_dir, "crosshair_settings.json")

    def _load_settings(self):
        try:
            with open(self._settings_path(), "r") as f:
                data = json.load(f)
            self.current_offset_x = data.get("offset_x")
            self.current_offset_y = data.get("offset_y")
            self.current_style = data.get("style", "box")
            self.resolution_mode = data.get("resolution_mode", "auto")
            self.active = bool(data.get("active", False))
        except FileNotFoundError:
            pass
        except Exception as e:
            decky.logger.error(f"Could not load settings: {e}")

    def _save_settings(self):
        try:
            path = self._settings_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(
                    {
                        "offset_x": self.current_offset_x,
                        "offset_y": self.current_offset_y,
                        "style": self.current_style,
                        "resolution_mode": self.resolution_mode,
                        "active": self.active,
                    },
                    f,
                )
        except Exception as e:
            decky.logger.error(f"Could not save settings: {e}")

    # ------------------------------------------------------------------ #
    # Screen resolution detection
    # ------------------------------------------------------------------ #
    def detect_resolution(self):
        """Read the active display's native mode from /sys/class/drm.

        Prefers an enabled external display (docked), otherwise the built-in
        panel (eDP). The result is always returned landscape (width >= height)
        because handheld/tablet panels are often natively portrait.
        """
        candidates = []
        for conn in glob.glob("/sys/class/drm/card*-*"):
            try:
                with open(os.path.join(conn, "status")) as f:
                    if f.read().strip() != "connected":
                        continue
                enabled = True
                enabled_path = os.path.join(conn, "enabled")
                if os.path.exists(enabled_path):
                    with open(enabled_path) as f:
                        enabled = f.read().strip() == "enabled"
                with open(os.path.join(conn, "modes")) as f:
                    first = f.readline().strip()
                if "x" not in first:
                    continue
                w_str, h_str = first.split("x", 1)
                w = int("".join(c for c in w_str if c.isdigit()))
                h = int("".join(c for c in h_str if c.isdigit()))
                internal = "-eDP-" in os.path.basename(conn) or "-DSI-" in os.path.basename(conn)
                candidates.append((enabled, not internal, max(w, h), min(w, h), os.path.basename(conn)))
            except Exception:
                continue

        if not candidates:
            decky.logger.warning("No display found in /sys/class/drm; using 1280x800")
            return DEFAULT_RESOLUTION

        # Enabled first, then external before internal.
        candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)
        enabled, _external, w, h, name = candidates[0]
        decky.logger.info(f"Detected display {name}: {w}x{h} (enabled={enabled})")
        return (w, h)

    def _target_resolution(self):
        if self.resolution_mode and self.resolution_mode != "auto":
            try:
                w, h = self.resolution_mode.lower().split("x")
                return (int(w), int(h))
            except Exception:
                pass
        return self.detect_resolution()

    def _centered_offsets(self, style, resolution=None):
        w, h = resolution or self._target_resolution()
        gx, gy = GLYPH_OFFSETS.get(style, GLYPH_OFFSETS["box"])
        return (w // 2 - gx, h // 2 - gy)

    # ------------------------------------------------------------------ #
    # MangoHud config
    # ------------------------------------------------------------------ #
    def find_mangohud_config_path(self):
        """Find the active MangoHUD config file path by looking for mangoapp process"""
        try:
            for proc_dir in os.listdir("/proc"):
                if not proc_dir.isdigit():
                    continue
                proc_path = f"/proc/{proc_dir}"
                try:
                    with open(f"{proc_path}/cmdline", "r") as f:
                        cmdline = f.read()
                    if "mangoapp" in cmdline:
                        with open(f"{proc_path}/environ", "r") as f:
                            environ = f.read()
                        for env_var in environ.split("\0"):
                            if env_var.startswith("MANGOHUD_CONFIGFILE="):
                                config_path = env_var.split("=", 1)[1]
                                decky.logger.info(f"Found MangoHUD config file: {config_path}")
                                return config_path
                except (FileNotFoundError, PermissionError, IOError):
                    continue

            common_paths = [
                os.path.expanduser("~/.config/MangoHud/MangoHud.conf"),
                "/tmp/mangohud.conf",
                "/tmp/MangoHud.conf",
            ]
            for path in common_paths:
                if os.path.exists(path):
                    decky.logger.info(f"Using fallback MangoHUD config: {path}")
                    return path

            default_path = "/tmp/mangohud_crosshair.conf"
            decky.logger.info(f"No MangoHUD config found, creating default: {default_path}")
            return default_path
        except Exception as e:
            decky.logger.error(f"Error finding MangoHUD config: {str(e)}")
            return "/tmp/mangohud_crosshair.conf"

    async def write_crosshair_config(self, custom_text_1: str, custom_text_2: str, custom_text_3: str, offset_x: int, offset_y: int):
        try:
            config_path = self.find_mangohud_config_path()
            crosshair_config = f"""legacy_layout=false
background_alpha=0
alpha=1
background_color=020202
text_color=FF007B
custom_text={custom_text_1}
custom_text={custom_text_2}
custom_text={custom_text_3}
offset_x={offset_x}
offset_y={offset_y}"""
            with open(config_path, "w") as f:
                f.write(crosshair_config)
            decky.logger.info(f"Crosshair configuration written to {config_path} ({offset_x},{offset_y})")
        except Exception as e:
            decky.logger.error(f"Error in write_crosshair_config: {str(e)}")
            raise e

    async def _apply(self, style, offset_x, offset_y):
        self.current_style = style
        self.current_offset_x = int(offset_x)
        self.current_offset_y = int(offset_y)
        self.active = True
        t1, t2, t3 = STYLES.get(style, STYLES["box"])
        await self.write_crosshair_config(t1, t2, t3, self.current_offset_x, self.current_offset_y)
        self._save_settings()

    # ------------------------------------------------------------------ #
    # Methods called from the frontend
    # ------------------------------------------------------------------ #
    async def get_screen_info(self) -> dict:
        detected = self.detect_resolution()
        target = self._target_resolution()
        return {
            "detected": f"{detected[0]}x{detected[1]}",
            "target": f"{target[0]}x{target[1]}",
            "mode": self.resolution_mode,
        }

    async def set_resolution_mode(self, mode: str):
        self.resolution_mode = mode or "auto"
        self._save_settings()
        # Re-centre straight away if a crosshair is already showing.
        if self.active:
            x, y = self._centered_offsets(self.current_style)
            await self._apply(self.current_style, x, y)

    async def make_centered_crosshair(self, style: str):
        x, y = self._centered_offsets(style)
        await self._apply(style, x, y)

    async def recenter_crosshair(self):
        x, y = self._centered_offsets(self.current_style)
        await self._apply(self.current_style, x, y)

    # Original fixed presets, kept for compatibility.
    async def make_800p_crosshair(self):
        await self._apply("box", *self._centered_offsets("box", (1280, 800)))

    async def make_1080p_crosshair(self):
        await self._apply("box", 938, 520)

    async def make_800p_dot_crosshair(self):
        await self._apply("dot", *self._centered_offsets("dot", (1280, 800)))

    async def make_1080p_dot_crosshair(self):
        await self._apply("dot", 952, 520)

    async def remove_crosshair(self):
        self.active = False
        await self.write_crosshair_config("", "", "", 0, 0)
        self._save_settings()

    async def adjust_crosshair_offset(self, x_delta: int, y_delta: int):
        if self.current_offset_x is None or self.current_offset_y is None:
            self.current_offset_x, self.current_offset_y = self._centered_offsets(self.current_style)
        await self._apply(
            self.current_style,
            self.current_offset_x + int(x_delta),
            self.current_offset_y + int(y_delta),
        )

    async def get_current_offsets(self) -> list:
        if self.current_offset_x is None or self.current_offset_y is None:
            return list(self._centered_offsets(self.current_style))
        return [self.current_offset_x, self.current_offset_y]

    async def _main(self):
        self._load_settings()
        decky.logger.info("Crosshair Plugin initialized!")

    async def _unload(self):
        decky.logger.info("Crosshair Plugin unloaded!")
