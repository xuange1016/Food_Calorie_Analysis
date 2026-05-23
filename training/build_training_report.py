"""
Build a Markdown report from Food-101 training and evaluation artifacts.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def format_seconds(seconds: float) -> str:
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}小时{minutes}分钟{sec}秒"
    if minutes:
        return f"{minutes}分钟{sec}秒"
    return f"{sec}秒"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Food-101 training report.")
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--dataset-summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    args = parser.parse_args()

    history = load_json(args.history)
    metrics = load_json(args.metrics)
    dataset_summary = load_json(args.dataset_summary)

    if not isinstance(history, list) or not history:
        raise ValueError("训练历史为空，无法生成报告。")
    if not isinstance(metrics, dict):
        raise ValueError("评估指标格式错误。")
    if not isinstance(dataset_summary, dict):
        raise ValueError("数据集摘要格式错误。")

    best_epoch = max(history, key=lambda item: item["val_acc"])
    last_epoch = history[-1]
    total_train_time = sum(float(item.get("epoch_seconds", 0)) for item in history)

    train_count = sum(int(item["train"]) for item in dataset_summary.values())
    val_count = sum(int(item["val"]) for item in dataset_summary.values())
    test_count = sum(int(item["test"]) for item in dataset_summary.values())

    per_class = metrics.get("per_class", {})
    class_rows = []
    for class_name, item in sorted(per_class.items()):
        class_rows.append(
            f"| {class_name} | {item['accuracy']:.4f} | {item['correct']} / {item['total']} |"
        )

    content = "\n".join(
        [
            "# Food-101 101类模型训练报告",
            "",
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 1. 训练目标",
            "",
            "本次训练目标是将原 10 类菜品识别模型扩展为 Food-101 全量 101 类图像分类模型，并保留每轮 checkpoint，支持中断后继续训练。",
            "",
            "## 2. 数据集",
            "",
            f"- 类别数：{len(dataset_summary)}",
            f"- 训练集：{train_count} 张",
            f"- 验证集：{val_count} 张",
            f"- 测试集：{test_count} 张",
            "- 验证集从官方训练集按固定随机种子切分得到，测试集沿用 Food-101 官方 test 划分。",
            "",
            "## 3. 训练配置",
            "",
            f"- 模型：ResNet18",
            f"- 输出模型：`{args.model_path}`",
            f"- 图像尺寸：{metrics.get('image_size', 224)}",
            f"- 完成 epoch：{last_epoch['epoch']}",
            f"- 最佳 epoch：{best_epoch['epoch']}",
            f"- 最佳验证准确率：{best_epoch['val_acc']:.4f}",
            f"- 总训练耗时：{format_seconds(total_train_time)}",
            "- 耗时按每轮 wall-clock 统计，如果电脑休眠或进程被暂停，单轮耗时会包含暂停时间。",
            "",
            "## 4. 测试集结果",
            "",
            f"- 测试样本数：{metrics.get('test_samples')}",
            f"- 测试准确率：{metrics.get('test_accuracy'):.4f}",
            "",
            "## 5. 训练过程",
            "",
            "| Epoch | Train Loss | Train Acc | Val Loss | Val Acc | 耗时 |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
            *[
                (
                    f"| {item['epoch']} | {item['train_loss']:.4f} | {item['train_acc']:.4f} | "
                    f"{item['val_loss']:.4f} | {item['val_acc']:.4f} | {format_seconds(item['epoch_seconds'])} |"
                )
                for item in history
            ],
            "",
            "## 6. 各类别测试准确率",
            "",
            "| 类别 | 准确率 | 正确/总数 |",
            "| --- | ---: | ---: |",
            *class_rows,
            "",
            "## 7. 说明",
            "",
            "- `checkpoint_latest.pth` 可用于断点续训。",
            "- `checkpoint_best.pth` 保存验证集表现最好的 checkpoint。",
            "- 最终模型文件保存的是验证集最佳权重。",
        ]
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(f"训练报告已生成: {args.output}")


if __name__ == "__main__":
    main()
