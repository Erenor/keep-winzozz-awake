import ctypes
import threading
import time
from ctypes import wintypes
from PIL import Image, ImageDraw
import pystray


# =====================================================
#   WINDOWS POWER FLAGS (VLC-style)
# =====================================================

PowerRequestDisplayRequired = 0
PowerRequestSystemRequired = 1
PowerRequestAwayModeRequired = 2
PowerRequestExecutionRequired = 3

POWER_REQUEST_CONTEXT_VERSION = 0
POWER_REQUEST_CONTEXT_SIMPLE_STRING = 1


class POWER_REQUEST_CONTEXT(ctypes.Structure):
    _fields_ = [
        ("Version", wintypes.ULONG),
        ("Flags", wintypes.ULONG),
        ("SimpleString", wintypes.LPWSTR)
    ]


power_handle = None
stay_awake = False
icon = None


# =====================================================
#   FUNCTIONS TO ENABLE / DISABLE FULL PROTECTION
# =====================================================

def enable_full_awake():
    """Enable all Windows power requests (same as VLC)."""
    global power_handle

    if power_handle:
        return  # Already active

    ctx = POWER_REQUEST_CONTEXT()
    ctx.Version = POWER_REQUEST_CONTEXT_VERSION
    ctx.Flags = POWER_REQUEST_CONTEXT_SIMPLE_STRING
    ctx.SimpleString = "StayAwake Full Protection"

    PowerCreateRequest = ctypes.windll.kernel32.PowerCreateRequest
    PowerCreateRequest.restype = wintypes.HANDLE

    power_handle = PowerCreateRequest(ctypes.byref(ctx))

    if not power_handle:
        print("Error: Could not create power request handle.")
        return

    # Apply all relevant power requests
    for req_type in (
        PowerRequestSystemRequired,
        PowerRequestAwayModeRequired,
        PowerRequestExecutionRequired,
        PowerRequestDisplayRequired
    ):
        ctypes.windll.kernel32.PowerSetRequest(power_handle, req_type)

    print("✓ Full Awake Mode ENABLED (Windows will NOT auto-reboot)")


def disable_full_awake():
    """Clear all power requests."""
    global power_handle

    if not power_handle:
        return

    for req_type in (
        PowerRequestSystemRequired,
        PowerRequestAwayModeRequired,
        PowerRequestExecutionRequired,
        PowerRequestDisplayRequired
    ):
        ctypes.windll.kernel32.PowerClearRequest(power_handle, req_type)

    ctypes.windll.kernel32.CloseHandle(power_handle)
    power_handle = None

    print("✗ Full Awake Mode DISABLED")


# =====================================================
#   TRAY ICON / UI
# =====================================================

def create_image():
    """Create the tray icon with a green or gray circle."""
    img = Image.new("RGB", (64, 64), "white")
    draw = ImageDraw.Draw(img)
    draw.ellipse(
        (16, 16, 48, 48),
        fill=(0, 255, 0) if stay_awake else (128, 128, 128)
    )
    return img


def toggle_awake(icon_obj, item):
    """Toggle the awake state and update icon + menu."""
    global stay_awake, icon

    stay_awake = not stay_awake

    if stay_awake:
        enable_full_awake()
    else:
        disable_full_awake()

    # Update icon graphic
    icon.icon = create_image()

    # Rebuild menu with updated text
    icon.menu = pystray.Menu(
        pystray.MenuItem(
            "🟢 Awake Mode ON" if stay_awake else "⚫ Awake Mode OFF",
            toggle_awake
        ),
        pystray.MenuItem("❌ Exit", exit_app)
    )

    # Force redraw on Windows
    icon.visible = True


def exit_app(icon_obj, item):
    """Exit the tray app safely."""
    disable_full_awake()
    icon.stop()


def run_icon():
    global icon

    icon = pystray.Icon(
        "StayAwake",
        create_image(),
        menu=pystray.Menu(
            pystray.MenuItem("⚫ Awake Mode OFF", toggle_awake),
            pystray.MenuItem("❌ Exit", exit_app)
        ),
        title="StayAwake"
    )
    icon.run()


# =====================================================
#   MAIN LOOP
# =====================================================

if __name__ == "__main__":
    threading.Thread(target=run_icon, daemon=True).start()
    print("StayAwake tray app running. Check your system tray!")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        disable_full_awake()
        print("Exiting…")
