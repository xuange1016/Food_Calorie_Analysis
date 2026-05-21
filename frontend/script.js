const imageInput = document.querySelector("#imageInput");
const previewImage = document.querySelector("#previewImage");
const emptyPreview = document.querySelector("#emptyPreview");
const predictButton = document.querySelector("#predictButton");
const statusText = document.querySelector("#statusText");

const foodName = document.querySelector("#foodName");
const confidence = document.querySelector("#confidence");
const calories = document.querySelector("#calories");
const protein = document.querySelector("#protein");
const fat = document.querySelector("#fat");
const carbohydrate = document.querySelector("#carbohydrate");
const unitText = document.querySelector("#unitText");
const suggestion = document.querySelector("#suggestion");
const topPredictions = document.querySelector("#topPredictions");

let selectedFile = null;

imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  selectedFile = file || null;

  if (!selectedFile) {
    previewImage.hidden = true;
    emptyPreview.hidden = false;
    return;
  }

  const imageUrl = URL.createObjectURL(selectedFile);
  previewImage.src = imageUrl;
  previewImage.hidden = false;
  emptyPreview.hidden = true;
  statusText.textContent = "图片已选择，可以开始识别。";
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

    renderResult(data);
    statusText.textContent = "识别完成。";
  } catch (error) {
    statusText.textContent = error.message;
  } finally {
    predictButton.disabled = false;
  }
});

function renderResult(data) {
  foodName.textContent = `${data.display_name} (${data.food_name})`;
  confidence.textContent = `${(data.confidence * 100).toFixed(1)}%`;

  calories.textContent = data.nutrition.calories;
  protein.textContent = data.nutrition.protein;
  fat.textContent = data.nutrition.fat;
  carbohydrate.textContent = data.nutrition.carbohydrate;
  unitText.textContent = data.nutrition.unit;
  suggestion.textContent = data.suggestion;

  topPredictions.innerHTML = "";
  data.top_predictions.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = `${item.food_name}: ${(item.confidence * 100).toFixed(1)}%`;
    topPredictions.appendChild(li);
  });
}
