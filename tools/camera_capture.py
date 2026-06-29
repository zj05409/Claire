from datetime import datetime
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_DIR = ROOT / "captured"
SETTINGS_FILE = ROOT / "tools" / "camera-settings.json"


for package_dir in (ROOT / "tools" / "ocr_packages", ROOT / "tools" / "camera_packages"):
    if package_dir.exists():
        sys.path.insert(0, str(package_dir))


def _load_cv2():
    try:
        import cv2
        return cv2
    except Exception as error:
        raise RuntimeError(
            "拍照功能需要先安装摄像头支持。请双击“安装拍照支持.bat”，"
            "安装完成后再重新打开发布工具。"
        ) from error


def _open_camera(cv2, index):
    camera = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not camera.isOpened():
        camera.release()
        camera = cv2.VideoCapture(index)
    if not camera.isOpened():
        camera.release()
        return None
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    return camera


def _read_settings():
    if not SETTINGS_FILE.exists():
        return {}
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_settings(settings):
    SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")


def _camera_order(camera_indexes=None):
    if camera_indexes:
        return list(dict.fromkeys(camera_indexes))

    fallback_indexes = [1, 2, 3, 4, 0]
    settings = _read_settings()
    preferred = settings.get("preferred_index")
    ordered = []
    if isinstance(preferred, int) and preferred in fallback_indexes:
        ordered.append(preferred)

    # Index 0 is often a virtual webcam such as Iriun. Try the likely phone
    # camera indexes first, then fall back to 0 for single-camera computers.
    ordered.extend(fallback_indexes)

    result = []
    for index in ordered:
        if index not in result:
            result.append(index)
    return result


def _save_frame(cv2, frame, output):
    frame = _crop_black_borders(cv2, frame)
    ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ok:
        raise RuntimeError("照片编码失败，请再试一次。")
    output.write_bytes(encoded.tobytes())
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError(f"照片保存失败：{output}")


def _rotate_frame(cv2, frame, degrees):
    degrees = degrees % 360
    if degrees == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    if degrees == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    if degrees == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return frame


def _crop_black_borders(cv2, frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mask = gray > 12
    rows = mask.sum(axis=1)
    cols = mask.sum(axis=0)
    min_row_pixels = max(10, int(frame.shape[1] * 0.08))
    min_col_pixels = max(10, int(frame.shape[0] * 0.08))
    useful_rows = [index for index, count in enumerate(rows) if count >= min_row_pixels]
    useful_cols = [index for index, count in enumerate(cols) if count >= min_col_pixels]
    if not useful_rows or not useful_cols:
        return frame
    x = min(useful_cols)
    y = min(useful_rows)
    width = max(useful_cols) - x + 1
    height = max(useful_rows) - y + 1
    if width < frame.shape[1] * 0.35 or height < frame.shape[0] * 0.35:
        return frame
    pad = 8
    left = max(0, x - pad)
    top = max(0, y - pad)
    right = min(frame.shape[1], x + width + pad)
    bottom = min(frame.shape[0], y + height + pad)
    return frame[top:bottom, left:right]


def capture_photo(prefix, rotate_degrees=0, camera_indexes=None, remember_camera=True, rotate_clockwise=False):
    """Open a small preview window and save one photo from a Windows camera."""
    cv2 = _load_cv2()
    if rotate_clockwise and not rotate_degrees:
        rotate_degrees = 90
    camera_indexes = _camera_order(camera_indexes)
    current_index = 0
    camera = None

    for position, index in enumerate(camera_indexes):
        camera = _open_camera(cv2, index)
        if camera:
            current_index = position
            break

    if not camera:
        raise RuntimeError(
            "没有找到可用摄像头。请先确认安卓手机已经在 Windows 中连接为摄像头，"
            "或者电脑本身有可用摄像头。"
        )

    CAPTURE_DIR.mkdir(exist_ok=True)
    window_name = "Claire Camera"

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                continue

            frame = _rotate_frame(cv2, frame, rotate_degrees)

            preview = frame.copy()
            cv2.putText(
                preview,
                f"Camera {camera_indexes[current_index]}    Rotate {rotate_degrees % 360}    Space/Enter: save    C: switch    Esc: cancel",
                (24, 42),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow(window_name, preview)
            key = cv2.waitKey(30) & 0xFF

            if key in (13, 32):
                output = CAPTURE_DIR / f"{prefix}-{datetime.now():%Y%m%d-%H%M%S}.jpg"
                _save_frame(cv2, frame, output)
                if remember_camera:
                    _write_settings({"preferred_index": camera_indexes[current_index]})
                return output

            if key == 27:
                raise RuntimeError("已取消拍照。")

            if key in (ord("c"), ord("C")):
                camera.release()
                next_camera = None
                for step in range(1, len(camera_indexes) + 1):
                    candidate = (current_index + step) % len(camera_indexes)
                    next_camera = _open_camera(cv2, camera_indexes[candidate])
                    if next_camera:
                        current_index = candidate
                        break
                camera = next_camera
                if not camera:
                    raise RuntimeError("切换摄像头失败，没有找到其他可用摄像头。")
    finally:
        camera.release()
        cv2.destroyAllWindows()
