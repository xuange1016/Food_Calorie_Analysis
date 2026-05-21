# learn 目录说明

这个目录是项目的“学习版源码”，用于理解项目实现逻辑。

正式运行代码在：

```text
backend/
frontend/
training/
```

学习版代码在：

```text
learn/
├── backend_learning/
├── training_learning/
├── frontend_learning/
└── README.md
```

学习版代码的特点：

- 和正式项目逻辑一致；
- 增加了更详细的中文注释；
- 更强调“为什么这样写”；
- 主要用于阅读和学习，不作为最终运行入口；
- 不建议直接替换正式代码。

## 推荐学习顺序

1. `training_learning/dataset_prepare_learning.py`
   - 理解 Food-101 如何整理成训练集、验证集、测试集。

2. `training_learning/train_learning.py`
   - 理解 ResNet18 迁移学习训练流程。

3. `backend_learning/predict_learning.py`
   - 理解单张图片如何进入模型并得到预测类别。

4. `backend_learning/nutrition_learning.py`
   - 理解识别类别如何查询营养信息。

5. `backend_learning/app_learning.py`
   - 理解 Flask 后端如何把上传、预测、营养查询串起来。

6. `frontend_learning/script_learning.js`
   - 理解前端如何上传图片、调用接口、展示结果。

## 项目主流程

```text
用户上传图片
  ↓
前端通过 fetch 提交图片
  ↓
Flask /predict 接口接收图片
  ↓
predict.py 加载模型并预测类别
  ↓
nutrition.py 查询营养信息
  ↓
后端返回 JSON
  ↓
前端展示类别、置信度、营养值和建议
```

## 需要重点理解的概念

- 图像分类：输入一张图片，输出一个类别。
- 迁移学习：使用预训练模型，再针对自己的类别微调。
- ResNet18：一种经典卷积神经网络。
- 置信度：模型认为某个类别最可能的概率。
- JSON：前后端传递结构化数据的格式。
- Flask：Python Web 后端框架。
- 本地营养表：营养数据不是模型预测出来的，而是根据类别查表得到的。
