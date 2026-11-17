# Crosshair Plugin

Fork of [Crosshair](https://github.com/xXJSONDeruloXx/crosshair-plugin) by JSON Derulo, with auto-centering on any resolution, an adjustable nudge step and saved positions.

The Crosshair Plugin is a tool for the Steam Deck that overlays a crosshair on the screen. It uses MangoHud's configuration to display a customizable aiming aid, making it useful for games that don’t provide a native crosshair.

## Features

- Automatically centers the crosshair on any screen (reads the display's resolution).
- Resolution override for ROG Flow Z13 (2560x1600 / 1920x1200), 1080p and Steam Deck 800p.
- Adjustable nudge step (1/5/10/50 px); your position is saved across reboots.
- Adjustable offsets to fine-tune the crosshair's position.
- Displays the current x and y offsets in the UI.

## Usage

1. Open the plugin from Decky Loader.
2. Leave **Screen resolution** on Auto-detect (or pick your screen), then tap **Centered Crosshair Box** or **Dot**.
3. Adjust the crosshair's position using the directional buttons (Up, Down, Left, Right).
4. View the current offsets in the plugin UI for reference.

## How It Works

- The plugin generates a MangoHud configuration file with the crosshair settings.
- Offset adjustments are handled dynamically, and the configuration is updated automatically.
- NOTE: this may conflict with any MangoHUD overrides you have set, or override plugins such as MangoPeel.