"""
整理 Food-101 数据集，可筛选部分类别，也可直接整理完整 101 类。

运行示例：
    python training/dataset_prepare.py --raw-dir data/raw/food-101 --output-dir data

脚本做什么：
1. 读取 Food-101 原始目录中的 images 和 meta/train.txt、meta/test.txt；
2. 筛选配置文件中的类别，或通过 --all-classes 使用完整 101 类；
3. 从原始 train 列表中再划分一部分作为 val；
4. 把图片复制到 data/train、data/val、data/test；
5. 生成 backend/models/class_names.json，保证训练和预测类别顺序一致。

注意：
本脚本不会删除任何已有文件。如果目标文件已存在，会跳过复制。
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLASSES_PATH = PROJECT_ROOT / "training" / "selected_classes.json"
DEFAULT_CLASS_NAMES_PATH = PROJECT_ROOT / "backend" / "models" / "class_names.json"


def load_selected_classes(config_path: Path) -> list[str]:
    """读取要筛选的 Food-101 类别名。"""
    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    classes = [item["food101_name"] for item in data["classes"]]
    if not classes:
        raise ValueError("selected_classes.json 中没有配置任何类别。")
    return classes


def load_all_classes(classes_file: Path) -> list[str]:
    """读取 Food-101 官方 classes.txt 中的完整类别列表。"""
    with classes_file.open("r", encoding="utf-8") as f:
        classes = [line.strip() for line in f if line.strip()]
    if not classes:
        raise ValueError(f"类别文件为空: {classes_file}")
    return classes


def read_meta_list(meta_file: Path) -> dict[str, list[str]]:
    """读取 Food-101 的 train.txt 或 test.txt，并按类别分组。"""
    grouped: dict[str, list[str]] = {}

    with meta_file.open("r", encoding="utf-8") as f:
        for line in f:
            item = line.strip()
            if not item:
                continue

            class_name = item.split("/", 1)[0]
            grouped.setdefault(class_name, []).append(item)

    return grouped


def copy_image_if_needed(src: Path, dst: Path) -> bool:
    """复制单张图片。已存在则跳过，返回是否实际复制。"""
    if dst.exists():
        return False

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def prepare_split(
    image_items: list[str],
    images_dir: Path,
    output_split_dir: Path,
) -> tuple[int, int]:
    """把某个 split 的图片复制到目标目录。"""
    copied = 0
    skipped = 0

    for item in image_items:
        src = images_dir / f"{item}.jpg"
        dst = output_split_dir / f"{item}.jpg"

        if not src.exists():
            print(f"[WARN] 原始图片不存在，跳过: {src}")
            skipped += 1
            continue

        if copy_image_if_needed(src, dst):
            copied += 1
        else:
            skipped += 1

    return copied, skipped


def save_class_names(classes: list[str], output_path: Path) -> None:
    """保存类别顺序，后续训练和预测必须使用同一份。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(classes, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare selected Food-101 classes.")
    parser.add_argument("--raw-dir", type=Path, default=PROJECT_ROOT / "data" / "raw" / "food-101")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data")
    parser.add_argument("--classes", type=Path, default=DEFAULT_CLASSES_PATH)
    parser.add_argument("--all-classes", action="store_true", help="使用 Food-101 官方 101 类完整类别。")
    parser.add_argument("--class-names-output", type=Path, default=DEFAULT_CLASS_NAMES_PATH)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw_dir = args.raw_dir
    images_dir = raw_dir / "images"
    train_meta = raw_dir / "meta" / "train.txt"
    test_meta = raw_dir / "meta" / "test.txt"
    all_classes_file = raw_dir / "meta" / "classes.txt"

    if not images_dir.exists():
        raise FileNotFoundError(f"未找到 images 目录: {images_dir}")
    if not train_meta.exists():
        raise FileNotFoundError(f"未找到 train.txt: {train_meta}")
    if not test_meta.exists():
        raise FileNotFoundError(f"未找到 test.txt: {test_meta}")
    if args.all_classes and not all_classes_file.exists():
        raise FileNotFoundError(f"未找到 classes.txt: {all_classes_file}")

    selected_classes = load_all_classes(all_classes_file) if args.all_classes else load_selected_classes(args.classes)
    train_grouped = read_meta_list(train_meta)
    test_grouped = read_meta_list(test_meta)

    random.seed(args.seed)
    summary: dict[str, dict[str, int]] = {}

    print("开始整理 Food-101 数据集")
    print(f"原始数据目录: {raw_dir}")
    print(f"输出目录: {args.output_dir}")
    print(f"筛选类别数: {len(selected_classes)}")
    print()

    for class_name in selected_classes:
        if class_name not in train_grouped:
            raise ValueError(f"类别 {class_name} 不在 Food-101 train.txt 中，请检查类别名。")
        if class_name not in test_grouped:
            raise ValueError(f"类别 {class_name} 不在 Food-101 test.txt 中，请检查类别名。")

        train_items = train_grouped[class_name][:]
        test_items = test_grouped[class_name][:]
        random.shuffle(train_items)

        val_count = int(len(train_items) * args.val_ratio)
        val_items = train_items[:val_count]
        real_train_items = train_items[val_count:]

        train_copied, train_skipped = prepare_split(
            real_train_items,
            images_dir,
            args.output_dir / "train",
        )
        val_copied, val_skipped = prepare_split(
            val_items,
            images_dir,
            args.output_dir / "val",
        )
        test_copied, test_skipped = prepare_split(
            test_items,
            images_dir,
            args.output_dir / "test",
        )

        summary[class_name] = {
            "train": len(real_train_items),
            "val": len(val_items),
            "test": len(test_items),
            "copied": train_copied + val_copied + test_copied,
            "skipped": train_skipped + val_skipped + test_skipped,
        }

        print(
            f"{class_name}: train={len(real_train_items)}, "
            f"val={len(val_items)}, test={len(test_items)}"
        )

    # torchvision.datasets.ImageFolder 会按字母顺序读取类别。
    # 这里也保存字母顺序，保证训练、预测和后端展示不会类别错位。
    save_class_names(sorted(selected_classes), args.class_names_output)

    summary_path = args.output_dir / "dataset_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print()
    print("数据集整理完成。")
    print(f"类别顺序已保存: {args.class_names_output}")
    print(f"整理摘要已保存: {summary_path}")


if __name__ == "__main__":
    main()
