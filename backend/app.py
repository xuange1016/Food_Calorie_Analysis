"""
Flask 后端入口。

运行：
    python backend/app.py
"""

from __future__ import annotations

import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from nutrition import get_nutrition_result
from predict import predict_image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


app = Flask(__name__, static_folder=None)
CORS(app)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def is_allowed_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:filename>")
def frontend_files(filename: str):
    return send_from_directory(FRONTEND_DIR, filename)


@app.post("/predict")
def predict():
    if "image" not in request.files:
        return jsonify({"error": "没有上传图片，请选择或拍摄一张食物图片。"}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "图片文件名为空，请重新选择图片。"}), 400

    if not is_allowed_image(file.filename):
        return jsonify({"error": "图片格式不支持，请上传 jpg、jpeg 或 png 文件。"}), 400

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
