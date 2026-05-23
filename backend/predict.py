"""
单张图片预测模块。

后端和命令行测试都会调用这里，避免把预测逻辑写散。
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import torch
from PIL import Image
from torch import nn
from torchvision import models, transforms


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEGACY_MODEL_PATH = PROJECT_ROOT / "backend" / "models" / "food_model.pth"
FOOD101_MODEL_PATH = PROJECT_ROOT / "training_runs" / "food101_101class" / "food_model_101class.pth"
DEFAULT_MODEL_PATH = Path(os.environ.get("FOOD_CALORIE_MODEL_PATH", FOOD101_MODEL_PATH))
if not DEFAULT_MODEL_PATH.exists():
    DEFAULT_MODEL_PATH = LEGACY_MODEL_PATH
DEFAULT_CLASS_NAMES_PATH = PROJECT_ROOT / "backend" / "models" / "class_names.json"
_MODEL_CACHE: dict[Path, tuple[nn.Module, list[str], int, torch.device]] = {}


def load_class_names(path: Path = DEFAULT_CLASS_NAMES_PATH) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"类别文件不存在: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_model(num_classes: int) -> nn.Module:
    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def load_model(model_path: Path = DEFAULT_MODEL_PATH) -> tuple[nn.Module, list[str], int, torch.device]:
    model_path = model_path.resolve()
    if model_path in _MODEL_CACHE:
        return _MODEL_CACHE[model_path]

    if not model_path.exists():
        raise FileNotFoundError(f"模型文件不存在: {model_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(model_path, map_location=device)
    class_names = checkpoint.get("class_names") or load_class_names()
    image_size = int(checkpoint.get("image_size", 224))

    model = build_model(num_classes=len(class_names))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    model_bundle = (model, class_names, image_size, device)
    _MODEL_CACHE[model_path] = model_bundle
    return model_bundle


def get_model_info(model_path: str | Path = DEFAULT_MODEL_PATH) -> dict:
    model, class_names, image_size, device = load_model(Path(model_path))
    return {
        "model_path": str(Path(model_path).resolve()),
        "num_classes": len(class_names),
        "image_size": image_size,
        "device": str(device),
    }


def build_transform(image_size: int) -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )


def predict_image(image_path: str | Path, topk: int = 3, model_path: str | Path = DEFAULT_MODEL_PATH) -> dict:
    model, class_names, image_size, device = load_model(Path(model_path))
    transform = build_transform(image_size)

    image = Image.open(image_path).convert("RGB")
    inputs = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(inputs)
        probs = torch.softmax(outputs, dim=1)[0]
        top_probs, top_indices = torch.topk(probs, k=min(topk, len(class_names)))

    predictions = []
    for prob, index in zip(top_probs.tolist(), top_indices.tolist()):
        predictions.append(
            {
                "food_name": class_names[index],
                "confidence": round(float(prob), 4),
            }
        )

    best = predictions[0]
    return {
        "food_name": best["food_name"],
        "confidence": best["confidence"],
        "top_predictions": predictions,
    }
