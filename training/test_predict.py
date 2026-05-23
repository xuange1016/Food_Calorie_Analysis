"""
命令行测试单张图片预测。

运行：
    python training/test_predict.py --image path/to/image.jpg
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from backend.predict import predict_image
from backend.nutrition import get_nutrition_result


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict one food image.")
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=PROJECT_ROOT / "backend" / "models" / "food_model.pth")
    parser.add_argument("--topk", type=int, default=5)
    args = parser.parse_args()

    result = predict_image(args.image, topk=args.topk, model_path=args.model_path)
    nutrition = get_nutrition_result(result["food_name"])

    print("预测结果:")
    print(f"类别: {result['food_name']}")
    print(f"置信度: {result['confidence']:.4f}")
    print(f"Top-{args.topk}:")
    for item in result["top_predictions"]:
        print(f"  {item['food_name']}: {item['confidence']:.4f}")
    print("营养信息:")
    print(nutrition)


if __name__ == "__main__":
    main()
