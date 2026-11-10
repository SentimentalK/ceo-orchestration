#!/usr/bin/env python3
"""Check a Spec file before dispatch. Read-only; exit 1 when something is missing.

Usage: spec_check.py master <spec file>     (roles/conductor.md C3)
       spec_check.py worker <spec file>     (references/spec.md)
"""
import re
import sys
from pathlib import Path

MASTER_SECTIONS = {"规则文件": "规则文件", "启动输入": "启动输入", "范围": "范围", "每波要点": "验收",
                   "上游输入": "上游", "环境说明": "环境", "收尾报告要求": "收尾|报告要求"}
MASTER_CONTRADICTS = {"run-use": "Master 不执行 run-use（master R12.3）",
                      r"check[^\n]*--types": "Master 读 inbox 不带 --types（master R12.2）"}
WORKER_SECTIONS = ["角色", "目标", "步骤", "数据", "约束", "验收", "结束"]


def master(text):
    out = []
    first = next((l for l in text.splitlines() if l.strip()), "")
    path = re.search(r"(/\S*roles/master\.md)", first)
    if not path:
        out.append("第一句没有指向 roles/master.md 的绝对路径")
    elif not Path(path.group(1)).is_file():
        out.append(f"规则文件不存在：{path.group(1)}")
    out += [f"缺段：{name}" for name, pat in MASTER_SECTIONS.items() if not re.search(pat, text)]
    if not re.search("直接实现|设计加派发", text):
        out.append("范围段没有写形态（直接实现 / 设计加派发）")
    out += [why for pat, why in MASTER_CONTRADICTS.items() if re.search(pat, text)]
    return out


def worker(text):
    body = {m.group(1): m.group(2) for m in re.finditer(r"【(.+?)】(.*?)(?=【|\Z)", text, re.S)}
    out = [f"缺段：【{s}】" for s in WORKER_SECTIONS if s not in body]
    if "约束" in body and not re.search(r"可写[：:]\s*\S", body["约束"]):
        out.append("【约束】没有可写白名单")
    if "验收" in body and not re.search(r"`[^`]+`|^\s*\d+\.\s*\S+", body["验收"], re.M):
        out.append("【验收】没有可执行的命令")
    if "目标" in body and not re.search(r"@\s*[0-9a-f]{7,40}", body["目标"]):
        out.append("【目标】没有基线 SHA")
    return out


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("master", "worker"):
        sys.exit(__doc__)
    problems = {"master": master, "worker": worker}[sys.argv[1]](Path(sys.argv[2]).read_text())
    print("\n".join(problems) or "ok")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
