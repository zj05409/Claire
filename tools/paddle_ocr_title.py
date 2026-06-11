import json
import sys
from pathlib import Path

from PIL import Image
from paddleocr import PaddleOCR


def main():
    source = Path(sys.argv[1])
    crop_path = source.parent / f".{source.stem}-title-crop.jpg"
    try:
        with Image.open(source) as image:
            image.crop((0, 0, image.width, max(1, int(image.height * 0.3)))).convert("RGB").save(crop_path, quality=95)
        ocr = PaddleOCR(
            lang="ch",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,
        )
        results = ocr.predict(str(crop_path))
        candidates = []
        for result in results:
            payload = result.json.get("res", {})
            texts = payload.get("rec_texts", [])
            scores = payload.get("rec_scores", [])
            boxes = payload.get("rec_boxes", [])
            for text, score, box in zip(texts, scores, boxes):
                candidates.append({"text": text, "score": float(score), "box": box})
        print(json.dumps(candidates, ensure_ascii=False))
    finally:
        crop_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
