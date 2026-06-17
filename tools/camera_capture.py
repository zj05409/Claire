from datetime import datetime
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_DIR = ROOT / "captured"


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


def capture_photo(prefix):
    """Open a small preview window and save one photo from a Windows camera."""
    cv2 = _load_cv2()
    camera_indexes = [0, 1, 2, 3, 4]
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
    window_name = "Claire Camera - Space/Enter save, C switch, Esc cancel"

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                continue

            cv2.putText(
                frame,
                "Space/Enter: save    C: switch camera    Esc: cancel",
                (24, 42),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(30) & 0xFF

            if key in (13, 32):
                output = CAPTURE_DIR / f"{prefix}-{datetime.now():%Y%m%d-%H%M%S}.jpg"
                if not cv2.imwrite(str(output), frame):
                    raise RuntimeError("照片保存失败，请再试一次。")
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
