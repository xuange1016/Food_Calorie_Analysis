"""
评估训练好的模型在测试集上的准确率。

运行：
    python training/evaluate.py --data-dir data/food101_10class
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torchvision import datasets
from tqdm import tqdm

from train import build_transforms


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "food101_10class"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "backend" / "models" / "food_model.pth"
sys.path.append(str(PROJECT_ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate food model on test set.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--metrics-path", type=Path, default=None)
    args = parser.parse_args()

    if not args.model_path.exists():
        raise FileNotFoundError(f"模型文件不存在: {args.model_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.model_path, map_location=device)
    class_names = checkpoint["class_names"]
    image_size = int(checkpoint.get("image_size", 224))

    from backend.predict import build_model

    model = build_model(num_classes=len(class_names))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    transform = build_transforms(image_size)["val"]
    test_dir = args.data_dir / "test"
    test_dataset = datasets.ImageFolder(test_dir, transform=transform)

    if test_dataset.classes != class_names:
        print("[WARN] 测试集类别顺序和模型类别顺序不一致。")
        print(f"测试集: {test_dataset.classes}")
        print(f"模型: {class_names}")

    loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
    )

    correct = 0
    total = 0

    per_class_total = {name: 0 for name in class_names}
    per_class_correct = {name: 0 for name in class_names}

    with torch.no_grad():
        for inputs, labels in tqdm(loader, desc="test"):
            inputs = inputs.to(device)
            labels = labels.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)

            correct += torch.sum(preds == labels).item()
            total += labels.size(0)

            for label, pred in zip(labels.cpu().tolist(), preds.cpu().tolist()):
                class_name = class_names[label]
                per_class_total[class_name] += 1
                if label == pred:
                    per_class_correct[class_name] += 1

    accuracy = correct / total
    metrics = {
        "model_path": str(args.model_path),
        "data_dir": str(args.data_dir),
        "image_size": image_size,
        "num_classes": len(class_names),
        "test_samples": total,
        "test_accuracy": round(accuracy, 6),
        "per_class": {},
    }

    print(f"测试样本数: {total}")
    print(f"测试准确率: {accuracy:.4f}")
    print("各类别准确率:")
    for class_name in class_names:
        class_total = per_class_total[class_name]
        class_correct = per_class_correct[class_name]
        class_acc = class_correct / class_total if class_total else 0
        metrics["per_class"][class_name] = {
            "accuracy": round(class_acc, 6),
            "correct": class_correct,
            "total": class_total,
        }
        print(f"  {class_name}: {class_acc:.4f} ({class_correct}/{class_total})")

    if args.metrics_path is not None:
        args.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with args.metrics_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        print(f"评估指标已保存: {args.metrics_path}")


if __name__ == "__main__":
    main()
