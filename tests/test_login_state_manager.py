from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src"

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from spider_vtbasmr.manager.login_state_manager import LoginStateManager


def main() -> None:
    login_state_manager = LoginStateManager()
    login_result = login_state_manager.create_login_state(is_headless=True)
    print(f"Saved login state to: {login_result.state_path}")
    print(f"Final URL: {login_result.final_url}")


if __name__ == "__main__":
    main()
