"""Composite Rachel's real face from a portrait photo onto the kitchen banner figure.

Uses OpenCV Haar cascade for face detection and Poisson seamless cloning for blending.
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "assets/generated/rachelsbakes_banner_kitchen.png"
SOURCE = Path("/Users/carldawson/Desktop/AED7FA48-28EB-4369-9976-403B0DBE2E82_1_105_c.jpeg")
OUT = REPO / "assets/openai-tmp/rachelsbakes_banner_kitchen_face.png"


def detect_face(img_bgr: np.ndarray, cascade_name: str = "haarcascade_frontalface_alt2.xml") -> tuple[int, int, int, int]:
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + cascade_name)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=4, minSize=(80, 80))
    if len(faces) == 0:
        raise SystemExit(f"no face detected with {cascade_name}")
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    return tuple(int(v) for v in faces[0])  # x, y, w, h


def color_match(src: np.ndarray, ref: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Match src color stats to ref within mask region (LAB mean/std transfer)."""
    src_lab = cv2.cvtColor(src, cv2.COLOR_BGR2LAB).astype(np.float32)
    ref_lab = cv2.cvtColor(ref, cv2.COLOR_BGR2LAB).astype(np.float32)
    m = mask > 0
    out = src_lab.copy()
    for c in range(3):
        s = src_lab[..., c][m]
        r = ref_lab[..., c][m]
        if s.size == 0 or r.size == 0:
            continue
        s_mean, s_std = s.mean(), s.std() + 1e-6
        r_mean, r_std = r.mean(), r.std() + 1e-6
        out[..., c] = ((src_lab[..., c] - s_mean) * (r_std / s_std)) + r_mean
    out = np.clip(out, 0, 255).astype(np.uint8)
    return cv2.cvtColor(out, cv2.COLOR_LAB2BGR)


def main() -> None:
    target_bgr = cv2.imread(str(TARGET))
    source_bgr = cv2.imread(str(SOURCE))
    if target_bgr is None or source_bgr is None:
        raise SystemExit("failed to load images")

    # Hardcoded target face bbox (visually identified on 1536x1024 banner).
    # Haar misfires on the banner due to wordmark/cookware artefacts.
    tx, ty, tw, th = detect_face(target_bgr, "haarcascade_frontalface_alt2.xml")
    sx, sy, sw, sh = detect_face(source_bgr)
    print(f"target face: x={tx} y={ty} w={tw} h={th}")
    print(f"source face: x={sx} y={sy} w={sw} h={sh}")

    # Expand source crop to include forehead/chin/cheeks, exclude most hair
    pad_x = int(sw * 0.10)
    pad_y_top = int(sh * 0.15)
    pad_y_bot = int(sh * 0.20)
    s0 = max(0, sx - pad_x)
    s1 = min(source_bgr.shape[1], sx + sw + pad_x)
    r0 = max(0, sy - pad_y_top)
    r1 = min(source_bgr.shape[0], sy + sh + pad_y_bot)
    face_crop = source_bgr[r0:r1, s0:s1].copy()

    # Resize crop to match target face width (slight downscale to keep face inside head)
    scale = (tw * 1.05) / face_crop.shape[1]
    new_w = max(1, int(face_crop.shape[1] * scale))
    new_h = max(1, int(face_crop.shape[0] * scale))
    face_resized = cv2.resize(face_crop, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # Tight T-zone mask: eyes/nose/mouth only — keep original head's hair,
    # jawline, ears and skin tone framing so it doesn't read as "plonked on".
    mask = np.zeros(face_resized.shape[:2], dtype=np.uint8)
    cv2.ellipse(
        mask,
        (new_w // 2, int(new_h * 0.56)),
        (int(new_w * 0.28), int(new_h * 0.34)),
        0, 0, 360, 255, -1,
    )
    mask = cv2.GaussianBlur(mask, (71, 71), 0)
    _, mask_bin = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)

    # Determine target center: align with detected target face center
    tcx = tx + tw // 2
    tcy = ty + int(th * 0.55)  # face oval centered slightly below detected box top

    # Color-match source crop to target face region
    # Take target patch around face for stats reference
    half_w = new_w // 2
    half_h = new_h // 2
    x0 = max(0, tcx - half_w)
    y0 = max(0, tcy - half_h)
    x1 = min(target_bgr.shape[1], x0 + new_w)
    y1 = min(target_bgr.shape[0], y0 + new_h)
    # Adjust if clipped
    new_w_eff = x1 - x0
    new_h_eff = y1 - y0
    face_resized = face_resized[:new_h_eff, :new_w_eff]
    mask_bin = mask_bin[:new_h_eff, :new_w_eff]

    target_patch = target_bgr[y0:y1, x0:x1]
    matched = color_match(face_resized, target_patch, mask_bin)

    # NORMAL_CLONE with a small T-zone mask + targeted skin-tone match.
    # MIXED_CLONE produced color-cast banding near the original eyebrows.
    clone_center = (x0 + new_w_eff // 2, y0 + new_h_eff // 2)
    output = cv2.seamlessClone(matched, target_bgr, mask_bin, clone_center, cv2.NORMAL_CLONE)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT), output)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
