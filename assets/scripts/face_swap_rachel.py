"""Landmark-based face swap (Rachel -> kitchen banner figure).

Uses insightface 'buffalo_l' for detection + 5-point keypoints, similarity-warps
Rachel's face onto the target face, builds a convex-hull mask from the target's
landmarks (so the swap follows the target head shape), color-matches in LAB,
then seamlessClones (NORMAL) for an invisible seam.
"""
from pathlib import Path
import sys
import cv2
import numpy as np
from insightface.app import FaceAnalysis

REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "assets/generated/rachelsbakes_banner_kitchen.png"
SOURCE = Path("/Users/carldawson/Desktop/AED7FA48-28EB-4369-9976-403B0DBE2E82_1_105_c.jpeg")
OUT = REPO / "assets/openai-tmp/rachelsbakes_banner_kitchen_face.png"


def color_match(src, ref, mask):
    src_lab = cv2.cvtColor(src, cv2.COLOR_BGR2LAB).astype(np.float32)
    ref_lab = cv2.cvtColor(ref, cv2.COLOR_BGR2LAB).astype(np.float32)
    m = mask > 0
    if m.sum() < 50:
        return src
    out = src_lab.copy()
    for c in range(3):
        s = src_lab[..., c][m]
        r = ref_lab[..., c][m]
        s_mu, s_sd = s.mean(), s.std() + 1e-6
        r_mu, r_sd = r.mean(), r.std() + 1e-6
        out[..., c] = (src_lab[..., c] - s_mu) * (r_sd / s_sd) + r_mu
    out = np.clip(out, 0, 255).astype(np.uint8)
    return cv2.cvtColor(out, cv2.COLOR_LAB2BGR)


def main():
    app = FaceAnalysis(name="buffalo_l", allowed_modules=["detection", "landmark_2d_106"])
    app.prepare(ctx_id=-1, det_size=(640, 640))

    target_bgr = cv2.imread(str(TARGET))
    source_bgr = cv2.imread(str(SOURCE))
    if target_bgr is None or source_bgr is None:
        sys.exit("could not read images")

    t_faces = app.get(target_bgr)
    s_faces = app.get(source_bgr)
    if not t_faces or not s_faces:
        sys.exit(f"face not found (target={len(t_faces)}, source={len(s_faces)})")

    # pick largest face on each
    t_face = max(t_faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    s_face = max(s_faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    print("target bbox:", t_face.bbox.astype(int).tolist(), "kps:", t_face.kps.shape)
    print("source bbox:", s_face.bbox.astype(int).tolist(), "kps:", s_face.kps.shape)

    # Pre-downscale source to roughly target face size to avoid 5x downsample in warp
    s_w = s_face.bbox[2] - s_face.bbox[0]
    t_w = t_face.bbox[2] - t_face.bbox[0]
    pre_scale = (t_w * 2.0) / s_w  # keep ~2x headroom for warp resampling
    if pre_scale < 1.0:
        new_size = (int(source_bgr.shape[1] * pre_scale), int(source_bgr.shape[0] * pre_scale))
        source_small = cv2.resize(source_bgr, new_size, interpolation=cv2.INTER_AREA)
        s_kps_small = s_face.kps.astype(np.float32) * pre_scale
    else:
        source_small = source_bgr
        s_kps_small = s_face.kps.astype(np.float32)

    # Similarity transform (rotation+scale+translation) from source 5-pt -> target 5-pt
    M, _ = cv2.estimateAffinePartial2D(s_kps_small,
                                       t_face.kps.astype(np.float32),
                                       method=cv2.LMEDS)
    h, w = target_bgr.shape[:2]
    warped_src = cv2.warpAffine(source_small, M, (w, h), flags=cv2.INTER_AREA,
                                borderMode=cv2.BORDER_REFLECT_101)

    # Build mask from TARGET face landmarks (so result follows target head shape)
    if hasattr(t_face, "landmark_2d_106") and t_face.landmark_2d_106 is not None:
        pts = t_face.landmark_2d_106.astype(np.int32)
    else:
        # fallback: ellipse around bbox
        x1, y1, x2, y2 = t_face.bbox.astype(int)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        pts = cv2.ellipse2Poly((cx, cy), ((x2 - x1) // 2, (y2 - y1) // 2 + 10), 0, 0, 360, 5)

    hull = cv2.convexHull(pts)
    mask = np.zeros((h, w), np.uint8)
    cv2.fillConvexPoly(mask, hull, 255)

    # Shrink mask slightly inward, then heavy feather → soft edge for seam
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask = cv2.erode(mask, kernel, iterations=1)
    mask_blur = cv2.GaussianBlur(mask, (51, 51), 0)
    mask_bin = (mask_blur > 8).astype(np.uint8) * 255

    # Color-match warped source to target inside the mask
    warped_matched = color_match(warped_src, target_bgr, mask_bin)

    # Center for seamlessClone = centroid of mask
    ys, xs = np.where(mask_bin > 0)
    if len(xs) == 0:
        sys.exit("empty mask")
    cx, cy = int(xs.mean()), int(ys.mean())

    output = cv2.seamlessClone(warped_matched, target_bgr, mask_bin, (cx, cy),
                               cv2.NORMAL_CLONE)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT), output)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
