from __future__ import annotations

CHANNEL_MODES = ("whatsapp", "web", "both")


def channels_for_mode(mode: str) -> list[str]:
    if mode == "whatsapp":
        return ["whatsapp"]
    if mode == "web":
        return ["web"]
    if mode == "both":
        return ["whatsapp", "web"]
    raise ValueError(f"Unsupported channel mode: {mode}")
