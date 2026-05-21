# 基于机器视觉的食堂/外卖菜品识别与热量估算助手

## 项目简介

本项目为《人工智能概论》课程设计，方向为机器视觉应用。系统支持用户上传食物图片，后端调用食物图像分类模型识别菜品类别，并根据本地营养信息表估算热量、蛋白质、脂肪和碳水化合物，最后给出简单饮食建议。

当前版本基于 Food-101 数据集筛选 10 类食物进行训练，使用 ResNet18 迁移学习完成图像分类，并通过 Flask + HTML/CSS/JavaScript 实现 Web demo。

## 项目结构

```text
backend/                 Flask 后端、模型预测、营养查询
frontend/                Web 页面
training/                数据整理、模型训练、模型评估脚本
docs/                    项目说明、展示说明、提交清单
report/                  课程设计报告
environment.yml          conda 环境配置
requirements.txt         基础 Python 依赖
requirements-torch-cu128.txt  CUDA 版 PyTorch 依赖
```

## 数据与模型结果

本项目使用 Food-101 数据集中筛选出的 10 类食物：

```text
caesar_salad, chicken_wings, chocolate_cake, dumplings, filet_mignon,
fried_rice, hamburger, pizza, ramen, sushi
```

数据集划分：

```text
训练集：6000 张
验证集：1500 张
测试集：2500 张
```

模型训练结果：

```text
模型：ResNet18
最佳验证准确率：78.60%
测试准确率：84.04%
模型文件：backend/models/food_model.pth
```

## 环境配置

推荐使用 conda 创建环境：

```powershell
conda env create -f environment.yml
conda activate food-calorie
pip install -r requirements-torch-cu128.txt
```

如果电脑没有 NVIDIA 显卡，可以使用 CPU 版 PyTorch：

```powershell
pip install -r requirements-torch-cpu.txt
```

## 运行 Web demo

```powershell
conda activate food-calorie
cd 项目根目录
python backend/app.py
```

浏览器访问：

```text
http://127.0.0.1:5000
```

页面支持上传图片、查看预测类别、置信度、Top-3 预测、营养估算和饮食建议。

## 重新训练模型

```powershell
python training/dataset_prepare.py --raw-dir data/food-101 --output-dir data/food101_10class
python training/train.py --data-dir data/food101_10class --epochs 8 --batch-size 32 --image-size 224
python training/evaluate.py --data-dir data/food101_10class --batch-size 32
```

## 课程设计材料

```text
report/基于机器视觉的食堂外卖菜品识别与热量估算助手_课程设计报告.docx
docs/项目总文档.md
docs/demo展示说明.md
docs/提交材料清单.md
```

## 说明

营养信息来自本地平均营养值表，单位为每 100 克估算值，仅用于课程设计展示，不作为医学或健康诊断依据。
