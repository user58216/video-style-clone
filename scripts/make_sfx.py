# -*- coding: utf-8 -*-
"""程序化音效合成：riser / ding / impact（零素材，纯 numpy 生成 wav）

用法:
    python make_sfx.py --out sfx.wav --dur 2.0 --riser --ding --impact [--sr 44100] [--gain 1.0]

配方详见 references/audio-sfx.md。
"""
import argparse, wave
import numpy as np

def synth(dur=2.0, sr=44100, riser=True, ding=True, impact=True, seed=7):
    rng = np.random.default_rng(seed)
    t = np.arange(int(sr * dur)) / sr
    n = len(t)
    mix = np.zeros(n)

    if riser:
        d = min(1.2, dur * 0.6)
        m = int(d * sr)
        t1 = t[:m]
        f = 80 + (640 - 80) * (t1 / d) ** 1.6
        ph = 2 * np.pi * np.cumsum(f) / sr
        mix[:m] += 0.20 * (t1 / d) ** 1.4 * np.sin(ph)
        noise = np.convolve(rng.standard_normal(m), np.ones(24) / 24, "same")
        mix[:m] += 0.14 * (t1 / d) ** 2 * noise

    if ding:
        i0 = int(min(1.0, dur * 0.5) * sr)
        tt = t[i0:] - t[i0]
        for f0, amp, dec in ((880, .20, .7), (1320, .13, .55), (1760, .09, .45)):
            mix[i0:] += amp * np.exp(-tt / dec) * np.sin(2 * np.pi * f0 * tt)

    if impact:
        i0 = int(min(1.7, dur * 0.85) * sr)
        tt = t[i0:] - t[i0]
        mix[i0:] += 0.30 * np.exp(-tt / 0.28) * np.sin(2 * np.pi * 55 * tt)
        mix[i0:] += 0.10 * np.exp(-tt / 0.08) * rng.standard_normal(len(tt))

    env = np.ones(n)
    fade = min(int(0.25 * sr), n // 2)
    env[-fade:] = np.linspace(1, 0, fade)
    mix *= env
    return mix

def main():
    ap = argparse.ArgumentParser(description="合成启动动画电子音效（riser/ding/impact）")
    ap.add_argument("--out", default="sfx.wav")
    ap.add_argument("--dur", type=float, default=2.0)
    ap.add_argument("--sr", type=int, default=44100)
    ap.add_argument("--gain", type=float, default=1.0)
    ap.add_argument("--riser", action="store_true", help="低频扫频+噪声上扬（蓄力）")
    ap.add_argument("--ding", action="store_true", help="高频音簇（标题/主体出现标记）")
    ap.add_argument("--impact", action="store_true", help="低频冲击（收尾落点）")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    if not (args.riser or args.ding or args.impact):
        args.riser = args.ding = args.impact = True

    mix = synth(args.dur, args.sr, args.riser, args.ding, args.impact, args.seed) * args.gain
    peak = np.max(np.abs(mix)) or 1.0
    if peak > 0.95:
        mix *= 0.95 / peak
    d8 = int(0.008 * args.sr)
    right = np.concatenate([np.zeros(d8), mix[:-d8]])
    st = np.stack([mix, right], axis=1)
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open(args.out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(args.sr)
        w.writeframes(pcm.tobytes())
    print(f"OK: {args.out} ({args.dur}s, sr={args.sr}, peak={peak:.2f})")

if __name__ == "__main__":
    main()
