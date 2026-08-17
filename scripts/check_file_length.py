"""文件长度门禁：Python 源文件不超过 500 行（前端 max-lines / Java FileLength 由各自工具管）。"""

import sys
from pathlib import Path

MAX_LINES = 500
SCAN_DIRS = ["agent", "backend", "tests", "scripts"]

# 存量基线，只减不增
BASELINE = {
    "agent/evals/seed/parse_ledger.py",
    "tests/automation.py",
}


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    violations = []
    for d in SCAN_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for py in sorted(base.rglob("*.py")):
            if ".venv" in py.parts:
                continue
            rel = py.relative_to(root).as_posix()
            lines = len(py.read_text(encoding="utf-8").splitlines())
            if lines > MAX_LINES and rel not in BASELINE:
                violations.append(f"{rel}: {lines} 行（上限 {MAX_LINES}）")
    if violations:
        print("文件长度超限：")
        for v in violations:
            print(f"  {v}")
        return 1
    print(f"文件长度检查通过（上限 {MAX_LINES} 行）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
