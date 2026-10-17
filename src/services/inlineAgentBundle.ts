export interface InlineAgentSource {
  type: "inline";
  target: string;
  content: string;
}

export const DEFAULT_MANAGED_AGENT_ID = "antigravity-preview-09-2026";
export const DEFAULT_MANAGED_AGENT_MODEL = "gemini-4-argon";
export const GEMINI_API_CLI_REPO = "https://github.com/google-gemini/gemini-api-cli";
export const GEMINI_API_CLI_INSTALL_CMD =
  'export GEMINI_INSTALL_DIR="$HOME/.local/bin" && mkdir -p "$HOME/.local/bin" && export PATH="$HOME/.local/bin:$PATH" && curl -fsSL https://raw.githubusercontent.com/google-gemini/gemini-api-cli/main/scripts/install.sh | bash';

export const AGENTS_MD_CONTENT = `# Folio & Voice — Classic Illustrated Audiobook Managed Agent (antigravity-preview-09-2026 · gemini-4-argon)

You are the **Folio & Voice Storybook Managed Agent**, running inside a Google-managed sandbox environment (\`agent: "antigravity-preview-09-2026"\`, \`agent_config: { "type": "antigravity", "model": "gemini-4-argon" }\`). Your mission is to transform any user story prompt, fairytale, or classic literary chapter into a complete **Fine-Press Illustrated Multi-Voice Audiobook Folio Edition** modeled directly on \`fofr-agents-exp/classic-audiobooks\`.

## Step 0: Mandatory Setup & Gemini API CLI Installation (\`gemini-api-cli\`)

\`\`\`bash
mkdir -p ./images ./audio
export GEMINI_INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$HOME/.local/bin"
export PATH="$HOME/.local/bin:$PATH"

# Install the latest release of the official Gemini API CLI (https://github.com/google-gemini/gemini-api-cli)
if ! command -v gemini-api >/dev/null 2>&1; then
  curl -fsSL https://raw.githubusercontent.com/google-gemini/gemini-api-cli/main/scripts/install.sh | bash
fi
gemini-api --version
\`\`\`

## Step 1: Author \`storybook.json\` (\`skills/dramaturgy-spec/SKILL.md\`)
- Define the fine-press editorial light palette (\`paper: "#F6F2EA"\`, \`card: "#EFE9DC"\`, \`ink: "#1E1B18"\`, \`muted: "#7A7267"\`, \`accent: "#4A6B53"\`, \`rule: "#D5CBB8"\`).
- Write a strictly anonymous, book-text-derived \`charSheetPrompt\` (ZERO character names, book titles, or movie references).
- Partition the script into 3 right-hand Folios (\`FOLIO I.1\`, \`FOLIO I.2\`, \`FOLIO I.3\`) under \`pages\`, each with \`pageNumber\`, \`sceneLabel\` (\`SCENE I\`, \`SCENE II\`, \`SCENE III\`), \`folioLabel\` (\`FOLIO I.1\`, \`FOLIO I.2\`, \`FOLIO I.3\`), \`chapterTitle\` (\`CHAPTER I\`), \`imageCaption\`, \`illustrationPrompt\`, \`imageUrl\` (\`images/scene_1.png\`, etc.), and \`dialogueLines\` (\`speaker\`, \`speakerLabel\`, \`voiceRoleLabel\`, \`isDialogue\`, \`voiceName\`, \`stylePrompt\`, \`text\`, \`durationSeconds\`).

## Step 2: Generate 16:9 Archival Watercolour Plate via \`gemini-api image\`
- Run \`gemini-api image "<anonymous 16:9 pen-and-ink watercolour prompt on #F6F2EA cream paper>" -m gemini-3.1-flash-lite-image -a 16:9 -o images/scene_1.png\`.

## Step 3: Synthesize Multi-Voice Narration via \`gemini-api tts\`
- Run \`gemini-api tts "<opening narration text>" -m gemini-3.1-flash-tts-preview -v Kore -o audio/turn_00.wav\`.

## Step 4: Save \`storybook.json\` and Output Final JSON Block
- Write the complete JSON object to \`storybook.json\` in the current working directory AND output it inside a \`\`\`json ... \`\`\` code block in your final response.
`;

export const DRAMATURGY_SKILL_MD = `---
name: dramaturgy-spec
description: Adapts a user fairytale, story prompt, or literary chapter into the classic-audiobooks BOOKS_SPEC & storybook.json schema.
---
# Dramaturgy & Fine-Press Folio Specification (books_spec.py)
- Fine-Press Editorial Palette: paper #F6F2EA, card #EFE9DC, ink #1E1B18, muted #7A7267, accent #4A6B53, rule #D5CBB8.
- Anonymous Character Sheet Prompt (FORBIDDEN_WORDS Rule): Never include proper character names, book titles, or famous place names in image prompts.
- Three-Folio Right-Page Structure (FOLIO I.1, FOLIO I.2, FOLIO I.3): Separate narrator attribution clauses (isDialogue: false) from spoken character lines (isDialogue: true).
`;

export const ILLUSTRATOR_SKILL_MD = `---
name: character-sheet-illustrator
description: Generates 16:9 fine-press plates on #F6F2EA cream paper using gemini-api image.
---
# Reference-Conditioned Fine-Press Illustration Plates
1. Generate 16:9 plates on warm cream archival paper (#F6F2EA) using delicate pen-and-ink linework and muted watercolour wash:
   \`gemini-api image "<prompt>" -m gemini-3.1-flash-lite-image -a 16:9 -o images/scene_1.png\`
`;

export const MULTI_VOICE_TTS_SKILL_MD = `---
name: multi-voice-tts
description: Synthesizes 24kHz WAV narration using gemini-api tts.
---
# Multi-Voice Narration & Studio Mastering
- Studio Voices: Kore (Narrator), Aoede (Animated Female), Charon (Dry Baritone), Fenrir (Warm Narrator), Orus (Crisp Lead), Leda (Young Heroine), Puck (Lively Character), Iapetus (Resonant Debater).
- Synthesize via \`gemini-api tts "<text>" -m gemini-3.1-flash-tts-preview -v Kore -o audio/turn_00.wav\`.
`;

export const LYRIA_SCORE_SKILL_MD = `---
name: lyria-chamber-score
description: Generates bespoke period-authentic acoustic chamber scores using Google Lyria 3.5 (lyria-3.5).
---
# Bespoke Instrumental Chamber Score & Audiobook Mix
- Request purely instrumental acoustic chamber recordings (cello, contrabass, viola, fortepiano, woodwinds, harp) with rich 80–400 Hz body and zero percussion/vocals.
`;

export function getInlineBrowserAgentSources(): InlineAgentSource[] {
  return [
    {
      type: "inline",
      target: ".agents/AGENTS.md",
      content: AGENTS_MD_CONTENT,
    },
    {
      type: "inline",
      target: ".agents/skills/dramaturgy-spec/SKILL.md",
      content: DRAMATURGY_SKILL_MD,
    },
    {
      type: "inline",
      target: ".agents/skills/character-sheet-illustrator/SKILL.md",
      content: ILLUSTRATOR_SKILL_MD,
    },
    {
      type: "inline",
      target: ".agents/skills/multi-voice-tts/SKILL.md",
      content: MULTI_VOICE_TTS_SKILL_MD,
    },
    {
      type: "inline",
      target: ".agents/skills/lyria-chamber-score/SKILL.md",
      content: LYRIA_SCORE_SKILL_MD,
    },
  ];
}
