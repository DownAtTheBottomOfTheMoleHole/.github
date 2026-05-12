"""Shrink Rachel to 5'3" proportions and recomposite without smearing the
rest of the kitchen. Strategy: only touch pixels in the area "exposed" by
shrinking (old silhouette minus new figure); everything else stays pristine.
"""
from pathlib import Path
import cv2
import numpy as np
import mediapipe as mp

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "assets/openai-tmp/rachelsbakes_banner_kitchen_inswapper.png"
OUT = REPO / "assets/openai-tmp/rachelsbakes_banner_kitchen_shorter.png"

SCALE = 0.82  # 5'3" / ~6'4"


def segment(img: np.ndarray) -> np.ndarray:
    seg = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
    res = seg.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    raw = (res.segmentation_mask * 255).astype(np.uint8)
    _, m = cv2.threshold(raw, 90, 255, cv2.THRESH_BINARY)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN,
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE,
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:
        biggest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        m = np.where(lab == biggest, 255, 0).astype(np.uint8)
    return m


def main() -> None:
    img = cv2.imread(str(SRC))
    if img is None:
        raise SystemExit(f"cannot read {SRC}")
    h, w = img.shape[:2]

    old_mask = segment(img)
    ys, xs = np.where(old_mask > 0)
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    print(f"old bbox: x={x0}-{x1}, y={y0}-{y1}")

    new_w = max(1, int(round((x1 - x0 + 1) * SCALE)))
    new_h = max(1, int(round((y1 - y0 + 1) * SCALE)))
    crop_img = img[y0:y1 + 1, x0:x1 + 1]
    crop_mask = old_mask[y0:y1 + 1, x0:x1 + 1]
    small_img = cv2.resize(crop_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    small_mask = cv2.resize(crop_mask, (new_w, new_h), interpolation=cv2.INTER_AREA)
    _, small_mask = cv2.threshold(small_mask, 128, 255, cv2.THRESH_BINARY)

    cx = (x0 + x1) // 2
    paste_x = cx - new_w // 2
    paste_y = y1 - new_h + 1

    new_mask = np.zeros_like(old_mask)
    new_fig = np.zeros_like(img)
    px0, py0 = max(0, paste_x), max(0, paste_y)
    px1, py1 = min(w, paste_x + new_w), min(h, paste_y + new_h)
    sx0, sy0 = px0 - paste_x, py0 - paste_y
    sx1, sy1 = sx0 + (px1 - px0), sy0 + (py1 - py0)
    new_mask[py0:py1, px0:px1] = small_mask[sy0:sy1, sx0:sx1]
    new_fig[py0:py1, px0:px1] = small_img[sy0:sy1, sx0:sx1]

    # Pixels that were Rachel before but not after — these are the only
    # background pixels that need any repair.
    expose = cv2.subtract(old_mask, new_mask)
    expose_dil = cv2.dilate(expose, np.ones((25, 25), np.uint8), iterations=5)
    expose_dil = cv2.subtract(expose_dil, new_mask)

    # Telea inpaint with a large radius gives smooth fills on the kitchen
    # walls/cabinets surrounding Rachel, without the patch-replication
    # artifacts that shiftMap produced near the fridge.
    bg = cv2.inpaint(img, expose_dil, 25, cv2.INPAINT_TELEA)

    out = img.copy()
    ea = cv2.GaussianBlur(expose_dil, (15, 15), 0).astype(np.float32) / 255.0
    ea3 = np.dstack([ea] * 3)
    out = (bg.astype(np.float32) * ea3
           + out.astype(np.float32) * (1 - ea3)).astype(np.uint8)

    fa = cv2.GaussianBlur(new_mask, (5, 5), 0).astype(np.float32) / 255.0
    fa3 = np.dstack([fa] * 3)
    out = (new_fig.astype(np.float32) * fa3
           + out.astype(np.float32) * (1 - fa3)).astype(np.uint8)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT), out)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
