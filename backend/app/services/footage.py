"""素材管理业务规则：状态流转、字段校验与筛选口径都收在这里。

列表、归档动作、导出三条路径共用下方这一份规则常量；
新增素材类型或调整状态时只改这里，接口与页面会跟着对齐。
"""
from __future__ import annotations

from typing import Any

from app.store import store

MODULE = "footage"
LABEL = "素材管理"
ENTITY = "拍摄素材"
KEYWORD_FIELD = "素材编号"
LIST_FIELDS = ["素材编号", "素材类型", "拍摄日期", "文件大小", "存储介质", "转码格式", "备份位置", "素材状态"]
REQUIRED_FIELDS = ["素材编号", "素材类型", "拍摄日期"]
STATUS_ORDER = ["待转码", "转码中", "已归档", "已丢失"]
ACTION_RULES = {"提交转码": "转码中", "确认归档": "已归档", "登记丢失": "已丢失"}
NEGATIVE_ACTIONS: list[str] = []
EXPORT_LIMIT = 10000


class FootageService:
    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = store.rows(MODULE)
        if keyword:
            rows = [row for row in rows if keyword in str(row.get(KEYWORD_FIELD, ""))]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        total = len(rows)
        start = max(page - 1, 0) * size
        return rows[start:start + size], total

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        return store.find(MODULE, entry_id)

    def create_entry(self, values: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
        missing = [field for field in REQUIRED_FIELDS if not str(values.get(field) or "").strip()]
        if missing:
            return None, missing
        rows = store.rows(MODULE)
        entry = {"id": max((int(row.get("id", 0)) for row in rows), default=0) + 1}
        entry.update({field: values.get(field) for field in REQUIRED_FIELDS})
        entry["status"] = STATUS_ORDER[0]
        entry["pending"] = True
        entry["abnormal"] = False
        rows.append(entry)
        return entry, []

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"{ENTITY} {entry_id} 不存在或已归档"
        if action not in ACTION_RULES:
            return None, f"动作「{action}」不属于{LABEL}可执行范围"
        target = ACTION_RULES[action]
        if target not in STATUS_ORDER:
            return None, f"目标状态「{target}」不在允许的状态序列里"
        entry["status"] = target
        entry["pending"] = target != STATUS_ORDER[-1]
        entry["abnormal"] = action in NEGATIVE_ACTIONS
        return entry, f"{ENTITY}已{action}"

    def export_entries(self) -> dict[str, Any]:
        """导出清单：与列表走同一套筛选口径，只是取全量，返回结构保持不变。"""
        items, total = self.list_entries(page=1, size=EXPORT_LIMIT)
        return {"module": MODULE, "total": total, "items": items}

    def describe_rules(self) -> dict[str, Any]:
        """把这份规则原样暴露给页面，保证页面状态与归档结果来自同一处。"""
        return {
            "module": MODULE,
            "label": LABEL,
            "entity": ENTITY,
            "columns": LIST_FIELDS,
            "requiredFields": REQUIRED_FIELDS,
            "statuses": STATUS_ORDER,
            "actions": list(ACTION_RULES),
        }
