"""
营养信息查询模块。

模型只负责识别食物类别，热量和营养值来自本地 JSON 平均值表。
"""

from __future__ import annotations

import json
from pathlib import Path


DEFAULT_NUTRITION_PATH = Path(__file__).resolve().parent / "food_nutrition.json"
DEFAULT_DISPLAY_NAMES_PATH = Path(__file__).resolve().parent / "food_display_names.json"


def load_nutrition_table(path: Path = DEFAULT_NUTRITION_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"营养信息文件不存在: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_display_names(path: Path = DEFAULT_DISPLAY_NAMES_PATH) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_nutrition(food_name: str, path: Path = DEFAULT_NUTRITION_PATH) -> dict:
    table = load_nutrition_table(path)
    if food_name not in table:
        raise KeyError(f"未找到 {food_name} 的营养信息。")
    return table[food_name]


def build_suggestion(nutrition: dict) -> str:
    """根据营养数值生成兜底建议。JSON 中已有 suggestion 时优先使用。"""
    if nutrition.get("suggestion"):
        return nutrition["suggestion"]

    calories = float(nutrition.get("calories", 0))
    protein = float(nutrition.get("protein", 0))
    fat = float(nutrition.get("fat", 0))
    carbohydrate = float(nutrition.get("carbohydrate", 0))

    if calories >= 280 or fat >= 15:
        return "热量或脂肪偏高，建议控制摄入量并搭配蔬菜。"
    if protein >= 18:
        return "蛋白质含量较高，适合运动后补充，但仍需注意均衡搭配。"
    if carbohydrate >= 30:
        return "碳水含量较高，适合作为主食，建议搭配蛋白质和蔬菜。"
    return "营养相对均衡，可以作为正常一餐的一部分。"


def get_nutrition_result(food_name: str) -> dict:
    nutrition = get_nutrition(food_name)
    display_names = load_display_names()
    return {
        "display_name": nutrition.get("display_name") or display_names.get(food_name, food_name),
        "category": nutrition.get("category", "未分类"),
        "calories": nutrition.get("calories"),
        "protein": nutrition.get("protein"),
        "fat": nutrition.get("fat"),
        "carbohydrate": nutrition.get("carbohydrate"),
        "unit": nutrition.get("unit", "每100克估算值"),
        "suggestion": build_suggestion(nutrition),
    }
