import sys
from pathlib import Path

# Add project root and sales_api to sys.path for pytest
ROOT_DIR = Path(__file__).parent
SALES_API_DIR = ROOT_DIR / "sales_api"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SALES_API_DIR) not in sys.path:
    sys.path.insert(0, str(SALES_API_DIR))
