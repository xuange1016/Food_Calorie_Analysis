param(
    [string]$CondaEnv = "food-calorie",
    [int]$Epochs = 30,
    [int]$BatchSize = 32,
    [int]$NumWorkers = 4,
    [double]$LearningRate = 0.001
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RunDir = Join-Path $Root "training_runs\food101_101class"
$LogDir = Join-Path $RunDir "logs"
$CheckpointDir = Join-Path $RunDir "checkpoints"
$DataDir = Join-Path $Root "data\food101_101class"
$ClassNamesPath = Join-Path $RunDir "class_names_101.json"
$ModelPath = Join-Path $RunDir "food_model_101class.pth"
$HistoryPath = Join-Path $RunDir "training_history.json"
$MetricsPath = Join-Path $RunDir "evaluation_metrics.json"
$ReportPath = Join-Path $RunDir "Food101_101class_training_report.md"
$DatasetSummary = Join-Path $DataDir "dataset_summary.json"

New-Item -ItemType Directory -Path $RunDir -Force | Out-Null
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
New-Item -ItemType Directory -Path $CheckpointDir -Force | Out-Null

function Invoke-Logged {
    param(
        [string]$StepName,
        [string[]]$CommandArgs,
        [string]$LogPath
    )

    Write-Host "[$StepName] 开始"
    & conda run -n $CondaEnv python @CommandArgs 2>&1 | Tee-Object -FilePath $LogPath
    if ($LASTEXITCODE -ne 0) {
        throw "[$StepName] 失败，退出码: $LASTEXITCODE"
    }
    Write-Host "[$StepName] 完成"
}

Invoke-Logged `
    -StepName "prepare-dataset" `
    -LogPath (Join-Path $LogDir "01_prepare_dataset.log") `
    -CommandArgs @(
        (Join-Path $Root "training\dataset_prepare.py"),
        "--raw-dir", (Join-Path $Root "data\food-101"),
        "--output-dir", $DataDir,
        "--all-classes",
        "--class-names-output", $ClassNamesPath,
        "--val-ratio", "0.2",
        "--seed", "42"
    )

Invoke-Logged `
    -StepName "train" `
    -LogPath (Join-Path $LogDir "02_train.log") `
    -CommandArgs @(
        (Join-Path $Root "training\train.py"),
        "--data-dir", $DataDir,
        "--model-path", $ModelPath,
        "--class-names", $ClassNamesPath,
        "--epochs", "$Epochs",
        "--batch-size", "$BatchSize",
        "--image-size", "224",
        "--lr", "$LearningRate",
        "--num-workers", "$NumWorkers",
        "--checkpoint-dir", $CheckpointDir,
        "--history-path", $HistoryPath,
        "--auto-resume",
        "--amp"
    )

Invoke-Logged `
    -StepName "evaluate" `
    -LogPath (Join-Path $LogDir "03_evaluate.log") `
    -CommandArgs @(
        (Join-Path $Root "training\evaluate.py"),
        "--data-dir", $DataDir,
        "--model-path", $ModelPath,
        "--batch-size", "$BatchSize",
        "--num-workers", "$NumWorkers",
        "--metrics-path", $MetricsPath
    )

Invoke-Logged `
    -StepName "report" `
    -LogPath (Join-Path $LogDir "04_report.log") `
    -CommandArgs @(
        (Join-Path $Root "training\build_training_report.py"),
        "--history", $HistoryPath,
        "--metrics", $MetricsPath,
        "--dataset-summary", $DatasetSummary,
        "--output", $ReportPath,
        "--model-path", $ModelPath
    )

Write-Host "全部完成。报告路径: $ReportPath"
