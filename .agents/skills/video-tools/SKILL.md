---
name: video-tools
description: Edit local video with CapCut CLI, OpenMontage or Claude Video Effects and place the results on an editable Concat timeline in this Windows workspace.
---

# Video tools

Run commands from the repository root in PowerShell. Read the README for setup, the demo and the command table.

- `./video-tools/concat-desk.cmd doctor` checks the local tool entry points.
- `new "<project folder>"` creates a Concat project. Create the parent first. Default video format is 1080×1920 at 30 fps.
- `add "<project folder>" "<MP4>"` imports a clip. Use separate `add` calls to keep cuts editable.
- `stitch "<project folder>" "<clip 1>" "<clip 2>"` renders a single clip with OpenMontage. Use `--transition crossfade` for a crossfade.
- `effects` lists presets. `effect "<project folder>" moody "<MP4>"` renders a preset before importing its result.
- `capcut "<project folder>" "<draft folder>"` makes a strict, verified draft proxy. When the draft has embedded source audio or fails strict verification, export from CapCut and import the MP4 with `add`.
- `inspect "<project folder>"` reads the saved timeline. `edit "<project folder>" "<command JSON file>"` applies one native Concat command. See the [MCP reference for v0.2.9](https://github.com/jub0t/Concat/blob/v0.2.9/docs/MCP.md).

The bridge appends to the timeline by default. Pass `--at` with a time in seconds on import commands to place explicitly. Close the project in Concat before running project commands, then reopen it to review. Keep its `bridge-media` folder. Rendered effects and stitched shots arrive as flattened clips and can be trimmed or moved in Concat.
