---
name: video-style-clone
description: 效仿用户提供的参考视频，分析其类型、风格、节奏与叙事结构，用 Python+PIL 程序化逐帧渲染并合成一条同类型新视频（MG 动画、概念广告、片头、启动动画等），支持点阵、线稿扫描、AI 检测框、数字雨、粒子、神经网络球等风格技法，并可部署为软件启动动画。触发场景：用户提供视频路径并要求"效仿这个视频 / 照着做一个同类型的 / 仿照这个风格做动画 / 做一个类似的视频"，或要求把视频设为软件启动画面。全程本地处理，无需上传素材。
name_cn: 效仿视频创作
description_cn: 给我一段参考视频，我先看懂它的类型与风格，再用代码逐帧绘制一条同类型的新视频（如复古点阵 MG 动画、概念广告、启动动画），全程本地完成，还能直接部署为软件启动画面。
create_source: super-agent-skill-creator
---

# 效仿视频创作（Video Style Clone）

## 总览

用户提供一段参考视频，产出一条同类型、同风格的新视频 MP4（默认 1920×1080 / 30fps / H.264）。核心方法：解析参考片 → 确认方向 → 分镜设计 → 程序化逐帧渲染 → 合成 → 双重质检 → 交付（可选：部署为启动动画）。所有画面由代码绘制，不复制参考片受版权保护的素材。

## 工作流

### Step 1 素材解析

运行 `scripts/analyze_reference.py <视频路径>`（内部执行 ffprobe + ffmpeg 抽帧 + PIL 拼图）：

```powershell
python <skill>/scripts/analyze_reference.py "D:\...\参考视频.mp4" --fps 2 --cols 5
```

输出 `.temp/ref_video/meta.json`、关键帧序列与 `contact_sheet.jpg`。用视觉模型分析拼图，要求输出五项：整体类型与叙事逻辑、逐格内容变化、文字/颜色/风格、节奏与转场、音画氛围。

### Step 2 需求确认

用提问工具一次确认三个决策点：
1. **主题内容**：效仿结构换品牌 / 通用主题 / 用户自定义；
2. **文案语言**：原语言 / 中文 / 双语；
3. **配乐**：程序生成 / 无声（用户后期剪映配）。

### Step 3 分镜设计

- 按参考片幕数与时长比例排场景时间轴表（起止秒、内容、动效、转场）；
- 节奏照抄参考片：快切段每幕 0.8~1.2s，点题句与结尾放缓至 2s 级缓动；
- 黑白反转、噪点闪切、白闪是复古风格的低成本高质量转场。

### Step 4 逐帧渲染

读取 [references/rendering.md](references/rendering.md)（渲染骨架、技法库、坑清单、分镜实录）。要点：

- 场景时间轴表驱动，`fn(img, dr, tt, dur)` 签名的场景函数；
- 所有随机固定种子，保证帧间稳定；
- 先渲染约 15 个抽样帧拼图预览，确认后再全量渲染到 `.temp/`；
- 技法按需取用：点阵化 / 线稿扫描绘制 / AI 检测框+标签 / 数字雨 / 粒子汇聚 / 神经网络球 / 轨道环 / 打字机 / glow。

### Step 5 合成与双重质检

```powershell
# 合成
ffmpeg -y -v error -framerate 30 -i ".temp\frames\f%04d.jpg" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart "<输出.mp4>"
# 终检：成品再抽帧拼图，逐格核对无黑场/无空帧/无缺失
ffmpeg -y -v error -i "<输出.mp4>" -vf "fps=2,scale=384:-1,tile=8x5" ".temp\final_check.jpg"
```

### Step 6 交付

- 输出到用户偏好目录（本项目默认 `D:\TeleAgent输出\<项目名>\`）；
- 调用 `report_final_files` 上报成品；
- 清理 `.temp/` 中间帧。

### 进阶：部署为启动动画

用户要求"设为启动画面/启动动画"时，读取 [references/boot-deploy.md](references/boot-deploy.md)。要点：部署 MP4 到启动器 `media/startup.mp4`，按视频时长 `T` 适配 `launcher.json` 时间轴（`HoldAt≈T-3`、`TransitionStart≈T-1.3`、`TransitionEnd≈T-0.3`，ScreenFrames 对准结尾主体图形），`--self-test` 无界面自检，接管快捷方式并保留官方图标，修改前备份配置。

## 红线

- 参考视频仅用于风格与结构分析，不复制其受版权保护的具体画面、角色、品牌元素；
- 产出含版权角色/商标时提醒用户仅限个人使用；
- 数据真实，不虚构"识别率""坐标"等标签以外的误导性内容（风格化标签除外）。
