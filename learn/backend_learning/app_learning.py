"""
学习版：Flask 后端入口。

这个文件对应正式项目中的：
    backend/app.py

后端负责把几个模块串起来：
1. 接收前端上传的图片；
2. 检查图片是否合法；
3. 保存临时图片；
4. 调用模型预测模块；
5. 调用营养查询模块；
6. 返回 JSON 给前端。
"""

from __future__ import annotations

import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# 学习版中为了方便阅读，仍然可以参考正式模块的函数命名。
# 正式项目运行时使用 backend/app.py。
from nutrition_learning import get_nutrition_result
from predict_learning import predict_image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


app = Flask(__name__, static_folder=None)
CORS(app)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def is_allowed_image(filename: str) -> bool:
    """判断上传文件扩展名是否合法。"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.get("/")
def index():
    """返回前端首页。

    用户访问 http://127.0.0.1:5000 时，实际返回 frontend/index.html。
    """
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:filename>")
def frontend_files(filename: str):
    """返回前端静态文件，例如 style.css 和 script.js。"""
    return send_from_directory(FRONTEND_DIR, filename)


@app.post("/predict")
def predict():
    """图片预测接口。

    前端会把图片放在表单字段 image 中提交。
    后端返回 JSON。
    """
    if "image" not in request.files:
        return jsonify({"error": "没有上传图片，请选择或拍摄一张食物图片。"}), 400

    file = request.files["image"]

    if not file.filename:
        return jsonify({"error": "图片文件名为空，请重新选择图片。"}), 400

    if not is_allowed_image(file.filename):
        return jsonify({"error": "图片格式不支持，请上传 jpg、jpeg 或 png 文件。"}), 400

    # secure_filename 用来处理文件名中的特殊字符。
    # uuid 用来避免不同用户上传同名文件互相覆盖。
    safe_name = secure_filename(file.filename)
    ext = Path(safe_name).suffix.lower()
    upload_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
    file.save(upload_path)

    try:
        prediction = predict_image(upload_path)
        nutrition = get_nutrition_result(prediction["food_name"])
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 500
    except KeyError as exc:
        return jsonify({"error": str(exc), "prediction": prediction}), 500
    except Exception as exc:
        return jsonify({"error": f"识别失败: {exc}"}), 500

    return jsonify(
        {
            "food_name": prediction["food_name"],
            "display_name": nutrition["display_name"],
            "confidence": prediction["confidence"],
            "top_predictions": prediction["top_predictions"],
            "nutrition": {
                "calories": nutrition["calories"],
                "protein": nutrition["protein"],
                "fat": nutrition["fat"],
                "carbohydrate": nutrition["carbohydrate"],
                "unit": nutrition["unit"],
            },
            "suggestion": nutrition["suggestion"],
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
