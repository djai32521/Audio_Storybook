import "dotenv/config";
import express from "express";
import path from "path";
import fs from "fs";
import {
  createInteraction,
  streamInteraction,
  resolveServerApiKey,
  listEnvironmentFiles,
  downloadEnvironmentFile,
  downloadSandboxStorybookAssets,
  type InlineSource,
  DEFAULT_AGENT_NAME,
  DEFAULT_MODEL_NAME,
} from "./server/lib/agentClient.ts";
import {
  extractJsonFromText,
  normalizeManagedAgentStorybook,
} from "./server/lib/jsonExtractor.ts";

function getAgentInlineSources(dirPath: string, baseTarget = ".agents"): InlineSource[] {
  let sources: InlineSource[] = [];
  if (!fs.existsSync(dirPath)) return sources;

  const entries = fs.readdirSync(dirPath, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);
    const targetPath = path.posix.join(baseTarget, entry.name);
    if (entry.isDirectory()) {
      sources = sources.concat(getAgentInlineSources(fullPath, targetPath));
    } else if (entry.isFile()) {
      sources.push({
        type: "inline",
        content: fs.readFileSync(fullPath, "utf-8"),
        target: targetPath,
      });
    }
  }
  return sources;
}

const activeInteractions = new Map<string, AbortController>();

async function startServer() {
  const app = express();
  const PORT = Number(process.env.PORT || 3000);

  app.use(express.json({ limit: "25mb" }));

  // Health & Agent Config introspection endpoint
  app.get("/api/agent-config", (_req, res) => {
    const agentDir = path.join(process.cwd(), "agent");
    const inlineSources = getAgentInlineSources(agentDir);
    res.json({
      agent: DEFAULT_AGENT_NAME,
      agentConfig: {
        type: "antigravity",
        model: DEFAULT_MODEL_NAME,
      },
      cliRepo: "https://github.com/google-gemini/gemini-api-cli",
      mountedFiles: inlineSources.map((s) => s.target),
      modelsCatalog: [
        { role: "Managed Agent Orchestrator", model: "gemini-4-argon (Gemini 4 Argon)", agent: "antigravity-preview-09-2026" },
        { role: "Story & Script Adaptation", model: "gemini-3.1-pro-preview / gemini-3.8-flash", tool: "gemini-api generate" },
        { role: "Book Cover & Spread Illustrations", model: "gemini-3.1-flash-lite-image", tool: "gemini-api image" },
        { role: "Multi-Voice Dramatized Narration", model: "gemini-3.1-flash-tts-preview", tool: "tts-generation skill" },
        { role: "Ambient Musical Soundtrack", model: "lyria-3-clip-preview", tool: "music-generation skill" },
      ],
    });
  });

  // Project Gutenberg search proxy for classic literature adaptation
  app.get("/api/gutenberg/search", async (req, res) => {
    try {
      const q = String(req.query.q || "alice in wonderland");
      const resp = await fetch(`https://gutendex.com/books?search=${encodeURIComponent(q)}`);
      if (!resp.ok) {
        return res.status(resp.status).json({ error: `Gutendex error ${resp.status}` });
      }
      const data = await resp.json();
      res.json(data);
    } catch (err: any) {
      res.status(500).json({ error: err?.message || "Failed to search Project Gutenberg" });
    }
  });

  app.post("/api/cancel", (req, res) => {
    const { sessionId } = req.body;
    if (sessionId && activeInteractions.has(sessionId)) {
      activeInteractions.get(sessionId)?.abort();
      activeInteractions.delete(sessionId);
      return res.json({ status: "cancelled" });
    }
    res.status(404).json({ error: "Session not found" });
  });

  // Environments Files API proxy endpoints: list files, download a single file, or reconstruct storybook from sandbox
  app.get("/api/environments/:envId/files", async (req, res) => {
    try {
      const dirPath = String(req.query.path || "workspace");
      const recursive = req.query.recursive !== "false";
      const files = await listEnvironmentFiles(req.params.envId, dirPath, { recursive });
      res.json({ environmentId: req.params.envId, path: dirPath, files });
    } catch (err: any) {
      res.status(500).json({ error: err?.message || "Failed to list environment files" });
    }
  });

  app.get("/api/environments/:envId/file", async (req, res) => {
    try {
      const filePath = String(req.query.path || "");
      if (!filePath) {
        return res.status(400).json({ error: "Query parameter ?path= is required" });
      }
      const { buffer, mimeType } = await downloadEnvironmentFile(req.params.envId, filePath);
      res.setHeader("Content-Type", mimeType);
      res.setHeader("Cache-Control", "public, max-age=3600");
      res.send(buffer);
    } catch (err: any) {
      res.status(404).json({ error: err?.message || "File not found in environment" });
    }
  });

  app.get("/api/environments/:envId/storybook", async (req, res) => {
    try {
      const assets = await downloadSandboxStorybookAssets(req.params.envId);
      if (!assets.storybookData) {
        return res.status(404).json({ error: "No storybook.json found in environment" });
      }
      const storybook = normalizeManagedAgentStorybook(
        assets.storybookData,
        assets.imageAssets,
        assets.audioAssets,
        assets.timelineManifest
      );
      res.json({
        storybook,
        environmentId: req.params.envId,
        filesCount: assets.files.length,
      });
    } catch (err: any) {
      res.status(500).json({ error: err?.message || "Failed to load storybook from environment" });
    }
  });

  // Main Managed Agent SSE endpoint for generating a complete Illustrated Storybook & Audiobook
  app.post("/api/generate-storybook", async (req, res) => {
    const {
      prompt,
      classicBookTitle,
      visualStyle,
      pageCount = 4,
      narratorVoice = "Charon",
      agentName = DEFAULT_AGENT_NAME,
      modelName = DEFAULT_MODEL_NAME,
      environmentId,
      previousInteractionId,
      sessionId,
      apiKey,
    } = req.body;
    const resolvedApiKey = resolveServerApiKey(apiKey);

    if (!prompt && !classicBookTitle) {
      return res.status(400).json({ error: "A story prompt or classic book title is required" });
    }

    if (!resolvedApiKey) {
      return res.status(400).json({
        error: "No valid GEMINI_API_KEY configured. Please provide a valid Gemini API key.",
      });
    }

    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");

    const sendEvent = (event: string, data: unknown) => {
      res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
    };

    const abortController = new AbortController();
    if (sessionId) {
      activeInteractions.set(sessionId, abortController);
    }

    try {
      const agentDir = path.join(process.cwd(), "agent");
      const inlineSources = getAgentInlineSources(agentDir);

      sendEvent("status", {
        message: `Booting Managed Agent (${agentName} / ${modelName}) & mounting ${inlineSources.length} skill files...`,
        agent: agentName,
        model: modelName,
      });

      const fullPrompt = [
        classicBookTitle
          ? `Create an illustrated storybook and dramatized multi-voice audiobook adaptation of the classic work "${classicBookTitle}".`
          : `Create an original illustrated storybook and dramatized multi-voice audiobook based on this request: "${prompt}".`,
        prompt && classicBookTitle ? `Additional user direction: ${prompt}` : "",
        `Target number of illustrated page spreads: ${pageCount}.`,
        visualStyle ? `Visual art direction: ${visualStyle}.` : "",
        `Primary Storyteller / Narrator voice: ${narratorVoice} (plus distinct Gemini TTS voices for speaking characters).`,
        "",
        "Follow /.agents/AGENTS.md strictly:",
        "1. Install the latest release of the Gemini API CLI (`curl -fsSL https://raw.githubusercontent.com/google-gemini/gemini-api-cli/main/scripts/install.sh | bash` into $HOME/.local/bin) and verify `gemini-api --version`.",
        "2. Author `./workspace/data/storybook.json` with character voice casting, dialogue lines, and detailed visual prompts.",
        "3. Generate `./workspace/images/cover.png` and `./workspace/images/page_1.png` ... `./workspace/images/page_" +
          pageCount +
          ".png` using `gemini-api image` (`gemini-3.1-flash-lite-image`).",
        "4. Generate dramatized multi-voice narration `./workspace/audio/page_1.mp3` ... using `gemini-3.1-flash-tts-preview`.",
        "5. Generate ambient instrumental music `./workspace/audio/ambient.mp3` (`lyria-3-clip-preview`) and mix `./workspace/audio/full_storybook.mp3`.",
      ]
        .filter(Boolean)
        .join("\n");

      const response = await createInteraction({
        prompt: fullPrompt,
        inlineSources,
        environmentId,
        previousInteractionId,
        agentName,
        modelName,
        apiKey: resolvedApiKey,
        signal: abortController.signal,
      });

      let fullText = "";
      let activeEnvId: string | undefined = environmentId;
      let interactionId: string | undefined;

      await streamInteraction(response, {
        onCreated: (id, envId) => {
          interactionId = id;
          if (envId) activeEnvId = envId;
          sendEvent("created", { id, envId: activeEnvId, agent: agentName, model: modelName });
        },
        onStatus: (status) => {
          sendEvent("status", { message: `Agent status: ${status}` });
        },
        onThinking: (thought) => {
          sendEvent("thinking", { thought });
        },
        onText: (text) => {
          fullText += text;
          sendEvent("text", { text });
        },
        onToolCall: (name, args, id) => {
          sendEvent("tool_call", { name, args, id });
        },
        onToolResult: (name, result, isError, callId) => {
          sendEvent("tool_result", { name, result, isError, callId });
        },
        onComplete: (_interaction, envId) => {
          if (envId) activeEnvId = envId;
          sendEvent("status", { message: "Agent completed generation. Downloading sandbox workspace..." });
        },
        onError: (err) => {
          throw new Error(`Managed Agent error: ${JSON.stringify(err)}`);
        },
      });

      let storybookData: any = extractJsonFromText(fullText);
      let timelineManifest: any = null;
      let imageAssets: Record<string, string> = {};
      let audioAssets: Record<string, string> = {};

      if (activeEnvId) {
        try {
          const downloaded = await downloadSandboxStorybookAssets(activeEnvId, {
            apiKey: resolvedApiKey,
            signal: abortController.signal,
            onStatus: (message) => sendEvent("status", { message }),
          });
          if (downloaded.storybookData) {
            storybookData = downloaded.storybookData;
          }
          timelineManifest = downloaded.timelineManifest;
          imageAssets = downloaded.imageAssets;
          audioAssets = downloaded.audioAssets;
        } catch {
          // Proceed with storybookData extracted from model_output if sandbox file download fails
        }
      }

      if (!storybookData) {
        throw new Error("Could not extract storybook.json from sandbox workspace or agent output.");
      }

      storybookData = normalizeManagedAgentStorybook(
        storybookData,
        imageAssets,
        audioAssets,
        timelineManifest
      );

      sendEvent("result", {
        storybook: storybookData,
        environmentId: activeEnvId,
        interactionId,
        agent: agentName,
        model: modelName,
      });
      res.end();
    } catch (error: any) {
      if (error?.name === "AbortError") {
        sendEvent("cancelled", { message: "Storybook generation was cancelled." });
      } else {
        sendEvent("error", { message: error?.message || "An unexpected error occurred" });
      }
      res.end();
    } finally {
      if (sessionId) {
        activeInteractions.delete(sessionId);
      }
    }
  });

  if (process.env.NODE_ENV !== "production") {
    const { createServer: createViteServer } = await import("vite");
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*all", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Storybook Managed Agent Studio running on http://localhost:${PORT}`);
  });
}

startServer();
