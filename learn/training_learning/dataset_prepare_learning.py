"""
学习版：Food-101 数据整理脚本。

这个文件对应正式项目中的：
    training/dataset_prepare.py

为什么需要整理数据？
Food-101 原始数据是完整 101 类，而项目第一版只训练 10 类。
所以要根据 selected_classes.json 筛选出需要的类别，并整理成：

data/food101_10class/
├── train/
├── val/
└── test/

ImageFolder 训练时要求每个类别是一个文件夹。
"""

from __future__ import annotations

import json
import random
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLASSES_PATH = PROJECT_ROOT / "training" / "selected_classes.json"


def load_selected_classes() -> list[str]:
    """读取要筛选的 10 个 Food-101 类别名。"""
    with CLASSES_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [item["food101_name"] for item in data["classes"]]


def read_meta_list(meta_file: Path) -> dict[str, list[str]]:
    """读取 Food-101 的 train.txt 或 test.txt。

    文件中的每一行类似：
        pizza/1001116

    这个函数会按类别分组：
        {
            "pizza": ["pizza/1001116", ...]
        }
    """
    grouped: dict[str, list[str]] = {}

    with meta_file.open("r", encoding="utf-8") as f:
        for line in f:
            item = line.strip()
            if not item:
                continue
            class_name = item.split("/", 1)[0]
            grouped.setdefault(class_name, []).append(item)

    return grouped


def copy_image(src: Path, dst: Path) -> None:
    """复制图片到目标目录。

    dst.parent.mkdir 会先创建类别目录。
    shutil.copy2 会保留文件元信息。
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)


def prepare_dataset(raw_dir: Path, output_dir: Path, val_ratio: float = 0.2) -> None:
    """整理 Food-101 10 类子集。"""
    selected_classes = load_selected_classes()
    images_dir = raw_dir / "images"
    train_meta = raw_dir / "meta" / "train.txt"
    test_meta = raw_dir / "meta" / "test.txt"

    train_grouped = read_meta_list(train_meta)
    test_grouped = read_meta_list(test_meta)

    random.seed(42)

    for class_name in selected_classes:
        train_items = train_grouped[class_name][:]
        test_items = test_grouped[class_name][:]

        random.shuffle(train_items)
        val_count = int(len(train_items) * val_ratio)

        val_items = train_items[:val_count]
        real_train_items = train_items[val_count:]

        for split, items in [
            ("train", real_train_items),
            ("val", val_items),
            ("test", test_items),
        ]:
            for item in items:
                src = images_dir / f"{item}.jpg"
                dst = output_dir / split / f"{item}.jpg"
                copy_image(src, dst)

        print(
            f"{class_name}: train={len(real_train_items)}, "
            f"val={len(val_items)}, test={len(test_items)}"
        )


if __name__ == "__main__":
    prepare_dataset(
        raw_dir=PROJECT_ROOT / "data" / "food-101",
        output_dir=PROJECT_ROOT / "data" / "food101_10class",
    )
