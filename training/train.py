"""
训练食物分类模型。

运行示例：
    python training/train.py --epochs 8 --batch-size 32
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from tqdm import tqdm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "backend" / "models" / "food_model.pth"
DEFAULT_CLASS_NAMES_PATH = PROJECT_ROOT / "backend" / "models" / "class_names.json"


def load_class_names(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_transforms(image_size: int) -> dict[str, transforms.Compose]:
    """训练集使用随机增强，验证/测试集使用稳定预处理。"""
    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    )
    return {
        "train": transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                normalize,
            ]
        ),
        "val": transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                normalize,
            ]
        ),
    }


def build_model(num_classes: int, pretrained: bool) -> nn.Module:
    """创建 ResNet18，并把最后分类层改成食物类别数。"""
    weights = models.ResNet18_Weights.DEFAULT if pretrained else None
    model = models.resnet18(weights=weights)
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)
    return model


def run_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer | None,
    device: torch.device,
    phase: str,
) -> tuple[float, float]:
    is_train = optimizer is not None
    model.train() if is_train else model.eval()

    running_loss = 0.0
    running_corrects = 0
    total = 0

    for inputs, labels in tqdm(loader, desc=phase):
        inputs = inputs.to(device)
        labels = labels.to(device)

        with torch.set_grad_enabled(is_train):
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            _, preds = torch.max(outputs, 1)

            if is_train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        batch_size = inputs.size(0)
        running_loss += loss.item() * batch_size
        running_corrects += torch.sum(preds == labels).item()
        total += batch_size

    epoch_loss = running_loss / total
    epoch_acc = running_corrects / total
    return epoch_loss, epoch_acc


def main() -> None:
    parser = argparse.ArgumentParser(description="Train food classification model.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--class-names", type=Path, default=DEFAULT_CLASS_NAMES_PATH)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--no-pretrained", action="store_true")
    args = parser.parse_args()

    train_dir = args.data_dir / "train"
    val_dir = args.data_dir / "val"
    if not train_dir.exists() or not val_dir.exists():
        raise FileNotFoundError("未找到 data/train 或 data/val，请先准备数据集。")
    if not args.class_names.exists():
        raise FileNotFoundError("未找到 class_names.json，请先运行数据整理脚本。")

    configured_class_names = load_class_names(args.class_names)
    transform_map = build_transforms(args.image_size)

    datasets_map = {
        "train": datasets.ImageFolder(train_dir, transform=transform_map["train"]),
        "val": datasets.ImageFolder(val_dir, transform=transform_map["val"]),
    }

    class_names = datasets_map["train"].classes
    num_classes = len(class_names)
    if class_names != configured_class_names:
        print("[INFO] ImageFolder 会按字母顺序读取类别。")
        print(f"配置类别顺序: {configured_class_names}")
        print(f"训练实际顺序: {class_names}")
        print("后续预测将使用训练实际顺序，避免类别错位。")
        args.class_names.parent.mkdir(parents=True, exist_ok=True)
        with args.class_names.open("w", encoding="utf-8") as f:
            json.dump(class_names, f, ensure_ascii=False, indent=2)

    loaders = {
        phase: DataLoader(
            datasets_map[phase],
            batch_size=args.batch_size,
            shuffle=(phase == "train"),
            num_workers=args.num_workers,
        )
        for phase in ["train", "val"]
    }

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")
    print(f"类别数: {num_classes}")
    print(f"训练样本: {len(datasets_map['train'])}")
    print(f"验证样本: {len(datasets_map['val'])}")

    model = build_model(num_classes=num_classes, pretrained=not args.no_pretrained)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    best_acc = 0.0
    best_state = copy.deepcopy(model.state_dict())

    for epoch in range(1, args.epochs + 1):
        print(f"\nEpoch {epoch}/{args.epochs}")
        train_loss, train_acc = run_one_epoch(
            model, loaders["train"], criterion, optimizer, device, "train"
        )
        val_loss, val_acc = run_one_epoch(
            model, loaders["val"], criterion, None, device, "val"
        )

        print(
            f"train_loss={train_loss:.4f}, train_acc={train_acc:.4f}, "
            f"val_loss={val_loss:.4f}, val_acc={val_acc:.4f}"
        )

        if val_acc > best_acc:
            best_acc = val_acc
            best_state = copy.deepcopy(model.state_dict())

    model.load_state_dict(best_state)
    args.model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "class_names": class_names,
            "image_size": args.image_size,
            "model_name": "resnet18",
        },
        args.model_path,
    )

    print(f"\n训练完成，最佳验证准确率: {best_acc:.4f}")
    print(f"模型已保存: {args.model_path}")


if __name__ == "__main__":
    main()
