"""
Generate Food-101 display-name and nutrition configuration files.
"""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLASSES_PATH = PROJECT_ROOT / "data" / "food-101" / "meta" / "classes.txt"
DISPLAY_NAMES_PATH = PROJECT_ROOT / "backend" / "food_display_names.json"
NUTRITION_PATH = PROJECT_ROOT / "backend" / "food_nutrition.json"


DISPLAY_NAMES = {
    "apple_pie": "苹果派",
    "baby_back_ribs": "猪肋排",
    "baklava": "巴克拉瓦酥饼",
    "beef_carpaccio": "生牛肉片",
    "beef_tartare": "鞑靼牛肉",
    "beet_salad": "甜菜沙拉",
    "beignets": "贝涅甜甜圈",
    "bibimbap": "韩式拌饭",
    "bread_pudding": "面包布丁",
    "breakfast_burrito": "早餐卷饼",
    "bruschetta": "意式烤面包",
    "caesar_salad": "凯撒沙拉",
    "cannoli": "奶油甜馅煎饼卷",
    "caprese_salad": "卡布里沙拉",
    "carrot_cake": "胡萝卜蛋糕",
    "ceviche": "酸橘汁腌鱼",
    "cheesecake": "芝士蛋糕",
    "cheese_plate": "奶酪拼盘",
    "chicken_curry": "咖喱鸡",
    "chicken_quesadilla": "鸡肉奶酪饼",
    "chicken_wings": "鸡翅",
    "chocolate_cake": "巧克力蛋糕",
    "chocolate_mousse": "巧克力慕斯",
    "churros": "西班牙油条",
    "clam_chowder": "蛤蜊浓汤",
    "club_sandwich": "总汇三明治",
    "crab_cakes": "蟹肉饼",
    "creme_brulee": "焦糖布丁",
    "croque_madame": "法式火腿芝士三明治",
    "cup_cakes": "纸杯蛋糕",
    "deviled_eggs": "魔鬼蛋",
    "donuts": "甜甜圈",
    "dumplings": "饺子",
    "edamame": "毛豆",
    "eggs_benedict": "班尼迪克蛋",
    "escargots": "法式焗蜗牛",
    "falafel": "炸鹰嘴豆丸",
    "filet_mignon": "菲力牛排",
    "fish_and_chips": "炸鱼薯条",
    "foie_gras": "鹅肝",
    "french_fries": "薯条",
    "french_onion_soup": "法式洋葱汤",
    "french_toast": "法式吐司",
    "fried_calamari": "炸鱿鱼圈",
    "fried_rice": "炒饭",
    "frozen_yogurt": "冻酸奶",
    "garlic_bread": "蒜香面包",
    "gnocchi": "意式土豆团子",
    "greek_salad": "希腊沙拉",
    "grilled_cheese_sandwich": "烤奶酪三明治",
    "grilled_salmon": "烤三文鱼",
    "guacamole": "牛油果酱",
    "gyoza": "日式煎饺",
    "hamburger": "汉堡",
    "hot_and_sour_soup": "酸辣汤",
    "hot_dog": "热狗",
    "huevos_rancheros": "墨西哥牧场鸡蛋",
    "hummus": "鹰嘴豆泥",
    "ice_cream": "冰淇淋",
    "lasagna": "千层面",
    "lobster_bisque": "龙虾浓汤",
    "lobster_roll_sandwich": "龙虾卷三明治",
    "macaroni_and_cheese": "芝士通心粉",
    "macarons": "马卡龙",
    "miso_soup": "味噌汤",
    "mussels": "贻贝",
    "nachos": "玉米片",
    "omelette": "煎蛋卷",
    "onion_rings": "洋葱圈",
    "oysters": "牡蛎",
    "pad_thai": "泰式炒河粉",
    "paella": "西班牙海鲜饭",
    "pancakes": "松饼",
    "panna_cotta": "意式奶冻",
    "peking_duck": "北京烤鸭",
    "pho": "越南河粉",
    "pizza": "披萨",
    "pork_chop": "猪排",
    "poutine": "肉汁奶酪薯条",
    "prime_rib": "上等肋排",
    "pulled_pork_sandwich": "手撕猪肉三明治",
    "ramen": "拉面",
    "ravioli": "意式方饺",
    "red_velvet_cake": "红丝绒蛋糕",
    "risotto": "意式烩饭",
    "samosa": "咖喱角",
    "sashimi": "刺身",
    "scallops": "扇贝",
    "seaweed_salad": "海藻沙拉",
    "shrimp_and_grits": "虾仁玉米糁",
    "spaghetti_bolognese": "肉酱意面",
    "spaghetti_carbonara": "培根蛋酱意面",
    "spring_rolls": "春卷",
    "steak": "牛排",
    "strawberry_shortcake": "草莓奶油蛋糕",
    "sushi": "寿司",
    "tacos": "塔可",
    "takoyaki": "章鱼烧",
    "tiramisu": "提拉米苏",
    "tuna_tartare": "鞑靼金枪鱼",
    "waffles": "华夫饼",
}


CATEGORIES = {
    "甜点": {
        "apple_pie", "baklava", "beignets", "bread_pudding", "cannoli",
        "carrot_cake", "cheesecake", "chocolate_cake", "chocolate_mousse",
        "churros", "creme_brulee", "cup_cakes", "donuts", "frozen_yogurt",
        "ice_cream", "macarons", "pancakes", "panna_cotta", "red_velvet_cake",
        "strawberry_shortcake", "tiramisu", "waffles",
    },
    "肉类": {
        "baby_back_ribs", "beef_carpaccio", "beef_tartare", "chicken_curry",
        "chicken_wings", "filet_mignon", "foie_gras", "peking_duck",
        "pork_chop", "prime_rib", "steak",
    },
    "海鲜": {
        "ceviche", "crab_cakes", "escargots", "fish_and_chips",
        "fried_calamari", "grilled_salmon", "lobster_roll_sandwich",
        "mussels", "oysters", "sashimi", "scallops", "shrimp_and_grits",
        "tuna_tartare",
    },
    "汤类": {"clam_chowder", "french_onion_soup", "hot_and_sour_soup", "lobster_bisque", "miso_soup"},
    "沙拉": {"beet_salad", "caesar_salad", "caprese_salad", "greek_salad", "seaweed_salad"},
    "蛋类": {"deviled_eggs", "eggs_benedict", "huevos_rancheros", "omelette"},
    "豆类": {"edamame", "falafel", "hummus"},
    "奶制品": {"cheese_plate"},
    "小食": {
        "bruschetta", "french_fries", "garlic_bread", "guacamole", "nachos",
        "onion_rings", "poutine", "samosa", "spring_rolls", "takoyaki",
    },
}


BASE_NUTRITION = {
    "甜点": (330, 5.0, 17.0, 43.0, "甜点类通常糖分和热量较高，建议作为加餐少量食用，并搭配无糖饮品或正餐中减少主食。"),
    "肉类": (260, 22.0, 18.0, 3.0, "肉类菜品蛋白质较高，但脂肪和钠含量可能偏高，建议搭配蔬菜并注意份量。"),
    "海鲜": (170, 18.0, 7.0, 8.0, "海鲜类蛋白质较丰富，整体脂肪相对可控，建议注意烹调方式和蘸料盐分。"),
    "汤类": (90, 5.0, 4.0, 9.0, "汤类热量通常不高，但钠含量可能偏高，建议少喝浓汤或控制汤底摄入。"),
    "沙拉": (130, 5.0, 9.0, 10.0, "沙拉类相对清爽，但酱料可能带来额外脂肪和钠，建议酱料分开少量添加。"),
    "蛋类": (190, 11.0, 14.0, 6.0, "蛋类蛋白质较好，饱腹感强，建议搭配蔬菜和全谷物保持均衡。"),
    "豆类": (190, 10.0, 10.0, 18.0, "豆类富含植物蛋白和膳食纤维，适合作为均衡饮食的一部分。"),
    "奶制品": (350, 20.0, 28.0, 4.0, "奶酪等奶制品钙和蛋白质较多，但脂肪和钠也可能偏高，建议控制份量。"),
    "小食": (300, 7.0, 16.0, 33.0, "小食类常见油炸或高盐做法，建议少量尝试，不建议替代正餐。"),
    "主食": (220, 9.0, 9.0, 28.0, "主食类碳水占比较高，适合作为一餐能量来源，建议搭配蔬菜和优质蛋白。"),
}


OVERRIDES = {
    "edamame": (120, 11.0, 5.0, 10.0),
    "foie_gras": (460, 11.0, 45.0, 3.0),
    "miso_soup": (40, 3.0, 2.0, 5.0),
    "oysters": (80, 9.0, 2.0, 5.0),
    "pho": (90, 6.0, 2.0, 14.0),
    "pizza": (266, 11.0, 10.0, 33.0),
    "ramen": (170, 7.0, 5.0, 24.0),
    "fried_rice": (188, 5.0, 6.0, 28.0),
    "hamburger": (295, 17.0, 14.0, 24.0),
    "sushi": (140, 6.0, 3.0, 23.0),
    "sashimi": (130, 22.0, 4.0, 0.0),
    "steak": (250, 26.0, 15.0, 0.0),
}


def class_category(food_name: str) -> str:
    for category, names in CATEGORIES.items():
        if food_name in names:
            return category
    return "主食"


def varied(base: tuple[float, float, float, float], index: int) -> tuple[float, float, float, float]:
    calories, protein, fat, carbohydrate = base
    return (
        round(calories + ((index % 5) - 2) * 8, 1),
        round(max(0, protein + ((index % 3) - 1) * 1.2), 1),
        round(max(0, fat + ((index % 4) - 1.5) * 1.0), 1),
        round(max(0, carbohydrate + ((index % 5) - 2) * 2.0), 1),
    )


def main() -> None:
    classes = [line.strip() for line in CLASSES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    missing = [name for name in classes if name not in DISPLAY_NAMES]
    if missing:
        raise ValueError(f"缺少中文映射: {missing}")

    nutrition_table = {}
    for index, food_name in enumerate(classes):
        category = class_category(food_name)
        base_calories, base_protein, base_fat, base_carbs, suggestion = BASE_NUTRITION[category]
        calories, protein, fat, carbs = OVERRIDES.get(
            food_name,
            varied((base_calories, base_protein, base_fat, base_carbs), index),
        )
        nutrition_table[food_name] = {
            "display_name": DISPLAY_NAMES[food_name],
            "category": category,
            "calories": calories,
            "protein": protein,
            "fat": fat,
            "carbohydrate": carbs,
            "unit": "每100克估算值",
            "suggestion": suggestion,
        }

    DISPLAY_NAMES_PATH.write_text(json.dumps(DISPLAY_NAMES, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    NUTRITION_PATH.write_text(json.dumps(nutrition_table, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"中文映射已生成: {DISPLAY_NAMES_PATH} ({len(DISPLAY_NAMES)} 类)")
    print(f"营养配置已生成: {NUTRITION_PATH} ({len(nutrition_table)} 类)")


if __name__ == "__main__":
    main()
