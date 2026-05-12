"""Face swap using insightface inswapper_128 model."""
from pathlib import Path
import cv2
import insightface
from insightface.app import FaceAnalysis

REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "assets/openai-tmp/edited_1778281685544_1.png"  # pristine
SOURCE = Path("/Users/carldawson/Desktop/AED7FA48-28EB-4369-9976-403B0DBE2E82_1_105_c.jpeg")
OUT = REPO / "assets/openai-tmp/rachelsbakes_banner_kitchen_inswapper.png"
MODEL_PATH = Path.home() / ".insightface/models/inswapper_128.onnx"


def main() -> None:
    app = FaceAnalysis(name="buffalo_l",
                       allowed_modules=["detection", "landmark_2d_106", "recognition"])
    app.prepare(ctx_id=-1, det_size=(640, 640))

    swapper = insightface.model_zoo.get_model(str(MODEL_PATH), download=False)

    target_bgr = cv2.imread(str(TARGET))
    source_bgr = cv2.imread(str(SOURCE))
    if target_bgr is None or source_bgr is None:
        raise SystemExit("could not read inputs")

    t_faces = app.get(target_bgr)
    s_faces = app.get(source_bgr)
    if not t_faces or not s_faces:
        raise SystemExit(f"no face detected (target={len(t_faces)}, source={len(s_faces)})")

    t_face = max(t_faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
    s_face = max(s_faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
    print("target bbox:", t_face.bbox.astype(int).tolist())
    print("source bbox:", s_face.bbox.astype(int).tolist())

    out = swapper.get(target_bgr, t_face, s_face, paste_back=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT), out)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
