# -*- coding: utf-8 -*-
"""manifest.json → 剪映草稿(.draft/draft_content.json) 生成器  · AI灵匣
视频剪辑技能包「双线贯通」架构的第二条自动线（剪映线）：
  01~07 方案层产出 → 08 桥接器 storyboard_to_manifest.py → manifest.json
  → 本脚本 → 剪映草稿（买家在剪映打开后一键导出成片）

与 ffmpeg 线共用同一个 manifest.json，实现「一个方案、两条渲染线」。

依赖：pyJianYingDraft（仅生成草稿 JSON，不需要剪映本体安装）
      ffmpeg（仅用于探测素材真实时长，用 imageio-ffmpeg 自带或系统 ffmpeg）
"""
import argparse, os, json, subprocess, re

try:
    from pyJianYingDraft import (ScriptFile, VideoMaterial, VideoSegment,
        AudioMaterial, AudioSegment, TextSegment, Timerange, TrackSpec, TrackType, TextStyle)
except ImportError:
    raise SystemExit("缺少依赖 pyJianYingDraft，请先 pip install pyJianYingDraft")


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def probe_duration(path):
    """用 ffmpeg -i 解析素材时长（秒），失败返回 None。"""
    try:
        out = subprocess.run([ffmpeg_exe(), "-i", path], stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE, text=True, timeout=30).stderr
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", out)
        if m:
            h, mi, s = map(float, m.groups())
            return h * 3600 + mi * 60 + s
    except Exception:
        pass
    return None


def main():
    ap = argparse.ArgumentParser(description="manifest → 剪映草稿")
    ap.add_argument("--manifest", required=True, help="08 桥接器产出的 manifest.json")
    ap.add_argument("--output", required=True, help="输出草稿文件夹，如 ./成片_剪映/我的视频.draft")
    ap.add_argument("--title", default="", help="可选片头标题文字")
    ap.add_argument("--audio", default="", help="可选背景音乐/配音路径")
    a = ap.parse_args()

    cfg = json.load(open(a.manifest, encoding="utf-8"))
    w = int(cfg.get("resolution", {}).get("w", 1080))
    h = int(cfg.get("resolution", {}).get("h", 1920))
    fps = int(cfg.get("fps", 30))
    clips = cfg.get("clips", [])
    if isinstance(clips, str):
        clips = [clips]
    if not clips:
        raise SystemExit("manifest 里没有任何素材路径")

    base = os.path.dirname(os.path.abspath(a.manifest))
    sf = ScriptFile(width=w, height=h, fps=fps, maintrack_adsorb=True)
    vt = sf.append_track(TrackSpec(TrackType.video))

    # 视频轨：按真实时长顺序排布
    cum = 0
    placed = 0
    for p in clips:
        if not os.path.isabs(p):
            p = os.path.join(base, p)
        if not os.path.exists(p):
            print("⚠️ 跳过不存在的素材：%s" % p)
            continue
        mat = VideoMaterial(p)
        # 以 pyJianYingDraft 自身认可的素材时长为准（微秒），避免与 ffprobe 报的 Duration 不一致导致越界
        d_us = int(getattr(mat, "duration", 0) or 0)
        if d_us <= 0:
            dur = probe_duration(p)
            if dur is None:
                print("⚠️ 无法探测时长，按默认 5s 处理：%s" % p)
                dur = 5.0
            d_us = int(dur * 1_000_000)
        sf.add_segment(VideoSegment(mat, Timerange(cum, d_us)), track=vt)
        cum += d_us
        placed += 1
    if placed == 0:
        raise SystemExit("没有可用素材，无法生成草稿")

    # 字幕轨：直接吃 manifest 里的 srt（与 ffmpeg 线同一份字幕）
    sub = cfg.get("subtitle")
    if sub and sub not in (False, "false", "False"):
        sp = sub if os.path.isabs(sub) else os.path.join(base, sub)
        if os.path.exists(sp):
            sub_track = sf.append_track(TrackSpec(TrackType.text, name="字幕"))
            sf.import_srt(sp, track_name="字幕",
                          text_style=TextStyle(size=8, color=(1.0, 1.0, 1.0)))
            print("✅ 已导入字幕：%s" % sp)
        else:
            print("⚠️ 字幕文件不存在：%s" % sp)

    # 片头标题轨
    title = a.title or cfg.get("title", "")
    if title:
        tx = sf.append_track(TrackSpec(TrackType.text, name="标题"))
        sf.add_segment(TextSegment(title, Timerange(0, 2_000_000),
                       style=TextStyle(size=10, bold=True)), track=tx)

    # 音频轨
    audio = a.audio or cfg.get("audio", "")
    if audio:
        apath = audio if os.path.isabs(audio) else os.path.join(base, audio)
        if os.path.exists(apath):
            au = sf.append_track(TrackSpec(TrackType.audio))
            sf.add_segment(AudioSegment(AudioMaterial(apath), Timerange(0, cum)), track=au)
            print("✅ 已加入音频：%s" % apath)
        else:
            print("⚠️ 音频文件不存在：%s" % apath)

    # 写出草稿文件夹（剪映识别 .draft 目录）
    out = a.output
    if not out.endswith(".draft"):
        out = out + ".draft"
    os.makedirs(out, exist_ok=True)
    target = os.path.join(out, "draft_content.json")
    sf.dump(target)
    print("✅ 剪映草稿已生成：%s" % target)
    print("   视频片段=%d  总时长≈%.2fs  分辨率=%dx%d  fps=%d" % (placed, cum / 1e6, w, h, fps))
    print("   下一步：把 %s 文件夹放进剪映「草稿」目录，打开即见时间线，点导出成片。" % out)


if __name__ == "__main__":
    main()
