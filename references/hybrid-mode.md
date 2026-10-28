# 混合模式：原片保留 + 自制段落（hybrid-mode）

路线 B 完整参考。适用于：参考片本身质量高需完整保留（含原声），用户要求"在这个视频基础上"追加品牌/图标相关的自制段落，做成某软件的启动动画。

## 目录
1. [流程总览](#流程总览)
2. [Step B1 原片规格适配](#step-b1-原片规格适配)
3. [Step B2 品牌/图标特征提取](#step-b2-品牌图标特征提取)
4. [Step B3 AI 生成同画风主画面](#step-b3-ai-生成同画风主画面)
5. [Step B4 程序叠加动态元素](#step-b4-程序叠加动态元素)
6. [Step B5 音效设计与合成](#step-b5-音效设计与合成)
7. [Step B6 拼接与衔接细节](#step-b6-拼接与衔接细节)
8. [实战案例时间轴](#实战案例时间轴)

## 流程总览

```
参考视频 ─► B1 原片适配(1080p/30fps) ─┐
品牌图标 ─► B2 特征提取(形状/配色)     ├─► B6 拼接(视频concat+音频concat) ─► 成品
风格分析 ─► B3 AI生成同画风主画面      │
            B4 程序叠加动态元素(逐帧)  ─┤
            B5 合成音效(make_sfx.py)  ─┘
```

## Step B1 原片规格适配

目标规格：1920×1080 / 30fps / yuv420p（与自制段一致，便于拼接）。

```bash
# 非标准比例直接拉伸（形变 <1% 不可见）；保留音轨转 AAC
ffmpeg -y -i ref.mp4 -vf "scale=1920:1080,fps=30" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -ar 44100 -ac 2 part1.mp4
```

注意记录原片时长 `T1`（自制段起点）与结尾画面亮度/内容（决定衔接方式）。

## Step B2 品牌/图标特征提取

目标是拿到"形状语言 + 配色"供 AI 生图与程序绘制：

- **优先向用户索要品牌 logo 图**（PNG/SVG）——最通用可靠；
- Windows 下可从 exe 提取：`[System.Drawing.Icon]::ExtractAssociatedIcon("app.exe")`（PowerShell）；
- 用视觉模型分析图标，输出：主体形状与构图、具体色值（如 `#28D0FF→#3B2BE8` 渐变）、内部细节、风格关键词。

## Step B3 AI 生成同画风主画面

用所在环境的图像生成能力，prompt 构造公式：

```
[原片风格关键词（来自 Step 1 分析）] + [品牌图标形状与配色] + [构图指令：主体居中、
圆环/刻度等呼应元素] + [质感指令：平涂/硬光影/做旧纹理] + [负面约束：画面无文字]
```

示例（二次元 PV 案例）：二次元动漫赛璐璐风格，深墨蓝做旧背景，画面正中巨大的发光抽象 A 标志，青蓝到靛紫弥散渐变自发光，右上四角星芒，外围水墨缺角日食圆环与几何刻度线，黑色羽毛点缀，高对比硬光影，画面干净无任何文字。

规格建议：生成 2K~4K 横图（如 3840×2160），为 Ken Burns 留裁切余量。

## Step B4 程序叠加动态元素

以生成图为底，逐帧渲染自制段（骨架与技法见 references/rendering.md），常用叠加：

| 元素 | 实现 |
|---|---|
| Ken Burns 缓推 | 按 `s: 1.06→1.00` 缩放裁切中心窗口再 resize 回目标尺寸 |
| 光晕呼吸 | glow sprite 以 `alpha = a0 + a1*sin(wt)` 叠加在主体位置 |
| 旋转刻度环 | 双圈 tick 线，正/反相位旋转，低不透明度 |
| 星芒闪烁 | 十字细线 + 中心点，长度与 alpha 随 sin 抖动 |
| 羽毛/粒子飘落 | 固定 x、y 循环下落 + 旋转多边形 |
| 故障风标题 | 文字先以红/蓝 RGB 偏移帧出现，随后白色定格；上下配红蓝波形条（随机高度逐帧抖动） |
| 衔接淡入 | 首帧覆盖与原片结尾同亮度的纯色层，0.15~0.2s 淡出 |
| 收尾闪白 | 末段 0.15~0.2s 轻度过曝（配合启动器窗口淡入） |

标题布局建议：主标题避开主体图形，置于画面下方 1/4 处；副标题（中文/标语）再下一行。

## Step B5 音效设计与合成

用 `scripts/make_sfx.py`（配方详见 references/audio-sfx.md）：

```bash
python scripts/make_sfx.py --out sfx.wav --dur 2.0 --riser --ding --impact
```

设计原则：与原片音乐情绪衔接（原片淡出 → riser 接力 → 标题时刻 ding → 收尾 impact），总长与自制段一致。

## Step B6 拼接与衔接细节

```bash
# 自制段帧序列 -> part2.mp4
ffmpeg -y -framerate 30 -i frames/e%04d.jpg -c:v libx264 -crf 18 -pix_fmt yuv420p part2.mp4

# 视频 concat + 原声与音效 concat
ffmpeg -y -i part1.mp4 -i part2.mp4 -i sfx.wav -filter_complex \
  "[0:v][1:v]concat=n=2:v=1:a=0[outv];\
   [0:a]aresample=44100,aformat=channel_layouts=stereo[a0];\
   [a0][2:a]concat=n=2:v=0:a=1[outa]" \
  -map "[outv]" -map "[outa]" -c:v libx264 -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart output/final.mp4
```

衔接细节清单：
- 自制段首帧亮度 ≈ 原片结尾帧亮度（如原片淡出到深灰，则从同灰度淡入）；
- 视频/音频两路总时长对齐（误差 <0.1s）；
- 原片尾部若是淡出黑/灰帧，插入点选在完全淡出之后；
- 终检抽帧拼图，逐格核对：原片完整、插入点无跳帧、标题无缺失、结尾正常。

## 实战案例时间轴

《二次元 PV + TeleAgent 图标段》（10.33s 原片 + 2.0s 自制 = 12.33s）：

| 时间 | 内容 |
|---|---|
| 0–10.33 | 原片完整保留（1080p30 适配，原声保留） |
| 10.33–11.0 | 黑场淡入 → 图标主画面（Ken Burns + 光晕呼吸 + 刻度环 + 羽毛 + 星芒） |
| 11.0–11.6 | 标题故障帧（红蓝 RGB 偏移）→ 白色定格 + 副标浮现 + 波形条 |
| 11.6–12.15 | 全元素稳定展示（音效 impact 落点 11.7） |
| 12.15–12.33 | 轻度闪白（配合启动器真实窗口淡入） |

部署参数（详见 references/boot-deploy.md）：`T=12.33` → HoldAt=8.6、TransitionStart=11.0、TransitionEnd=12.0，ScreenFrames 起点矩形对准画面中心图标。
