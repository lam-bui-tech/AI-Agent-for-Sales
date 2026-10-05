import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
INVENTORY_FILE = DATA_DIR / "inventory.json"

def load_inventory() -> Dict[str, Any]:
    if not INVENTORY_FILE.exists():
        return {}
    with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_inventory(data: Dict[str, Any]):
    with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def check_inventory(sku: str) -> Dict[str, Any]:
    """
    Kiểm tra trạng thái tồn kho thời gian thực của sản phẩm.
    """
    clean_sku = sku.strip().upper()
    inventory = load_inventory()
    
    item = inventory.get(clean_sku)
    if not item:
        return {
            "sku": clean_sku,
            "found": False,
            "available": False,
            "quantity": 0,
            "message": f"Sản phẩm mã '{clean_sku}' không tồn tại trong hệ thống kho hoặc đã ngừng kinh doanh."
        }
        
    return {
        "sku": clean_sku,
        "name": item.get("name", ""),
        "found": True,
        "available": item.get("available", False) and item.get("quantity", 0) > 0,
        "quantity": item.get("quantity", 0),
        "warehouse": item.get("warehouse_location", "Kho trung tâm"),
        "warehouse_location": item.get("warehouse_location", "Kho trung tâm"),
        "price_vnd": item.get("price_vnd", 0),
        "updated_at": item.get("updated_at", datetime.now().isoformat()),
        "message": f"Sản phẩm {clean_sku} hiện {'còn ' + str(item.get('quantity')) + ' máy tại ' + item.get('warehouse_location', 'kho') if item.get('quantity', 0) > 0 else 'tạm thời hết hàng'}."
    }

def adjust_inventory(sku: str, quantity: int) -> Dict[str, Any]:
    """
    Điều chỉnh số lượng tồn kho (dùng cho admin/demo kịch bản thay đổi tồn kho).
    """
    clean_sku = sku.strip().upper()
    inventory = load_inventory()
    
    if clean_sku not in inventory:
        return {"success": False, "message": f"SKU {clean_sku} không tồn tại."}
        
    inventory[clean_sku]["quantity"] = max(0, quantity)
    inventory[clean_sku]["available"] = quantity > 0
    inventory[clean_sku]["updated_at"] = datetime.now().isoformat()
    save_inventory(inventory)
    
    return {
        "success": True,
        "sku": clean_sku,
        "quantity": inventory[clean_sku]["quantity"],
        "available": inventory[clean_sku]["available"],
        "updated_at": inventory[clean_sku]["updated_at"]
    }
