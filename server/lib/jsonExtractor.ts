export function extractJsonFromText(text: string): Record<string, unknown> | null {
  try {
    return JSON.parse(text);
  } catch {
    const codeBlockMatch = text.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
    if (codeBlockMatch?.[1]) {
      try {
        return JSON.parse(codeBlockMatch[1]);
      } catch {
        // continue
      }
    }
    const firstBrace = text.indexOf("{");
    const lastBrace = text.lastIndexOf("}");
    if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
      try {
        return JSON.parse(text.slice(firstBrace, lastBrace + 1));
      } catch {
        // continue
      }
    }
    return null;
  }
}

const DEFAULT_PALETTE = {
  paper: "#F6F2EA",
  card: "#EFE9DC",
  ink: "#1E1B18",
  muted: "#7A7267",
  accent: "#4A6B53",
  rule: "#D5CBB8",
  coverCloth: "#3D5845",
  coverSpine: "#2B3F31",
};

const ROMANS = ["I", "II", "III", "IV", "V", "VI"];

export function normalizeManagedAgentStorybook(
  rawInput: Record<string, any>,
  imageAssets: Record<string, string> = {},
  audioAssets: Record<string, string> = {},
  timelineManifest?: Record<string, any> | null
): Record<string, any> {
  const raw = rawInput?.storybook || rawInput?.book || rawInput || {};
  const bookId = String(raw.id || raw.book_id || `folio_${Date.now()}`);
  const roman = String(raw.roman || "I");
  const title = String(raw.title || "Commissioned Fairytale Folio");
  const author = String(raw.author || "Folio & Voice Press");
  const year = String(raw.year || "1815");
  const subtitle = String(raw.subtitle || raw.chapter_title || "Chapter I");
  const genreFooterLeft = String(
    raw.genreFooterLeft || raw.genre || "ILLUSTRATED FAIRYTALE FOLIO"
  ).toUpperCase();
  const settingFooterRight = String(
    raw.settingFooterRight || raw.setting || "CHAMBER EDITION"
  ).toUpperCase();

  const palette = {
    ...DEFAULT_PALETTE,
    ...(raw.palette || {}),
  };

  // Resolve character sheet image from sandbox assets if present
  const charSheetKey = Object.keys(imageAssets).find(
    (k) =>
      k.toLowerCase().includes("char_sheet") ||
      k.toLowerCase().includes("charsheet")
  );
  const charSheetImageUrl =
    (raw.charSheetImageUrl && imageAssets[raw.charSheetImageUrl]) ||
    (charSheetKey ? imageAssets[charSheetKey] : undefined) ||
    raw.charSheetImageUrl;

  // Resolve music & master audio from sandbox assets if present
  const lyriaKey = Object.keys(audioAssets).find(
    (k) =>
      k.toLowerCase().includes("lyria") ||
      k.toLowerCase().includes("ambient") ||
      k.toLowerCase().includes("score") ||
      k.toLowerCase().includes("music")
  );
  const masterKey = Object.keys(audioAssets).find(
    (k) =>
      k.toLowerCase().includes("master") ||
      k.toLowerCase().includes("full_storybook") ||
      k.toLowerCase().includes("audiobook")
  );

  const backgroundMusicDataUrl =
    (raw.backgroundMusicUrl && audioAssets[raw.backgroundMusicUrl]) ||
    (lyriaKey ? audioAssets[lyriaKey] : undefined) ||
    raw.backgroundMusicDataUrl;

  const fullAudiobookDataUrl =
    (raw.fullAudiobookUrl && audioAssets[raw.fullAudiobookUrl]) ||
    (masterKey ? audioAssets[masterKey] : undefined) ||
    raw.fullAudiobookDataUrl;

  const hasMixedMasterAudio = Boolean(
    fullAudiobookDataUrl || raw.masterAudioUrl
  );
  const titleCardEndSec = Number(
    timelineManifest?.titleCardEndSec ??
      raw.titleCardEndSec ??
      (hasMixedMasterAudio ? 1.8 : 2.6)
  );
  let timelineCursor = hasMixedMasterAudio
    ? titleCardEndSec
    : titleCardEndSec + 2.8;

  // Build pages either from `raw.pages`, `raw.folios`, or `raw.scenes` + `raw.turns` (classic-audiobooks schema)
  let pages: any[] = [];

  if (Array.isArray(raw.pages) && raw.pages.length > 0) {
    pages = raw.pages.map((p: any, idx: number) => {
      const pnum = p.pageNumber || idx + 1;
      const rom = ROMANS[idx] || String(pnum);
      const sceneImgKey = Object.keys(imageAssets).find(
        (k) =>
          k.includes(`scene_${pnum}`) ||
          k.includes(`page_${pnum}`) ||
          k === p.imageUrl
      );
      const pageImg =
        (p.imageUrl && imageAssets[p.imageUrl]) ||
        (sceneImgKey ? imageAssets[sceneImgKey] : undefined) ||
        p.imageDataUrl ||
        p.imageUrl;

      const pageAudioKey = Object.keys(audioAssets).find(
        (k) =>
          k.includes(`page_${pnum}`) ||
          k.includes(`scene_${pnum}`) ||
          k === p.audioUrl
      );
      const pageAudio =
        (p.audioUrl && audioAssets[p.audioUrl]) ||
        (pageAudioKey ? audioAssets[pageAudioKey] : undefined) ||
        p.audioDataUrl;

      const rawTurns = Array.isArray(p.dialogueLines || p.turns)
        ? p.dialogueLines || p.turns
        : [
            {
              speaker: "Narrator",
              speakerLabel: "NARRATOR",
              voiceRoleLabel: "Literary Narration",
              isDialogue: false,
              voiceName: raw.narratorVoice || "Kore",
              text: p.narrativeText || "",
              durationSeconds: 5,
            },
          ];

      const pageDurationSec = Number(p.durationSeconds || 0);
      const totalChars = Math.max(
        1,
        rawTurns.reduce(
          (sum: number, t: any) =>
            sum + String(t.text || t.display_text || t.tts_text || " ").length,
          0
        )
      );
      const interTurnPause = 0.28;
      const totalTurnPauses = Math.max(0, rawTurns.length - 1) * interTurnPause;
      const speakablePageSec =
        pageDurationSec > totalTurnPauses + 1
          ? pageDurationSec - totalTurnPauses
          : 0;

      const folioStartSec = Number(
        (p.startSec ?? timelineCursor).toFixed(3)
      );
      let lineCursor = folioStartSec;

      const dialogueLines = rawTurns.map((t: any, lIdx: number) => {
        const textStr = t.text || t.display_text || t.tts_text || "";
        const charWeight = Math.max(1, textStr.length) / totalChars;
        const dur = Number(
          (
            t.durationSeconds ||
            t.duration_sec ||
            (speakablePageSec > 0
              ? Math.max(1.5, speakablePageSec * charWeight)
              : Math.max(2.5, Math.round(textStr.length / 15)))
          ).toFixed(2)
        );
        const startSec = Number((t.startSec ?? lineCursor).toFixed(3));
        const endSec = Number((t.endSec ?? startSec + dur).toFixed(3));
        lineCursor = Number((endSec + interTurnPause).toFixed(3));

        const spk = t.speaker || t.speaker_key || "Narrator";
        const isNarrator = /narrator|storyteller/i.test(spk);
        const isDialogue =
          typeof (t.isDialogue ?? t.is_dialogue) === "boolean"
            ? Boolean(t.isDialogue ?? t.is_dialogue)
            : !isNarrator;

        return {
          speaker: spk,
          speakerLabel:
            t.speakerLabel ||
            t.speaker_label ||
            String(spk).toUpperCase(),
          voiceRoleLabel:
            t.voiceRoleLabel ||
            (isDialogue ? "Character Dialogue" : "Literary Narration"),
          isDialogue,
          voiceName: t.voiceName || t.voice_id || raw.narratorVoice || "Kore",
          stylePrompt: t.stylePrompt || t.style,
          text: textStr,
          durationSeconds: dur,
          startSec,
          endSec,
          ...(!hasMixedMasterAudio && lIdx === 0 && pageAudio
            ? { audioDataUrl: pageAudio }
            : {}),
        };
      });

      const folioEndSec = Number(
        (
          p.endSec ??
          (pageDurationSec > 0
            ? folioStartSec + pageDurationSec
            : lineCursor + 0.4)
        ).toFixed(3)
      );
      // mix_storybook_audio.py inserts 1.4s inter_page_pause between pages
      timelineCursor = Number(
        (folioEndSec + (hasMixedMasterAudio ? 1.4 : 0.85)).toFixed(3)
      );

      const pageCaption =
        p.imageCaption ||
        p.caption ||
        p.title ||
        p.chapterTitle ||
        `Scene ${rom}`;

      const plates =
        Array.isArray(p.plates) && p.plates.length > 0
          ? p.plates.map((pl: any, plIdx: number) => ({
              ...pl,
              plateNumberRoman: pl.plateNumberRoman || ROMANS[plIdx] || "I",
              plateLabel:
                pl.plateLabel ||
                `PLATE ${ROMANS[plIdx] || "I"} OF ${p.plates.length}`,
              imageDataUrl:
                (pl.imageUrl && imageAssets[pl.imageUrl]) ||
                pl.imageDataUrl ||
                pageImg,
            }))
          : [
              {
                plateNumberRoman: rom,
                plateLabel: `PLATE ${rom} OF ${
                  ROMANS[Math.min(raw.pages.length - 1, 5)] || "III"
                }`,
                title: pageCaption,
                illustrationPrompt: p.illustrationPrompt || "",
                imageUrl: pageImg,
                imageDataUrl: pageImg,
              },
              ...(charSheetImageUrl
                ? [
                    {
                      plateNumberRoman: "I",
                      plateLabel: "CHARACTER SHEET",
                      title: "Character Reference Sheet",
                      illustrationPrompt:
                        raw.char_sheet_prompt || raw.charSheetPrompt || "",
                      imageUrl: charSheetImageUrl,
                      imageDataUrl: charSheetImageUrl,
                    },
                  ]
                : []),
            ];

      return {
        ...p,
        pageNumber: pnum,
        sceneIdx: typeof p.sceneIdx === "number" ? p.sceneIdx : idx,
        sceneLabel: p.sceneLabel || `SCENE ${rom}`,
        folioLabel: p.folioLabel || p.folio || `FOLIO ${roman}.${pnum}`,
        chapterTitle: (
          p.chapterTitle ||
          p.title ||
          subtitle
        ).toUpperCase(),
        narrativeText: p.narrativeText || dialogueLines[0]?.text || "",
        illustrationPrompt: p.illustrationPrompt || "",
        imageCaption: pageCaption,
        imageUrl: pageImg,
        imageDataUrl: pageImg,
        dioramaUrl: p.dioramaUrl || pageImg,
        audioDataUrl: pageAudio,
        startSec: folioStartSec,
        endSec: folioEndSec,
        plates,
        dialogueLines,
      };
    });
  } else if (Array.isArray(raw.scenes) && raw.scenes.length > 0) {
    // Classic-audiobooks `books_spec.py` format (`scenes` + `turns`)
    const allTurns: any[] = Array.isArray(raw.turns) ? raw.turns : [];
    const getTurnFolioIdx = (t: any) =>
      typeof t.folio_idx === "number"
        ? t.folio_idx
        : typeof t.page_idx === "number"
        ? t.page_idx
        : undefined;
    const maxFolioIdx = allTurns.reduce(
      (acc, t) => Math.max(acc, getTurnFolioIdx(t) ?? 0),
      0
    );
    const folioCount = Math.max(
      1,
      Math.min(3, maxFolioIdx + 1 || raw.scenes.length)
    );

    for (let fIdx = 0; fIdx < folioCount; fIdx++) {
      const pnum = fIdx + 1;
      const rom = ROMANS[fIdx] || String(pnum);
      const sceneObj = raw.scenes[fIdx] || raw.scenes[0] || {};
      const sceneImgKey = Object.keys(imageAssets).find(
        (k) =>
          k.includes(`scene_${pnum}`) ||
          k.includes(`page_${pnum}`) ||
          (sceneObj.id && k.includes(sceneObj.id))
      );
      const pageImg =
        (sceneImgKey ? imageAssets[sceneImgKey] : undefined) ||
        sceneObj.imageUrl ||
        sceneObj.image_url ||
        "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/01_pride_and_prejudice_diorama_scene_1.png";

      const folioTurns = allTurns.filter((t, tIdx) => {
        const tf = getTurnFolioIdx(t);
        return typeof tf === "number"
          ? tf === fIdx
          : Math.floor((tIdx / Math.max(1, allTurns.length)) * folioCount) ===
              fIdx;
      });

      const dialogueLines = folioTurns.map((t: any, tIdx: number) => {
        const turnWavKey = Object.keys(audioAssets).find((k) =>
          k.includes(`turn_${String(tIdx).padStart(2, "0")}`)
        );
        return {
          speaker: t.speaker || t.speaker_key || "Narrator",
          speakerLabel:
            t.speakerLabel ||
            t.speaker_label ||
            String(t.speaker || t.speaker_key || "NARRATOR")
              .replace(/_/g, " ")
              .toUpperCase(),
          voiceRoleLabel:
            t.is_dialogue || t.isDialogue
              ? "Character Dialogue"
              : "Literary Narration",
          isDialogue: Boolean(t.is_dialogue ?? t.isDialogue),
          voiceName: t.voice_id || t.voiceName || "Kore",
          stylePrompt: t.style || t.stylePrompt,
          text: t.display_text || t.text || t.tts_text || "",
          durationSeconds:
            t.duration_sec ||
            t.durationSeconds ||
            Math.max(
              2.5,
              Math.round(String(t.display_text || t.text || "").length / 15)
            ),
          ...(turnWavKey ? { audioDataUrl: audioAssets[turnWavKey] } : {}),
        };
      });

      pages.push({
        pageNumber: pnum,
        sceneIdx: fIdx,
        sceneLabel: `SCENE ${rom}`,
        folioLabel: `FOLIO ${roman}.${pnum}`,
        chapterTitle: subtitle.toUpperCase(),
        narrativeText: dialogueLines[0]?.text || "",
        illustrationPrompt: sceneObj.prompt || "",
        imageCaption: sceneObj.caption || `Scene ${rom}`,
        imageUrl: pageImg,
        imageDataUrl: pageImg,
        dioramaUrl: pageImg,
        plates: [
          {
            plateNumberRoman: rom,
            plateLabel: `PLATE ${rom} OF ${ROMANS[folioCount - 1] || "III"}`,
            title: sceneObj.caption || `Scene ${rom}`,
            illustrationPrompt: sceneObj.prompt || "",
            imageUrl: pageImg,
            imageDataUrl: pageImg,
          },
          ...(charSheetImageUrl
            ? [
                {
                  plateNumberRoman: "I",
                  plateLabel: "CHARACTER SHEET",
                  title: "Anonymous Character Reference Sheet",
                  illustrationPrompt:
                    raw.char_sheet_prompt || raw.charSheetPrompt || "",
                  imageUrl: charSheetImageUrl,
                  imageDataUrl: charSheetImageUrl,
                },
              ]
            : []),
        ],
        dialogueLines,
      });
    }
  }

  const coverImg =
    (raw.coverImageUrl && imageAssets[raw.coverImageUrl]) ||
    imageAssets["images/cover.png"] ||
    imageAssets["images/cover.jpg"] ||
    imageAssets["cover.png"] ||
    imageAssets["cover.jpg"] ||
    pages[0]?.imageUrl ||
    raw.coverImageUrl;

  const totalDurationSeconds = Number(
    raw.totalDurationSeconds ||
      timelineManifest?.totalDurationSeconds ||
      Math.max(30, timelineCursor + 2.0)
  );

  return {
    ...raw,
    id: bookId,
    roman,
    bookHeaderLeft:
      raw.bookHeaderLeft || `BOOK ${roman}  ·  ${author.toUpperCase()}`,
    year,
    genreFooterLeft,
    settingFooterRight,
    title,
    subtitle,
    author,
    palette,
    sourceType: raw.sourceType || "original",
    visualStyle:
      raw.visualStyle ||
      "1810s Regency fine dip-pen sepia ink line drawing with delicate muted watercolour wash on warm cream archival paper (#F6F2EA)",
    mood: raw.mood || genreFooterLeft,
    musicPrompt:
      raw.musicPrompt || raw.music_prompt || raw.ambientMusicPrompt || "",
    charSheetPrompt: raw.charSheetPrompt || raw.char_sheet_prompt || "",
    charSheetImageUrl,
    coverImagePrompt:
      raw.coverImagePrompt || pages[0]?.illustrationPrompt || title,
    coverImageUrl: coverImg,
    coverImageDataUrl: coverImg,
    masterAudioUrl: fullAudiobookDataUrl || raw.masterAudioUrl,
    backgroundMusicUrl:
      backgroundMusicDataUrl ||
      raw.backgroundMusicUrl ||
      "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/music/01_pride_and_prejudice_lyria.mp3",
    backgroundMusicDataUrl,
    fullAudiobookDataUrl,
    titleCardEndSec,
    totalDurationSeconds,
    modelsUsed: raw.modelsUsed || {
      orchestrator: "antigravity-preview-09-2026 (gemini-4-argon)",
      cli: "gemini-api-cli v0.4.0 (github.com/google-gemini/gemini-api-cli)",
      writer: "gemini-4-argon / books_spec.py",
      illustrator: "gemini-3.1-flash-lite-image + generate_popup_assets.py",
      narrator: "gemini-3.1-flash-tts-preview + voice_mastering.py",
      composer: "lyria-3-clip-preview + mix_storybook_audio.py",
    },
    characters:
      Array.isArray(raw.characters) && raw.characters.length > 0
        ? raw.characters
        : [
            {
              id: "narrator",
              name: "Narrator",
              role: "Literary Narration",
              description: "Poised fine-press literary narrator",
              voiceName: "Kore",
              voiceStyle: "warm, unhurried literary storytelling",
            },
          ],
    pages,
  };
}

