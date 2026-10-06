"""Photo -> plant name. Uses the free Pl@ntNet API (https://my.plantnet.org).
If PLANTNET_API_KEY is not set, the app falls back to typed plant names."""

import io
import os

import requests
from PIL import Image, ImageOps

PLANTNET_URL = "https://my-api.plantnet.org/v2/identify/all"


def prepare(raw: bytes) -> tuple[bytes, tuple[float, float] | None]:
    """Shrink a big phone photo to a small JPEG and read GPS from EXIF if present."""
    img = Image.open(io.BytesIO(raw))
    gps = _exif_gps(img)
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue(), gps


def _exif_gps(img) -> tuple[float, float] | None:
    try:
        gps = img.getexif().get_ifd(0x8825)
        if not gps:
            return None

        def conv(v):
            d, m, s = [float(x) for x in v]
            return d + m / 60 + s / 3600

        lat, lng = conv(gps[2]), conv(gps[4])
        if gps.get(1) == "S":
            lat = -lat
        if gps.get(3) == "W":
            lng = -lng
        return lat, lng
    except Exception:
        return None


def available() -> bool:
    return bool(os.environ.get("PLANTNET_API_KEY"))


def identify(jpeg: bytes, top: int = 3) -> list[dict]:
    """Returns [{'scientific', 'common', 'score'}, ...] best match first."""
    key = os.environ.get("PLANTNET_API_KEY")
    if not key:
        return []
    r = None
    for organ in ("auto", "leaf"):
        r = requests.post(
            PLANTNET_URL,
            params={"api-key": key},
            files=[("images", ("photo.jpg", jpeg, "image/jpeg"))],
            data={"organs": [organ]},
            timeout=60,
        )
        if r.status_code == 404:  # PlantNet: no species found in this photo
            return []
        if r.status_code == 400 and organ == "auto":
            continue
        break
    r.raise_for_status()
    out = []
    for res in r.json().get("results", [])[:top]:
        sp = res.get("species", {})
        commons = sp.get("commonNames") or []
        out.append(
            {
                "scientific": sp.get("scientificNameWithoutAuthor", "unknown"),
                "common": commons[0] if commons else "",
                "score": float(res.get("score", 0)),
            }
        )
    return out
