const imageInput = document.querySelector("#imageInput");
const previewImage = document.querySelector("#previewImage");
const previewBox = document.querySelector(".preview-box");
const emptyPreview = document.querySelector("#emptyPreview");
const predictButton = document.querySelector("#predictButton");
const statusText = document.querySelector("#statusText");
const modelInfoText = document.querySelector("#modelInfoText");
const baseUrlInput = document.querySelector("#baseUrlInput");
const cloudModelInput = document.querySelector("#cloudModelInput");
const temperatureInput = document.querySelector("#temperatureInput");
const apiKeyInput = document.querySelector("#apiKeyInput");
const saveConfigButton = document.querySelector("#saveConfigButton");

const foodName = document.querySelector("#foodName");
const confidence = document.querySelector("#confidence");
const calories = document.querySelector("#calories");
const protein = document.querySelector("#protein");
const fat = document.querySelector("#fat");
const carbohydrate = document.querySelector("#carbohydrate");
const unitText = document.querySelector("#unitText");
const foodIntro = document.querySelector("#foodIntro");
const calorieAnalysis = document.querySelector("#calorieAnalysis");
const suggestion = document.querySelector("#suggestion");
const structuredAdvice = document.querySelector("#structuredAdvice");
const topPredictions = document.querySelector("#topPredictions");
const adviceButton = document.querySelector("#adviceButton");
const goalInput = document.querySelector("#goalInput");
const genderInput = document.querySelector("#genderInput");
const ageInput = document.querySelector("#ageInput");
const heightInput = document.querySelector("#heightInput");
const weightInput = document.querySelector("#weightInput");
const bodyFatInput = document.querySelector("#bodyFatInput");
const activityInput = document.querySelector("#activityInput");
const notesInput = document.querySelector("#notesInput");
const bmiText = document.querySelector("#bmiText");

let selectedFile = null;
let latestResult = null;

loadCloudConfig();
loadModelInfo();

imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  selectedFile = file || null;

  if (!selectedFile) {
    previewImage.hidden = true;
    emptyPreview.hidden = false;
    previewBox.classList.remove("has-image");
    return;
  }

  const imageUrl = URL.createObjectURL(selectedFile);
  previewImage.src = imageUrl;
  previewImage.hidden = false;
  emptyPreview.hidden = true;
  previewBox.classList.add("has-image");
  statusText.textContent = "图片已选择，可以开始识别。";
});

saveConfigButton.addEventListener("click", () => {
  saveCloudConfig();
  statusText.textContent = "云端模型配置已保存到本机浏览器。";
});

[heightInput, weightInput].forEach((input) => {
  input.addEventListener("input", updateBmiText);
});

predictButton.addEventListener("click", async () => {
  if (!selectedFile) {
    statusText.textContent = "请先选择或拍摄一张食物图片。";
    return;
  }

  const formData = new FormData();
  formData.append("image", selectedFile);

  predictButton.disabled = true;
  statusText.textContent = "正在识别，请稍候...";

  try {
    const response = await fetch("/predict", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "识别失败");
    }

    latestResult = data;
    renderResult(data);
    statusText.textContent = "识别完成。";
  } catch (error) {
    statusText.textContent = error.message;
  } finally {
    predictButton.disabled = false;
  }
});

adviceButton.addEventListener("click", async () => {
  if (!latestResult) {
    suggestion.textContent = "请先上传图片并完成识别。";
    return;
  }

  const config = readCloudConfig();
  if (!config.base_url || !config.model || !config.api_key) {
    suggestion.textContent = "请先在右上角填写 Base URL、模型名称和 API Key。";
    return;
  }

  adviceButton.disabled = true;
  structuredAdvice.hidden = true;
  structuredAdvice.innerHTML = "";
  suggestion.hidden = false;
  suggestion.textContent = "正在生成要点建议...";
  statusText.textContent = "正在调用云端模型生成要点建议...";

  try {
    const response = await fetch("/llm-advice", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        config,
        profile: collectProfile(),
        result: latestResult,
      }),
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || "云端模型调用失败");
    }

    const fullText = await response.text();
    renderAdviceCards(parseAdviceSections(fullText));
    suggestion.hidden = true;
    statusText.textContent = "AI 饮食建议生成完成。";
  } catch (error) {
    suggestion.hidden = false;
    suggestion.textContent = error.message;
    statusText.textContent = "生成建议失败。";
  } finally {
    adviceButton.disabled = false;
  }
});

function renderResult(data) {
  foodName.textContent = data.display_name;
  confidence.textContent = `${(data.confidence * 100).toFixed(1)}%`;

  calories.textContent = data.nutrition.calories;
  protein.textContent = data.nutrition.protein;
  fat.textContent = data.nutrition.fat;
  carbohydrate.textContent = data.nutrition.carbohydrate;
  unitText.textContent = `${data.nutrition.category || "未分类"} | ${data.nutrition.unit}`;
  suggestion.textContent = data.suggestion;
  suggestion.hidden = false;
  structuredAdvice.hidden = true;
  structuredAdvice.innerHTML = "";
  foodIntro.textContent = data.food_intro || "暂无食物介绍。";
  calorieAnalysis.textContent = data.calorie_analysis || "暂无热量分析。";

  topPredictions.innerHTML = "";
  data.top_predictions.forEach((item) => {
    const li = document.createElement("li");
    const name = document.createElement("span");
    name.className = "prediction-name";
    name.textContent = item.display_name || item.food_name;
    const confidence = document.createElement("strong");
    confidence.className = "prediction-score";
    confidence.textContent = `${(item.confidence * 100).toFixed(1)}%`;
    li.append(name, confidence);
    topPredictions.appendChild(li);
  });
}

function collectProfile() {
  const bmi = calculateBmi();
  return {
    goal: goalInput.value,
    gender: genderInput.value,
    age: numberOrNull(ageInput.value),
    height_cm: numberOrNull(heightInput.value),
    weight_kg: numberOrNull(weightInput.value),
    body_fat_percent: numberOrNull(bodyFatInput.value),
    activity_level: activityInput.value,
    notes: notesInput.value.trim(),
    bmi: bmi ? Number(bmi.value.toFixed(1)) : null,
    bmi_label: bmi ? bmi.label : "未知",
  };
}

function numberOrNull(value) {
  const number = Number(value);
  return Number.isFinite(number) && value !== "" ? number : null;
}

function calculateBmi() {
  const height = numberOrNull(heightInput.value);
  const weight = numberOrNull(weightInput.value);
  if (!height || !weight) {
    return null;
  }
  const bmi = weight / (height / 100) ** 2;
  let label = "正常";
  if (bmi < 18.5) {
    label = "偏瘦";
  } else if (bmi < 24) {
    label = "正常";
  } else if (bmi < 28) {
    label = "超重";
  } else {
    label = "肥胖";
  }
  return { value: bmi, label };
}

function updateBmiText() {
  const bmi = calculateBmi();
  bmiText.classList.remove("bmi-normal", "bmi-warning", "bmi-danger");
  if (!bmi) {
    bmiText.textContent = "填写身高和体重后自动计算 BMI。";
    return;
  }
  const className = bmi.label === "正常" ? "bmi-normal" : bmi.label === "超重" || bmi.label === "肥胖" ? "bmi-danger" : "bmi-warning";
  bmiText.classList.add(className);
  bmiText.textContent = `BMI：${bmi.value.toFixed(1)}，状态：${bmi.label}。`;
}

function readCloudConfig() {
  return {
    base_url: baseUrlInput.value.trim(),
    model: cloudModelInput.value.trim(),
    api_key: apiKeyInput.value.trim(),
    temperature: Number(temperatureInput.value || 0.3),
  };
}

function saveCloudConfig() {
  localStorage.setItem("foodCalorieCloudConfig", JSON.stringify(readCloudConfig()));
}

function loadCloudConfig() {
  const raw = localStorage.getItem("foodCalorieCloudConfig");
  if (!raw) {
    baseUrlInput.value = "https://api.openai.com/v1";
    cloudModelInput.value = "gpt-4.1-mini";
    return;
  }
  try {
    const config = JSON.parse(raw);
    baseUrlInput.value = config.base_url || "https://api.openai.com/v1";
    cloudModelInput.value = config.model || "gpt-4.1-mini";
    apiKeyInput.value = config.api_key || "";
    temperatureInput.value = config.temperature ?? 0.3;
  } catch (error) {
    baseUrlInput.value = "https://api.openai.com/v1";
    cloudModelInput.value = "gpt-4.1-mini";
  }
}

function parseJsonObject(text) {
  const cleaned = text
    .replace(/^```json/i, "")
    .replace(/^```/i, "")
    .replace(/```$/i, "")
    .trim();
  try {
    return JSON.parse(cleaned);
  } catch (error) {
    const start = cleaned.indexOf("{");
    const end = cleaned.lastIndexOf("}");
    if (start >= 0 && end > start) {
      try {
        return JSON.parse(cleaned.slice(start, end + 1));
      } catch (innerError) {
        return null;
      }
    }
    return null;
  }
}

function renderStructuredAdvice(data) {
  structuredAdvice.innerHTML = "";
  structuredAdvice.hidden = false;

  addAdviceSection("食物画像", [
    data.food_profile?.detailed_intro,
    data.food_profile?.confidence_note,
  ]);
  addAdviceSection("身体评估", [
    `BMI：${data.body_assessment?.bmi ?? "未知"}（${data.body_assessment?.bmi_label ?? "未知"}）`,
    data.body_assessment?.profile_summary,
  ]);
  addAdviceSection("热量判断", [
    data.calorie_analysis?.per_100g,
    data.calorie_analysis?.portion_guidance,
  ]);
  addAdviceSection("目标策略", data.goal_strategy);
  addAdviceSection("进餐时机", data.meal_timing);
  addAdviceSection("注意事项", data.cautions);
  addAdviceSection("一句话总结", [data.one_sentence_summary]);
}

function parseAdviceSections(text) {
  const cleanedText = cleanAdviceText(text);
  const fallback = [
    { title: "分析", items: [cleanedText || "暂未生成有效建议。"] },
  ];
  if (!cleanedText) {
    return fallback;
  }

  const titles = ["身体评估", "目标策略", "进餐时机", "注意事项", "结论"];
  let normalized = cleanedText.replace(/\r/g, "").trim();
  titles.forEach((title) => {
    normalized = normalized.replace(new RegExp(`${title}\\s*[-—]\\s*`, "g"), `${title}：`);
  });

  const matches = titles
    .map((title) => {
      const match = normalized.match(new RegExp(`${title}\\s*[：:]`));
      return match ? { title, index: match.index, markerLength: match[0].length } : null;
    })
    .filter(Boolean)
    .sort((a, b) => a.index - b.index);

  const sections = matches.map((match, index) => {
    const start = match.index + match.markerLength;
    const end = matches[index + 1]?.index ?? normalized.length;
    const body = normalized.slice(start, end).trim();
    if (!body) {
      return null;
    }
    return {
      title: match.title,
      items: body
        .replace(/#{1,6}/g, "")
        .replace(/\*\*/g, "")
        .split(/\n+|[；;]/)
        .map((item) => item.replace(/^[-•\d.、\s]+/, "").trim())
        .filter(Boolean)
        .slice(0, 3),
    };
  }).filter(Boolean);

  return sections.length ? sections : fallback;
}

function cleanAdviceText(text) {
  return (text || "")
    .replace(/\r/g, "")
    .replace(/```[\s\S]*?```/g, "")
    .replace(/#{1,6}\s*/g, "")
    .replace(/\*\*/g, "")
    .replace(/^\s*[-•]\s*/gm, "")
    .trim();
}

function renderAdviceCards(sections) {
  structuredAdvice.innerHTML = "";
  structuredAdvice.hidden = false;
  sections.forEach((section) => addAdviceSection(section.title, section.items));
}

function addAdviceSection(title, items) {
  const filtered = (Array.isArray(items) ? items : [items]).filter(Boolean);
  if (!filtered.length) {
    return;
  }

  const section = document.createElement("section");
  section.className = `advice-section ${getAdviceClass(title)}`;
  const heading = document.createElement("h3");
  const icon = document.createElement("span");
  icon.className = "advice-icon";
  icon.textContent = getAdviceIcon(title);
  const titleText = document.createElement("span");
  titleText.textContent = title;
  heading.append(icon, titleText);
  section.appendChild(heading);

  if (filtered.length === 1) {
    const paragraph = document.createElement("p");
    paragraph.textContent = filtered[0];
    section.appendChild(paragraph);
  } else {
    const list = document.createElement("ul");
    filtered.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      list.appendChild(li);
    });
    section.appendChild(list);
  }
  structuredAdvice.appendChild(section);
}

function getAdviceClass(title) {
  const classMap = {
    身体评估: "advice-body",
    目标策略: "advice-goal",
    进餐时机: "advice-timing",
    注意事项: "advice-caution",
    结论: "advice-summary",
  };
  return classMap[title] || "advice-default";
}

function getAdviceIcon(title) {
  const iconMap = {
    身体评估: "⟳",
    目标策略: "✓",
    进餐时机: "◷",
    注意事项: "!",
    结论: "◆",
  };
  return iconMap[title] || "•";
}

async function loadModelInfo() {
  if (!modelInfoText) {
    return;
  }

  try {
    const response = await fetch("/model-info");
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "模型信息读取失败");
    }

    modelInfoText.textContent = `当前模型：${data.num_classes} 类，输入尺寸 ${data.image_size}，运行设备 ${data.device}。`;
  } catch (error) {
    modelInfoText.textContent = "当前模型信息暂不可用，请确认后端服务和模型文件已准备好。";
  }
}
