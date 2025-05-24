# MySoloKeeper - 打灰机✈️守护程序🛡️

<div align="center">

[![GitHub release](https://img.shields.io/github/v/release/RusianHu/MySoloKeeper?style=for-the-badge&logo=github&color=blue)](https://github.com/RusianHu/MySoloKeeper/releases)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/github/license/RusianHu/MySoloKeeper?style=for-the-badge&color=green)](./LICENSE)
[![Stars](https://img.shields.io/github/stars/RusianHu/MySoloKeeper?style=for-the-badge&logo=github&color=yellow)](https://github.com/RusianHu/MySoloKeeper/stargazers)

</div>

利用开源AI视觉模型（smolVLM2）与 MediaPipe 库，提供多种混合检测模式进行实时人类活动检测，守护你的安全

 当程序检测到人形智慧生物，如 <strong> 人类 / 兽人 / 哥布林 / 精灵 / 半身人 / 虎人 / 夺心魔 / 魅魔</strong> 出现时，自动最小化指定的程序窗口。

 ---

<div align="center">
<h1>爽撸开始！</h1>
</div>

![1.png](/image/1.png)

![2.png](/image/2.png)

<details>
<summary><strong>✨ 特性</strong></summary>

- 🎯 **多模式检测**: 支持MediaPipe独立检测、SmolVLM独立检测和混合模式
- 🛡️ **进程守护**: 选择任意运行中的程序进行守护
- 📹 **摄像头监控**: 实时摄像头画面显示，不同颜色框标记检测结果
- 🤖 **MediaPipe检测**: 快速的本地人脸和姿态检测（默认模式）
- 🧠 **SmolVLM检测**: 高精度的AI视觉模型检测
- 🔄 **混合模式**: 结合两种检测方式的优势
- 🔒 **隐私保护**: 可调节摄像头画面模糊度，保护隐私的同时不影响检测功能

</details>

<details>
<summary><strong>📐坐标系统和检测逻辑</strong></summary>

### 坐标系统说明

MySoloKeeper 使用标准的计算机图形坐标系统：

```
图像坐标系：
(0,0) ────────────────→ X轴 (向右)
  │
  │    (x,y)
  │       ┌─────────┐ ← 检测框
  │       │         │   width
  │       │  人类   │   height
  │       │  活动   │
  │       └─────────┘
  │    (x+width, y+height)
  ↓
Y轴 (向下)
```

### 坐标参数详解

- **原点位置**: `(0, 0)` 位于图像的**左上角**
- **X轴方向**: 从左到右 (→)
- **Y轴方向**: 从上到下 (↓)
- **检测框定义**:
  - `x`: 检测框左上角的X坐标
  - `y`: 检测框左上角的Y坐标
  - `width`: 检测框的宽度
  - `height`: 检测框的高度

### 检测逻辑流程

1. **图像捕获**: 从摄像头获取实时画面
2. **尺寸获取**: 自动检测实际图像尺寸
3. **模型推理**: 将图像和尺寸信息发送给SmolVLM进行人类活动检测
4. **坐标解析**: 从模型响应中提取检测坐标
5. **坐标验证**: 验证坐标的有效性和合理性
   - 检查坐标是否为数字类型
   - 验证坐标是否在实际图像范围内
   - 检查检测框大小是否合理
   - 验证宽高比是否符合人类特征
6. **坐标平滑**: 应用平滑算法减少检测抖动
7. **绘制显示**: 在画面上绘制检测框
8. **守护触发**: 如果启用守护且检测到人类，执行守护动作

### 坐标验证规则

- **最小检测尺寸**: 30像素 (宽度和高度)
- **最大检测尺寸**: 实际图像尺寸的95%
- **宽高比范围**: 0.3 - 3.0 (适应不同姿态的人类)
- **坐标范围**: 必须在实际图像尺寸范围内 (动态检测)

### 坐标准确性保证

程序采用多重机制确保坐标的准确性：

1. **动态尺寸检测**: 自动获取实际图像尺寸，避免固定分辨率假设
2. **明确的坐标系统说明**: 在提示词中详细说明坐标系统和要求
3. **实时尺寸传递**: 将实际图像尺寸传递给模型，确保坐标在正确范围内
4. **多层验证**: 对模型返回的坐标进行严格验证和过滤

### 平滑处理算法

为了减少检测抖动，系统采用加权平均算法：

```
平滑坐标 = 当前检测坐标 × 0.3 + 上一帧坐标 × 0.7
```

这样可以保持检测的响应性，同时减少不必要的抖动。

</details>

## 系统要求

- Windows 10/11 64位
- Python 3.8+
- 摄像头设备
- SmolVLM服务运行在 http://localhost:8080
- 正确安装 [llama.cpp](https://github.com/ggml-org/llama.cpp) 并配置好环境变量

## 安装方式

### 步骤一：安装 [llama.cpp](https://github.com/ggml-org/llama.cpp) （二进制文件）

1. 直接用官方的 llama.cpp [GitHub Release 页面](https://github.com/ggml-org/llama.cpp/releases/) 下载已经编译好并支持 CUDA 的 Windows x64 二进制包，里面包含了可执行文件 llama.exe（同目录下还有必要的 DLL）。

2. 注意：官方 Release 里，Windows CUDA 版被拆成了两类资产：

3. `cudart-llama-bin-win-cuda-12.4-x64.zip` 只包含三份 CUDA 运行时的 DLL（cudart64_12.dll, cublas64_12.dll, cublasLt64_12.dll），用于给已经编译好的 llama.exe 提供新版 CUDA 库（12.4） ，`llama-b5464-bin-win-cuda-12.4-x64.zip` 才是完整的二进制包，里面有 `llama.exe` （以此类推）。

### 步骤二：从GitHub下载

1. **克隆仓库**
   ```bash
   git clone https://github.com/RusianHu/MySoloKeeper.git
   cd MySoloKeeper
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
   ```

3. **下载模型文件**（仅在使用SmolVLM功能时需要）
   ```bash
   python download_models.py
   ```

   **重要提醒**：
   - 模型文件需要手动下载到 `models` 文件夹
   - 运行 `download_models.py` 脚本会自动创建 `models` 目录并下载所需的模型文件
   - 模型文件较大（约1-2GB），请确保网络连接稳定
   - 推荐使用huggingface镜像源进行下载
   - `download_models.py` 脚本需要 `huggingface_hub` 库，已包含在 `requirements.txt` 中

4. **运行程序**
   ```bash
   python start.py
   ```

## 快速开始

### 1. 启动SmolVLM服务

确保你的SmolVLM服务已经启动并运行在 `http://localhost:8080`。

### 2. 运行程序

**方法一：手动安装依赖**
```bash
# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 运行程序
python main.py
```

**方法二：使用启动脚本（推荐）**
```bash
python start.py
```

启动脚本会自动：
- 检查Python版本
- 安装缺失的依赖库
- 检查SmolVLM服务状态
- 启动主程序


<details>
<summary><strong>📖 使用说明</strong></summary>

### 基本操作

1. **启动程序**: 运行 `python start.py`
2. **开始检测**: 点击"开始检测"按钮启动摄像头和人类活动检测
3. **选择进程**: 在右侧进程列表中选择要守护的程序
4. **启用守护**: 开启"启用守护"开关
5. **配置设置**: 根据需要调整检测间隔、声音报警等设置

### 界面说明

- **左侧面板**: 摄像头显示区域和检测控制
- **右侧面板**: 进程管理、守护设置和程序配置
- **状态栏**: 显示程序运行状态和SmolVLM连接状态

### 功能详解

#### 人类活动检测

**检测模式**：
- **MediaPipe独立检测**（默认）：使用本地MediaPipe进行快速人脸和姿态检测
- **SmolVLM独立检测**：使用AI视觉模型进行高精度人类活动检测
- **混合模式**：SmolVLM主检测 + MediaPipe验证，提供最高准确性

**检测框颜色**：
- 绿色框：MediaPipe检测结果（人脸和姿态）
- 蓝色框：SmolVLM检测结果（人类活动）
- 彩色骨骼线：MediaPipe姿态检测结果

**特性**：
- 支持多人的同时检测
- 智能坐标平滑，减少检测抖动
- 实时模式切换，无需重启程序

#### 进程守护
- 自动扫描所有有窗口的运行进程
- 支持选择任意程序进行守护
- 检测到人类活动时自动最小化目标程序窗口

#### 声音报警
- 检测到人类活动时播放柔和的和弦音提醒
- 支持系统声音和自定义音频文件
- 可在设置中启用/禁用

#### 隐私保护
- **摄像头模糊度调节**: 在摄像头区域下方提供模糊度滑块
- **前端模糊**: 只影响用户界面显示，不影响后台检测功能
- **实时调节**: 可随时调整模糊程度，范围0-20
- **隐私友好**: 在保持检测功能的同时保护用户隐私

</details>

<details>
<summary><strong>⚙️ 配置选项</strong></summary>

### 检测模式选择
- **MediaPipe独立检测**：快速本地检测，无需网络连接，适合日常使用
- **SmolVLM独立检测**：高精度AI检测，需要SmolVLM服务运行
- **混合模式**：结合两种检测方式，提供最高准确性

### 检测间隔
- 范围：0.1-5.0秒
- 建议：1.0秒（平衡性能和响应速度）
- MediaPipe模式可以使用更短间隔（如0.1-0.5秒）
- SmolVLM模式建议使用较长间隔（如1.0-2.0秒）

<details>
<summary><strong>📋 MediaPipe 辅助检测配置详解</strong></summary>

#### 🔧 配置参数说明

在 `config.py` 文件中，您可以调整以下MediaPipe辅助检测参数：

##### 基础配置
```python
USE_MEDIAPIPE = True  # 是否启用 MediaPipe 辅助检测
MEDIAPIPE_CONFIDENCE = 0.5  # MediaPipe 检测置信度阈值
```

##### 辅助检测参数

**1. 人脸重叠度阈值**
```python
MEDIAPIPE_FACE_OVERLAP_THRESHOLD = 0.3  # 范围: 0.0-1.0
```
- **作用**: 判断SmolVLM检测框与MediaPipe人脸的重叠程度
- **数值含义**: 0.3 = 30%的人脸区域与检测框重叠
- **调整建议**:
  - 降低 (如0.2): 更容易通过人脸验证，更敏感
  - 提高 (如0.5): 需要更高重叠度才通过验证，更严格

**2. 姿态存在度阈值**
```python
MEDIAPIPE_POSE_PRESENCE_THRESHOLD = 0.3  # 范围: 0.0-1.0
```
- **作用**: 判断检测框内人体关键点的比例
- **数值含义**: 0.3 = 30%的可见关键点在检测框内
- **调整建议**:
  - 降低 (如0.2): 更容易通过姿态验证
  - 提高 (如0.5): 需要更多关键点才通过验证

**3. 置信度调整幅度**
```python
MEDIAPIPE_CONFIDENCE_BOOST = 0.2    # 验证通过时的置信度提升
MEDIAPIPE_CONFIDENCE_PENALTY = 0.1  # 验证失败时的置信度降低
```
- **作用**: 控制MediaPipe验证对最终置信度的影响

**4. 最终过滤阈值**
```python
MEDIAPIPE_FINAL_CONFIDENCE_THRESHOLD = 0.3  # 范围: 0.0-1.0
```
- **作用**: 只保留置信度高于此值的检测结果

#### 🎛️ 常用调整场景

**检测太敏感，误报较多**
```python
MEDIAPIPE_FACE_OVERLAP_THRESHOLD = 0.4      # 提高人脸阈值
MEDIAPIPE_POSE_PRESENCE_THRESHOLD = 0.4     # 提高姿态阈值
MEDIAPIPE_FINAL_CONFIDENCE_THRESHOLD = 0.4  # 提高最终阈值
```

**检测不够敏感，漏检较多**
```python
MEDIAPIPE_FACE_OVERLAP_THRESHOLD = 0.2      # 降低人脸阈值
MEDIAPIPE_POSE_PRESENCE_THRESHOLD = 0.2     # 降低姿态阈值
MEDIAPIPE_FINAL_CONFIDENCE_THRESHOLD = 0.2  # 降低最终阈值
```

**更依赖人脸检测**
```python
MEDIAPIPE_FACE_OVERLAP_THRESHOLD = 0.2      # 降低人脸阈值
MEDIAPIPE_POSE_PRESENCE_THRESHOLD = 0.5     # 提高姿态阈值
```

**更依赖姿态检测**
```python
MEDIAPIPE_FACE_OVERLAP_THRESHOLD = 0.5      # 提高人脸阈值
MEDIAPIPE_POSE_PRESENCE_THRESHOLD = 0.2     # 降低姿态阈值
```

#### 📊 实时监控

程序运行时会在控制台输出验证信息：
```
MediaPipe验证通过: 人脸0.35, 姿态0.54
MediaPipe验证失败: 人脸0.12, 姿态0.23
```

通过观察这些数值，您可以了解：
- 当前检测的准确性
- 是否需要调整阈值
- 哪种检测方式更有效

#### ⚡ 性能考虑

- MediaPipe检测会增加一定的计算开销
- 如果性能不足，可以考虑：
  1. 设置 `USE_MEDIAPIPE = False` 禁用辅助检测
  2. 增加检测间隔时间
  3. 降低摄像头分辨率

**注意**: 修改配置文件后，需要重启程序才能生效。

</details>

### 声音报警
- 启用后检测到人类活动时播放柔和的和弦音
- 支持自定义音频文件（放置alert.wav文件）

### 主题设置
- **跟随系统**: 自动根据系统主题切换深色/浅色模式
- **浅色主题**: 明亮的界面风格，适合白天使用
- **深色主题**: 护眼的暗色界面，适合夜间使用
- 通过菜单栏 "设置" → "主题" 进行切换

### MediaPipe独立模式触发标准
可在 `config.py` 中调整以下参数：

```python
# MediaPipe 独立模式触发标准
MEDIAPIPE_ONLY_FACE_CONFIDENCE_THRESHOLD = 0.6  # 人脸检测置信度阈值
MEDIAPIPE_ONLY_POSE_VISIBILITY_THRESHOLD = 0.5   # 姿态关键点可见度阈值
MEDIAPIPE_ONLY_MIN_POSE_LANDMARKS = 5            # 最少需要的可见姿态关键点数量
MEDIAPIPE_ONLY_REQUIRE_BOTH = False              # 是否需要同时检测到人脸和姿态才触发守护
```

**参数说明**：
- `MEDIAPIPE_ONLY_FACE_CONFIDENCE_THRESHOLD`: 人脸检测的最低置信度，越高越严格
- `MEDIAPIPE_ONLY_POSE_VISIBILITY_THRESHOLD`: 姿态关键点的最低可见度，越高越严格
- `MEDIAPIPE_ONLY_MIN_POSE_LANDMARKS`: 需要检测到的最少姿态关键点数量
- `MEDIAPIPE_ONLY_REQUIRE_BOTH`: 设为True时需要同时检测到人脸和姿态才触发守护

</details>

## 使用方法

1. **启动程序**：
   ```bash
   python start.py
   ```
   或直接运行：
   ```bash
   python main.py
   ```

2. **选择检测模式**（启动时）：
   - **选项1：MediaPipe独立检测**（推荐）：快速、稳定、无需额外配置
   - **选项2：包含SmolVLM检测**：自动启动SmolVLM服务，提供高精度AI检测

3. **界面内检测模式**：
   - **MediaPipe独立检测**：快速本地检测
   - **SmolVLM独立检测**：高精度AI检测
   - **混合模式**：最高精度，结合两种检测方式

4. **选择要守护的进程**：
   - 点击"刷新进程列表"
   - 从列表中选择要守护的程序
   - 点击"选择进程"

5. **开始检测**：
   - 点击"开始检测"按钮
   - 程序将开始监控摄像头画面
   - 观察检测框颜色：绿色=MediaPipe，蓝色=SmolVLM

6. **启用守护**：
   - 确保已选择进程并开始检测
   - 开启"启用守护"开关

7. **调整设置**：
   - 调节检测间隔滑块
   - 调节摄像头模糊度（隐私保护）
   - 开启/关闭声音报警
   - 实时切换检测模式

### 启动示例

**推荐方式（MediaPipe模式）**：
```bash
python start.py
# 选择 1 或直接按回车，程序将以MediaPipe独立检测模式启动
```

**包含SmolVLM功能**：
```bash
python start.py
# 选择 2，程序会检查SmolVLM服务状态
# 如果服务未运行，可以选择：
# 1. 自动启动SmolVLM服务（推荐）- 程序会自动在新窗口启动服务
# 2. 手动启动服务后重新运行
# 3. 继续启动程序，稍后切换模式
# 4. 使用MediaPipe模式
```

**直接启动（跳过选择）**：
```bash
python main.py
# 直接启动程序，默认MediaPipe模式，可在界面中切换
```

## 文件结构

```
MySoloKeeper/
├── main.py                 # 主程序入口
├── start.py                # 启动脚本
├── gui.py                  # 图形界面模块
├── camera_handler.py       # 摄像头处理模块
├── smolvlm_client.py      # SmolVLM API客户端
├── process_manager.py      # 进程管理模块
├── coordinate_processor.py # 坐标处理和平滑模块
├── audio_manager.py        # 声音管理模块
├── config.py              # 配置文件
├── requirements.txt       # 依赖列表
├── README.md              # 说明文档
└── models/                # SmolVLM模型文件目录
```

## 故障排除

### 常见问题

1. **摄像头无法启动**
   - 检查摄像头是否被其他程序占用
   - 确认摄像头权限设置
   - 尝试更换摄像头索引

2. **SmolVLM连接失败**
   - 确认SmolVLM服务正在运行
   - 检查端口8080是否被占用
   - 查看防火墙设置

3. **进程最小化失败**
   - 确认已安装pywin32库
   - 检查目标程序是否有管理员权限
   - 某些全屏程序可能无法最小化

4. **声音无法播放**
   - 检查系统音频设置
   - 确认pygame库正确安装
   - 尝试使用系统声音模式

### 性能优化

**检测模式选择**：
- **低配置设备**：使用MediaPipe独立检测，间隔0.5-1.0秒
- **中等配置设备**：使用SmolVLM独立检测，间隔1.0-2.0秒
- **高配置设备**：使用混合模式，间隔0.5-1.0秒

**其他优化**：
- 适当调整检测间隔以平衡性能和响应速度
- 确保摄像头分辨率设置合理（默认640x480）
- 关闭不必要的后台程序以释放系统资源

## 许可证

本项目采用 [MIT](./LICENSE) 许可证。
