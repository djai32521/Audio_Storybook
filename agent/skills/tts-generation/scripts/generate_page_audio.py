#!/usr/bin/env python3
"""Synthesizes dramatized multi-voice narration for each storybook page using gemini-3.1-flash-tts-preview."""

import argparse
import io
import json
from pathlib import Path
import wave
from google import genai
from google.genai import types
from pydub import AudioSegment

VALID_VOICES = {
    "Puck", "Charon", "Kore", "Fenrir", "Aoede", "Zephyr", "Leda", "Orus"
}


def pcm_to_segment(pcm_bytes: bytes, sample_rate: int = 24000) -> AudioSegment:
  buf = io.BytesIO()
  with wave.open(buf, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    wf.writeframes(pcm_bytes)
  buf.seek(0)
  return AudioSegment.from_wav(buf)


def synthesize_single_line(client: genai.Client, text: str, voice_name: str, style_prompt: str = "") -> AudioSegment:
  voice = voice_name if voice_name in VALID_VOICES else "Charon"
  prompt = f"Say in a {style_prompt} tone: {text}" if style_prompt else text
  response = client.models.generate_content(
      model="gemini-3.1-flash-tts-preview",
      contents=prompt,
      config=types.GenerateContentConfig(
          response_modalities=["AUDIO"],
          speech_config=types.SpeechConfig(
              voice_config=types.VoiceConfig(
                  prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
              )
          ),
      ),
  )
  pcm_data = response.candidates[0].content.parts[0].inline_data.data
  return pcm_to_segment(pcm_data)


def synthesize_two_speaker_page(client: genai.Client, lines: list[dict], speaker_voices: dict[str, str]) -> AudioSegment:
  transcript_lines = []
  for item in lines:
    speaker = item.get("speaker", "The Storyteller")
    style = item.get("stylePrompt", "")
    text = item.get("text", "")
    prefix = f"[{style}] " if style else ""
    transcript_lines.append(f"{speaker}: {prefix}{text}")

  prompt = "Read this dramatized storybook scene with expressive theatrical pacing:\n\n" + "\n".join(transcript_lines)
  speaker_configs = [
      types.SpeakerVoiceConfig(
          speaker=spk,
          voice_config=types.VoiceConfig(
              prebuilt_voice_config=types.PrebuiltVoiceConfig(
                  voice_name=v if v in VALID_VOICES else "Charon"
              )
          ),
      )
      for spk, v in list(speaker_voices.items())[:2]
  ]

  response = client.models.generate_content(
      model="gemini-3.1-flash-tts-preview",
      contents=prompt,
      config=types.GenerateContentConfig(
          response_modalities=["AUDIO"],
          speech_config=types.SpeechConfig(
              multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                  speaker_voice_configs=speaker_configs
              )
          ),
      ),
  )
  pcm_data = response.candidates[0].content.parts[0].inline_data.data
  return pcm_to_segment(pcm_data)


def main():
  parser = argparse.ArgumentParser(description="Generate dramatized multi-voice TTS audio per page")
  parser.add_argument("--storybook", required=True, help="Path to storybook.json")
  parser.add_argument("--out-dir", default="./workspace/audio", help="Output audio directory")
  args = parser.parse_args()

  storybook_path = Path(args.storybook)
  out_dir = Path(args.out_dir)
  out_dir.mkdir(parents=True, exist_ok=True)

  data = json.loads(storybook_path.read_text(encoding="utf-8"))
  client = genai.Client()

  char_voices = {
      c.get("name", "The Storyteller"): c.get("voiceName", "Charon")
      for c in data.get("characters", [])
  }

  for page in data.get("pages", []):
    pnum = page.get("pageNumber", 1)
    lines = page.get("dialogueLines") or [
        {
            "speaker": "The Storyteller",
            "voiceName": "Charon",
            "stylePrompt": "Warmly, with classic storybook cadence",
            "text": page.get("narrativeText", ""),
        }
    ]

    unique_speakers = {}
    for line in lines:
      spk = line.get("speaker", "The Storyteller")
      vname = line.get("voiceName") or char_voices.get(spk, "Charon")
      unique_speakers[spk] = vname if vname in VALID_VOICES else "Charon"

    try:
      if len(unique_speakers) == 2 and len(lines) > 1:
        page_seg = synthesize_two_speaker_page(client, lines, unique_speakers)
      else:
        combined = AudioSegment.silent(duration=150)
        pause = AudioSegment.silent(duration=280)
        for idx, line in enumerate(lines):
          spk = line.get("speaker", "The Storyteller")
          vname = unique_speakers.get(spk, "Charon")
          seg = synthesize_single_line(
              client,
              line.get("text", ""),
              vname,
              line.get("stylePrompt", ""),
          )
          combined += seg
          if idx < len(lines) - 1:
            combined += pause
        page_seg = combined

      out_file = out_dir / f"page_{pnum}.mp3"
      page_seg.export(str(out_file), format="mp3", bitrate="192k")
      page["audioUrl"] = f"audio/page_{pnum}.mp3"
      page["durationSeconds"] = round(len(page_seg) / 1000.0, 1)
      print(f"[TTS] Saved {out_file} ({page['durationSeconds']}s)")
    except Exception as exc:
      print(f"[TTS] Error on page {pnum}: {exc}")

  storybook_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
  main()
