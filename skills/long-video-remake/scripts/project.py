#!/usr/bin/env python3
"""Resumable long-video project preparation, generation and MP4 assembly."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import ark
import imageio_ffmpeg


def ffmpeg():
    return imageio_ffmpeg.get_ffmpeg_exe()


def run(command, *, cwd=None, allow_failure=False):
    result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode and not allow_failure:
        raise RuntimeError(f"FFmpeg 失败：{result.stderr[-1600:]}")
    return result


def probe(path):
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    result = run([ffmpeg(), "-hide_banner", "-i", str(path)], allow_failure=True)
    info = result.stderr
    duration = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", info)
    video = next((line for line in info.splitlines() if " Video: " in line), "")
    if not duration or not video:
        raise ValueError(f"无法读取视频信息：{path.name}。{info[-600:]}")
    size = re.search(r"(?<!\d)(\d{3,5})x(\d{3,5})(?!\d)", video)
    fps = re.search(r"(\d+(?:\.\d+)?)\s+fps", video)
    if not size:
        raise ValueError(f"无法读取画幅：{path.name}")
    seconds = int(duration[1]) * 3600 + int(duration[2]) * 60 + float(duration[3])
    return {"path": str(path), "duration": round(seconds, 3), "width": int(size[1]), "height": int(size[2]),
            "fps": float(fps[1]) if fps else None, "has_audio": any(" Audio: " in line for line in info.splitlines())}


def boundaries(duration, cuts):
    if duration <= 0:
        raise ValueError("视频时长无效。")
    if duration < 4:
        return [0.0, duration]
    points = [0.0]
    cuts = sorted(float(x) for x in cuts if 0 < float(x) < duration)
    while duration - points[-1] > 15:
        start = points[-1]
        target = min(start + 10, duration - 4)
        choices = [x for x in cuts if start + 4 <= x <= min(start + 15, duration - 4)]
        end = min(choices, key=lambda x: abs(x - target)) if choices else target
        points.append(round(end, 3))
    points.append(round(duration, 3))
    return points


def scene_cuts(args):
    source = probe(args.input)
    if not 0 < args.threshold < 1:
        raise ValueError("镜头阈值应在 0 到 1 之间。")
    filter_graph = f"fps=2,scale=320:-1,select=gt(scene\\,{args.threshold}),showinfo"
    result = run([ffmpeg(), "-hide_banner", "-loglevel", "info", "-i", source["path"],
                  "-vf", filter_graph, "-an", "-f", "null", "-"], allow_failure=True)
    if result.returncode:
        raise RuntimeError(f"镜头检测失败：{result.stderr[-900:]}")
    raw = [float(x) for x in re.findall(r"showinfo[^\n]*?pts_time:\s*([\d.]+)", result.stderr)]
    cuts = []
    for point in raw:
        if 0 < point < source["duration"] and (not cuts or point - cuts[-1] >= args.min_gap):
            cuts.append(round(point, 3))
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(cuts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source": source["path"], "cuts": cuts, "output": args.output}, ensure_ascii=False))


def save(manifest, path):
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load(path):
    path = Path(path).expanduser().resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("segments"), list):
        raise ValueError("项目清单格式无效。")
    return data, path


def resolve(project, value):
    if not value:
        return None
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (project / path).resolve()


def init(args):
    source = probe(args.input)
    project = Path(args.output).expanduser().resolve()
    manifest_path = project / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"项目已存在：{manifest_path}。使用现有清单续跑。")
    cuts = json.loads(Path(args.cuts).read_text(encoding="utf-8")) if args.cuts else []
    if not isinstance(cuts, list):
        raise ValueError("切点文件必须是秒数数组。")
    ratio = args.ratio or ("9:16" if source["height"] > source["width"] else "16:9")
    points = boundaries(source["duration"], cuts)
    (project / "refs").mkdir(parents=True, exist_ok=True)
    (project / "specs").mkdir(exist_ok=True)
    (project / "candidates").mkdir(exist_ok=True)
    (project / "work").mkdir(exist_ok=True)
    segments = []
    for index, (start, end) in enumerate(zip(points, points[1:]), 1):
        sid = f"S{index:03d}"
        clip = project / "refs" / f"{sid}.mp4"
        run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-ss", str(start), "-i", source["path"],
             "-t", str(round(end - start, 3)), "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libx264",
             "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-movflags", "+faststart", str(clip)])
        segments.append({"id": sid, "source_start": start, "source_end": end, "source_clip": f"refs/{sid}.mp4",
                         "operation": args.mode, "source_ref_url": None, "spec": None, "candidate_video": None,
                         "candidate_spec_sha256": None, "accepted_video": None, "dialogue": "", "notes": ""})
    manifest = {"version": 1, "source": source, "model": ark.MODEL, "resolution": args.resolution,
                "ratio": ratio, "project_name": args.project_name,
                "global_requirements": {"replace_person": False, "replace_voice": False, "target_person": "",
                                        "target_voice": "", "preserve": [], "change": []},
                "music": None, "subtitles": None, "segments": segments, "final_video": None}
    save(manifest, manifest_path)
    print(json.dumps({"manifest": str(manifest_path), "segments": len(segments), "duration": source["duration"],
                      "generation_seconds": sum(s["source_end"] - s["source_start"] for s in segments if s["operation"] == "generate")},
                     ensure_ascii=False))


def batch(args):
    manifest, path = load(args.manifest)
    project = path.parent
    pending = []
    for segment in manifest["segments"]:
        if args.segment and segment["id"] != args.segment:
            continue
        if segment["operation"] != "generate" or segment.get("accepted_video"):
            continue
        spec_path = resolve(project, segment.get("spec"))
        if spec_path is None or not spec_path.is_file():
            raise ValueError(f"{segment['id']} 缺少 spec JSON。")
        spec_bytes = spec_path.read_bytes()
        spec = json.loads(spec_bytes)
        payload = ark.validate_spec(spec)
        if spec.get("project", "default") != manifest["project_name"]:
            raise ValueError(f"{segment['id']} 的素材项目与整片项目不一致。")
        if payload["resolution"] != manifest["resolution"] or payload["ratio"] != manifest["ratio"]:
            raise ValueError(f"{segment['id']} 的分辨率或画幅与项目不一致。")
        pending.append((segment, spec_path, payload["duration"], hashlib.sha256(spec_bytes).hexdigest()))
    summary = {"segments": len(pending), "generation_seconds": sum(x[2] for x in pending),
               "model": manifest["model"], "resolution": manifest["resolution"]}
    if not args.submit:
        print(json.dumps({**summary, "submitted": False}, ensure_ascii=False))
        return
    for segment, spec_path, _, spec_hash in pending:
        candidate = project / "candidates" / f"{spec_path.stem}.mp4"
        receipt = spec_path.with_suffix(".receipt.json")
        recorded = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else None
        if recorded and recorded.get("spec_sha256") != spec_hash:
            raise ValueError(f"{segment['id']} 的 spec 已改变；使用新版本文件名，不能复用旧任务回执。")
        if candidate.is_file() and candidate.stat().st_size:
            if segment.get("candidate_spec_sha256") not in (None, spec_hash) or not recorded:
                raise ValueError(f"{segment['id']} 候选片段无法对应当前请求。")
            segment["candidate_video"] = str(candidate.relative_to(project))
            segment["candidate_spec_sha256"] = spec_hash
            save(manifest, path)
            continue
        if recorded:
            task_id = recorded["task_id"]
        else:
            ark.generate(argparse.Namespace(spec=str(spec_path), dry_run=False, receipt=str(receipt),
                                            wait=False, timeout=args.timeout, interval=args.interval, output=None))
            task_id = json.loads(receipt.read_text(encoding="utf-8"))["task_id"]
        result = ark.wait_task(argparse.Namespace(id=task_id, timeout=args.timeout, interval=args.interval,
                                                   output=str(candidate)))
        if result.get("status") != "succeeded":
            raise RuntimeError(f"{segment['id']} 生成失败：{json.dumps(result, ensure_ascii=False)[:500]}")
        probe(candidate)
        segment["candidate_video"] = str(candidate.relative_to(project))
        segment["candidate_spec_sha256"] = spec_hash
        save(manifest, path)
        print(json.dumps({"segment": segment["id"], "candidate": segment["candidate_video"]}, ensure_ascii=False), flush=True)
    print(json.dumps({**summary, "submitted": True}, ensure_ascii=False))


def accept(args):
    manifest, path = load(args.manifest)
    segment = next((s for s in manifest["segments"] if s["id"] == args.segment), None)
    if segment is None:
        raise ValueError("片段 ID 不存在。")
    if segment["operation"] != "generate":
        raise ValueError("原片复用片段无需验收候选视频。")
    candidate = resolve(path.parent, args.video or segment.get("candidate_video"))
    if candidate is None:
        raise ValueError("该片段尚无候选视频。")
    probe(candidate)
    segment["accepted_video"] = str(candidate.relative_to(path.parent)) if candidate.is_relative_to(path.parent) else str(candidate)
    save(manifest, path)
    print(json.dumps({"segment": args.segment, "accepted_video": segment["accepted_video"]}, ensure_ascii=False))


def dimensions(ratio, resolution):
    short = {"480p": 480, "720p": 720, "1080p": 1080}.get(resolution)
    if not short:
        raise ValueError("本地拼接支持 480p、720p、1080p；4k 请先按目标画幅手工设置。")
    shapes = {"9:16": (short, short * 16 // 9), "16:9": (short * 16 // 9, short),
              "1:1": (short, short), "4:3": (short * 4 // 3, short),
              "3:4": (short, short * 4 // 3), "21:9": (short * 7 // 3, short)}
    if ratio not in shapes:
        raise ValueError("拼接前请在项目清单指定明确画幅。")
    return shapes[ratio]


def assemble(args):
    manifest, path = load(args.manifest)
    project = path.parent
    width, height = dimensions(manifest["ratio"], manifest["resolution"])
    normalized = []
    for segment in manifest["segments"]:
        src = resolve(project, segment.get("accepted_video") if segment["operation"] == "generate" else segment["source_clip"])
        if src is None or not src.is_file():
            raise ValueError(f"{segment['id']} 未完成验收或源文件缺失，不能导出成片。")
        media = probe(src)
        dest = project / "work" / f"{segment['id']}-normalized.mp4"
        command = [ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(src)]
        if not media["has_audio"]:
            command += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
        command += ["-map", "0:v:0", "-map", "0:a:0" if media["has_audio"] else "1:a:0",
                    "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
                    "-af", "aresample=48000,apad", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                    "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-t", str(media["duration"]), str(dest)]
        run(command)
        normalized.append(dest)
    concat = project / "work" / "concat.txt"
    concat.write_text("".join("file '" + str(p).replace("'", "'\\''") + "'\n" for p in normalized), encoding="utf-8")
    joined = project / "work" / "joined.mp4"
    run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-c", "copy", str(joined)])
    output = resolve(project, args.output or "final.mp4")
    output.parent.mkdir(parents=True, exist_ok=True)
    music = resolve(project, manifest.get("music"))
    subtitles = resolve(project, manifest.get("subtitles"))
    if music and not music.is_file():
        raise FileNotFoundError(music)
    if subtitles and not subtitles.is_file():
        raise FileNotFoundError(subtitles)
    if not music and not subtitles:
        shutil.copy2(joined, output)
    else:
        command = [ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(joined)]
        if music:
            command += ["-stream_loop", "-1", "-i", str(music)]
        if subtitles:
            shutil.copy2(subtitles, project / "work" / "captions.srt")
            command += ["-vf", "subtitles=captions.srt", "-c:v", "libx264", "-crf", "19", "-preset", "veryfast"]
        else:
            command += ["-c:v", "copy"]
        if music:
            command += ["-filter_complex", "[0:a]volume=1[a0];[1:a]volume=0.12[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=0[aout]",
                        "-map", "0:v:0", "-map", "[aout]"]
        else:
            command += ["-map", "0:v:0", "-map", "0:a:0"]
        command += ["-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(output)]
        run(command, cwd=project / "work")
    verify(output)
    manifest["final_video"] = str(output)
    save(manifest, path)
    print(json.dumps({"final_video": str(output), "duration": probe(output)["duration"], "segments": len(normalized)}, ensure_ascii=False))


def verify(path):
    info = probe(path)
    if not info["has_audio"]:
        raise ValueError("成片没有音轨。")
    run([ffmpeg(), "-hide_banner", "-v", "error", "-i", str(path), "-f", "null", "-"])
    return info


def parser():
    p = argparse.ArgumentParser(description="长视频分段、Seedance 生成、验收和成片工具")
    sub = p.add_subparsers(dest="command", required=True)
    x = sub.add_parser("inspect"); x.add_argument("input")
    x = sub.add_parser("cuts"); x.add_argument("input"); x.add_argument("--threshold", type=float, default=0.35)
    x.add_argument("--min-gap", type=float, default=1.0); x.add_argument("--output")
    x = sub.add_parser("init"); x.add_argument("--input", required=True); x.add_argument("--output", required=True)
    x.add_argument("--cuts", help="JSON 秒数数组，可在镜头分析后提供")
    x.add_argument("--mode", choices=["generate", "reuse"], default="generate")
    x.add_argument("--ratio", choices=["9:16", "16:9", "1:1", "4:3", "3:4", "21:9"])
    x.add_argument("--resolution", choices=["480p", "720p", "1080p"], default="720p")
    x.add_argument("--project-name", default="default")
    x = sub.add_parser("batch"); x.add_argument("--manifest", required=True); x.add_argument("--submit", action="store_true")
    x.add_argument("--segment", help="只预检或生成指定片段，适合先验收高风险镜头")
    x.add_argument("--timeout", type=int, default=3600); x.add_argument("--interval", type=int, default=15)
    x = sub.add_parser("accept"); x.add_argument("--manifest", required=True); x.add_argument("--segment", required=True); x.add_argument("--video")
    x = sub.add_parser("assemble"); x.add_argument("--manifest", required=True); x.add_argument("--output")
    x = sub.add_parser("verify"); x.add_argument("input")
    return p


def main():
    args = parser().parse_args()
    try:
        if args.command == "inspect": print(json.dumps(probe(args.input), ensure_ascii=False, indent=2))
        elif args.command == "cuts": scene_cuts(args)
        elif args.command == "init": init(args)
        elif args.command == "batch": batch(args)
        elif args.command == "accept": accept(args)
        elif args.command == "assemble": assemble(args)
        elif args.command == "verify": print(json.dumps(verify(args.input), ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError, FileNotFoundError, FileExistsError, OSError, json.JSONDecodeError) as e:
        print(f"错误：{e}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
