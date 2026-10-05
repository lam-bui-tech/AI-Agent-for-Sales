import base64
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

CONTAINER_NAME = os.getenv("OPENCLAW_CONTAINER", "openclaw-cont")
CONTAINER_QR_PATH = "/tmp/openclaw/openclaw-zalouser-qr-default.png"
ROOT_DIR = Path(__file__).resolve().parent.parent
LOCAL_QR_PATH = ROOT_DIR / "zalo_qr_login.png"
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_QR_PATH = STATIC_DIR / "zalo_qr_login.png"


def run_docker_cmd(cmd_args: list[str], timeout: int = 15) -> tuple[int, str]:
    """Chạy lệnh docker exec và trả về (returncode, output)."""
    full_cmd = ["docker", "exec", CONTAINER_NAME] + cmd_args
    try:
        proc = subprocess.run(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
        return proc.returncode, proc.stdout
    except subprocess.TimeoutExpired:
        return -1, "Command timed out"
    except Exception as e:
        return -1, str(e)


def is_login_in_progress() -> bool:
    """Kiểm tra xem tiến trình login zalouser có đang chạy trong container hay không."""
    code, out = run_docker_cmd(["pgrep", "-f", "channels login --channel zalouser"])
    return code == 0 and bool(out.strip())


def get_qr_image_bytes() -> Optional[bytes]:
    """Đọc dữ liệu nhị phân của ảnh QR nếu có."""
    if LOCAL_QR_PATH.exists():
        try:
            return LOCAL_QR_PATH.read_bytes()
        except Exception:
            pass
    return None


def fetch_qr_from_container() -> bool:
    """Sao chép file QR từ container ra host workspace."""
    try:
        STATIC_DIR.mkdir(parents=True, exist_ok=True)
        # Kiểm tra file trong container
        code, out = run_docker_cmd(["test", "-f", CONTAINER_QR_PATH])
        if code != 0:
            return False

        # docker cp
        cp_cmd = ["docker", "cp", f"{CONTAINER_NAME}:{CONTAINER_QR_PATH}", str(LOCAL_QR_PATH)]
        res = subprocess.run(cp_cmd, capture_output=True, timeout=10)
        if res.returncode == 0 and LOCAL_QR_PATH.exists():
            # Đồng thời sync sang static
            try:
                STATIC_QR_PATH.write_bytes(LOCAL_QR_PATH.read_bytes())
            except Exception:
                pass
            return True
    except Exception as e:
        print(f"Error copying QR from container: {e}")
    return False


def initiate_zalo_login(force: bool = False) -> Dict[str, Any]:
    """
    Bắt đầu quy trình đăng nhập Zalo:
    1. Kiểm tra tiến trình hiện có hoặc khởi tạo tiến trình mới nếu cần/force.
    2. Chờ file QR được sinh trong container.
    3. Tải ảnh QR về workspace máy chủ và trả về thông tin kèm base64.
    """
    already_running = is_login_in_progress()

    if force or not already_running:
        # Dừng tiến trình cũ nếu force
        if already_running:
            run_docker_cmd(["pkill", "-f", "channels login --channel zalouser"])
            time.sleep(1)

        # Xóa QR cũ trong container và trên host
        run_docker_cmd(["rm", "-f", CONTAINER_QR_PATH])
        if LOCAL_QR_PATH.exists():
            try:
                LOCAL_QR_PATH.unlink()
            except Exception:
                pass

        # Bật tiến trình login nền trong container
        start_cmd = [
            "docker", "exec", "-d", CONTAINER_NAME,
            "bash", "-c", "openclaw channels login --channel zalouser > /tmp/openclaw/login.log 2>&1"
        ]
        subprocess.run(start_cmd, capture_output=True)

    # Chờ file QR xuất hiện (tối đa 15 giây)
    qr_ready = False
    for _ in range(30):
        time.sleep(0.5)
        if fetch_qr_from_container():
            qr_ready = True
            break

    if not qr_ready:
        if LOCAL_QR_PATH.exists():
            qr_ready = True

    if not qr_ready:
        return {
            "status": "error",
            "message": "Không thể tạo mã QR đăng nhập Zalo từ OpenClaw. Vui lòng thử lại sau.",
            "login_in_progress": is_login_in_progress()
        }

    img_bytes = LOCAL_QR_PATH.read_bytes()
    b64_str = base64.b64encode(img_bytes).decode("utf-8")

    return {
        "status": "ready_to_scan",
        "message": "Mã đăng nhập Zalo đã sẵn sàng. Vui lòng mở ứng dụng Zalo trên điện thoại, chọn Quét mã QR để đăng nhập.",
        "qr_image_url": "/api/zalo/qr.png",
        "qr_base64": f"data:image/png;base64,{b64_str}",
        "local_file_path": str(LOCAL_QR_PATH),
        "expires_in_seconds": 180,
        "created_at": datetime.now().isoformat()
    }


def get_zalo_status() -> Dict[str, Any]:
    """Kiểm tra trạng thái liên kết Zalo trên OpenClaw."""
    code, out = run_docker_cmd(["openclaw", "channels", "status", "--channel", "zalouser"])
    in_progress = is_login_in_progress()
    
    # Kiểm tra log
    _, log_out = run_docker_cmd(["cat", "/tmp/openclaw/login.log"])

    out_lower = out.lower()
    is_authenticated = "not authenticated" not in out_lower and "not linked" not in out_lower and "linked" in out_lower

    status_str = "connected" if is_authenticated else ("waiting_for_scan" if in_progress else "not_authenticated")

    return {
        "is_authenticated": is_authenticated,
        "status": status_str,
        "login_in_progress": in_progress,
        "qr_available": LOCAL_QR_PATH.exists(),
        "qr_image_url": "/api/zalo/qr.png" if LOCAL_QR_PATH.exists() else None,
        "raw_status": out.strip(),
        "recent_log": log_out.strip() if log_out else None
    }
