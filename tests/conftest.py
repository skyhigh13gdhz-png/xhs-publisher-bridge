import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault('BRIDGE_TOKEN', 'test-secret')
os.environ.setdefault('PUBLIC_BASE_URL', 'https://example.com')
os.environ.setdefault('MYAIBOT_API_KEY', 'test-key')
os.environ.setdefault('FEISHU_APP_ID', 'cli_test')
os.environ.setdefault('FEISHU_APP_SECRET', 'test-secret')
