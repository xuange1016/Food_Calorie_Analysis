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


def build_food_intro(nutrition: dict) -> str:
    """Generate a short local introduction from the nutrition table."""
    name = nutrition.get("display_name", "该食物")
    category = nutrition.get("category", "未分类")
    calories = nutrition.get("calories")
    protein = nutrition.get("protein")
    fat = nutrition.get("fat")
    carbohydrate = nutrition.get("carbohydrate")

    macro_notes = []
    if protein is not None and float(protein) >= 18:
        macro_notes.append("蛋白质占比较高")
    if fat is not None and float(fat) >= 15:
        macro_notes.append("脂肪含量偏高")
    if carbohydrate is not None and float(carbohydrate) >= 30:
        macro_notes.append("碳水含量较高")
    if calories is not None and float(calories) >= 280:
        macro_notes.append("单位热量较高")

    feature_text = "，".join(macro_notes) if macro_notes else "营养分布相对温和"
    return (
        f"{name}属于{category}类食物。按本项目营养表估算，每100克约含 {calories} kcal 热量、"
        f"{protein} g 蛋白质、{fat} g 脂肪和 {carbohydrate} g 碳水，整体特点是{feature_text}。"
        "实际摄入还会受到份量、烹饪方式、酱料和配菜影响，建议结合个人目标判断是否适合当前这一餐。"
    )


def build_calorie_analysis(nutrition: dict) -> str:
    calories = float(nutrition.get("calories", 0))
    protein = float(nutrition.get("protein", 0))
    fat = float(nutrition.get("fat", 0))
    carbohydrate = float(nutrition.get("carbohydrate", 0))

    if calories >= 300:
        energy_level = "热量密度较高"
    elif calories >= 180:
        energy_level = "热量密度中等"
    else:
        energy_level = "热量密度较低"

    protein_ratio = protein * 4 / calories if calories else 0
    fat_ratio = fat * 9 / calories if calories else 0
    carb_ratio = carbohydrate * 4 / calories if calories else 0

    return (
        f"该食物每100克约 {calories:g} kcal，属于{energy_level}。按三大营养素粗略折算，"
        f"蛋白质供能约占 {protein_ratio * 100:.0f}%，脂肪约占 {fat_ratio * 100:.0f}%，"
        f"碳水约占 {carb_ratio * 100:.0f}%。如果目标是减脂，重点关注份量和额外油脂；"
        "如果目标是增肌，可以结合全天蛋白质目标和训练前后进餐时机来安排。"
    )


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
        "food_intro": nutrition.get("food_intro") or build_food_intro(nutrition),
        "calorie_analysis": nutrition.get("calorie_analysis") or build_calorie_analysis(nutrition),
    }
