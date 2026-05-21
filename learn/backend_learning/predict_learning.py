"""
学习版：单张图片预测模块。

这个文件对应正式项目中的：
    backend/predict.py

模型预测的核心流程：
1. 加载训练好的模型文件 food_model.pth；
2. 读取类别顺序 class_names；
3. 用 Pillow 打开用户上传的图片；
4. 对图片做和训练时一致的预处理；
5. 把图片张量输入 ResNet18；
6. 用 softmax 得到每个类别的概率；
7. 取概率最高的类别作为预测结果。
"""

from __future__ import annotations

import json
from pathlib import Path

import torch
from PIL import Image
from torch import nn
from torchvision import models, transforms


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "backend" / "models" / "food_model.pth"
DEFAULT_CLASS_NAMES_PATH = PROJECT_ROOT / "backend" / "models" / "class_names.json"


def load_class_names(path: Path = DEFAULT_CLASS_NAMES_PATH) -> list[str]:
    """读取类别名称列表。

    模型输出的是数字编号，例如 7。
    class_names 用来把数字编号转换成具体类别，例如 pizza。

    注意：
    训练和预测必须使用同一份 class_names，否则会出现类别错位。
    """
    if not path.exists():
        raise FileNotFoundError(f"类别文件不存在: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_model(num_classes: int) -> nn.Module:
    """创建 ResNet18 模型结构。

    这里 weights=None，因为预测时不需要重新下载预训练权重。
    模型权重会从 food_model.pth 中加载。

    最后一层 fc 要改成 num_classes 个输出。
    当前项目 num_classes = 10。
    """
    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def load_model(model_path: Path = DEFAULT_MODEL_PATH):
    """加载训练好的模型。

    checkpoint 是训练脚本保存的字典，里面包含：
    - model_state_dict: 模型参数；
    - class_names: 类别顺序；
    - image_size: 图片输入尺寸；
    - model_name: 模型名称。
    """
    if not model_path.exists():
        raise FileNotFoundError(f"模型文件不存在: {model_path}")

    # 如果电脑有 CUDA 显卡，就用 GPU；否则用 CPU。
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    checkpoint = torch.load(model_path, map_location=device)
    class_names = checkpoint.get("class_names") or load_class_names()
    image_size = int(checkpoint.get("image_size", 224))

    model = build_model(num_classes=len(class_names))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    return model, class_names, image_size, device


def build_transform(image_size: int) -> transforms.Compose:
    """构造预测阶段的图片预处理。

    这里必须和训练时验证集/测试集预处理保持一致：
    - Resize 到固定大小；
    - 转成 Tensor；
    - 使用 ImageNet 均值和标准差归一化。
    """
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


def predict_image(image_path: str | Path, topk: int = 3) -> dict:
    """预测单张图片。

    参数：
        image_path: 图片路径；
        topk: 返回概率最高的前几个类别。

    返回：
        {
            "food_name": "pizza",
            "confidence": 0.98,
            "top_predictions": [...]
        }
    """
    model, class_names, image_size, device = load_model()
    transform = build_transform(image_size)

    # convert("RGB") 是为了保证图片一定是三通道。
    image = Image.open(image_path).convert("RGB")

    # 模型输入要求是 [batch, channel, height, width]。
    # 单张图片原本是 [channel, height, width]，
    # unsqueeze(0) 用来补一个 batch 维度。
    inputs = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(inputs)

        # softmax 把模型原始输出转换成概率。
        probs = torch.softmax(outputs, dim=1)[0]

        # 取概率最高的 topk 个类别。
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
