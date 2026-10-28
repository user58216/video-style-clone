# 程序化音效合成与音轨拼接（audio-sfx）

用 numpy 合成启动动画/自制段的电子音效，并与原片音轨拼接。零外部素材，纯本地生成。

## 目录
1. [快速使用](#快速使用)
2. [合成配方详解](#合成配方详解)
3. [与原片音轨拼接](#与原片音轨拼接)
4. [设计原则](#设计原则)

## 快速使用

```bash
# 标准"标题揭示"三件套：上扬 + 高音点缀 + 低频冲击（2 秒立体声）
python scripts/make_sfx.py --out sfx.wav --dur 2.0 --riser --ding --impact

# 仅低频冲击（短促收尾）
python scripts/make_sfx.py --out thud.wav --dur 0.8 --impact

# 自定义采样率与响度
python scripts/make_sfx.py --out sfx.wav --dur 2.0 --riser --ding --impact --sr 48000 --gain 0.9
```

## 合成配方详解

全部配方等价于以下 numpy 逻辑（make_sfx.py 的内核，可按需改参）：

```python
import numpy as np, wave
SR = 44100; D = 2.0
t = np.arange(int(SR * D)) / SR
mix = np.zeros(len(t))

# 1) riser（0 ~ 1.2s）：正弦扫频 80→640Hz + 带通噪声涨潮，制造"蓄力上扬"
t1 = t[:int(1.2 * SR)]
f = 80 + (640 - 80) * (t1 / 1.2) ** 1.6          # 扫频曲线（幂次控制紧张感）
ph = 2 * np.pi * np.cumsum(f) / SR                # 相位积分保证频率连续
mix[:len(t1)] += 0.20 * (t1 / 1.2) ** 1.4 * np.sin(ph)
noise = np.convolve(rng.standard_normal(len(t1)), np.ones(24)/24, "same")  # 简易低通
mix[:len(t1)] += 0.14 * (t1 / 1.2) ** 2 * noise

# 2) ding（1.0s 起）：高频音簇 + 指数衰减，标记"标题/主体出现"
for f0, amp, dec in ((880, .20, .7), (1320, .13, .55), (1760, .09, .45)):
    tt = t[t >= 1.0] - 1.0
    mix[t >= 1.0] += amp * np.exp(-tt / dec) * np.sin(2 * np.pi * f0 * tt)

# 3) impact（1.7s 起）：低频正弦冲击 + 噪声瞬态，收尾"落点"
tt = t[t >= 1.7] - 1.7
mix[t >= 1.7] += 0.30 * np.exp(-tt / 0.28) * np.sin(2 * np.pi * 55 * tt)
mix[t >= 1.7] += 0.10 * np.exp(-tt / 0.08) * rng.standard_normal(len(tt))

# 4) 全局末尾淡出 + 立体声（右声道延迟 8ms 增加宽度）
env = np.ones(len(t)); env[-int(0.25 * SR):] = np.linspace(1, 0, int(0.25 * SR))
mix *= env
d8 = int(0.008 * SR)
st = np.stack([mix, np.concatenate([np.zeros(d8), mix[:-d8]])], axis=1)
# int16 PCM 写 wav（clip 到 [-1,1]）
```

参数调节经验：
- 扫频幂次 `**1.6`：越大越"后程发力"，适合 2s 级；短视频（<1s）改 `**1.2`；
- ding 音簇频率比取 1 : 1.5 : 2（纯五度+八度）听感和谐；
- impact 中心频率 50–65Hz，衰减 0.25–0.35s，过短发闷、过长浑浊；
- 响度叠加后 clip 前先检查峰值（`np.max(np.abs(st))`），建议 ≤0.95。

## 与原片音轨拼接

前提：原片已适配为目标规格（见 references/hybrid-mode.md Step B1），自制段视频已单独合成。

```bash
ffmpeg -y -i part1.mp4 -i part2.mp4 -i sfx.wav -filter_complex \
  "[0:v][1:v]concat=n=2:v=1:a=0[outv];\
   [0:a]aresample=44100,aformat=channel_layouts=stereo[a0];\
   [a0][2:a]concat=n=2:v=0:a=1[outa]" \
  -map "[outv]" -map "[outa]" -c:v libx264 -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart output/final.mp4
```

要点：
- `[0:a]aresample=44100,aformat=channel_layouts=stereo` 统一音频参数后再 concat，否则采样率/声道不一致会报错；
- 视频 `concat=n=2:v=1:a=0` 与音频 `concat=n=2:v=0:a=1` 分路拼接，两路总时长需对齐（差 <0.1s）；
- 无声原片时省略 `[0:a]` 分支，直接把 sfx 作为唯一音轨 `-map 2:a`。

## 设计原则

- **情绪衔接**：原片音乐淡出 → riser 接力（蓄力）→ ding（主体出现同步）→ impact（收尾落点），四段各司其职；
- **落点对齐**：ding 时刻与标题/主体出现帧对齐（±1 帧内），impact 对齐收尾闪白或定格帧；
- **克制**：音效为陪衬，峰值响度不超过原片音乐；原片有声时避免整段铺满；
- **可复现**：随机噪声用固定种子，保证重跑一致。
