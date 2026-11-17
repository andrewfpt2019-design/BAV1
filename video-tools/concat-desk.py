"""Run local video tools and place their outputs on a Concat timeline."""

import argparse
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
from queue import Empty, Queue
import shutil
import subprocess
import sys
from threading import Thread
from uuid import uuid4


TOOLS = Path(__file__).resolve().parent
RUNTIME = TOOLS / ".runtime"
FFMPEG = RUNTIME / "ffmpeg-8.0.1-essentials_build" / "bin"
NODE = RUNTIME / "node" / "node.exe"
CAPCUT = TOOLS / "capcut-cli" / "dist" / "index.js"
EFFECTS = TOOLS / "claude-video-effects" / "scripts" / "fx.py"
CONCAT = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Concat" / "concat.exe"


def run_json(args, **kwargs):
    result = subprocess.run(
        args, check=True, stdout=subprocess.PIPE, encoding="utf-8", **kwargs
    )
    return json.loads(result.stdout)


def streams(path):
    data = run_json([
        FFMPEG / "ffprobe.exe", "-v", "error", "-show_entries",
        "stream=codec_type", "-of", "json", path,
    ])
    return {stream["codec_type"] for stream in data["streams"]}


class ConcatClient:
    def __init__(self, process):
        self.process = process
        self.next_id = 0
        self.replies = Queue()
        Thread(target=self.read_replies, daemon=True).start()

    def read_replies(self):
        for line in self.process.stdout:
            self.replies.put(line)
        self.replies.put(None)

    def send(self, message):
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", **message}) + "\n")
        self.process.stdin.flush()

    def request(self, method, params):
        self.next_id += 1
        self.send({"id": self.next_id, "method": method, "params": params})
        while True:
            try:
                line = self.replies.get(timeout=90)
            except Empty as error:
                raise RuntimeError(f"Concat did not reply to {method}") from error
            if line is None:
                raise RuntimeError(f"Concat stopped while handling {method}")
            reply = json.loads(line)
            if reply.get("id") == self.next_id:
                if "error" in reply:
                    raise RuntimeError(reply["error"]["message"])
                return reply["result"]

    def call(self, name, /, **arguments):
        result = self.request("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            raise RuntimeError(result["content"][0]["text"])
        return result.get("structuredContent", result.get("content"))


@contextmanager
def concat(root):
    env = {**os.environ, "CONCAT_MCP_ROOTS": str(root)}
    with subprocess.Popen(
        [CONCAT, "--mcp", "headless"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        encoding="utf-8", env=env, creationflags=subprocess.CREATE_NO_WINDOW,
    ) as process:
        client = ConcatClient(process)
        try:
            client.request("initialize", {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "concat-desk", "version": "1.0"},
            })
            client.send({"method": "notifications/initialized"})
            yield client
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def stitch(args, output):
    from tools.video.video_stitch import VideoStitch

    result = VideoStitch().execute({
        "operation": "stitch",
        "clips": [str(path) for path in args.inputs],
        "output_path": str(output),
        "transition": args.transition,
        "transition_duration": args.transition_duration,
        "auto_normalize": True,
    })
    if not result.success:
        raise RuntimeError(result.error)
    return any("audio" in streams(path) for path in args.inputs)


def effect(args, output):
    command = [sys.executable, EFFECTS, args.preset, args.input, output, "--width", str(args.width)]
    for flag, value in [("--start", args.start), ("--end", args.end), ("--text", args.text)]:
        if value is not None:
            command.extend([flag, str(value)])
    for option in args.opt:
        command.extend(["--opt", option])
    subprocess.run(command, check=True, stdout=sys.stderr)
    return "audio" in streams(args.input)


def capcut(args, output):
    command = [NODE, CAPCUT]
    videos = run_json([*command, "materials", args.draft, "--type", "videos"])
    audios = run_json([*command, "materials", args.draft, "--type", "audios"])
    for source in videos + audios:
        path = source.get("path")
        if not path or not Path(path).is_file():
            raise RuntimeError("CapCut draft has unavailable media. Export from CapCut and use add.")
    for source in videos:
        if "audio" in streams(source["path"]):
            raise RuntimeError(
                "CapCut's proxy drops audio embedded in video. Export from CapCut and use add."
            )
    subprocess.run([
        *command, "render", args.draft, "--out", output, "--strict", "--verify",
        "--burn-captions", "--all-video-tracks", "--scale", "1", "--crf", "18",
    ], check=True, stdout=sys.stderr)
    return bool(audios)


def import_clip(client, args, path):
    project = str(args.project)
    timeline = client.call("timeline_read", path=project)["timeline"]
    start = timeline["duration"] if args.at is None else args.at
    imported = client.call("media_import", path=project, file=str(path))
    media_id = imported.get("createdId")
    if not media_id:
        raise RuntimeError(f"Concat did not import {path}")
    client.call("clips_add_sequence", path=project, mediaIds=[media_id], start=start)


def append_media(client, args):
    media_dir = args.project / "bridge-media"
    media_dir.mkdir(exist_ok=True)
    source = args.input if args.command == "add" else None
    label = args.label or (source.stem if source else args.command)
    if Path(label).name != label or label in {".", ".."} or ":" in label:
        raise ValueError("Use a file name without a directory for --label")
    output = media_dir / f"{label}-{uuid4().hex[:10]}{source.suffix if source else '.mp4'}"
    save_started = False
    try:
        if source:
            shutil.copy2(source, output)
        else:
            expect_audio = {"stitch": stitch, "effect": effect, "capcut": capcut}[args.command](
                args, output
            )
            available = streams(output)
            if "video" not in available or (expect_audio and "audio" not in available):
                raise RuntimeError("Rendered clip is missing its video or expected audio stream")
        import_clip(client, args, output)
        save_started = True
        client.call("project_save", path=str(args.project))
    finally:
        # A save may have reached disk even if the connection failed afterward.
        if not save_started:
            output.unlink(missing_ok=True)
    return {"project": str(args.project), "media": str(output)}


def finite_seconds(value):
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("Expected a finite non-negative time in seconds")
    return number


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Check Concat and the local tool entry points")
    commands.add_parser("effects", help="List available effect presets")
    create = commands.add_parser("new", help="Create a Concat project")
    create.add_argument("project", type=Path)
    create.add_argument("--width", type=int, default=1080)
    create.add_argument("--height", type=int, default=1920)
    create.add_argument("--fps", type=int, default=30)
    inspect = commands.add_parser("inspect", help="Read the saved timeline")
    inspect.add_argument("project", type=Path)
    edit = commands.add_parser("edit", help="Apply a native Concat edit command from a JSON file")
    edit.add_argument("project", type=Path)
    edit.add_argument("file", type=Path)
    add = commands.add_parser("add", help="Import a media file")
    montage = commands.add_parser("stitch", help="Join video clips with OpenMontage")
    fx = commands.add_parser("effect", help="Render a Claude Video Effects preset")
    draft = commands.add_parser("capcut", help="Render a supported CapCut draft proxy")
    for command in (add, montage, fx, draft):
        command.add_argument("project", type=Path)
        command.add_argument("--at", type=finite_seconds, help="Start time; defaults to timeline end")
        command.add_argument("--label", help="Name prefix for the imported file")
    add.add_argument("input", type=Path)
    montage.add_argument("inputs", type=Path, nargs="+")
    montage.add_argument("--transition", choices=["cut", "crossfade", "fade"], default="cut")
    montage.add_argument("--transition-duration", type=finite_seconds, default=0.5)
    fx.add_argument("preset")
    fx.add_argument("input", type=Path)
    fx.add_argument("--width", type=int, default=1080, help="Output short side")
    fx.add_argument("--start", type=finite_seconds)
    fx.add_argument("--end", type=finite_seconds)
    fx.add_argument("--text")
    fx.add_argument("--opt", action="append", default=[])
    draft.add_argument("draft", type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    os.environ["PATH"] = str(FFMPEG) + os.pathsep + os.environ["PATH"]
    os.environ["PYTHONUTF8"] = "1"
    sys.path.insert(0, str(TOOLS / "OpenMontage"))
    if args.command == "effects":
        subprocess.run([sys.executable, EFFECTS, "--list"], check=True)
        return
    if args.command == "doctor":
        from tools.video.video_stitch import VideoStitch

        with concat(TOOLS.parent) as client:
            version = client.call("concat_version")["concat"]
        subprocess.run([NODE, CAPCUT, "--version"], check=True, stdout=sys.stderr)
        subprocess.run([sys.executable, EFFECTS, "--list"], check=True, stdout=subprocess.DEVNULL)
        subprocess.run([FFMPEG / "ffprobe.exe", "-version"], check=True, stdout=subprocess.DEVNULL)
        result = {"concat": version, "openmontage": VideoStitch.name, "python": sys.version.split()[0]}
    else:
        args.project = args.project.resolve()
        if getattr(args, "input", None):
            args.input = args.input.resolve(strict=True)
        if args.command == "stitch":
            args.inputs = [path.resolve(strict=True) for path in args.inputs]
        if args.command == "capcut":
            args.draft = args.draft.resolve(strict=True)
        with concat(args.project.parent) as client:
            path = str(args.project)
            if args.command == "new":
                client.call(
                    "project_create", location=str(args.project.parent), name=args.project.name,
                    video={"width": args.width, "height": args.height, "rateNum": args.fps, "rateDen": 1},
                )
                result = {"project": path}
            else:
                client.call("project_open", path=path)
                if args.command == "inspect":
                    result = client.call("timeline_read", path=path)
                elif args.command == "edit":
                    command = json.loads(args.file.read_text(encoding="utf-8-sig"))
                    result = client.call("edit_apply", path=path, command=command)
                    client.call("project_save", path=path)
                else:
                    result = append_media(client, args)
            client.call("project_close", path=path)
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(f"concat-desk: {error}")
