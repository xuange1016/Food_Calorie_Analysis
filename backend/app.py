"""
Flask 后端入口。

运行：
    python backend/app.py
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import requests
from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

try:
    from .nutrition import get_nutrition_result
    from .predict import get_model_info, predict_image
except ImportError:
    from nutrition import get_nutrition_result
    from predict import get_model_info, predict_image


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


@app.get("/model-info")
def model_info():
    try:
        return jsonify(get_model_info())
    except Exception as exc:
        return jsonify({"error": f"模型信息读取失败: {exc}"}), 500


def normalize_chat_completions_url(base_url: str) -> str:
    base_url = (base_url or "").strip().rstrip("/")
    if not base_url:
        raise ValueError("请填写云端模型 Base URL。")
    if base_url.endswith("/chat/completions"):
        return base_url
    if base_url.endswith("/v1"):
        return f"{base_url}/chat/completions"
    return f"{base_url}/v1/chat/completions"


def build_advice_prompt(payload: dict) -> list[dict]:
    profile = payload.get("profile") or {}
    result = payload.get("result") or {}
    nutrition = result.get("nutrition") or {}
    top_predictions = result.get("top_predictions") or []
    goal = profile.get("goal") or "均衡饮食"
    bmi = profile.get("bmi")
    bmi_label = profile.get("bmi_label")

    system_prompt = (
        "你是一位谨慎、专业、鼓励型的健康主义营养顾问。"
        "你只能基于用户提供的信息和食物识别结果给出一般健康建议，不能做医学诊断。"
        "如用户体脂、年龄、体重等信息缺失，应明确说明不确定性。"
        "请使用中文，语气专业、温和、可执行。"
        "不要返回 JSON、Markdown 代码块或长篇文章。"
        "不要使用 ###、**、项目符号 Markdown 或编号 Markdown。"
        "请输出适合网页卡片展示的简短要点。"
    )
    user_prompt = {
        "task": "根据食物图片识别结果、本地热量分析和用户个人信息，生成个性化饮食建议。",
        "format": (
            "只输出以下 5 个小节，每个小节 1-2 句话或 2 条以内短要点，整体不超过 450 字：\n"
            "身体评估：结合 BMI、体脂、目标说明当前状态。\n"
            "目标策略：围绕用户目标给出最关键的饮食策略。\n"
            "进餐时机：说明训练前后或正餐搭配建议。\n"
            "注意事项：说明不确定性和风险提醒。\n"
            "结论：用一句话总结是否适合当前目标。\n"
            "小节标题必须完全使用上述标题和中文冒号。"
        ),
        "user_profile": {
            "goal": goal,
            "age": profile.get("age"),
            "gender": profile.get("gender"),
            "height_cm": profile.get("height_cm"),
            "weight_kg": profile.get("weight_kg"),
            "body_fat_percent": profile.get("body_fat_percent"),
            "activity_level": profile.get("activity_level"),
            "bmi": bmi,
            "bmi_label": bmi_label,
            "notes": profile.get("notes"),
        },
        "food_recognition": {
            "food_name": result.get("food_name"),
            "display_name": result.get("display_name"),
            "confidence": result.get("confidence"),
            "top_predictions": top_predictions,
        },
        "local_nutrition_per_100g": {
            "calories": nutrition.get("calories"),
            "protein": nutrition.get("protein"),
            "fat": nutrition.get("fat"),
            "carbohydrate": nutrition.get("carbohydrate"),
            "unit": nutrition.get("unit"),
            "category": nutrition.get("category"),
        },
        "local_analysis": {
            "food_intro": result.get("food_intro"),
            "calorie_analysis": result.get("calorie_analysis"),
            "fallback_suggestion": result.get("suggestion"),
        },
    }
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
    ]


@app.post("/llm-advice")
def llm_advice():
    payload = request.get_json(silent=True) or {}
    config = payload.get("config") or {}
    model = (config.get("model") or "").strip()
    api_key = (config.get("api_key") or "").strip()
    temperature = float(config.get("temperature") or 0.35)

    if not model:
        return jsonify({"error": "请填写云端模型名称。"}), 400
    if not api_key:
        return jsonify({"error": "请填写 API Key。"}), 400

    try:
        url = normalize_chat_completions_url(config.get("base_url") or "")
        messages = build_advice_prompt(payload)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    request_body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        upstream = requests.post(url, headers=headers, json=request_body, timeout=(15, 120))
    except requests.RequestException as exc:
        return Response(f"【云端模型连接失败】{exc}", mimetype="text/plain; charset=utf-8", status=502)

    if upstream.status_code >= 400:
        return Response(
            f"【云端模型请求失败】HTTP {upstream.status_code}: {upstream.text[:800]}",
            mimetype="text/plain; charset=utf-8",
            status=502,
        )

    try:
        event = upstream.json()
        content = event["choices"][0]["message"]["content"]
    except Exception:
        content = upstream.text

    return Response(content, mimetype="text/plain; charset=utf-8")


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
        prediction = predict_image(upload_path, topk=5)
        nutrition = get_nutrition_result(prediction["food_name"])
        for item in prediction["top_predictions"]:
            item["display_name"] = get_nutrition_result(item["food_name"])["display_name"]
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
                "category": nutrition["category"],
            },
            "suggestion": nutrition["suggestion"],
            "food_intro": nutrition["food_intro"],
            "calorie_analysis": nutrition["calorie_analysis"],
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
