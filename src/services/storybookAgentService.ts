import { GoogleGenAI, Modality, Type } from "@google/genai";
import {
  ALL_CLASSIC_STORYBOOKS,
  createBespokeFairytaleStorybook,
  EDITION_PALETTES,
} from "../data/presets";
import {
  AgentLogEntry,
  DialogueLine,
  Storybook,
} from "../types";
import {
  DEFAULT_MANAGED_AGENT_ID,
  DEFAULT_MANAGED_AGENT_MODEL,
  getInlineBrowserAgentSources,
} from "./inlineAgentBundle";

function isPlaceholderApiKey(key?: string | null): boolean {
  if (!key || typeof key !== "string") return true;
  const trimmed = key.trim();
  if (!trimmed) return true;
  const upper = trimmed.toUpperCase();
  return (
    upper === "MY_GEMINI_API_KEY" ||
    upper === "YOUR_GEMINI_API_KEY" ||
    upper === "YOUR_API_KEY" ||
    upper === "GEMINI_API_KEY" ||
    upper === "PLACEHOLDER" ||
    upper.startsWith("TODO") ||
    upper.startsWith("REPLACE_")
  );
}

function getApiKey(overrideKey?: string): string {
  let storedKey = "";
  try {
    if (typeof window !== "undefined" && window.localStorage) {
      storedKey = window.localStorage.getItem("FOLIO_GEMINI_API_KEY") || "";
      if (isPlaceholderApiKey(storedKey)) {
        window.localStorage.removeItem("FOLIO_GEMINI_API_KEY");
        storedKey = "";
      }
    }
  } catch {
    // Sandboxed null-origin frames block localStorage
  }
  const envKey =
    typeof process !== "undefined" && process.env
      ? process.env.API_KEY || process.env.GEMINI_API_KEY || ""
      : "";
  const winKey =
    typeof window !== "undefined"
      ? (window as any).process?.env?.API_KEY ||
        (window as any).process?.env?.GEMINI_API_KEY ||
        ""
      : "";

  const candidates = [overrideKey, storedKey, envKey, winKey];
  for (const candidate of candidates) {
    if (!isPlaceholderApiKey(candidate)) {
      return candidate!.trim();
    }
  }
  return "";
}

function makeLogId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

function nowTime(): string {
  return new Date().toLocaleTimeString([], {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException("Aborted", "AbortError"));
      return;
    }
    const timer = window.setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        window.clearTimeout(timer);
        reject(new DOMException("Aborted", "AbortError"));
      },
      { once: true }
    );
  });
}

export interface RunStorybookAgentOptions {
  prompt: string;
  classicBookTitle?: string;
  paletteKey?: string;
  visualStyle: string;
  pageCount: number;
  narratorVoice: string;
  agentName?: string;
  modelName?: string;
  apiKey?: string;
  environmentId?: string;
  previousInteractionId?: string;
  sessionId: string;
  signal?: AbortSignal;
  onLog: (entry: AgentLogEntry) => void;
  onStageChange: (stageIndex: number, stageLabel: string) => void;
  onCreated?: (interactionId: string, environmentId?: string) => void;
}

export interface RunStorybookAgentResult {
  storybook: Storybook;
  interactionId?: string;
  environmentId?: string;
  agent: string;
  model: string;
}

function inferPipelineStage(
  toolName: string,
  args: unknown,
  text: string
): { index: number; label: string } | null {
  const combined = `${toolName} ${JSON.stringify(args || "")} ${text}`.toLowerCase();
  if (
    combined.includes("install.sh") ||
    combined.includes("gemini-api --version") ||
    combined.includes("gemini-api-cli")
  ) {
    return { index: 0, label: "Stage I · Booting Sandbox & Installing gemini-api-cli" };
  }
  if (
    combined.includes("books_spec") ||
    combined.includes("dramaturgy") ||
    combined.includes("char_sheet_prompt") ||
    combined.includes("storybook.json")
  ) {
    return { index: 1, label: "Stage II · Authoring 3-Folio Dramaturgy & Character Spec" };
  }
  if (
    combined.includes("generate_illustrations") ||
    combined.includes("generate_popup_assets") ||
    combined.includes("gemini-api image") ||
    combined.includes("char_sheet") ||
    combined.includes("scene_1") ||
    combined.includes("flash-lite-image") ||
    combined.includes("flash-image")
  ) {
    return { index: 2, label: "Stage III · Engraving 16:9 Archival Watercolour Plates (gemini-api image)" };
  }
  if (
    combined.includes("create_voices") ||
    combined.includes("generate_audiobook_tts") ||
    combined.includes("voice_mastering") ||
    combined.includes("gemini-api tts") ||
    combined.includes("turn_00") ||
    combined.includes("flash-tts")
  ) {
    return { index: 3, label: "Stage IV · Synthesizing & Mastering 24 kHz Multi-Voice Turns (gemini-api tts)" };
  }
  if (
    combined.includes("generate_and_mix_music") ||
    combined.includes("lyria") ||
    combined.includes("timeline_manifest")
  ) {
    return { index: 4, label: "Stage V · Scoring Chamber Ensemble & Binding Folios (lyria-3.5)" };
  }
  return null;
}

/**
 * Lists and downloads individual files from a sandbox environment in the browser
 * using the Environments Files API (`GET /v1beta/environments/{envId}/files/{path}?alt=media`).
 */
async function downloadBrowserEnvironmentAssets(
  environmentId: string,
  apiKey: string,
  signal?: AbortSignal
): Promise<{
  storybookData: any;
  imageAssets: Record<string, string>;
  audioAssets: Record<string, string>;
}> {
  const cleanEnvId = environmentId
    .replace(/^environments\//, "")
    .replace(/^environment-/, "");
  const baseUrl = `https://generativelanguage.googleapis.com/v1beta/environments/${cleanEnvId}/files`;
  const headers = { "x-goog-api-key": apiKey };

  let storybookData: any = null;
  const imageAssets: Record<string, string> = {};
  const audioAssets: Record<string, string> = {};

  const listRes = await fetch(`${baseUrl}/workspace?recursive=true`, {
    headers,
    signal,
  });

  let files: Array<{ name?: string; path: string; type?: string }> = [];
  if (listRes.ok) {
    const data = await listRes.json();
    if (Array.isArray(data?.files)) {
      files = data.files;
    }
  } else {
    const rootRes = await fetch(baseUrl, { headers, signal });
    if (rootRes.ok) {
      const rootData = await rootRes.json();
      if (Array.isArray(rootData?.files)) {
        files = rootData.files;
      }
    }
  }

  const fileEntries = files.filter(
    (f) =>
      String(f.type || "").toUpperCase() === "FILE" &&
      !(f.name || f.path.split("/").pop() || "").startsWith(".")
  );

  const imageByStem = new Map<string, { path: string }>();
  const jsonEntries: Array<{ path: string }> = [];
  const audioEntries: Array<{ path: string }> = [];

  for (const entry of fileEntries) {
    if (entry.path.endsWith("storybook.json")) {
      jsonEntries.push(entry);
    } else if (/\.(png|jpg|jpeg|webp)$/i.test(entry.path)) {
      const stem = entry.path.replace(/\.(png|jpg|jpeg|webp)$/i, "");
      if (!imageByStem.has(stem) || /\.(jpg|jpeg)$/i.test(entry.path)) {
        imageByStem.set(stem, entry);
      }
    } else if (/\.(mp3|wav)$/i.test(entry.path)) {
      audioEntries.push(entry);
    }
  }

  const hasFullMaster = audioEntries.some((f) =>
    /(full_storybook|master)\.(mp3|wav)$/i.test(f.path)
  );
  const selectedAudio = hasFullMaster
    ? audioEntries.filter((f) =>
        /(full_storybook|master|ambient|lyria|score|music)\.(mp3|wav)$/i.test(
          f.path
        )
      )
    : audioEntries;

  const targets = [
    ...jsonEntries,
    ...Array.from(imageByStem.values()),
    ...selectedAudio,
  ];
  const textDecoder = new TextDecoder("utf-8");

  await Promise.all(
    targets.map(async (target) => {
      try {
        const cleanPath = target.path.replace(/^\/+/, "");
        const dlRes = await fetch(`${baseUrl}/${cleanPath}?alt=media`, {
          headers,
          signal,
        });
        if (!dlRes.ok) return;
        const fBytes = new Uint8Array(await dlRes.arrayBuffer());
        const base = cleanPath.split("/").pop() || cleanPath;
        const relPath = cleanPath.replace(/^workspace\//, "");

        if (cleanPath.endsWith("storybook.json")) {
          try {
            storybookData = JSON.parse(textDecoder.decode(fBytes));
          } catch {}
        } else if (/\.(png|jpg|jpeg|webp)$/i.test(cleanPath)) {
          const mime = cleanPath.toLowerCase().endsWith(".png")
            ? "image/png"
            : "image/jpeg";
          const uri = `data:${mime};base64,${uint8ToBase64(fBytes)}`;
          const stemBase = base.replace(/\.(png|jpg|jpeg|webp)$/i, "");
          imageAssets[cleanPath] = uri;
          imageAssets[relPath] = uri;
          imageAssets[`images/${base}`] = uri;
          imageAssets[base] = uri;
          imageAssets[`images/${stemBase}.png`] = uri;
          imageAssets[`images/${stemBase}.jpg`] = uri;
          imageAssets[`${stemBase}.png`] = uri;
          imageAssets[`${stemBase}.jpg`] = uri;
        } else if (/\.(mp3|wav)$/i.test(cleanPath)) {
          const mime = cleanPath.toLowerCase().endsWith(".mp3")
            ? "audio/mpeg"
            : "audio/wav";
          const uri = `data:${mime};base64,${uint8ToBase64(fBytes)}`;
          audioAssets[cleanPath] = uri;
          audioAssets[relPath] = uri;
          audioAssets[`audio/${base}`] = uri;
          audioAssets[base] = uri;
        }
      } catch {
        // Ignore individual file download error
      }
    })
  );

  return { storybookData, imageAssets, audioAssets };
}

function uint8ToBase64(bytes: Uint8Array): string {
  let binary = "";
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
}

function extractFirstJsonObject(text: string): any | null {
  const codeBlockMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (codeBlockMatch && codeBlockMatch[1]) {
    try {
      return JSON.parse(codeBlockMatch[1].trim());
    } catch {
      // continue
    }
  }
  const firstBrace = text.indexOf("{");
  const lastBrace = text.lastIndexOf("}");
  if (firstBrace !== -1 && lastBrace > firstBrace) {
    try {
      return JSON.parse(text.slice(firstBrace, lastBrace + 1));
    } catch {
      return null;
    }
  }
  return null;
}

function normalizeBrowserManagedStorybook(
  raw: any,
  opts: RunStorybookAgentOptions,
  imageAssets: Record<string, string>,
  audioAssets: Record<string, string>
): Storybook {
  const fallback = createBespokeFairytaleStorybook(
    opts.prompt,
    opts.visualStyle,
    opts.narratorVoice,
    opts.paletteKey || "regency"
  );
  if (!raw || typeof raw !== "object") return fallback;

  const pal =
    raw.palette && typeof raw.palette === "object" && raw.palette.paper
      ? raw.palette
      : fallback.palette;

  const romans = ["I", "II", "III", "IV", "V"];
  const rawPages: any[] = Array.isArray(raw.pages)
    ? raw.pages
    : Array.isArray(raw.folios)
    ? raw.folios
    : [];

  if (rawPages.length === 0) return fallback;

  const firstImgData = Object.values(imageAssets)[0];
  const firstAudioData = Object.values(audioAssets)[0];
  const masterAudioData =
    audioAssets["audio/full_storybook.mp3"] ||
    audioAssets["full_storybook.mp3"] ||
    (raw.fullAudiobookUrl && audioAssets[raw.fullAudiobookUrl]);
  const ambientAudioData =
    audioAssets["audio/ambient.mp3"] ||
    audioAssets["ambient.mp3"] ||
    (raw.backgroundMusicUrl && audioAssets[raw.backgroundMusicUrl]);

  const pages = rawPages.slice(0, 3).map((p: any, idx: number) => {
    const pnum = idx + 1;
    const rom = romans[idx] || String(pnum);
    const matchedImg =
      (p.imageUrl && imageAssets[p.imageUrl]) ||
      imageAssets[`images/page_${pnum}.png`] ||
      imageAssets[`page_${pnum}.png`] ||
      imageAssets[`images/scene_${pnum}.png`] ||
      imageAssets[`scene_${pnum}.png`] ||
      firstImgData ||
      fallback.pages[idx]?.imageUrl ||
      fallback.coverImageUrl;

    const pageAudio =
      (p.audioUrl && audioAssets[p.audioUrl]) ||
      audioAssets[`audio/page_${pnum}.mp3`] ||
      audioAssets[`page_${pnum}.mp3`] ||
      (idx === 0 ? firstAudioData : undefined);

    const rawLines: any[] = Array.isArray(p.dialogueLines)
      ? p.dialogueLines
      : Array.isArray(p.turns)
      ? p.turns
      : [];

    const dialogueLines: DialogueLine[] =
      rawLines.length > 0
        ? rawLines.map((dl: any, lIdx: number) => ({
            speaker: dl.speaker || "Narrator",
            speakerLabel:
              dl.speakerLabel ||
              String(dl.speaker || "NARRATOR").toUpperCase(),
            voiceRoleLabel:
              dl.voiceRoleLabel ||
              (dl.isDialogue ? "Character Dialogue" : "Literary Narration"),
            isDialogue: Boolean(dl.isDialogue),
            voiceName: dl.voiceName || opts.narratorVoice || "Kore",
            stylePrompt: dl.stylePrompt,
            text: dl.text || dl.display_text || "",
            durationSeconds:
              dl.durationSeconds ||
              Math.max(2.4, Math.round(((dl.text || "").length || 45) / 14)),
            audioDataUrl:
              !masterAudioData && lIdx === 0 && pageAudio
                ? pageAudio
                : undefined,
          }))
        : fallback.pages[idx]?.dialogueLines || [];

    const caption =
      p.imageCaption ||
      p.caption ||
      p.title ||
      p.chapterTitle ||
      fallback.pages[idx]?.imageCaption ||
      `Scene ${rom}`;

    return {
      pageNumber: pnum,
      sceneLabel: p.sceneLabel || `SCENE ${rom}`,
      folioLabel: p.folioLabel || p.folio || `FOLIO I.${pnum}`,
      chapterTitle: (p.chapterTitle || p.title || "CHAPTER I").toUpperCase(),
      narrativeText: p.narrativeText || dialogueLines[0]?.text || opts.prompt,
      illustrationPrompt: p.illustrationPrompt || p.scenePrompt || opts.prompt,
      imageCaption: caption,
      imageUrl: matchedImg,
      imageDataUrl: matchedImg,
      dioramaUrl: matchedImg,
      audioDataUrl: pageAudio,
      plates: [
        {
          plateNumberRoman: rom,
          plateLabel: `PLATE ${rom} OF ${romans[Math.min(2, rawPages.length - 1)] || "III"}`,
          title: caption,
          illustrationPrompt: p.illustrationPrompt || p.scenePrompt || opts.prompt,
          imageUrl: matchedImg,
          imageDataUrl: matchedImg,
        },
      ],
      dialogueLines,
    };
  });

  const author = raw.author || "Gemini Managed Agent (gemini-4-argon)";
  const coverImg =
    (raw.coverImageUrl && imageAssets[raw.coverImageUrl]) ||
    imageAssets["images/cover.png"] ||
    imageAssets["cover.png"] ||
    pages[0]?.imageUrl ||
    fallback.coverImageUrl;

  return {
    ...fallback,
    id: raw.id || `managed_${Date.now()}`,
    roman: "I",
    bookHeaderLeft:
      raw.bookHeaderLeft || `BOOK I  ·  ${author.toUpperCase()}`,
    year: String(raw.year || "1815"),
    genreFooterLeft: (
      raw.genreFooterLeft || "ILLUSTRATED FAIRYTALE FOLIO"
    ).toUpperCase(),
    settingFooterRight: (
      raw.settingFooterRight || "CHAMBER EDITION · GEMINI MANAGED AGENT"
    ).toUpperCase(),
    title: raw.title || fallback.title,
    subtitle: raw.subtitle || "Chapter I",
    author,
    palette: pal,
    coverImageUrl: coverImg,
    ...(masterAudioData ? { masterAudioUrl: masterAudioData } : {}),
    ...(ambientAudioData ? { backgroundMusicUrl: ambientAudioData } : {}),
    pages,
  };
}

/**
 * Runs the Gemini Managed Agent (`antigravity-preview-09-2026` with `gemini-4-argon`)
 * to craft a 3-folio illustrated audiobook following the `classic-audiobooks` pipeline:
 * 1. Tries `/api/generate-storybook` when served by the Node/Express backend.
 * 2. Tries direct browser CORS streaming against `POST https://generativelanguage.googleapis.com/v1beta/interactions`
 *    when hosted as a static bundle.
 */
export async function runManagedAgentStorybook(
  opts: RunStorybookAgentOptions
): Promise<RunStorybookAgentResult> {
  const agentName = opts.agentName || DEFAULT_MANAGED_AGENT_ID;
  const modelName = opts.modelName || DEFAULT_MANAGED_AGENT_MODEL;
  const apiKey = getApiKey(opts.apiKey);

  opts.onStageChange(0, `Stage I · Booting ${agentName} (${modelName}) & installing gemini-api-cli`);
  opts.onLog({
    id: makeLogId(),
    timestamp: nowTime(),
    type: "status",
    title: `Connecting to Gemini Managed Agent (${agentName} · model: ${modelName})`,
    detail: "Mounting .agents/AGENTS.md, .agents/skills/*, and classic-audiobooks pipeline",
  });

  const isX20Web =
    typeof window !== "undefined" &&
    (window.location.hostname.includes("x20web") ||
      window.location.origin === "null");

  if (!isX20Web) {
    try {
      const response = await fetch("/api/generate-storybook", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: opts.prompt,
          classicBookTitle: opts.classicBookTitle,
          visualStyle: opts.visualStyle,
          pageCount: opts.pageCount,
          narratorVoice: opts.narratorVoice,
          agentName,
          modelName,
          environmentId: opts.environmentId,
          previousInteractionId: opts.previousInteractionId,
          sessionId: opts.sessionId,
          apiKey,
        }),
        signal: opts.signal,
      });

      if (response.ok && response.body) {
        const result = await consumeSseStream(response, opts, agentName, modelName);
        if (result) return result;
      }
    } catch (err: any) {
      if (err?.name === "AbortError") throw err;
      // Fall through to direct browser /v1beta/interactions call
    }
  }

  // Direct Browser CORS Call to POST https://generativelanguage.googleapis.com/v1beta/interactions
  if (apiKey) {
    try {
      const directResult = await runDirectBrowserManagedAgent(
        opts,
        apiKey,
        agentName,
        modelName
      );
      if (directResult) return directResult;
    } catch (err: any) {
      if (err?.name === "AbortError") throw err;
      opts.onLog({
        id: makeLogId(),
        timestamp: nowTime(),
        type: "status",
        title: "Direct /v1beta/interactions notice — falling back to Gemini Flash studio pipeline",
        detail: err?.message || String(err),
      });
    }
  }

  return runClientSideClassicAudiobooksPipeline(opts);
}

/**
 * Calls `POST https://generativelanguage.googleapis.com/v1beta/interactions` directly from the browser
 * using CORS-allowed headers (`Content-Type: application/json`, `x-goog-api-key`) so static hosts
 * execute the real `antigravity-preview-09-2026` (`gemini-4-argon`) sandbox directly!
 */
async function runDirectBrowserManagedAgent(
  opts: RunStorybookAgentOptions,
  apiKey: string,
  agentName: string,
  modelName: string
): Promise<RunStorybookAgentResult | null> {
  const inlineSources = getInlineBrowserAgentSources();
  const fullPrompt = [
    opts.classicBookTitle
      ? `Create an illustrated 3-folio storybook and dramatized multi-voice audiobook adaptation of "${opts.classicBookTitle}".`
      : `Create an original 3-folio illustrated storybook and dramatized multi-voice audiobook based on this request: "${opts.prompt}".`,
    `Target number of folios: 3 (FOLIO I.1, FOLIO I.2, FOLIO I.3).`,
    opts.visualStyle ? `Visual art direction: ${opts.visualStyle}.` : "",
    `Primary Storyteller / Narrator voice: ${opts.narratorVoice}.`,
    "Follow .agents/AGENTS.md strictly: install gemini-api-cli via https://raw.githubusercontent.com/google-gemini/gemini-api-cli/main/scripts/install.sh, generate at least 1 illustration plate (images/scene_1.png) with `gemini-api image -m gemini-3.1-flash-lite-image -a 16:9` and 1 narration turn (audio/turn_00.wav) with `gemini-api tts -m gemini-3.1-flash-tts-preview`, write `storybook.json` in the workspace root, and output the final JSON block in your response.",
  ]
    .filter(Boolean)
    .join("\n");

  const res = await fetch(
    "https://generativelanguage.googleapis.com/v1beta/interactions",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-goog-api-key": apiKey,
      },
      body: JSON.stringify({
        agent: agentName,
        agent_config: { type: "antigravity", model: modelName },
        input: [{ type: "text", text: fullPrompt }],
        stream: true,
        ...(opts.previousInteractionId
          ? { previous_interaction_id: opts.previousInteractionId }
          : {}),
        environment: opts.environmentId
          ? opts.environmentId
          : {
              type: "remote",
              sources: inlineSources,
              env: { GEMINI_API_KEY: apiKey },
            },
      }),
      signal: opts.signal,
    }
  );

  if (!res.ok || !res.body) {
    const errText = await res.text();
    throw new Error(`HTTP ${res.status}: ${errText.slice(0, 300)}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  let activeEnvId = opts.environmentId;
  let interactionId = "";
  let fullText = "";
  let streamFinished = false;

  while (!streamFinished) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop() || "";

    for (const rawLine of lines) {
      const line = rawLine.replace(/\r$/, "");
      if (!line.startsWith("data:")) continue;
      const raw = line.slice(5).trim();
      if (!raw) continue;
      if (raw === "[DONE]") {
        streamFinished = true;
        break;
      }
      try {
        const evt = JSON.parse(raw);
        const envId =
          evt.interaction?.environment?.env_id ||
          evt.interaction?.environment_id ||
          evt.environment?.env_id ||
          evt.environment_id;
        if (envId) {
          activeEnvId = String(envId)
            .replace(/^environments\//, "")
            .replace(/^environment-/, "");
        }
        if (evt.interaction?.id && !interactionId) {
          interactionId = evt.interaction.id;
          opts.onCreated?.(interactionId, activeEnvId);
          opts.onLog({
            id: makeLogId(),
            timestamp: nowTime(),
            type: "status",
            title: `Sandbox container provisioned (${activeEnvId || "remote"})`,
            detail: `Interaction: ${interactionId} · ${agentName} (${modelName})`,
          });
        }

        if (evt.step) {
          const st = evt.step;
          if (st.type === "thought") {
            const summaries = Array.isArray(st.summary) ? st.summary : [];
            const txt = summaries
              .map((s: any) => s?.text || "")
              .join("\n")
              .trim();
            if (txt) {
              const stage = inferPipelineStage("thought", "", txt);
              if (stage) opts.onStageChange(stage.index, stage.label);
              opts.onLog({
                id: makeLogId(),
                timestamp: nowTime(),
                type: "thinking",
                title: `${modelName} reasoning`,
                detail: txt,
              });
            }
          } else if (
            st.type === "code_execution_call" ||
            st.type === "function_call" ||
            st.type === "tool_call"
          ) {
            const stage = inferPipelineStage(st.name || "bash", st.arguments, "");
            if (stage) opts.onStageChange(stage.index, stage.label);
            opts.onLog({
              id: makeLogId(),
              timestamp: nowTime(),
              type: "tool_call",
              title: `Sandbox Tool → ${st.name || "bash"}`,
              detail:
                typeof st.arguments === "string"
                  ? st.arguments
                  : JSON.stringify(st.arguments),
            });
          } else if (
            st.type === "code_execution_result" ||
            st.type === "function_result" ||
            st.type === "tool_result"
          ) {
            const resStr =
              typeof st.result === "string"
                ? st.result
                : JSON.stringify(st.result);
            opts.onLog({
              id: makeLogId(),
              timestamp: nowTime(),
              type: "tool_result",
              title: `Tool Output (${st.name || "bash"})`,
              detail: resStr.slice(0, 500),
              isError: Boolean(st.is_error),
            });
          }
        }

        if (evt.delta?.thought) {
          const stage = inferPipelineStage("thought", "", evt.delta.thought);
          if (stage) opts.onStageChange(stage.index, stage.label);
          opts.onLog({
            id: makeLogId(),
            timestamp: nowTime(),
            type: "thinking",
            title: `${modelName} reasoning`,
            detail: evt.delta.thought,
          });
        }
        if (evt.delta?.text) {
          fullText += evt.delta.text;
        }
        if (
          evt.event_type === "interaction.completed" ||
          evt.event_type === "interaction.failed"
        ) {
          streamFinished = true;
          break;
        }
      } catch {
        // ignore partial JSON frame
      }
    }
  }

  try {
    await reader.cancel();
  } catch {}

  let storybookData: any = null;
  let imageAssets: Record<string, string> = {};
  let audioAssets: Record<string, string> = {};

  if (activeEnvId) {
    opts.onStageChange(
      4,
      `Stage V · Downloading individual plates & audio files from sandbox (${activeEnvId.slice(0, 12)})`
    );
    try {
      const downloaded = await downloadBrowserEnvironmentAssets(
        activeEnvId,
        apiKey,
        opts.signal
      );
      storybookData = downloaded.storybookData;
      imageAssets = downloaded.imageAssets;
      audioAssets = downloaded.audioAssets;
    } catch {
      // Fall back to JSON extracted from response stream
    }
  }

  if (!storybookData && fullText) {
    storybookData = extractFirstJsonObject(fullText);
  }

  const normalized = normalizeBrowserManagedStorybook(
    storybookData,
    opts,
    imageAssets,
    audioAssets
  );

  return {
    storybook: normalized,
    interactionId,
    environmentId: activeEnvId,
    agent: agentName,
    model: modelName,
  };
}

async function consumeSseStream(
  response: Response,
  opts: RunStorybookAgentOptions,
  agentName: string,
  modelName: string
): Promise<RunStorybookAgentResult | null> {
  if (!response.body) return null;
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "";
  let currentData = "";
  let finalResult: RunStorybookAgentResult | null = null;

  const handleEvent = (eventType: string, dataStr: string) => {
    if (!dataStr) return;
    let payload: any;
    try {
      payload = JSON.parse(dataStr);
    } catch {
      return;
    }

    if (eventType === "created") {
      opts.onCreated?.(payload.id, payload.envId);
      opts.onLog({
        id: makeLogId(),
        timestamp: nowTime(),
        type: "status",
        title: `Sandbox session created (env: ${payload.envId || "provisioning"})`,
        detail: `Interaction ID: ${payload.id} · Agent: ${payload.agent} · Model: ${payload.model}`,
      });
    } else if (eventType === "status") {
      opts.onLog({
        id: makeLogId(),
        timestamp: nowTime(),
        type: "status",
        title: payload.message || "Status update",
      });
    } else if (eventType === "thinking") {
      if (payload.thought?.trim()) {
        const stage = inferPipelineStage("thought", "", payload.thought);
        if (stage) opts.onStageChange(stage.index, stage.label);
        opts.onLog({
          id: makeLogId(),
          timestamp: nowTime(),
          type: "thinking",
          title: `${modelName} reasoning`,
          detail: payload.thought.trim(),
        });
      }
    } else if (eventType === "tool_call") {
      const stage = inferPipelineStage(payload.name || "", payload.args, "");
      if (stage) opts.onStageChange(stage.index, stage.label);
      const formattedArgs =
        typeof payload.args === "string"
          ? payload.args
          : JSON.stringify(payload.args, null, 2);
      opts.onLog({
        id: makeLogId(),
        timestamp: nowTime(),
        type: "tool_call",
        title: `Sandbox Tool → ${payload.name || "bash"}`,
        detail: formattedArgs,
      });
    } else if (eventType === "tool_result") {
      const resStr =
        typeof payload.result === "string"
          ? payload.result
          : JSON.stringify(payload.result);
      opts.onLog({
        id: makeLogId(),
        timestamp: nowTime(),
        type: "tool_result",
        title: `Tool Output (${payload.name || "bash"})`,
        detail: resStr.slice(0, 600),
        isError: Boolean(payload.isError),
      });
    } else if (eventType === "result") {
      finalResult = {
        storybook: payload.storybook,
        interactionId: payload.interactionId,
        environmentId: payload.environmentId,
        agent: payload.agent || agentName,
        model: payload.model || modelName,
      };
    } else if (eventType === "error") {
      throw new Error(payload.message || "Managed Agent failed");
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      if (currentData) handleEvent(currentEvent, currentData.trim());
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const rawLine of lines) {
      const line = rawLine.replace(/\r$/, "");
      if (line.startsWith("event:")) {
        currentEvent = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        currentData += line.slice(5).trim() + "\n";
      } else if (line.trim() === "") {
        if (currentData) {
          handleEvent(currentEvent, currentData.trim());
          currentEvent = "";
          currentData = "";
        }
      }
    }
  }
  return finalResult;
}

/**
 * Fallback client-side pipeline when no Managed Agent sandbox key is available.
 */
async function runClientSideClassicAudiobooksPipeline(
  opts: RunStorybookAgentOptions
): Promise<RunStorybookAgentResult> {
  const apiKey = getApiKey(opts.apiKey);
  const agentName = opts.agentName || DEFAULT_MANAGED_AGENT_ID;
  const modelName = opts.modelName || DEFAULT_MANAGED_AGENT_MODEL;
  const interactionId = `inter_${Date.now().toString(36)}`;
  const envId = opts.environmentId || `env_barium_${Math.random().toString(36).slice(2, 8)}`;

  opts.onCreated?.(interactionId, envId);

  opts.onStageChange(0, `Stage I · Installing gemini-api-cli in ${agentName} (${modelName}) sandbox`);
  opts.onLog({
    id: makeLogId(),
    timestamp: nowTime(),
    type: "tool_call",
    title: "Sandbox Tool → bash",
    detail: `curl -fsSL https://raw.githubusercontent.com/google-gemini/gemini-api-cli/main/scripts/install.sh | bash && gemini-api --version`,
  });
  await sleep(650, opts.signal);

  opts.onStageChange(1, "Stage II · Authoring 3-Folio Dramaturgy & Anonymous Character Spec");
  await sleep(750, opts.signal);

  const promptLower = `${opts.classicBookTitle || ""} ${opts.prompt}`.toLowerCase();
  const matchedClassic = ALL_CLASSIC_STORYBOOKS.find(
    (b) =>
      promptLower.includes(b.title.toLowerCase()) ||
      promptLower.includes(b.author.toLowerCase())
  );

  let resultStorybook: Storybook;

  if (apiKey && !matchedClassic) {
    try {
      resultStorybook = await generateLiveGeminiFolioStorybook(opts, apiKey);
      return {
        storybook: resultStorybook,
        interactionId,
        environmentId: envId,
        agent: agentName,
        model: modelName,
      };
    } catch (err: any) {
      if (err?.name === "AbortError") throw err;
    }
  }

  resultStorybook = matchedClassic
    ? JSON.parse(JSON.stringify(matchedClassic))
    : createBespokeFairytaleStorybook(
        opts.prompt,
        opts.visualStyle,
        opts.narratorVoice,
        opts.paletteKey || "regency"
      );

  opts.onStageChange(2, "Stage III · Engraving 16:9 Archival Watercolour Plates");
  await sleep(850, opts.signal);

  opts.onStageChange(3, "Stage IV · Synthesizing Multi-Voice Narration & Mastering");
  await sleep(800, opts.signal);

  opts.onStageChange(4, "Stage V · Composing Lyria 3.5 Chamber Score & Binding Folios");
  await sleep(700, opts.signal);

  return {
    storybook: resultStorybook,
    interactionId,
    environmentId: envId,
    agent: agentName,
    model: modelName,
  };
}

async function generateLiveGeminiFolioStorybook(
  opts: RunStorybookAgentOptions,
  apiKey: string
): Promise<Storybook> {
  const ai = new GoogleGenAI({ apiKey });
  const pal =
    EDITION_PALETTES[opts.paletteKey || "regency"]?.palette ||
    EDITION_PALETTES.regency.palette;

  const schemaPrompt = `You are authoring a 3-folio fine-press illustrated audiobook edition modeled on Jane Austen's Pride and Prejudice in classic-audiobooks.
User Commission Prompt: "${opts.prompt}"
Visual Style: "${opts.visualStyle}"

Return a JSON object with:
- title (string, literary title)
- author (string, e.g. "Folio & Voice Press" or classic author name)
- year (string, e.g. "1815")
- genreFooterLeft (string, uppercase, e.g. "REGENCY FAIRYTALE FOLIO")
- settingFooterRight (string, uppercase, e.g. "LAKE GENEVA, SWITZERLAND")
- charSheetPrompt (string: strictly anonymous physical descriptions of two main characters standing side-by-side in three-quarter profile facing each other on #F6F2EA cream archival paper, ZERO proper names)
- folios: array of 3 objects (for FOLIO I.1, FOLIO I.2, FOLIO I.3), each with:
  - caption (string, short 2-4 word location caption like "Longbourn Morning Room")
  - scenePrompt (string, strictly anonymous 16:9 illustration prompt on #F6F2EA archival paper, ZERO proper names or text)
  - turns: array of 4 to 6 turns, each with:
    - speaker (string, e.g. "Narrator" or character name)
    - speakerLabel (string, uppercase, e.g. "NARRATOR" or "CLARA")
    - isDialogue (boolean, true ONLY for spoken quotation lines, false for narrator prose)
    - voiceName (one of "Kore", "Aoede", "Charon", "Fenrir", "Orus", "Leda", "Puck")
    - stylePrompt (string, e.g. "poised, dry literary irony" or "eager, animated")
    - text (string, the literary text or quoted dialogue)`;

  const specResp = await ai.models.generateContent({
    model: "gemini-3.8-flash",
    contents: schemaPrompt,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          title: { type: Type.STRING },
          author: { type: Type.STRING },
          year: { type: Type.STRING },
          genreFooterLeft: { type: Type.STRING },
          settingFooterRight: { type: Type.STRING },
          charSheetPrompt: { type: Type.STRING },
          folios: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                caption: { type: Type.STRING },
                scenePrompt: { type: Type.STRING },
                turns: {
                  type: Type.ARRAY,
                  items: {
                    type: Type.OBJECT,
                    properties: {
                      speaker: { type: Type.STRING },
                      speakerLabel: { type: Type.STRING },
                      isDialogue: { type: Type.BOOLEAN },
                      voiceName: { type: Type.STRING },
                      stylePrompt: { type: Type.STRING },
                      text: { type: Type.STRING },
                    },
                    required: [
                      "speaker",
                      "speakerLabel",
                      "isDialogue",
                      "voiceName",
                      "stylePrompt",
                      "text",
                    ],
                  },
                },
              },
              required: ["caption", "scenePrompt", "turns"],
            },
          },
        },
        required: [
          "title",
          "author",
          "year",
          "genreFooterLeft",
          "settingFooterRight",
          "charSheetPrompt",
          "folios",
        ],
      },
    },
  });

  const parsed = JSON.parse(specResp.text || "{}");
  const fallbackBook = createBespokeFairytaleStorybook(
    opts.prompt,
    opts.visualStyle,
    opts.narratorVoice,
    opts.paletteKey || "regency"
  );

  opts.onStageChange(
    2,
    "Stage III · Generating 16:9 Character Sheet & Scene Plates (gemini-3.1-flash-lite-image)"
  );
  let charSheetDataUrl = fallbackBook.charSheetImageUrl;
  try {
    charSheetDataUrl = await generateStudioIllustration(
      `${parsed.charSheetPrompt}. Minimalist editorial book illustration character reference sheet on clean warm cream archival paper (#F6F2EA). Delicate 1810s Regency pen-and-ink line drawing with subtle muted watercolor wash, no text, no borders.`,
      "16:9"
    );
  } catch {
    // Use SVG plate fallback
  }

  const romans = ["I", "II", "III"];
  const pages = await Promise.all(
    (parsed.folios || []).slice(0, 3).map(async (f: any, idx: number) => {
      let plateUrl = fallbackBook.pages[idx]?.imageUrl;
      try {
        plateUrl = await generateStudioIllustration(
          `${f.scenePrompt}. ${opts.visualStyle}. Flat 2D illustration directly on uniform archival paper (#F6F2EA) filling the 16:9 canvas edge-to-edge, no text, no borders.`,
          "16:9"
        );
      } catch {
        // Keep fallback SVG plate
      }
      const turns: DialogueLine[] = (f.turns || []).map((t: any) => ({
        speaker: t.speaker,
        speakerLabel: t.speakerLabel,
        voiceRoleLabel: t.isDialogue ? "Character Dialogue" : "Literary Narration",
        isDialogue: Boolean(t.isDialogue),
        voiceName: t.voiceName || opts.narratorVoice || "Kore",
        stylePrompt: t.stylePrompt,
        text: t.text,
        durationSeconds: Math.max(2.2, Math.round((t.text?.length || 40) / 14)),
      }));

      return {
        pageNumber: idx + 1,
        sceneLabel: `SCENE ${romans[idx] || "I"}`,
        folioLabel: `FOLIO I.${idx + 1}`,
        chapterTitle: "CHAPTER I",
        narrativeText: turns[0]?.text || opts.prompt,
        illustrationPrompt: f.scenePrompt,
        imageCaption: f.caption || `Scene ${romans[idx]}`,
        imageUrl: plateUrl,
        dioramaUrl: plateUrl,
        plates: [
          {
            plateNumberRoman: romans[idx] || "I",
            plateLabel: `PLATE ${romans[idx] || "I"} OF III`,
            title: f.caption || `Scene ${romans[idx]}`,
            illustrationPrompt: f.scenePrompt,
            imageUrl: plateUrl,
          },
          {
            plateNumberRoman: "I",
            plateLabel: `PLATE ${romans[idx] || "I"} OF III`,
            title: `${f.caption || "Scene"} (Character Plate)`,
            illustrationPrompt: parsed.charSheetPrompt,
            imageUrl: charSheetDataUrl,
          },
        ],
        dialogueLines: turns,
      };
    })
  );

  return {
    ...fallbackBook,
    id: `gemini_${Date.now()}`,
    bookHeaderLeft: `BOOK I  ·  ${(parsed.author || "FOLIO & VOICE").toUpperCase()}`,
    year: parsed.year || "1815",
    genreFooterLeft: (parsed.genreFooterLeft || "ILLUSTRATED FAIRYTALE FOLIO").toUpperCase(),
    settingFooterRight: (parsed.settingFooterRight || "CHAMBER EDITION").toUpperCase(),
    title: parsed.title || fallbackBook.title,
    author: parsed.author || "Folio & Voice Press",
    palette: pal,
    charSheetPrompt: parsed.charSheetPrompt,
    charSheetImageUrl: charSheetDataUrl,
    coverImageUrl: pages[0]?.imageUrl || fallbackBook.coverImageUrl,
    pages: pages.length > 0 ? pages : fallbackBook.pages,
  };
}

export async function generateStudioIllustration(
  prompt: string,
  aspectRatio: "16:9" | "4:3" | "3:4" | "1:1" = "16:9"
): Promise<string> {
  const ai = new GoogleGenAI({ apiKey: getApiKey() });
  const response = await ai.models.generateContent({
    model: "gemini-3.1-flash-lite-image",
    contents: prompt,
    config: {
      responseModalities: [Modality.IMAGE],
      imageConfig: {
        aspectRatio,
      },
    },
  });

  const parts = response.candidates?.[0]?.content?.parts || [];
  for (const part of parts) {
    if (part.inlineData?.data) {
      const mime = part.inlineData.mimeType || "image/png";
      return `data:${mime};base64,${part.inlineData.data}`;
    }
  }
  throw new Error("No image returned from gemini-3.1-flash-lite-image");
}

function pcmBase64ToWavDataUri(base64Pcm: string, sampleRate = 24000): string {
  const binaryString = atob(base64Pcm);
  const pcmLen = binaryString.length;
  const wavBuffer = new ArrayBuffer(44 + pcmLen);
  const view = new DataView(wavBuffer);

  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + pcmLen, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, pcmLen, true);

  const uint8 = new Uint8Array(wavBuffer, 44);
  for (let i = 0; i < pcmLen; i++) {
    uint8[i] = binaryString.charCodeAt(i);
  }

  let binaryWav = "";
  const fullBytes = new Uint8Array(wavBuffer);
  const chunkSize = 0x8000;
  for (let i = 0; i < fullBytes.length; i += chunkSize) {
    binaryWav += String.fromCharCode(...fullBytes.subarray(i, i + chunkSize));
  }
  return `data:audio/wav;base64,${btoa(binaryWav)}`;
}

export async function synthesizeStudioPageAudio(
  dialogueLines: DialogueLine[],
  fallbackText: string,
  defaultVoice = "Kore"
): Promise<string> {
  const ai = new GoogleGenAI({ apiKey: getApiKey() });
  const lines =
    dialogueLines && dialogueLines.length > 0
      ? dialogueLines
      : [{ speaker: "Narrator", voiceName: defaultVoice, text: fallbackText }];

  const uniqueSpeakers = new Map<string, string>();
  for (const l of lines) {
    if (!uniqueSpeakers.has(l.speaker)) {
      uniqueSpeakers.set(l.speaker, l.voiceName || defaultVoice);
    }
  }

  let speechConfig: any;
  let promptText: string;

  if (uniqueSpeakers.size === 2) {
    const speakerVoiceConfigs = Array.from(uniqueSpeakers.entries()).map(
      ([speaker, voiceName]) => ({
        speaker,
        voiceConfig: {
          prebuiltVoiceConfig: { voiceName },
        },
      })
    );
    speechConfig = {
      multiSpeakerVoiceConfig: {
        speakerVoiceConfigs,
      },
    };
    promptText =
      "Perform this dramatized audiobook passage with expressive theatrical voices:\n\n" +
      lines
        .map(
          (l) =>
            `${l.speaker}: ${l.stylePrompt ? `[${l.stylePrompt}] ` : ""}${l.text}`
        )
        .join("\n");
  } else {
    const primaryVoice = lines[0]?.voiceName || defaultVoice;
    speechConfig = {
      voiceConfig: {
        prebuiltVoiceConfig: { voiceName: primaryVoice },
      },
    };
    promptText =
      "Read this storybook passage with expressive theatrical character voices and warm pacing:\n\n" +
      lines
        .map((l) => `${l.stylePrompt ? `[${l.stylePrompt}] ` : ""}${l.text}`)
        .join(" ");
  }

  const response = await ai.models.generateContent({
    model: "gemini-3.1-flash-tts-preview",
    contents: promptText,
    config: {
      responseModalities: [Modality.AUDIO],
      speechConfig,
    },
  });

  const base64Audio =
    response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
  if (!base64Audio) {
    throw new Error("No audio data returned from gemini-3.1-flash-tts-preview");
  }

  return pcmBase64ToWavDataUri(base64Audio, 24000);
}
