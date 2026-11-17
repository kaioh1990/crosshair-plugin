import {
  ButtonItem,
  DropdownItem,
  PanelSection,
  PanelSectionRow,
  staticClasses,
} from "@decky/ui";
import { callable, definePlugin } from "@decky/api";
import { useState, useEffect } from "react";
import { FaCrosshairs } from "react-icons/fa";

interface ScreenInfo {
  mode: string; // "auto" or "WIDTHxHEIGHT"
  detected: string; // detected resolution, e.g. "1280x800"
  target: string; // resolution actually used for centering
}

const makeCenteredCrosshair = callable<[style: string], void>("make_centered_crosshair");
const recenterCrosshair = callable<[], void>("recenter_crosshair");
const setResolutionMode = callable<[mode: string], void>("set_resolution_mode");
const getScreenInfo = callable<[], ScreenInfo>("get_screen_info");
const adjustCrosshairOffset = callable<[number, number], void>("adjust_crosshair_offset");
const getCurrentOffsets = callable<[], number[]>("get_current_offsets");
const removeCrosshair = callable<[], void>("remove_crosshair");

const RESOLUTION_OPTIONS = [
  { data: "auto", label: "Auto-detect" },
  { data: "2560x1600", label: "2560 x 1600 (ROG Flow Z13)" },
  { data: "1920x1200", label: "1920 x 1200 (ROG Flow Z13 FHD)" },
  { data: "1920x1080", label: "1920 x 1080 (TV / monitor)" },
  { data: "1280x800", label: "1280 x 800 (Steam Deck)" },
];

const STEP_OPTIONS = [1, 5, 10, 50].map((n) => ({ data: n, label: `${n} px` }));

function Content() {
  const [status, setStatus] = useState("No action yet");
  const [xOffset, setXOffset] = useState(0);
  const [yOffset, setYOffset] = useState(0);
  const [screen, setScreen] = useState<ScreenInfo | null>(null);
  const [step, setStep] = useState(5);

  const refresh = async () => {
    try {
      const [x, y] = await getCurrentOffsets();
      setXOffset(x);
      setYOffset(y);
      setScreen(await getScreenInfo());
    } catch (error) {
      console.error(error);
    }
  };

  const run = async (action: () => Promise<unknown>, ok: string, fail: string) => {
    try {
      await action();
      setStatus(ok);
      await refresh();
    } catch (error) {
      console.error(error);
      setStatus(fail);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  return (
    <PanelSection title="Crosshair Plugin">
      <PanelSectionRow>
        <div style={{ fontSize: "12px" }}>
          This plugin replaces the performance overlay with a crosshair. To restore the performance overlay, toggle
          one of its levels in the QAM performance tab.
        </div>
      </PanelSectionRow>

      <PanelSectionRow>
        <DropdownItem
          label="Screen resolution"
          description={screen ? `Detected: ${screen.detected.replace("x", " x ")}` : undefined}
          rgOptions={RESOLUTION_OPTIONS}
          selectedOption={screen?.mode ?? "auto"}
          onChange={(opt) =>
            run(() => setResolutionMode(opt.data), `Screen set to ${opt.label}`, "Failed to set screen resolution.")
          }
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={() => run(() => makeCenteredCrosshair("box"), "Centered box crosshair applied!", "Failed to apply crosshair.")}
        >
          Centered Crosshair Box
        </ButtonItem>
      </PanelSectionRow>
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={() => run(() => makeCenteredCrosshair("dot"), "Centered dot crosshair applied!", "Failed to apply crosshair.")}
        >
          Centered Crosshair Dot
        </ButtonItem>
      </PanelSectionRow>
      <PanelSectionRow>
        <ButtonItem layout="below" onClick={() => run(recenterCrosshair, "Crosshair re-centered.", "Failed to re-center crosshair.")}>
          Re-center
        </ButtonItem>
      </PanelSectionRow>
      <PanelSectionRow>
        <ButtonItem layout="below" onClick={() => run(removeCrosshair, "Crosshair removed!", "Failed to remove crosshair.")}>
          Remove Crosshair
        </ButtonItem>
      </PanelSectionRow>

      <PanelSectionRow>
        <DropdownItem
          label="Nudge step"
          rgOptions={STEP_OPTIONS}
          selectedOption={step}
          onChange={(opt) => setStep(opt.data)}
        />
      </PanelSectionRow>
      <PanelSectionRow>
        <ButtonItem layout="below" onClick={() => run(() => adjustCrosshairOffset(0, -step), `Moved up ${step}px`, "Failed to move.")}>
          Up
        </ButtonItem>
        <ButtonItem layout="below" onClick={() => run(() => adjustCrosshairOffset(-step, 0), `Moved left ${step}px`, "Failed to move.")}>
          Left
        </ButtonItem>
        <ButtonItem layout="below" onClick={() => run(() => adjustCrosshairOffset(step, 0), `Moved right ${step}px`, "Failed to move.")}>
          Right
        </ButtonItem>
        <ButtonItem layout="below" onClick={() => run(() => adjustCrosshairOffset(0, step), `Moved down ${step}px`, "Failed to move.")}>
          Down
        </ButtonItem>
      </PanelSectionRow>

      <PanelSectionRow>
        <div>Status: {status}</div>
      </PanelSectionRow>
      <PanelSectionRow>
        <div>
          Current Offsets: X = {xOffset}, Y = {yOffset}
          {screen ? ` (screen ${screen.target.replace("x", " x ")})` : ""}
        </div>
      </PanelSectionRow>
    </PanelSection>
  );
}

export default definePlugin(() => ({
  name: "Crosshair Plugin",
  titleView: <div className={staticClasses.Title}>Crosshair Plugin</div>,
  content: <Content />,
  icon: <FaCrosshairs />,
}));
