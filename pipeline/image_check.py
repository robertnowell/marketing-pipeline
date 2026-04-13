"""Image validation — catch broken screenshots before posting.

Programmatic checks that run without an API key:
- Image downloads successfully (not 404, not 0 bytes)
- Valid image format (PNG/JPEG, not an HTML error page)
- Reasonable dimensions (not tiny placeholder, not absurdly large)
- Minimum file size (broken renders tend to be very small)
- Aspect ratio sanity (email screenshots should be taller than wide)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx


@dataclass
class ImageCheckResult:
    passed: bool
    width: int = 0
    height: int = 0
    file_size: int = 0
    format: str = ""
    issues: list[str] = field(default_factory=list)


# Minimum thresholds for email design screenshots
MIN_WIDTH = 300
MIN_HEIGHT = 400
MIN_FILE_SIZE = 10_000  # 10 KB — broken renders are usually tiny
MAX_ASPECT_RATIO = 1.5  # width/height — emails are taller than wide
MIN_ASPECT_RATIO = 0.2  # don't accept absurdly thin strips


def check_image(url: str) -> ImageCheckResult:
    """Download an image and validate it's usable for posting."""
    issues: list[str] = []

    # 1. Download
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        return ImageCheckResult(passed=False, issues=[f"Download failed: {e}"])

    data = resp.content
    file_size = len(data)

    # 2. Check it's actually image data, not an HTML error page
    content_type = resp.headers.get("content-type", "")
    if "text/html" in content_type:
        return ImageCheckResult(
            passed=False, file_size=file_size,
            issues=["Response is HTML, not an image (likely an error page)"],
        )

    # 3. File size check
    if file_size < MIN_FILE_SIZE:
        issues.append(f"File too small ({file_size} bytes) — likely broken or placeholder")

    # 4. Try to read image dimensions
    width, height, fmt = _get_image_info(data)

    if width == 0 or height == 0:
        issues.append("Could not read image dimensions — may not be a valid image file")
        return ImageCheckResult(
            passed=False, file_size=file_size, format=fmt, issues=issues,
        )

    # 5. Dimension checks
    if width < MIN_WIDTH:
        issues.append(f"Width {width}px below minimum {MIN_WIDTH}px")
    if height < MIN_HEIGHT:
        issues.append(f"Height {height}px below minimum {MIN_HEIGHT}px")

    # 6. Aspect ratio (email screenshots are tall)
    if height > 0:
        ratio = width / height
        if ratio > MAX_ASPECT_RATIO:
            issues.append(f"Too wide (aspect {ratio:.1f}) — email screenshots should be taller than wide")
        if ratio < MIN_ASPECT_RATIO:
            issues.append(f"Too narrow (aspect {ratio:.1f}) — may be a cropped strip")

    return ImageCheckResult(
        passed=len(issues) == 0,
        width=width,
        height=height,
        file_size=file_size,
        format=fmt,
        issues=issues,
    )


def check_image_visual(url: str, api_key: str | None = None) -> ImageCheckResult:
    """Run programmatic checks + AI vision check on an image.

    If api_key is provided, sends the image to Claude vision to check for
    rendering issues (missing hero images, blank sections, broken layouts).
    Without api_key, falls back to programmatic checks only.
    """
    result = check_image(url)
    if not result.passed:
        return result

    if not api_key:
        return result

    import base64

    import anthropic

    try:
        img_resp = httpx.get(url, timeout=15, follow_redirects=True)
        img_data = img_resp.content
        content_type = img_resp.headers.get("content-type", "image/png").split(";")[0].strip()
        if content_type not in ("image/png", "image/jpeg", "image/gif", "image/webp"):
            content_type = "image/png"

        b64 = base64.b64encode(img_data).decode()

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": content_type, "data": b64},
                    },
                    {
                        "type": "text",
                        "text": (
                            "Is this email design screenshot fully rendered? "
                            "Check for: missing or blank hero images at the top, "
                            "unrendered sections, broken layouts, grey/white placeholder "
                            "areas where content should be, cut-off content. "
                            "Reply exactly: PASS or FAIL followed by a one-line reason."
                        ),
                    },
                ],
            }],
        )

        verdict = response.content[0].text.strip()
        if verdict.upper().startswith("FAIL"):
            result.passed = False
            result.issues.append(f"Visual check: {verdict}")

    except Exception as e:
        result.issues.append(f"Visual check error (non-blocking): {e}")

    return result


def _get_image_info(data: bytes) -> tuple[int, int, str]:
    """Extract width, height, and format from image bytes without PIL."""
    # PNG: 8-byte signature, then IHDR chunk with width (4 bytes) and height (4 bytes)
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        if len(data) >= 24:
            width = int.from_bytes(data[16:20], "big")
            height = int.from_bytes(data[20:24], "big")
            return width, height, "png"

    # JPEG: look for SOF0/SOF2 markers
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC2):  # SOF0 or SOF2
                height = int.from_bytes(data[i + 5 : i + 7], "big")
                width = int.from_bytes(data[i + 7 : i + 9], "big")
                return width, height, "jpeg"
            # Skip to next marker
            length = int.from_bytes(data[i + 2 : i + 4], "big")
            i += 2 + length

    # WebP: RIFF header
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        if data[12:16] == b"VP8 " and len(data) >= 30:
            width = int.from_bytes(data[26:28], "little") & 0x3FFF
            height = int.from_bytes(data[28:30], "little") & 0x3FFF
            return width, height, "webp"

    return 0, 0, "unknown"
