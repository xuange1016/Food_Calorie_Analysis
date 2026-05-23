"""
训练食物分类模型。

运行示例：
    python training/train.py --epochs 8 --batch-size 32
"""

from __future__ import annotations

import argparse
import copy
import json
import time
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
DEFAULT_CHECKPOINT_DIR = PROJECT_ROOT / "backend" / "models" / "checkpoints"


def load_class_names(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
    scaler: torch.amp.GradScaler | None = None,
    use_amp: bool = False,
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
            with torch.amp.autocast(device_type=device.type, enabled=use_amp):
                outputs = model(inputs)
                loss = criterion(outputs, labels)
            _, preds = torch.max(outputs, 1)

            if is_train:
                optimizer.zero_grad()
                if scaler is not None and use_amp:
                    scaler.scale(loss).backward()
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    loss.backward()
                    optimizer.step()

        batch_size = inputs.size(0)
        running_loss += loss.item() * batch_size
        running_corrects += torch.sum(preds == labels).item()
        total += batch_size

    epoch_loss = running_loss / total
    epoch_acc = running_corrects / total
    return epoch_loss, epoch_acc


def build_checkpoint(
    epoch: int,
    model: nn.Module,
    optimizer: optim.Optimizer,
    class_names: list[str],
    image_size: int,
    best_acc: float,
    best_epoch: int,
    history: list[dict],
) -> dict:
    return {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "class_names": class_names,
        "image_size": image_size,
        "model_name": "resnet18",
        "best_acc": best_acc,
        "best_epoch": best_epoch,
        "history": history,
    }


def save_checkpoint(checkpoint: dict, checkpoint_dir: Path, epoch: int, is_best: bool) -> None:
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, checkpoint_dir / f"checkpoint_epoch_{epoch:03d}.pth")
    torch.save(checkpoint, checkpoint_dir / "checkpoint_latest.pth")
    if is_best:
        torch.save(checkpoint, checkpoint_dir / "checkpoint_best.pth")


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
    parser.add_argument("--checkpoint-dir", type=Path, default=DEFAULT_CHECKPOINT_DIR)
    parser.add_argument("--resume", type=Path, default=None, help="从指定 checkpoint 继续训练。")
    parser.add_argument("--auto-resume", action="store_true", help="如果存在 checkpoint_latest.pth，则自动续训。")
    parser.add_argument("--history-path", type=Path, default=None)
    parser.add_argument("--amp", action="store_true", help="在 CUDA 上使用自动混合精度训练。")
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
    use_amp = args.amp and device.type == "cuda"
    scaler = torch.amp.GradScaler(device=device.type, enabled=use_amp) if use_amp else None

    best_acc = 0.0
    best_epoch = 0
    best_state = copy.deepcopy(model.state_dict())
    history: list[dict] = []
    start_epoch = 1

    resume_path = args.resume
    latest_checkpoint = args.checkpoint_dir / "checkpoint_latest.pth"
    if resume_path is None and args.auto_resume and latest_checkpoint.exists():
        resume_path = latest_checkpoint

    if resume_path is not None:
        checkpoint = torch.load(resume_path, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        if "optimizer_state_dict" in checkpoint:
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        best_acc = float(checkpoint.get("best_acc", 0.0))
        best_epoch = int(checkpoint.get("best_epoch", 0))
        history = list(checkpoint.get("history", []))
        start_epoch = int(checkpoint.get("epoch", 0)) + 1
        best_checkpoint = args.checkpoint_dir / "checkpoint_best.pth"
        if best_checkpoint.exists():
            best_state = torch.load(best_checkpoint, map_location=device)["model_state_dict"]
        else:
            best_state = copy.deepcopy(model.state_dict())
        print(f"从 checkpoint 继续训练: {resume_path}")
        print(f"继续起点: epoch {start_epoch}, 当前最佳验证准确率: {best_acc:.4f}")

    if start_epoch > args.epochs:
        print(f"checkpoint 已完成到 epoch {start_epoch - 1}，目标 epochs={args.epochs}，无需继续训练。")

    for epoch in range(start_epoch, args.epochs + 1):
        epoch_start = time.time()
        print(f"\nEpoch {epoch}/{args.epochs}")
        train_loss, train_acc = run_one_epoch(
            model, loaders["train"], criterion, optimizer, device, "train", scaler, use_amp
        )
        val_loss, val_acc = run_one_epoch(
            model, loaders["val"], criterion, None, device, "val", None, use_amp
        )
        epoch_seconds = round(time.time() - epoch_start, 2)

        print(
            f"train_loss={train_loss:.4f}, train_acc={train_acc:.4f}, "
            f"val_loss={val_loss:.4f}, val_acc={val_acc:.4f}, "
            f"epoch_seconds={epoch_seconds}"
        )

        is_best = False
        if val_acc > best_acc:
            best_acc = val_acc
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            is_best = True

        history.append(
            {
                "epoch": epoch,
                "train_loss": round(train_loss, 6),
                "train_acc": round(train_acc, 6),
                "val_loss": round(val_loss, 6),
                "val_acc": round(val_acc, 6),
                "epoch_seconds": epoch_seconds,
                "is_best": is_best,
            }
        )

        checkpoint = build_checkpoint(
            epoch=epoch,
            model=model,
            optimizer=optimizer,
            class_names=class_names,
            image_size=args.image_size,
            best_acc=best_acc,
            best_epoch=best_epoch,
            history=history,
        )
        save_checkpoint(checkpoint, args.checkpoint_dir, epoch, is_best)
        history_path = args.history_path or args.checkpoint_dir / "training_history.json"
        save_json(history, history_path)
        print(f"checkpoint 已保存: {args.checkpoint_dir / 'checkpoint_latest.pth'}")

    model.load_state_dict(best_state)
    args.model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "class_names": class_names,
            "image_size": args.image_size,
            "model_name": "resnet18",
            "best_acc": best_acc,
            "best_epoch": best_epoch,
            "history": history,
        },
        args.model_path,
    )

    print(f"\n训练完成，最佳验证准确率: {best_acc:.4f}")
    print(f"最佳 epoch: {best_epoch}")
    print(f"模型已保存: {args.model_path}")


if __name__ == "__main__":
    main()
