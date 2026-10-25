# -*- coding: utf-8 -*-
"""参考视频素材解析：元数据 + 关键帧抽取 + 网格拼图（contact sheet）

用法:
    python analyze_reference.py <视频路径> [--fps 2] [--cols 5] [--outdir 输出目录]

输出:
    <outdir>/meta.json      视频技术参数
    <outdir>/frame_XXX.jpg  关键帧序列
    <outdir>/contact_sheet.jpg  网格拼图（供视觉模型分析）
"""
import argparse, json, os, subprocess, sys

def ffprobe_json(path):
    cmd = ["ffprobe", "-v", "error", "-print_format", "json",
           "-show_format", "-show_streams", path]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise RuntimeError("ffprobe failed: " + out.stderr[:500])
    return json.loads(out.stdout)

def extract_frames(path, fps, outdir):
    pat = os.path.join(outdir, "frame_%03d.jpg")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", path, "-vf", f"fps={fps}", "-q:v", "2", pat]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError("ffmpeg failed: " + r.stderr[:500])
    return sorted(f for f in os.listdir(outdir) if f.startswith("frame_") and f.endswith(".jpg"))

def contact_sheet(frames, outdir, cols, thumb_w=480, thumb_h=270):
    from PIL import Image
    import glob
    paths = [os.path.join(outdir, f) for f in frames]
    thumbs = [Image.open(p).resize((thumb_w, thumb_h)) for p in paths]
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, rows * thumb_h), (30, 30, 30))
    for i, im in enumerate(thumbs):
        sheet.paste(im, ((i % cols) * thumb_w, (i // cols) * thumb_h))
    out = os.path.join(outdir, "contact_sheet.jpg")
    sheet.save(out, quality=88)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--fps", type=float, default=2.0)
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--outdir", default=os.path.join(".temp", "ref_video"))
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    meta = ffprobe_json(args.video)
    v = next((s for s in meta["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in meta["streams"] if s["codec_type"] == "audio"), None)
    info = {
        "video": args.video,
        "duration": float(meta["format"]["duration"]),
        "width": v.get("width"), "height": v.get("height"),
        "fps": v.get("r_frame_rate"), "nb_frames": v.get("nb_frames"),
        "codec": v.get("codec_name"), "has_audio": a is not None,
    }
    with open(os.path.join(args.outdir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    frames = extract_frames(args.video, args.fps, args.outdir)
    sheet = contact_sheet(frames, args.outdir, args.cols)
    print(json.dumps({"meta": info, "frames": len(frames), "sheet": sheet},
                     ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
