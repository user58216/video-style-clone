# -*- coding: utf-8 -*-
"""渲染模板 + 开箱即跑的 3 秒 demo：验证环境后，改 SCENES 表即可创作自己的动画。

用法:
    python render_template.py                 # 渲染 demo 并尝试用 ffmpeg 合成 output/demo.mp4
    python render_template.py --no-ffmpeg     # 只输出帧序列

创作流程: 修改 SCENES 表（起始秒/时长/场景函数）→ 抽样预览 → 全量渲染。
技法库与坑清单见 references/rendering.md。
"""
import argparse, math, os, random, shutil, subprocess

W, H, FPS = 1920, 1080, 30
OUT = os.path.join("output", "frames")

random.seed(7)                     # 固定随机种子（帧间稳定的关键）
CX, CY = W // 2, H // 2

# ---------- 跨平台字体 fallback ----------
def load_font(key, size):
    from PIL import ImageFont
    candidates = {
        "sans_bd": ["C:/Windows/Fonts/arialbd.ttf",
                    "/System/Library/Fonts/Helvetica.ttc",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        "cjk":     ["C:/Windows/Fonts/msyh.ttc",
                    "/System/Library/Fonts/PingFang.ttc",
                    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"],
    }[key]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

from PIL import Image, ImageDraw
F_EN = load_font("sans_bd", 90)
F_CN = load_font("cjk", 44)

# ---------- 工具 ----------
def ease_in(x):  return x * x
def ease_out(x): return 1 - (1 - x) ** 3
def ease_io(x):  x = min(max(x, 0), 1); return 3 * x * x - 2 * x ** 3
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, k): return a + (b - a) * k

def make_glow(rgb, size=300, gamma=2.4):
    import numpy as np
    yy, xx = np.mgrid[-size:size, -size:size]
    d = np.sqrt(xx ** 2 + yy ** 2) / size
    a = (np.clip(1 - d, 0, 1) ** gamma * 255).astype("uint8")
    arr = np.zeros((2 * size, 2 * size, 4), "uint8")
    arr[..., 0], arr[..., 1], arr[..., 2] = rgb
    arr[..., 3] = a
    return Image.fromarray(arr, "RGBA")

GLOW_CYAN = make_glow((80, 190, 255), 340)

def paste_glow(img, sprite, cx, cy, scale=1.0, alpha=1.0):
    s = sprite if scale == 1.0 else sprite.resize(
        (int(sprite.width * scale), int(sprite.height * scale)), Image.BILINEAR)
    if alpha < 1.0:
        s = s.copy()
        s.putalpha(s.getchannel("A").point(lambda v: int(v * alpha)))
    img.paste(s, (int(cx - s.width / 2), int(cy - s.height / 2)), s)

# ---------- Demo 场景（共 3 秒，替换为你自己的分镜） ----------
PARTS = [(random.uniform(-500, 500), random.uniform(-320, 320), random.uniform(0, 0.3))
         for _ in range(42)]

def sc_gather(img, dr, tt, dur):
    """0.0-1.2 像素方块飞聚成光核"""
    dr.rectangle([0, 0, W, H], fill=(9, 11, 16))
    for (rx, ry, dly) in PARTS:
        k = ease_in(clamp((tt - dly) / 0.75))
        if k >= 1:
            continue
        x, y = CX + rx * (1 - k), CY + ry * (1 - k)
        r = 5 + 4 * (1 - k)
        dr.rectangle([x - r, y - r, x + r, y + r], fill=(200, 210, 235))
    born = clamp(tt / 0.6)
    r = (10 + 5 * math.sin(tt * 11)) * born
    dr.ellipse([CX - r, CY - r, CX + r, CY + r], fill=(255, 255, 255))
    paste_glow(img, GLOW_CYAN, CX, CY, 1.0 + born, 0.3 + 0.4 * born)

def sc_title(img, dr, tt, dur):
    """1.2-2.2 标题浮现 + 光晕呼吸"""
    dr.rectangle([0, 0, W, H], fill=(9, 11, 16))
    paste_glow(img, GLOW_CYAN, CX, CY - 40, 1.7 + 0.08 * math.sin(tt * 6),
               0.4 + 0.1 * math.sin(tt * 6))
    a = ease_out(clamp(tt / 0.35))
    txt = "YOUR TITLE"
    tw = dr.textlength(txt, font=F_EN)
    v = int(235 * a)
    dr.text((CX - tw / 2, CY - 60), txt, font=F_EN, fill=(v, v, v))
    cn = "改 SCENES 表开始创作"
    cw = dr.textlength(cn, font=F_CN)
    cv = int(170 * a)
    dr.text((CX - cw / 2, CY + 70), cn, font=F_CN, fill=(cv, cv, cv))

def sc_fade(img, dr, tt, dur):
    """2.2-3.0 收尾：轻微过曝"""
    sc_title(img, dr, tt + 1.0, dur)
    v = int(255 * ease_in(clamp((tt - 0.5) / (dur - 0.5))) * 0.55)
    if v > 0:
        dr.rectangle([0, 0, W, H], fill=(v, v, v))

SCENES = [
    (0.0, 1.2, sc_gather),
    (1.2, 1.0, sc_title),
    (2.2, 0.8, sc_fade),
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ffmpeg", action="store_true")
    ap.add_argument("--out", default=os.path.join("output", "demo.mp4"))
    args = ap.parse_args()
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)

    total_f = int(round(TOTAL * FPS))
    for i in range(total_f):
        render_frame(i / FPS).save(os.path.join(OUT, f"f{i:04d}.jpg"), quality=93)
    print(f"rendered {total_f} frames -> {OUT}")

    if args.no_ffmpeg:
        return
    ff = shutil.which("ffmpeg")
    if not ff:
        print("ffmpeg not found; encode manually:")
        print(f'  ffmpeg -y -framerate {FPS} -i "{OUT}/f%04d.jpg" -c:v libx264 -crf 18 '
              f'-pix_fmt yuv420p -movflags +faststart "{args.out}"')
        return
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    cmd = [ff, "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(OUT, "f%04d.jpg"),
           "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", args.out]
    subprocess.run(cmd, check=True)
    print(f"OK -> {args.out}")

if __name__ == "__main__":
    main()
