import fs from "fs";

export const DEFAULT_AGENT_NAME = "antigravity-preview-09-2026";
export const DEFAULT_MODEL_NAME = "gemini-4-argon";

export function isPlaceholderApiKey(key?: string | null): boolean {
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

export function resolveServerApiKey(overrideKey?: string): string {
  const candidates: Array<string | undefined> = [
    overrideKey,
    process.env.API_KEY,
    process.env.GEMINI_API_KEY,
  ];

  try {
    if (fs.existsSync("/app/.dev.env.json")) {
      const devEnv = JSON.parse(fs.readFileSync("/app/.dev.env.json", "utf-8"));
      candidates.push(devEnv?.API_KEY, devEnv?.GEMINI_API_KEY);
    }
  } catch {
    // Ignore if /app/.dev.env.json is not present or unreadable
  }

  for (const candidate of candidates) {
    if (!isPlaceholderApiKey(candidate)) {
      return candidate!.trim();
    }
  }
  return "";
}

export interface InlineSource {
  type: "inline";
  content: string;
  target: string;
}

export interface CreateInteractionOptions {
  prompt: string;
  inlineSources?: InlineSource[];
  environmentId?: string;
  previousInteractionId?: string;
  agentName?: string;
  modelName?: string;
  apiKey?: string;
  signal?: AbortSignal;
}

export type StreamCallbacks = {
  onCreated?: (id: string, envId?: string) => void;
  onStatus?: (status: string) => void;
  onThinking?: (thought: string) => void;
  onText?: (text: string) => void;
  onToolCall?: (name: string, args: unknown, id?: string) => void;
  onToolResult?: (name: string, result: unknown, isError?: boolean, callId?: string) => void;
  onComplete?: (interaction: Record<string, unknown>, envId?: string) => void;
  onError?: (error: unknown) => void;
};

export function extractEnvironmentId(obj: Record<string, unknown> | undefined): string | undefined {
  if (!obj) return undefined;
  const env = obj.environment as Record<string, unknown> | undefined;
  let id: unknown =
    env?.env_id ??
    env?.environment_id ??
    env?.id ??
    env?.name ??
    obj.env_id ??
    obj.environment_id;

  if (typeof id === "string" && id.trim().length > 0) {
    id = id.replace(/^environments\//, "").replace(/^environment-/, "");
    return id as string;
  }
  return undefined;
}

export function extractInteractionId(obj: Record<string, unknown> | undefined): string | undefined {
  if (!obj) return undefined;
  const id = obj.id ?? obj.interaction_id ?? obj.name;
  if (typeof id === "string" && id.trim().length > 0) {
    return id.replace(/^interactions\//, "");
  }
  return undefined;
}

export async function createInteraction(opts: CreateInteractionOptions): Promise<Response> {
  const apiKey = resolveServerApiKey(opts.apiKey);
  const url = "https://generativelanguage.googleapis.com/v1beta/interactions";

  const body: Record<string, unknown> = {
    agent: opts.agentName || DEFAULT_AGENT_NAME,
    agent_config: {
      type: "antigravity",
      model: opts.modelName || DEFAULT_MODEL_NAME,
    },
    input: [{ type: "text", text: opts.prompt }],
    stream: true,
    environment: opts.environmentId
      ? opts.environmentId
      : {
          type: "remote",
          sources: opts.inlineSources ?? [],
          env: {
            GEMINI_API_KEY: apiKey,
          },
        },
  };

  if (opts.previousInteractionId) {
    body.previous_interaction_id = opts.previousInteractionId;
  }

  return fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-goog-api-key": apiKey,
      "x-server-timeout": "600",
      "Api-Revision": "2026-05-20",
      "x-goog-api-client": "applet-storybook-managed-agent/1.0.0",
    },
    body: JSON.stringify(body),
    signal: opts.signal,
  });
}

export async function streamInteraction(response: Response, callbacks: StreamCallbacks) {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP error ${response.status}: ${errorText}`);
  }
  if (!response.body) {
    throw new Error("Response body is null");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "";
  let currentData = "";
  let capturedEnvId: string | undefined;

  let streamFinished = false;

  const processEvent = (eventType: string, dataStr: string) => {
    if (!dataStr) return;
    if (dataStr === "[DONE]" || eventType === "done") {
      streamFinished = true;
      return;
    }
    try {
      const data = JSON.parse(dataStr);
      const type = eventType || data.event_type;

      const envId =
        extractEnvironmentId(data) ??
        extractEnvironmentId(data.interaction) ??
        extractEnvironmentId(data.step);
      if (envId) capturedEnvId = envId;

      if (type === "interaction.created" || type === "interaction.start") {
        const id = extractInteractionId(data.interaction) ?? extractInteractionId(data);
        if (id) callbacks.onCreated?.(id, capturedEnvId);
      } else if (type === "interaction.status_update") {
        callbacks.onStatus?.(data.status);
      } else if (type === "step.start" && data.step) {
        const step = data.step;
        if (step.type === "thought") {
          const summaries = Array.isArray(step.summary) ? step.summary : [];
          const txt = summaries.map((s: any) => s?.text || "").join("\n").trim();
          if (txt) callbacks.onThinking?.(txt);
        } else if (step.type === "code_execution_call" || step.type === "function_call" || step.type === "tool_call") {
          callbacks.onToolCall?.(step.name || "bash", step.arguments, step.id);
        } else if (step.type === "code_execution_result" || step.type === "function_result" || step.type === "tool_result") {
          callbacks.onToolResult?.(step.name || "bash", step.result, step.is_error, step.call_id);
        }
      } else if (type === "step.delta") {
        const delta = data.delta;
        if (!delta) return;
        if (delta.type === "thinking" || delta.thought) {
          callbacks.onThinking?.(delta.thought || "");
        } else if (delta.type === "text" || typeof delta.text === "string") {
          callbacks.onText?.(delta.text || "");
        } else if (delta.type === "tool_call" || delta.type === "code_execution_call" || delta.type === "function_call") {
          callbacks.onToolCall?.(delta.name || "bash", delta.arguments, delta.id);
        } else if (delta.type === "tool_result" || delta.type === "code_execution_result" || delta.type === "function_result") {
          callbacks.onToolResult?.(delta.name || "bash", delta.result, delta.is_error, delta.call_id);
        }
      } else if (type === "interaction.completed" || type === "interaction.complete") {
        callbacks.onComplete?.(data.interaction || data, capturedEnvId);
        streamFinished = true;
      } else if (type === "interaction.failed" || type === "error") {
        callbacks.onError?.(data.error || data);
        streamFinished = true;
      }
    } catch {
      // Ignore partial JSON frames
    }
  };

  while (!streamFinished) {
    const { done, value } = await reader.read();
    if (done) {
      if (currentData) processEvent(currentEvent, currentData.trim());
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
          processEvent(currentEvent, currentData.trim());
          currentEvent = "";
          currentData = "";
          if (streamFinished) break;
        }
      }
    }
  }
  try {
    await reader.cancel();
  } catch {
    // ignore cancel errors
  }
}

export interface EnvironmentFileEntry {
  name: string;
  path: string;
  type: "FILE" | "DIRECTORY" | string;
  size_bytes?: string;
  mime_type?: string;
  created?: string;
  modified?: string;
}

const IGNORED_SANDBOX_ROOT_DIRS = new Set([
  ".agents",
  ".local",
  ".cache",
  ".npm",
  ".git",
  ".venv",
  "venv",
  "node_modules",
  "usr",
  "bin",
  "sbin",
  "lib",
  "lib64",
  "etc",
  "proc",
  "sys",
  "var",
  "tmp",
  "opt",
  "dev",
  "run",
  "boot",
  "root",
  "home",
  "mnt",
  "media",
  "srv",
]);

/**
 * Lists files or directories in a sandbox environment using the Environments Files API:
 * GET https://generativelanguage.googleapis.com/v1beta/environments/{envId}/files/{dirPath}
 */
export async function listEnvironmentFiles(
  environmentId: string,
  dirPath = "",
  opts?: { recursive?: boolean; apiKey?: string; signal?: AbortSignal }
): Promise<EnvironmentFileEntry[]> {
  const apiKey = resolveServerApiKey(opts?.apiKey);
  const cleanEnvId = environmentId
    .replace(/^environments\//, "")
    .replace(/^environment-/, "");
  const cleanPath = dirPath.replace(/^\/+/, "").replace(/\/+$/, "");
  const pathSuffix = cleanPath ? `/${cleanPath}` : "";
  const query = opts?.recursive ? "?recursive=true" : "";
  const url = `https://generativelanguage.googleapis.com/v1beta/environments/${cleanEnvId}/files${pathSuffix}${query}`;

  const res = await fetch(url, {
    method: "GET",
    headers: {
      "x-goog-api-key": apiKey,
      "Api-Revision": "2026-05-20",
    },
    signal: opts?.signal ?? AbortSignal.timeout(15000),
  });

  if (!res.ok) {
    return [];
  }

  const data = (await res.json()) as { files?: EnvironmentFileEntry[] };
  return Array.isArray(data?.files) ? data.files : [];
}

/**
 * Downloads a single file's raw bytes from a sandbox environment using the Environments Files API:
 * GET https://generativelanguage.googleapis.com/v1beta/environments/{envId}/files/{filePath}?alt=media
 */
export async function downloadEnvironmentFile(
  environmentId: string,
  filePath: string,
  opts?: { apiKey?: string; signal?: AbortSignal }
): Promise<{ buffer: Buffer; mimeType: string }> {
  const apiKey = resolveServerApiKey(opts?.apiKey);
  const cleanEnvId = environmentId
    .replace(/^environments\//, "")
    .replace(/^environment-/, "");
  const cleanPath = filePath.replace(/^\/+/, "");
  const url = `https://generativelanguage.googleapis.com/v1beta/environments/${cleanEnvId}/files/${cleanPath}?alt=media`;

  const res = await fetch(url, {
    method: "GET",
    headers: {
      "x-goog-api-key": apiKey,
      "Api-Revision": "2026-05-20",
    },
    signal: opts?.signal ?? AbortSignal.timeout(30000),
  });

  if (!res.ok) {
    throw new Error(`Failed to download ${cleanPath} (${res.status})`);
  }

  const arrayBuffer = await res.arrayBuffer();
  const mimeType = res.headers.get("content-type") || "application/octet-stream";
  return {
    buffer: Buffer.from(arrayBuffer),
    mimeType,
  };
}

/**
 * Discovers and downloads individual storybook assets (storybook.json, images, audio)
 * directly from the sandbox environment via the Environments Files API without downloading a full tar snapshot.
 */
export async function downloadSandboxStorybookAssets(
  environmentId: string,
  opts?: {
    apiKey?: string;
    signal?: AbortSignal;
    onStatus?: (message: string) => void;
  }
): Promise<{
  storybookData: Record<string, any> | null;
  timelineManifest: Record<string, any> | null;
  imageAssets: Record<string, string>;
  audioAssets: Record<string, string>;
  files: EnvironmentFileEntry[];
}> {
  const apiKey = resolveServerApiKey(opts?.apiKey);
  const imageAssets: Record<string, string> = {};
  const audioAssets: Record<string, string> = {};
  let storybookData: Record<string, any> | null = null;
  let timelineManifest: Record<string, any> | null = null;

  opts?.onStatus?.(
    `Listing workspace files in sandbox environment (${environmentId.slice(0, 12)})...`
  );

  // 1. List root entries first so we skip system directories like usr/ and .local/
  const rootEntries = await listEnvironmentFiles(environmentId, "", {
    recursive: false,
    apiKey,
    signal: opts?.signal,
  });

  const candidateFiles: EnvironmentFileEntry[] = [];
  const dirsToList: string[] = [];

  for (const entry of rootEntries) {
    const entryType = String(entry.type || "").toUpperCase();
    const name = entry.name || entry.path.split("/").pop() || "";
    if (entryType === "FILE") {
      if (!name.startsWith(".")) {
        candidateFiles.push(entry);
      }
    } else if (entryType === "DIRECTORY") {
      if (!IGNORED_SANDBOX_ROOT_DIRS.has(name) && !name.startsWith(".")) {
        dirsToList.push(entry.path);
      }
    }
  }

  if (dirsToList.length === 0) {
    dirsToList.push("workspace");
  }

  const nestedLists = await Promise.all(
    dirsToList.map((dirPath) =>
      listEnvironmentFiles(environmentId, dirPath, {
        recursive: true,
        apiKey,
        signal: opts?.signal,
      })
    )
  );

  for (const list of nestedLists) {
    for (const entry of list) {
      const entryType = String(entry.type || "").toUpperCase();
      const baseName = entry.name || entry.path.split("/").pop() || "";
      if (entryType === "FILE" && !baseName.startsWith(".")) {
        candidateFiles.push(entry);
      }
    }
  }

  // 2. Categorize and deduplicate target files to download individually
  const jsonFiles = candidateFiles.filter(
    (f) =>
      f.path.endsWith("storybook.json") ||
      f.path.endsWith("timeline_manifest.json")
  );

  // Group image files by directory + stem so if both page_1.jpg and page_1.png exist, we download once
  const imageByStem = new Map<string, EnvironmentFileEntry>();
  for (const f of candidateFiles) {
    if (!/\.(png|jpg|jpeg|webp)$/i.test(f.path)) continue;
    const stem = f.path.replace(/\.(png|jpg|jpeg|webp)$/i, "");
    const existing = imageByStem.get(stem);
    if (!existing) {
      imageByStem.set(stem, f);
    } else {
      // Prefer .jpg/.jpeg when both exist as they are smaller and faster to transfer
      if (/\.(jpg|jpeg)$/i.test(f.path) && !/\.(jpg|jpeg)$/i.test(existing.path)) {
        imageByStem.set(stem, f);
      }
    }
  }
  const imageFiles = Array.from(imageByStem.values());

  // Select audio files: if full_storybook.mp3 exists, download full_storybook.mp3 + ambient.mp3
  // (avoiding redundant downloads of intermediate page_1..N.mp3 tracks already mixed into full_storybook.mp3)
  const allAudioFiles = candidateFiles.filter((f) =>
    /\.(mp3|wav)$/i.test(f.path)
  );
  const hasFullMasterAudio = allAudioFiles.some((f) =>
    /(full_storybook|master)\.(mp3|wav)$/i.test(f.path)
  );
  const audioFiles = hasFullMasterAudio
    ? allAudioFiles.filter((f) =>
        /(full_storybook|master|ambient|lyria|score|music)\.(mp3|wav)$/i.test(
          f.path
        )
      )
    : allAudioFiles;

  const filesToDownload = [...jsonFiles, ...imageFiles, ...audioFiles];
  const cleanEnvId = environmentId
    .replace(/^environments\//, "")
    .replace(/^environment-/, "");

  // Pre-register direct proxy URLs (/api/environments/:envId/file?path=...) for every discovered image/audio file
  // so every asset reference resolves even before or if base64 inlining is skipped.
  for (const file of candidateFiles) {
    const filePath = file.path.replace(/^\/+/, "");
    const relWorkspacePath = filePath.replace(/^workspace\//, "");
    const baseName = filePath.split("/").pop() || filePath;
    const proxyUrl = `/api/environments/${cleanEnvId}/file?path=${encodeURIComponent(filePath)}`;

    if (/\.(png|jpg|jpeg|webp)$/i.test(filePath)) {
      const stemBase = baseName.replace(/\.(png|jpg|jpeg|webp)$/i, "");
      imageAssets[filePath] = proxyUrl;
      imageAssets[relWorkspacePath] = proxyUrl;
      imageAssets[`images/${baseName}`] = proxyUrl;
      imageAssets[baseName] = proxyUrl;
      imageAssets[`images/${stemBase}.png`] = proxyUrl;
      imageAssets[`images/${stemBase}.jpg`] = proxyUrl;
      imageAssets[`${stemBase}.png`] = proxyUrl;
      imageAssets[`${stemBase}.jpg`] = proxyUrl;
    } else if (/\.(mp3|wav)$/i.test(filePath)) {
      audioAssets[filePath] = proxyUrl;
      audioAssets[relWorkspacePath] = proxyUrl;
      audioAssets[`audio/${baseName}`] = proxyUrl;
      audioAssets[baseName] = proxyUrl;
    }
  }

  opts?.onStatus?.(
    `Downloading ${filesToDownload.length} individual files from sandbox environment...`
  );

  // 3. Download each individual file via GET /v1beta/environments/{envId}/files/{path}?alt=media
  // with bounded concurrency (3) so per-request timeouts only start when the request begins.
  const queue = [...filesToDownload];
  const concurrency = Math.min(3, queue.length);

  const workers = Array.from({ length: concurrency }, async () => {
    while (queue.length > 0) {
      const file = queue.shift();
      if (!file) break;
      try {
        const { buffer } = await downloadEnvironmentFile(
          environmentId,
          file.path,
          { apiKey, signal: opts?.signal }
        );
        const filePath = file.path.replace(/^\/+/, "");
        const relWorkspacePath = filePath.replace(/^workspace\//, "");
        const baseName = filePath.split("/").pop() || filePath;

        if (filePath.endsWith("storybook.json")) {
          try {
            storybookData = JSON.parse(buffer.toString("utf-8"));
          } catch {
            // ignore malformed JSON
          }
        } else if (filePath.endsWith("timeline_manifest.json")) {
          try {
            timelineManifest = JSON.parse(buffer.toString("utf-8"));
          } catch {
            // ignore malformed JSON
          }
        } else if (/\.(png|jpg|jpeg|webp)$/i.test(filePath)) {
          const mime = filePath.toLowerCase().endsWith(".png")
            ? "image/png"
            : filePath.toLowerCase().endsWith(".webp")
            ? "image/webp"
            : "image/jpeg";
          const dataUri = `data:${mime};base64,${buffer.toString("base64")}`;
          const stemBase = baseName.replace(/\.(png|jpg|jpeg|webp)$/i, "");

          imageAssets[filePath] = dataUri;
          imageAssets[relWorkspacePath] = dataUri;
          imageAssets[`images/${baseName}`] = dataUri;
          imageAssets[baseName] = dataUri;
          imageAssets[`images/${stemBase}.png`] = dataUri;
          imageAssets[`images/${stemBase}.jpg`] = dataUri;
          imageAssets[`${stemBase}.png`] = dataUri;
          imageAssets[`${stemBase}.jpg`] = dataUri;
        } else if (/\.(mp3|wav)$/i.test(filePath)) {
          const mime = filePath.toLowerCase().endsWith(".wav")
            ? "audio/wav"
            : "audio/mpeg";
          const dataUri = `data:${mime};base64,${buffer.toString("base64")}`;
          audioAssets[filePath] = dataUri;
          audioAssets[relWorkspacePath] = dataUri;
          audioAssets[`audio/${baseName}`] = dataUri;
          audioAssets[baseName] = dataUri;
        }
      } catch {
        // Proxy URL remains in imageAssets / audioAssets as fallback
      }
    }
  });

  await Promise.all(workers);

  return {
    storybookData,
    timelineManifest,
    imageAssets,
    audioAssets,
    files: candidateFiles,
  };
}

