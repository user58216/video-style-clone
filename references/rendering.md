# 逐帧渲染指南（rendering）

渲染阶段完整参考：脚本骨架、风格技法库、常见坑、分镜实录样例。

## 目录
1. [渲染脚本骨架](#渲染脚本骨架)
2. [风格技法库](#风格技法库)
3. [常见坑清单](#常见坑清单)
4. [分镜实录样例（AI起点 v2）](#分镜实录样例)

## 渲染脚本骨架

```python
import math, random, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
random.seed(7); np.random.seed(7)   # 全局固定种子
CX, CY = W // 2, H // 2

# 字体（Windows）
F_EN = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 66)
F_CN = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 46)
F_MONO = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 30)

# 缓动函数
def ease_in(x):  return x * x
def ease_out(x): return 1 - (1 - x) ** 3
def ease_io(x):  x = min(max(x, 0), 1); return 3*x*x - 2*x**3
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, k): return a + (b - a) * k

# 时间轴：(起始秒, 时长秒, 场景函数)；场景函数签名 fn(img, dr, tt, dur)
SCENES = [
    (0.0, 1.2, sc_opening),
    (1.2, 6.6, sc_montage),
    # ...
]
TOTAL = SCENES[-1][0] + SCENES[-1][1]

def render_frame(t):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    dr = ImageDraw.Draw(img)
    for (st, du, fn) in SCENES:
        if st <= t < st + du:
            fn(img, dr, t - st, du)
            break
    return img

# 主循环：先抽样预览，再全量
```

**渲染策略**：先渲染约 15 个抽样帧拼图预览确认分镜，再全量渲染；全量帧输出到 `.temp/`，交付后清理。

## 风格技法库

### 径向光晕（glow sprite，预生成后反复 paste）

```python
def make_glow(rgb, size=300, gamma=2.4):
    yy, xx = np.mgrid[-size:size, -size:size]
    d = np.sqrt(xx**2 + yy**2) / size
    a = (np.clip(1 - d, 0, 1) ** gamma * 255).astype(np.uint8)
    arr = np.zeros((2*size, 2*size, 4), np.uint8)
    arr[..., :3] = rgb; arr[..., 3] = a
    return Image.fromarray(arr, "RGBA")
# paste 时可缩放 scale 与衰减 alpha
```

### 点阵化（剪影 → 网格采样）

小画布画剪影 → numpy 按网格采样实心格 → 放大坐标画圆点。适合飞机、图标等复古点阵图形。

### 线稿扫描绘制（地标/建筑浮现）

元素系统：每元素带 y 范围，扫描线从下往上移动，只绘制 y0 >= scan_y 的元素；跨越扫描线的线段做线性裁剪画下半段。扫描线本体为亮横线 + 上下渐晕。

### AI 检测框 + 标签（AI 视觉识别味）

- 四角 L 形框线，从外扩 1.35 倍 ease_out 收拢到目标框；
- 标签条（黑底白字，等宽字体）：地名打字机浮现 + 经纬度 + "MATCH 98.4%"置信度从低值滚动到位；
- 扫过区域随机像素噪点闪烁（seed 随帧变化）。

### 数据洪流 / 数字雨

粒子从全屏边缘 ease_in 汇聚到中心亮核；数字雨为固定列 x + 下落 head_y，"0"/"1" 字符列向上渐隐（等宽字体）。

### 神经网络生长

预生成分层节点（层半径/点亮时刻/父子边），节点 age 控制弹出半径（`r * (1 + 0.5*exp(-4*age))`），边随 age 渐显。

### 伪 3D 旋转球（斐波那契球面 + 粒子汇聚）

- `fib_sphere(n)` 均匀布点，绕 Y 轴旋转矩阵投影，深度控制点径/亮度，近邻对连线；
- 粒子系统：每粒子存（起点，目标节点索引，3D 微偏移，色调），reach = ease_io(tt/T) 插值，成型后 sin 漂移；
- 颜色浅蓝→紫按随机色调插值；RGB 模式无 alpha，透明感靠向背景色插值。

### 轨道环终章

椭圆环（arc 分前后半，后半先画被球遮挡），城市光点沿椭圆匀速转 + 拖尾点 + 前后景亮度区分。

### 其他复古转场

黑白噪点块闪切、白闪、背景黑白反转硬切、打字机文字、星点收束成单点。

## 常见坑清单

1. **随机必须固定种子**：模块级 `random.seed(7)` 或场景内 `Random(seed)` 实例，否则帧间闪烁错乱；
2. PIL `RGB` 无 alpha：半透明色手动向背景插值 `col = bg + fg*a` 逐通道；
3. `fill` 四元组 RGBA 在 RGB 图上会报错；
4. Windows 字体路径：`msyh.ttc`（中文）、`arialbd.ttf`、`consolab.ttf`（等宽粗体）；
5. PowerShell 里 ffmpeg 不支持 glob 模式输入，拼图用 PIL；
6. 帧序列命名 `f%04d.jpg`（quality 93），合成 `-pix_fmt yuv420p -movflags +faststart`；
7. 渲染前必做抽样预览，避免全量返工。

## 分镜实录样例

案例《AI 起点 v2》（20s）：效仿黑白点阵复古未来主义 AI 概念广告，融入"AI 视觉识别世界地标"主题。

| # | 时间 | 场景 | 关键动效 |
|---|---|---|---|
| 1 | 0.0-1.2 | 数据起点 | 网格淡入、像素方块飞聚成光核、白闪 |
| 2 | 1.2-7.8 | 地标蒙太奇 ×6 | 每幕 1.1s：扫描绘制线稿→检测框锁定→标签+经纬度+置信度→噪点闪切 |
| 3 | 7.8-8.8 | 数据洪流 | 粒子汇聚+数字雨+中心亮核过曝 |
| 4 | 8.8-9.8 | 神经网络生长 | 三层节点树状点亮 |
| 5 | 9.8-11.8 | 点题 | 放射点+英文打字机+中文副标 |
| 6 | 11.8-12.6 | 单点闭环 | 星点收束、脉动过曝 |
| 7 | 12.6-13.8 | AI 球体 | 白底蓝色渐变球（全片首次上色） |
| 8 | 13.8-15.0 | 对话界面 | 打字机+光标+紫色噪点 |
| 9 | 15.0-17.5 | 粒子生成 | 620 粒子汇聚神经网络球 |
| 10 | 17.5-20.0 | 轨道终章 | 轨道环+6 城市光点环绕+拖尾 |

地标顺序（按文明时间线）：吉萨金字塔 → 自由女神像 → 埃菲尔铁塔 → 大本钟 → 上海外滩 → 哈利法塔。
点题文案：`All progress has a starting point.` / `所有进步，都有起点。`
