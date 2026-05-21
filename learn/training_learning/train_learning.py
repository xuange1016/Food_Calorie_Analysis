"""
学习版：模型训练脚本。

这个文件对应正式项目中的：
    training/train.py

训练脚本要做的事情：
1. 读取 data/food101_10class/train 和 val；
2. 构造图像预处理；
3. 加载 ResNet18 预训练模型；
4. 替换最后一层分类层；
5. 使用训练集更新模型参数；
6. 使用验证集评估模型；
7. 保存验证集表现最好的模型。
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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "food101_10class"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "backend" / "models" / "food_model.pth"
DEFAULT_CLASS_NAMES_PATH = PROJECT_ROOT / "backend" / "models" / "class_names.json"


def build_transforms(image_size: int) -> dict[str, transforms.Compose]:
    """定义训练和验证阶段的图片预处理。

    训练集可以使用随机增强，提高模型泛化能力。
    验证集不使用随机增强，保证评估结果稳定。
    """
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
    """构建 ResNet18 模型。

    pretrained=True 时，会加载 ImageNet 预训练权重。
    迁移学习的核心就是复用预训练模型的特征提取能力。
    """
    weights = models.ResNet18_Weights.DEFAULT if pretrained else None
    model = models.resnet18(weights=weights)

    # ResNet18 原本最后一层输出 ImageNet 的 1000 类。
    # 项目只需要输出 10 类食物，所以替换 fc 层。
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)
    return model


def run_one_epoch(model, loader, criterion, optimizer, device, phase):
    """训练或验证一个 epoch。

    optimizer 不为 None 表示训练阶段；
    optimizer 为 None 表示验证阶段。
    """
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

    return running_loss / total, running_corrects / total


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

    transform_map = build_transforms(args.image_size)

    train_dataset = datasets.ImageFolder(args.data_dir / "train", transform=transform_map["train"])
    val_dataset = datasets.ImageFolder(args.data_dir / "val", transform=transform_map["val"])

    # ImageFolder 会按字母顺序读取类别。
    # 保存这个顺序，预测时才能把模型输出编号转回正确类别名。
    class_names = train_dataset.classes
    args.class_names.parent.mkdir(parents=True, exist_ok=True)
    with args.class_names.open("w", encoding="utf-8") as f:
        json.dump(class_names, f, ensure_ascii=False, indent=2)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(num_classes=len(class_names), pretrained=not args.no_pretrained)
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    best_acc = 0.0
    best_state = copy.deepcopy(model.state_dict())

    for epoch in range(1, args.epochs + 1):
        print(f"Epoch {epoch}/{args.epochs}")
        train_loss, train_acc = run_one_epoch(model, train_loader, criterion, optimizer, device, "train")
        val_loss, val_acc = run_one_epoch(model, val_loader, criterion, None, device, "val")

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

    print(f"训练完成，最佳验证准确率: {best_acc:.4f}")


if __name__ == "__main__":
    main()
