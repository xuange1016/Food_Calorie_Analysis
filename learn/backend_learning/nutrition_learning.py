"""
学习版：营养信息查询模块。

这个文件对应正式项目中的：
    backend/nutrition.py

它的作用：
1. 读取 food_nutrition.json 营养表；
2. 根据模型预测出的 food_name 查询营养信息；
3. 返回前端需要展示的热量、蛋白质、脂肪、碳水和建议。

重要理解：
模型只负责“识别类别”，例如 pizza。
热量、蛋白质这些营养值不是模型算出来的，而是根据 pizza 这个类别从 JSON 表里查出来的。
"""

from __future__ import annotations

import json
from pathlib import Path


# Path(__file__) 表示当前这个 Python 文件。
# resolve() 会得到绝对路径。
# parent 表示上一级目录。
# 这里在学习版中仍然指向正式项目的营养表，方便你对照真实数据。
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NUTRITION_PATH = PROJECT_ROOT / "backend" / "food_nutrition.json"


def load_nutrition_table(path: Path = DEFAULT_NUTRITION_PATH) -> dict:
    """读取营养信息 JSON 文件。

    返回值是一个字典，例如：
        {
            "pizza": {
                "display_name": "披萨",
                "calories": 266,
                ...
            }
        }
    """
    if not path.exists():
        raise FileNotFoundError(f"营养信息文件不存在: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_nutrition(food_name: str, path: Path = DEFAULT_NUTRITION_PATH) -> dict:
    """根据食物英文类别名查询营养信息。

    参数：
        food_name: 模型预测出来的类别名，例如 "pizza"。

    如果 JSON 表里没有这个类别，就抛出 KeyError。
    后端接口会捕获这个错误，并返回友好提示。
    """
    table = load_nutrition_table(path)

    if food_name not in table:
        raise KeyError(f"未找到 {food_name} 的营养信息。")

    return table[food_name]


def build_suggestion(nutrition: dict) -> str:
    """生成饮食建议。

    当前项目大多数建议已经直接写在 JSON 里。
    如果 JSON 中没有 suggestion 字段，就根据营养数值做一个简单规则判断。
    """
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
    """返回前端最终需要的数据结构。

    这个函数是后端 app.py 最常调用的入口。
    它把原始 JSON 中的数据整理成统一格式。
    """
    nutrition = get_nutrition(food_name)

    return {
        "display_name": nutrition.get("display_name", food_name),
        "calories": nutrition.get("calories"),
        "protein": nutrition.get("protein"),
        "fat": nutrition.get("fat"),
        "carbohydrate": nutrition.get("carbohydrate"),
        "unit": nutrition.get("unit", "每100克估算值"),
        "suggestion": build_suggestion(nutrition),
    }
