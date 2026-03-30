import json
import os
import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Group
from django.utils import timezone


VIEWER_GROUP = "viewer"
EDITOR_GROUP = "editor"


def ensure_role_groups() -> None:
    for group_name in (VIEWER_GROUP, EDITOR_GROUP):
        Group.objects.get_or_create(name=group_name)


def user_is_editor(user) -> bool:
    return user.is_authenticated and (
        user.is_superuser or user.is_staff or user.groups.filter(name=EDITOR_GROUP).exists()
    )


def user_is_admin(user) -> bool:
    return user.is_authenticated and user.is_superuser


def user_role_label(user) -> str:
    if not user.is_authenticated:
        return "guest"
    if user.is_superuser:
        return "admin"
    if user.groups.filter(name=EDITOR_GROUP).exists():
        return "editor"
    return "viewer"


def assign_user_role(user, role: str) -> None:
    ensure_role_groups()
    viewer_group = Group.objects.get(name=VIEWER_GROUP)
    editor_group = Group.objects.get(name=EDITOR_GROUP)
    user.groups.remove(viewer_group, editor_group)

    if role == "admin":
        user.is_staff = True
        user.is_superuser = True
    elif role == "editor":
        user.groups.add(editor_group)
        user.is_staff = True
        user.is_superuser = False
    else:
        user.groups.add(viewer_group)
        user.is_staff = False
        user.is_superuser = False
    user.save(update_fields=["is_staff", "is_superuser"])


def infer_model_name(name: str, file_name: str) -> str:
    source = f"{name} {file_name}".lower()
    patterns = [
        ("Artificial Neural Network", r"\bann\b|\bmlp\b|neural"),
        ("Random Forest", r"\brf\b|random forest"),
        ("XGBoost", r"\bxgb\b|xgboost"),
        ("LightGBM", r"\blgbm\b|lightgbm"),
        ("CatBoost", r"\bcat\b|catboost"),
        ("Support Vector Machine", r"\bsvm\b"),
        ("Logistic Regression", r"logistic"),
        ("K-Nearest Neighbors", r"\bknn\b"),
        ("Decision Tree", r"decision tree|\bdt\b"),
        ("Naive Bayes", r"naive bayes|\bnb\b"),
        ("AdaBoost", r"adaboost|\bada\b"),
    ]
    for label, pattern in patterns:
        if re.search(pattern, source):
            return label
    return "Tidak diketahui"


def audit_log_path() -> str:
    return os.path.join(settings.MEDIA_ROOT, "audit", "raster_history.jsonl")


def append_audit_log(entry: dict) -> None:
    path = audit_log_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        **entry,
        "timestamp": timezone.now().isoformat(),
    }
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=True) + "\n")


def read_audit_logs(limit: int | None = None) -> list[dict]:
    path = audit_log_path()
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    rows.reverse()
    return rows[:limit] if limit is not None else rows


def get_next_raster_version(name: str, existing_names: list[str]) -> int:
    return 1 + sum(1 for item in existing_names if item == name)


def summarize_raster_audit(rasters) -> dict[int, dict]:
    logs = read_audit_logs()
    summary: dict[int, dict] = {}
    raster_ids = {r.id for r in rasters}
    for log in logs:
        raster_id = log.get("raster_id")
        if raster_id not in raster_ids or raster_id in summary:
            continue
        summary[raster_id] = {
            "action": log.get("action"),
            "user": log.get("user"),
            "version": log.get("version"),
            "timestamp": log.get("timestamp"),
            "previous_versions": log.get("previous_versions", []),
        }
    return summary


def file_stem(file_name: str) -> str:
    return Path(file_name).stem
