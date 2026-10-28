# video-style-clone · 通用启动动画/效仿视频创作 Skill

> **A universal Skill** for any AI agent (TeleAgent, Claude, or any LLM that reads Markdown) and any human: analyze a reference video's style, then programmatically render a brand-new same-type video — or keep the original clip and append a branded ending — and deploy it as a **boot/splash animation for any software**. Fully local, no uploads.
>
> 给我一段参考视频，我先"看懂"它的类型、风格、节奏与叙事，再用代码逐帧绘制一条同类型的新视频；或者保留原片、在结尾追加品牌图标定制段，并部署为**任意软件的启动画面**。全程本地处理，无需上传素材。

**v2.0 — 通用化改造**：不再绑定特定产品。三条使用路径：Agent Skill 自动触发 / 作为手册注入任何 AI 助手 / 人类直接运行脚本。

## ✨ 能做什么

- **路线 A · 纯程序化重绘**：复古点阵、线稿扫描、AI 检测框、数字雨、粒子汇聚、神经网络球、轨道环等技法，完整重制同类型 MG 动画/概念广告/片头
- **路线 B · 混合模式**：保留参考片原片与原声，结尾（或任意位置）追加品牌图标定制段（AI 生图 + 程序动态叠加 + 合成音效）
- **部署**：把成品接入任意"播放视频→衔接真实窗口"的启动器（Windows 案例完整可跑，Electron/Web/Unity 思路齐备）
- **程序化音效**：riser / ding / impact 一条命令合成，与原声无缝拼接
- **先确认后动手**：AI 接到任务后先回传《理解反馈》（参考片理解+需求理解+计划概要），经你确认才开始制作

## 🚀 三分钟上手

**环境**：Python 3（`numpy`、`Pillow`）+ ffmpeg（Windows/macOS/Linux 均可）。

```bash
# 1. 验证环境（渲染 3 秒 demo 并自动合成 output/demo.mp4）
python scripts/render_template.py

# 2. 解析参考视频（元数据 + 抽帧 + 拼图，供视觉模型/人工分析）
python scripts/analyze_reference.py "参考视频.mp4"

# 3. 合成音效
python scripts/make_sfx.py --out sfx.wav --dur 2.0 --riser --ding --impact

# 4. 修改 render_template.py 里的 SCENES 表，开始创作你自己的动画
```

### 三种使用方式

| 你是谁 | 怎么用 |
|---|---|
| **AI Agent 用户**（TeleAgent / Claude 等） | 把本仓库作为 Skill 安装，然后说："效仿这个视频做一个同类型的动画" / "把这条视频做成 XX 软件的启动动画" |
| **其他 AI 助手**（ChatGPT / Cursor 等） | 把 `SKILL.md` 和需要的 `references/*.md` 粘贴/注入为任务手册，按工作流执行 |
| **人类开发者** | 直接读 `references/`，把 `scripts/` 当工具箱用；分镜实录就是可抄的作业 |

## 🧭 工作流

```
参考视频 ─► ①素材解析 ─► ②理解确认(先复述理解·用户确认后才动手) ─► ③分镜设计
        ─► ④渲染(A:纯程序化 / B:原片保留+自制段) ─► ⑤合成+双重质检 ─► ⑥交付
        ─► ⑦(可选)部署为启动画面
```

## 📁 目录结构

```
video-style-clone/
├── SKILL.md                       # 技能主文件：双路线工作流 + 平台适配 + 红线
├── references/
│   ├── rendering.md               # 渲染骨架 / 技法库 / 跨平台字体 fallback / 坑清单 / 分镜实录×2
│   ├── hybrid-mode.md             # 路线 B：原片适配→图标特征→AI生图→程序叠加→拼接
│   ├── audio-sfx.md               # 音效合成配方 + 音轨拼接
│   └── boot-deploy.md             # 通用启动动画部署：三要素原理 + 适配公式 + 多技术栈
├── scripts/
│   ├── render_template.py         # 渲染骨架 + 3 秒开箱 demo
│   ├── analyze_reference.py       # 素材解析一条龙
│   └── make_sfx.py                # 参数化音效合成
├── docs/
│   ├── ROADMAP.md                 # 路线图与改进思路
│   └── 效仿视频创作Skill_解释说明.md
├── README.md
└── LICENSE (MIT)
```

## 🖥️ 部署到你自己的软件

任何"全屏播放视频 → 淡出进入主程序"的启动器都适用。核心三要素与时间轴公式见 [`references/boot-deploy.md`](references/boot-deploy.md)：

```
HoldAt ≈ T-3.5（软件未就绪时在此帧等待）
TransitionStart/End ≈ T-1.3 / T-0.3（真实窗口从结尾主体图形位置放大到全屏）
```

Windows 案例完整可跑；Electron / Web / Unity / macOS 思路见文档末尾。

## 📌 声明

- 本仓库仅包含原创技能文档与代码，**不包含任何参考视频素材或渲染成品**；
- 参考视频仅用于风格与结构分析，不复制其受版权保护的画面、角色或品牌元素；
- **TeleAgent** 是中电信人工智能公司产品的名称，相关权利归其权利方所有，本仓库为面向该产品的第三方技能扩展，与权利方无隶属关系。

## 📄 License

[MIT](LICENSE) © 2026 user58216
