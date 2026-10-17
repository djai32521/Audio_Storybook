#!/usr/bin/env python3
"""Generates cover and page illustrations from storybook.json using `gemini-api image` CLI (with SDK fallback)."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import shutil
import subprocess
from pathlib import Path
from google import genai
from google.genai import types


def run_gemini_cli_image(prompt: str, output_path: Path, aspect_ratio: str = "4:3") -> bool:
  """Invokes `gemini-api image` CLI to generate an illustration."""
  env = os.environ.copy()
  local_bin = str(Path.home() / ".local" / "bin")
  env["PATH"] = f"{local_bin}:{env.get('PATH', '')}"

  cli_bin = shutil.which("gemini-api", path=env["PATH"])
  if not cli_bin:
    return False

  output_path.parent.mkdir(parents=True, exist_ok=True)
  cmd = [
      cli_bin,
      "image",
      prompt,
      "--model",
      "gemini-3.1-flash-lite-image",
      "--aspect-ratio",
      aspect_ratio,
      "--out",
      str(output_path),
  ]
  print(f"[gemini-api CLI] Running: {' '.join(cmd[:6])} ... --out {output_path}")
  result = subprocess.run(cmd, env=env, capture_output=True, text=True)
  if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
    print(f"[gemini-api CLI] Saved {output_path} ({output_path.stat().st_size} bytes)")
    return True

  print(f"[gemini-api CLI] Warning ({result.returncode}): {result.stderr.strip()}")
  return False


def run_sdk_image_fallback(prompt: str, output_path: Path, aspect_ratio: str = "4:3") -> bool:
  """Fallback to google-genai SDK if CLI binary fails."""
  output_path.parent.mkdir(parents=True, exist_ok=True)
  client = genai.Client()
  response = client.models.generate_content(
      model="gemini-3.1-flash-lite-image",
      contents=prompt,
      config=types.GenerateContentConfig(
          response_modalities=["IMAGE"],
          image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
      ),
  )
  for part in response.candidates[0].content.parts:
    if part.inline_data and part.inline_data.data:
      output_path.write_bytes(part.inline_data.data)
      print(f"[SDK fallback] Saved {output_path} ({output_path.stat().st_size} bytes)")
      return True
  return False


def generate_single_image(task: dict) -> dict:
  prompt = task["prompt"]
  out_path = Path(task["out_path"])
  aspect = task.get("aspect_ratio", "4:3")
  label = task.get("label", out_path.name)

  if run_gemini_cli_image(prompt, out_path, aspect):
    return {"label": label, "path": str(out_path), "ok": True, "method": "gemini-api-cli"}

  if run_sdk_image_fallback(prompt, out_path, aspect):
    return {"label": label, "path": str(out_path), "ok": True, "method": "google-genai-sdk"}

  return {"label": label, "path": str(out_path), "ok": False, "method": "none"}


def main():
  parser = argparse.ArgumentParser(description="Generate storybook illustrations via gemini-api CLI")
  parser.add_argument("--storybook", required=True, help="Path to storybook.json")
  parser.add_argument("--out-dir", default="./workspace/images", help="Output images directory")
  args = parser.parse_args()

  storybook_path = Path(args.storybook)
  out_dir = Path(args.out_dir)
  out_dir.mkdir(parents=True, exist_ok=True)

  data = json.loads(storybook_path.read_text(encoding="utf-8"))
  style_prefix = data.get("visualStyle", "Classic Golden-Age watercolor storybook illustration")

  tasks = []
  cover_prompt = data.get("coverImagePrompt") or f"{style_prefix}: Front cover illustration for {data.get('title', 'Storybook')}"
  tasks.append({
      "label": "cover",
      "prompt": cover_prompt,
      "out_path": out_dir / "cover.png",
      "aspect_ratio": "3:4",
  })

  for page in data.get("pages", []):
    pnum = page.get("pageNumber", 1)
    raw_prompt = page.get("illustrationPrompt", page.get("narrativeText", ""))
    full_prompt = raw_prompt if style_prefix.lower() in raw_prompt.lower() else f"{style_prefix}. {raw_prompt}"
    tasks.append({
        "label": f"page_{pnum}",
        "prompt": full_prompt,
        "out_path": out_dir / f"page_{pnum}.png",
        "aspect_ratio": "4:3",
    })

  with ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(generate_single_image, t) for t in tasks]
    for fut in as_completed(futures):
      res = fut.result()
      print(f"Completed {res['label']}: ok={res['ok']} via {res['method']}")


if __name__ == "__main__":
  main()
