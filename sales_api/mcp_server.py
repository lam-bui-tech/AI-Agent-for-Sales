import os
import sys
import json
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional

# Reconfigure stdout/stderr for utf-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure sales_api directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

from catalog import search_products, get_product_details, get_policy_answer, calculate_pricing, compare_packages
from inventory import check_inventory
from leads import create_lead, register_trial
from handoffs import handoff_to_human
from db import init_db

init_db()

TOOLS_DEFINITIONS = [
    {
        "name": "search_products",
        "description": "Tìm kiếm danh sách gói phần mềm quản lý cho thuê trang phục ThueDo.net theo nhu cầu sử dụng, ngân sách và quy mô chi nhánh.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Nhu cầu của shop (ví dụ: 'áo dài 1 chi nhánh', 'studio váy cưới', 'chuỗi đồ biểu diễn')"
                },
                "max_price_vnd": {
                    "type": "integer",
                    "description": "Mức ngân sách tối đa theo tháng bằng VNĐ (ví dụ: 200000, 350000, 500000)"
                },
                "min_branches": {
                    "type": "integer",
                    "description": "Số chi nhánh tối thiểu cần quản lý"
                },
                "limit": {
                    "type": "integer",
                    "description": "Số lượng gói tối đa trả về (mặc định 3)"
                }
            }
        }
    },
    {
        "name": "get_product_details",
        "description": "Tra cứu toàn bộ thông số kỹ thuật chi tiết của một mã SKU cụ thể để giải thích cho khách hoặc so sánh chi tiết.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "Mã SKU của gói phần mềm hoặc thiết bị (ví dụ: 'PKG-STARTER', 'PKG-PRO', 'DEV-PRINTER-QR')"
                }
            },
            "required": ["sku"]
        }
    },
    {
        "name": "check_inventory",
        "description": "BẮT BUỘC GỌI khi khách hỏi thiết bị phần cứng hoặc gói cước còn hàng không, có sẵn không, giao ngay được không. Trả về số lượng khả dụng thời gian thực.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "Mã SKU cần kiểm tra tồn kho (ví dụ: 'DEV-PRINTER-QR', 'DEV-SCANNER-2D', 'PKG-PRO')"
                }
            },
            "required": ["sku"]
        }
    },
    {
        "name": "create_lead",
        "description": "Lưu thông tin khách hàng tiềm năng để nhân viên tư vấn liên hệ. CHỈ GỌI KHI KHÁCH ĐÃ ĐỒNG Ý CHO LƯU SỐ ĐIỆN THOẠI (consent_to_contact=True).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Kênh liên lạc: 'telegram', 'zalo', hoặc 'messenger'"
                },
                "phone": {
                    "type": "string",
                    "description": "Số điện thoại của khách hàng (bắt buộc đúng 10 số)"
                },
                "consent_to_contact": {
                    "type": "boolean",
                    "description": "Xác nhận khách đã đồng ý để nhân viên liên hệ tư vấn"
                },
                "name": {
                    "type": "string",
                    "description": "Tên khách hàng xưng hô"
                },
                "product_skus": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Danh sách các mã SKU khách đang quan tâm"
                },
                "budget_vnd": {
                    "type": "integer",
                    "description": "Ngân sách dự kiến của khách"
                },
                "needs_summary": {
                    "type": "string",
                    "description": "Tóm tắt nhu cầu chính của khách (ví dụ: 'studio váy cưới 2 chi nhánh cần in hợp đồng QR và dùng thử 15 ngày')"
                },
                "preferred_contact_method": {
                    "type": "string",
                    "description": "Kênh liên hệ khách mong muốn: 'Zalo', 'Telegram', hoặc 'Gọi trực tiếp'"
                },
                "status": {
                    "type": "string",
                    "description": "Trạng thái lead: 'new' hoặc 'discount_pending' (chờ duyệt giá deal)"
                }
            },
            "required": ["channel", "phone", "consent_to_contact"]
        }
    },
    {
        "name": "handoff_to_human",
        "description": "Chuyển giao cuộc hội thoại cho nhân viên kinh doanh xử lý khi khách hỏi giảm giá, mua số lượng lớn B2B, xuất hóa đơn VAT đặc biệt, khiếu nại, hoặc khi vượt thẩm quyền.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "conversation_id": {
                    "type": "string",
                    "description": "ID cuộc hội thoại (ví dụ: 'telegram:123456789')"
                },
                "reason": {
                    "type": "string",
                    "description": "Lý do chuyển: 'discount_request', 'bulk_purchase', 'invoice_request', 'complaint', 'product_not_found', 'customer_requests_human', 'agent_low_confidence'"
                },
                "summary": {
                    "type": "string",
                    "description": "Tóm tắt ngắn gọn lý do và bối cảnh chuyển ca để sales nắm được ngay"
                },
                "priority": {
                    "type": "string",
                    "description": "Mức độ ưu tiên: 'low', 'medium', 'high', 'urgent'"
                },
                "suggested_next_action": {
                    "type": "string",
                    "description": "Gợi ý hành động tiếp theo cho sales"
                },
                "preferred_contact_method": {
                    "type": "string",
                    "description": "Kênh liên hệ khách mong muốn: 'Zalo', 'Telegram', hoặc 'Gọi trực tiếp'"
                },
                "status": {
                    "type": "string",
                    "description": "Trạng thái ticket: 'open' hoặc 'discount_pending'"
                }
            },
            "required": ["conversation_id", "reason", "summary"]
        }
    },
    {
        "name": "get_policy_answer",
        "description": "Tra cứu chính sách dịch vụ ThueDo.net: Dùng thử 15 ngày, hóa đơn điện tử, in hợp đồng, hỗ trợ 24/7.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Chủ đề chính sách cần tra cứu: 'dùng thử', 'hóa đơn', 'hợp đồng', 'bảo mật', 'hỗ trợ'"
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "calculate_pricing",
        "description": "Tính toán chi phí gói phần mềm ThueDo.net theo chu kỳ đăng ký: 3 tháng nguyên giá, 6 tháng giảm 5%, 12 tháng giảm 10%.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "Mã SKU của gói phần mềm (PKG-STARTER, PKG-PRO, PKG-PREMIUM)"
                },
                "months": {
                    "type": "integer",
                    "description": "Số tháng đăng ký (ví dụ: 3, 6, 12)"
                }
            },
            "required": ["sku"]
        }
    },
    {
        "name": "compare_packages",
        "description": "So sánh chi tiết tính năng giữa 2 gói phần mềm ThueDo.net (quy mô chi nhánh, hợp đồng QR, hóa đơn điện tử, app mobile) định dạng 2 dòng không dùng bảng kẻ cột.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sku1": {
                    "type": "string",
                    "description": "Mã SKU gói thứ nhất (ví dụ: PKG-STARTER)"
                },
                "sku2": {
                    "type": "string",
                    "description": "Mã SKU gói thứ hai (ví dụ: PKG-PRO)"
                }
            },
            "required": ["sku1", "sku2"]
        }
    },
    {
        "name": "register_trial",
        "description": "Đăng ký kích hoạt chương trình dùng thử miễn phí 15 ngày phần mềm ThueDo.net cho chủ shop thời trang.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "shop_name": {
                    "type": "string",
                    "description": "Tên shop hoặc studio thời trang"
                },
                "fashion_type": {
                    "type": "string",
                    "description": "Mặt hàng kinh doanh (áo dài, váy cưới, đồ biểu diễn, dạ hội)"
                },
                "name": {
                    "type": "string",
                    "description": "Tên chủ shop hoặc người liên hệ"
                },
                "phone": {
                    "type": "string",
                    "description": "Số điện thoại liên hệ hợp lệ"
                },
                "branches_count": {
                    "type": "integer",
                    "description": "Số chi nhánh hiện tại (mặc định: 1)"
                },
                "preferred_contact_method": {
                    "type": "string",
                    "description": "Kênh liên hệ ưu tiên: 'Zalo' hoặc 'Gọi trực tiếp'"
                }
            },
            "required": ["shop_name", "fashion_type", "name", "phone"]
        }
    }
]

import urllib.request
import urllib.error

API_BASE_URLS = [
    os.getenv("SALES_API_URL", "http://sales-api:8088"),
    "http://sales-api:8088",
    "http://127.0.0.1:8088",
    "http://localhost:8088",
    "http://host.docker.internal:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8000"
]

def call_remote_api(endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Cố gắng gọi Sales API đang chạy trên host Windows"""
    for base_url in API_BASE_URLS:
        try:
            url = f"{base_url}/api/tools/{endpoint}"
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8"))
        except Exception:
            continue
    return None

def handle_tool_call(name: str, args: Dict[str, Any]) -> Any:
    # 1. Thử gọi Sales API tập trung qua HTTP
    remote_res = call_remote_api(name, args)
    if remote_res is not None:
        return remote_res

    # 2. Fallback sang logic local nếu service trên host chưa bật
    if name == "search_products":
        return search_products(
            query=args.get("query"),
            max_price_vnd=args.get("max_price_vnd"),
            min_branches=args.get("min_branches"),
            limit=args.get("limit", 3)
        )
    elif name == "get_product_details":
        return get_product_details(sku=args.get("sku", ""))
    elif name == "calculate_pricing":
        return calculate_pricing(sku=args.get("sku", ""), months=args.get("months", 1))
    elif name == "compare_packages":
        return compare_packages(sku1=args.get("sku1", ""), sku2=args.get("sku2", ""))
    elif name == "register_trial":
        return register_trial(
            shop_name=args.get("shop_name", ""),
            fashion_type=args.get("fashion_type", ""),
            name=args.get("name", ""),
            phone=args.get("phone", ""),
            branches_count=args.get("branches_count", 1),
            channel=args.get("channel", "telegram"),
            preferred_contact_method=args.get("preferred_contact_method", "Zalo")
        )
    elif name == "check_inventory":
        return check_inventory(sku=args.get("sku", ""))
    elif name == "create_lead":
        return create_lead(
            channel=args.get("channel", "telegram"),
            phone=args.get("phone", ""),
            consent_to_contact=args.get("consent_to_contact", False),
            name=args.get("name"),
            product_skus=args.get("product_skus"),
            budget_vnd=args.get("budget_vnd"),
            needs_summary=args.get("needs_summary"),
            preferred_contact_method=args.get("preferred_contact_method"),
            status=args.get("status", "new"),
            shop_name=args.get("shop_name"),
            fashion_type=args.get("fashion_type"),
            branches_count=args.get("branches_count", 1)
        )
    elif name == "handoff_to_human":
        return handoff_to_human(
            conversation_id=args.get("conversation_id", "unknown"),
            reason=args.get("reason", "customer_requests_human"),
            summary=args.get("summary", ""),
            priority=args.get("priority", "medium"),
            suggested_next_action=args.get("suggested_next_action"),
            preferred_contact_method=args.get("preferred_contact_method"),
            status=args.get("status", "open")
        )
    elif name == "get_policy_answer":
        return get_policy_answer(topic=args.get("topic", ""))
    else:
        raise ValueError(f"Unknown tool: {name}")

def send_response(response: Dict[str, Any]):
    line = json.dumps(response, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            msg = json.loads(line)
            msg_id = msg.get("id")
            method = msg.get("method")
            params = msg.get("params", {})

            if method == "initialize":
                send_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "thuedo-sales-tools",
                            "version": "2.0.0"
                        }
                    }
                })
            elif method == "notifications/initialized":
                # Không cần phản hồi với notification
                pass
            elif method == "tools/list":
                send_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": TOOLS_DEFINITIONS
                    }
                })
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                try:
                    result = handle_tool_call(tool_name, tool_args)
                    send_response({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                                }
                            ]
                        }
                    })
                except Exception as err:
                    send_response({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "isError": True,
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Error executing tool {tool_name}: {str(err)}"
                                }
                            ]
                        }
                    })
            elif method == "ping":
                send_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {}
                })
            else:
                if msg_id is not None:
                    send_response({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    })
        except Exception as e:
            sys.stderr.write(f"MCP server error: {e}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()
