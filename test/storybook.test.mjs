import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();

test("Managed Agent configuration uses antigravity-preview-09-2026 and gemini-4-argon", () => {
  const agentClientSrc = fs.readFileSync(
    path.join(ROOT, "server/lib/agentClient.ts"),
    "utf-8"
  );
  assert.match(agentClientSrc, /DEFAULT_AGENT_NAME\s*=\s*"antigravity-preview-09-2026"/);
  assert.match(agentClientSrc, /DEFAULT_MODEL_NAME\s*=\s*"gemini-4-argon"/);
  assert.match(agentClientSrc, /type:\s*"antigravity"/);

  const inlineBundleSrc = fs.readFileSync(
    path.join(ROOT, "src/services/inlineAgentBundle.ts"),
    "utf-8"
  );
  assert.match(inlineBundleSrc, /DEFAULT_MANAGED_AGENT_ID\s*=\s*"antigravity-preview-09-2026"/);
  assert.match(inlineBundleSrc, /DEFAULT_MANAGED_AGENT_MODEL\s*=\s*"gemini-4-argon"/);
});

test("agent/AGENTS.md and mounted classic-audiobooks scripts instruct installing and using gemini-api-cli", () => {
  const agentsMd = fs.readFileSync(path.join(ROOT, "agent/AGENTS.md"), "utf-8");
  assert.match(agentsMd, /https:\/\/github\.com\/google-gemini\/gemini-api-cli/);
  assert.match(agentsMd, /gemini-api --version/);
  assert.match(agentsMd, /scripts\/books_spec\.py/);
  assert.match(agentsMd, /scripts\/generate_illustrations\.py/);
  assert.match(agentsMd, /scripts\/generate_popup_assets\.py/);
  assert.match(agentsMd, /scripts\/generate_audiobook_tts\.py/);
  assert.match(agentsMd, /scripts\/voice_mastering\.py/);
  assert.match(agentsMd, /scripts\/generate_and_mix_music\.py/);

  assert.ok(
    fs.existsSync(path.join(ROOT, "agent/scripts/books_spec.py")),
    "agent/scripts/books_spec.py should exist"
  );
  assert.ok(
    fs.existsSync(path.join(ROOT, "agent/scripts/generate_popup_assets.py")),
    "agent/scripts/generate_popup_assets.py should exist"
  );
});

test("Fairytale Bound Book Cover and Jane Austen Two-Page Open Folio Spread match classic-audiobooks", () => {
  const presetsSrc = fs.readFileSync(
    path.join(ROOT, "src/data/presets.ts"),
    "utf-8"
  );
  assert.match(presetsSrc, /BOOK I  ·  JANE AUSTEN/);
  assert.match(presetsSrc, /Longbourn Morning Room/);
  assert.match(presetsSrc, /REGENCY SOCIAL SATIRE/);
  assert.match(presetsSrc, /LONGBOURN, HERTFORDSHIRE/);
  assert.match(presetsSrc, /antigravity-preview-09-2026 \(gemini-4-argon\)/);
  assert.match(presetsSrc, /gemini-api-cli/);
  assert.match(presetsSrc, /01_pride_and_prejudice_diorama_scene_1\.png/);
  assert.match(presetsSrc, /https:\/\/www\.gstatic\.com\/aistudio\/starter-apps\/audio-storybooks\/master\/01_pride_and_prejudice\.mp4/);
  assert.match(presetsSrc, /"startSec":\s*5\.4/);

  const appSrc = fs.readFileSync(path.join(ROOT, "src/App.tsx"), "utf-8");
  assert.match(appSrc, /folio-title-verso/);
  assert.match(appSrc, /austen-open-book/);
  assert.match(appSrc, /startBookNarration/);

  const cssSrc = fs.readFileSync(path.join(ROOT, "src/index.css"), "utf-8");
  assert.match(cssSrc, /52\.917%\s+47\.083%/);
  assert.match(cssSrc, /color-mix\(in srgb,\s*var\(--folio-ink\)\s*50%,\s*var\(--folio-paper\)\)/);
});

