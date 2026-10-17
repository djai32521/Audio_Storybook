import React, { useEffect, useRef, useState } from "react";
import {
  ALL_CLASSIC_STORYBOOKS,
  EDITION_PALETTES,
  FAIRYTALE_COMMISSION_PROMPTS,
  GEMINI_TTS_VOICES,
  INITIAL_SHOWCASE_STORYBOOK,
  VISUAL_STYLE_PRESETS,
} from "./data/presets";
import {
  AGENTS_MD_CONTENT,
  DEFAULT_MANAGED_AGENT_ID,
  DEFAULT_MANAGED_AGENT_MODEL,
  GEMINI_API_CLI_INSTALL_CMD,
} from "./services/inlineAgentBundle";
import {
  generateStudioIllustration,
  runManagedAgentStorybook,
  synthesizeStudioPageAudio,
} from "./services/storybookAgentService";
import { AgentLogEntry, Storybook, StorybookPalette } from "./types";
import {
  Language,
  TRANSLATIONS,
  KOREAN_BOOK_METAS,
  KOREAN_FAIRYTALE_PROMPTS,
  KOREAN_PIPELINE_STAGES,
} from "./data/translations";

const ROMAN_NUMERALS = ["I", "II", "III", "IV", "V", "VI"];

const PIPELINE_STAGES = [
  {
    index: 0,
    code: "STAGE I · SANDBOX & GEMINI-API-CLI",
    title:
      "Provisioning the Managed Agent container and installing the latest release of gemini-api-cli in the workspace.",
  },
  {
    index: 1,
    code: "STAGE II · DRAMATURGY & FOLIO SPEC",
    title:
      "Adapting the literary chapter into three balanced folios of narration and dialogue turns with anonymous period character descriptions.",
  },
  {
    index: 2,
    code: "STAGE III · ARCHIVAL PLATES & DIORAMA",
    title:
      "Painting the 16:9 character reference sheet and three 1810s pen-and-ink watercolour plates on #F6F2EA cream paper.",
  },
  {
    index: 3,
    code: "STAGE IV · MULTI-VOICE PERFORMANCE",
    title:
      "Synthesizing and mastering distinct 24 kHz dialogue and narration turns with natural breath pauses and room tone.",
  },
  {
    index: 4,
    code: "STAGE V · CHAMBER SCORE & BINDING",
    title:
      "Composing the Lyria 3.5 acoustic chamber score and binding all three folios into the open-book spread.",
  },
];

// Persistent Audio elements stored outside #root so VDOM re-renders never interrupt playback
function getMasterAudioEl(): HTMLAudioElement | null {
  if (typeof window === "undefined" || typeof Audio === "undefined") return null;
  const w = window as any;
  if (!w.__folioMasterAudioEl) {
    const el = new Audio();
    el.preload = "auto";
    w.__folioMasterAudioEl = el;
  }
  return w.__folioMasterAudioEl;
}

function getMusicAudioEl(): HTMLAudioElement | null {
  if (typeof window === "undefined" || typeof Audio === "undefined") return null;
  const w = window as any;
  if (!w.__folioMusicAudioEl) {
    const el = new Audio();
    el.preload = "auto";
    el.loop = true;
    w.__folioMusicAudioEl = el;
  }
  return w.__folioMusicAudioEl;
}

// Ensures any storybook (including newly commissioned Managed Agent books) has exact startSec/endSec
function ensureBookTimeline(book: Storybook): Storybook {
  const firstTurn = book.pages?.[0]?.dialogueLines?.[0];
  if (typeof firstTurn?.startSec === "number" && typeof firstTurn?.endSec === "number") {
    return book;
  }

  const titleEnd = book.titleCardEndSec ?? 2.6;
  let cursor = titleEnd + 2.8; // 5.4s first speech start (after 2.6s title card + 2.8s page turn & pop-up unfold)

  const pages = (book.pages || []).map((page, pIdx) => {
    const folioStart = pIdx === 0 ? titleEnd : cursor;
    if (pIdx > 0) {
      cursor += 0.85; // Folio crossfade / page-turn beat before first turn on new folio
    }
    const lines = (page.dialogueLines || []).map((line) => {
      const dur = Math.max(
        1.4,
        Number(line.durationSeconds || Math.max(2.4, (line.text || "").length / 15))
      );
      const startSec = Number(cursor.toFixed(3));
      const endSec = Number((cursor + dur).toFixed(3));
      cursor = endSec + (line.isDialogue ? 0.36 : 0.48);
      return {
        ...line,
        durationSeconds: dur,
        startSec,
        endSec,
      };
    });
    const folioEnd = Number((cursor + 0.4).toFixed(3));
    cursor = folioEnd;
    return {
      ...page,
      sceneIdx: typeof page.sceneIdx === "number" ? page.sceneIdx : pIdx,
      startSec: Number(folioStart.toFixed(3)),
      endSec: folioEnd,
      dialogueLines: lines,
    };
  });

  const totalDurationSeconds = Number(Math.max(book.totalDurationSeconds || 0, cursor + 1.2).toFixed(2));
  return {
    ...book,
    titleCardEndSec: titleEnd,
    totalDurationSeconds,
    pages,
  };
}

function formatTimecode(sec: number): string {
  const s = Math.max(0, Math.floor(sec || 0));
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `${m}:${rem < 10 ? "0" : ""}${rem}`;
}

export default function App() {
  // Primary folio view state:
  // "cover" = Open-Book Title & Commission Folio Spread (Home Page)
  // "crafting" = Open-Book Illuminator's Progress Spread while Managed Agent crafts the edition
  // "reader" = Open-Book Literary & Plate Spread (matches classic_novels_opening_chapters.mp4)
  const [viewMode, setViewMode] = useState<"cover" | "crafting" | "reader">("cover");
  const [isPageTurning, setIsPageTurning] = useState<boolean>(false);
  const [isRightFolioFading, setIsRightFolioFading] = useState<boolean>(false);
  const [isDioramaUnfolding, setIsDioramaUnfolding] = useState<boolean>(false);
  const [showOpeningTitleCard, setShowOpeningTitleCard] = useState<boolean>(false);
  const [showTitleCardModal, setShowTitleCardModal] = useState<boolean>(false);
  const [showAgentSpecModal, setShowAgentSpecModal] = useState<boolean>(false);

  // Active Storybook & Classic Library
  const [storybook, setStorybook] = useState<Storybook>(() =>
    ensureBookTimeline(INITIAL_SHOWCASE_STORYBOOK)
  );
  const [library, setLibrary] = useState<Storybook[]>(() =>
    ALL_CLASSIC_STORYBOOKS.map(ensureBookTimeline)
  );
  const [currentPageIdx, setCurrentPageIdx] = useState<number>(0);
  // activeLineIdx: -1 = pre-speech (all turns on folio in state-future 38% ink),
  // 0..N-1 = currently spoken turn in state-active 100% ink,
  // 999 = post-speech on folio (all turns on folio settled into state-past 50% ink)
  const [activeLineIdx, setActiveLineIdx] = useState<number>(-1);
  const [playbackTimeSec, setPlaybackTimeSec] = useState<number>(0);
  const [manualPlateIdx, setManualPlateIdx] = useState<number | null>(null);

  // Language State: defaults to Korean ("ko")
  const [language, setLanguage] = useState<Language>(() => {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        const saved = window.localStorage.getItem("AUDIO_STORYBOOK_LANG") as Language | null;
        if (saved === "en" || saved === "ko") return saved;
      }
    } catch {}
    return "ko";
  });

  const t = TRANSLATIONS[language];
  const activePipelineStages = language === "ko" ? KOREAN_PIPELINE_STAGES : PIPELINE_STAGES;
  const activeFairytalePrompts = language === "ko" ? KOREAN_FAIRYTALE_PROMPTS : FAIRYTALE_COMMISSION_PROMPTS;

  // Commission Folio State
  const [commissionPrompt, setCommissionPrompt] = useState<string>(() => {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        const savedLang = window.localStorage.getItem("AUDIO_STORYBOOK_LANG");
        if (savedLang === "en") return FAIRYTALE_COMMISSION_PROMPTS[0].prompt;
      }
    } catch {}
    return KOREAN_FAIRYTALE_PROMPTS[0].prompt;
  });

  const handleToggleLanguage = (newLang: Language) => {
    setLanguage(newLang);
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        window.localStorage.setItem("AUDIO_STORYBOOK_LANG", newLang);
      }
    } catch {}
    if (newLang === "ko") {
      if (commissionPrompt === FAIRYTALE_COMMISSION_PROMPTS[0].prompt) {
        setCommissionPrompt(KOREAN_FAIRYTALE_PROMPTS[0].prompt);
      }
    } else {
      if (commissionPrompt === KOREAN_FAIRYTALE_PROMPTS[0].prompt) {
        setCommissionPrompt(FAIRYTALE_COMMISSION_PROMPTS[0].prompt);
      }
    }
  };

  const [selectedPaletteKey, setSelectedPaletteKey] = useState<string>("regency");
  const [visualStyle, setVisualStyle] = useState<string>(VISUAL_STYLE_PRESETS[0].value);
  const [narratorVoice, setNarratorVoice] = useState<string>("Kore");
  const [agentName, setAgentName] = useState<string>(DEFAULT_MANAGED_AGENT_ID);
  const [modelName, setModelName] = useState<string>(DEFAULT_MANAGED_AGENT_MODEL);
  const [apiKeyInput, setApiKeyInput] = useState<string>(() => {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        return window.localStorage.getItem("FOLIO_GEMINI_API_KEY") || "";
      }
    } catch {
      // Null-origin sandbox blocks localStorage
    }
    return "";
  });

  // Managed Agent Execution State
  const [isRunningAgent, setIsRunningAgent] = useState<boolean>(false);
  const [activeStageIdx, setActiveStageIdx] = useState<number>(0);
  const [activeStageLabel, setActiveStageLabel] = useState<string>("Ready");
  const [agentLogs, setAgentLogs] = useState<AgentLogEntry[]>([]);
  const [environmentId, setEnvironmentId] = useState<string | undefined>(undefined);
  const [interactionId, setInteractionId] = useState<string | undefined>(undefined);
  const [agentError, setAgentError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Audio Playback & Chamber Score State
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);
  const [isMusicEnabled, setIsMusicEnabled] = useState<boolean>(true);
  const [isSynthesizingAudio, setIsSynthesizingAudio] = useState<boolean>(false);
  const [isRegeneratingPlate, setIsRegeneratingPlate] = useState<boolean>(false);
  const [statusNote, setStatusNote] = useState<string | null>(null);

  // Mutable refs for 60fps/80ms timeline loop so closures never read stale state
  const virtualClockRef = useRef<number>(0);
  const lastWallClockMsRef = useRef<number>(0);
  const currentPageIdxRef = useRef<number>(0);
  const activeLineIdxRef = useRef<number>(-1);
  const showOpeningTitleCardRef = useRef<boolean>(false);
  const lastSpokenTurnKeyRef = useRef<string>("");

  currentPageIdxRef.current = currentPageIdx;
  activeLineIdxRef.current = activeLineIdx;
  showOpeningTitleCardRef.current = showOpeningTitleCard;

  // Active Palette CSS Variables
  const activePalette: StorybookPalette =
    viewMode === "cover"
      ? EDITION_PALETTES[selectedPaletteKey]?.palette || EDITION_PALETTES.regency.palette
      : storybook.palette || EDITION_PALETTES.regency.palette;

  const paletteCssVars = {
    "--folio-paper": activePalette.paper,
    "--folio-card": activePalette.card,
    "--folio-ink": activePalette.ink,
    "--folio-muted": activePalette.muted,
    "--folio-accent": activePalette.accent,
    "--folio-rule": activePalette.rule,
  } as React.CSSProperties;

  const currentPage = storybook.pages[currentPageIdx] || storybook.pages[0];
  const dialogueLines = currentPage?.dialogueLines || [];
  const resolvedActiveLineIdx =
    activeLineIdx >= 0 && activeLineIdx < dialogueLines.length
      ? activeLineIdx
      : activeLineIdx >= 999 && dialogueLines.length > 0
      ? dialogueLines.length - 1
      : 0;
  const activeLine = dialogueLines[resolvedActiveLineIdx] || dialogueLines[0];

  const totalScenesRoman =
    ROMAN_NUMERALS[Math.max(0, storybook.pages.length - 1)] || "III";
  const currentSceneIdx =
    typeof currentPage?.sceneIdx === "number" ? currentPage.sceneIdx : currentPageIdx;
  const currentSceneRoman = ROMAN_NUMERALS[currentSceneIdx] || "I";

  const plates =
    currentPage?.plates && currentPage.plates.length > 0
      ? currentPage.plates
      : [
          {
            plateNumberRoman: currentSceneRoman,
            plateLabel: `PLATE ${currentSceneRoman} OF ${totalScenesRoman}`,
            title: currentPage?.imageCaption || storybook.title,
            illustrationPrompt:
              currentPage?.illustrationPrompt || storybook.coverImagePrompt,
            imageUrl:
              currentPage?.dioramaUrl ||
              currentPage?.imageUrl ||
              storybook.coverImageUrl,
          },
        ];

  const resolvedPlateIdx =
    manualPlateIdx !== null
      ? Math.min(manualPlateIdx, plates.length - 1)
      : Math.min(activeLine?.plateIndex ?? 0, plates.length - 1);
  const currentPlate = plates[resolvedPlateIdx] || plates[0];

  const canonicalPlateLabel =
    currentPlate?.plateLabel &&
    currentPlate.plateLabel.startsWith("PLATE ") &&
    !currentPlate.plateLabel.endsWith("OF I")
      ? currentPlate.plateLabel
      : `PLATE ${currentSceneRoman} OF ${totalScenesRoman}`;

  // Calculate continuous chapter reading progress [0..1] for the 2px right-page footer filament
  const titleEndSec = storybook.titleCardEndSec ?? 2.6;
  const totalDurSec = storybook.totalDurationSeconds || 113.25;
  const chapterProgress = Math.max(
    0,
    Math.min(1, (playbackTimeSec - titleEndSec) / Math.max(1, totalDurSec - titleEndSec))
  );

  // Stop all active audio & timers cleanly
  const stopAllPlayback = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    const masterEl = getMasterAudioEl();
    if (masterEl) {
      masterEl.pause();
    }
    const musicEl = getMusicAudioEl();
    if (musicEl) {
      musicEl.pause();
    }
    setIsPlayingAudio(false);
  };

  useEffect(() => {
    return () => {
      stopAllPlayback();
    };
  }, []);

  // Synchronize audio source & start auto-narration at `startAtSec`
  const startBookNarration = (
    targetBook: Storybook,
    startAtSec: number = 0,
    withOpeningTitleCard: boolean = true
  ) => {
    const normalized = ensureBookTimeline(targetBook);
    const masterEl = getMasterAudioEl();
    const musicEl = getMusicAudioEl();

    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }

    virtualClockRef.current = startAtSec;
    lastWallClockMsRef.current = typeof performance !== "undefined" ? performance.now() : Date.now();
    lastSpokenTurnKeyRef.current = "";
    setPlaybackTimeSec(startAtSec);

    const shouldShowIntroTitle = withOpeningTitleCard && startAtSec < 1.8;
    setShowOpeningTitleCard(shouldShowIntroTitle);
    showOpeningTitleCardRef.current = shouldShowIntroTitle;

    if (!shouldShowIntroTitle) {
      setIsDioramaUnfolding(true);
      setTimeout(() => setIsDioramaUnfolding(false), 1350);
    }

    // Play the mastered multi-voice + Lyria 3.5 MP4/WAV track if available
    if (normalized.masterAudioUrl && masterEl) {
      if (musicEl) musicEl.pause();
      const currentSrc = masterEl.getAttribute("data-book-src") || "";
      if (currentSrc !== normalized.masterAudioUrl) {
        masterEl.src = normalized.masterAudioUrl;
        masterEl.setAttribute("data-book-src", normalized.masterAudioUrl);
      }
      try {
        masterEl.currentTime = startAtSec;
      } catch {
        // Seek applied on loadedmetadata if not yet buffered
        masterEl.onloadedmetadata = () => {
          try {
            masterEl.currentTime = startAtSec;
          } catch {}
        };
      }
      masterEl.volume = 1.0;
      masterEl.play().catch(() => {
        // If browser autoplay blocks unmuted playback before gesture, virtualClockRef still drives visual highlighting
      });
    } else if (musicEl && isMusicEnabled && normalized.backgroundMusicUrl) {
      if (masterEl) masterEl.pause();
      musicEl.src = normalized.backgroundMusicUrl;
      musicEl.volume = 0.16;
      musicEl.play().catch(() => {});
    }

    setIsPlayingAudio(true);
  };

  // Master 80ms timeline loop: drives Opening Title Card -> 3D Page Turn & Pop-Up Unfold ->
  // 3-State Paragraph Highlighting -> Same-Scene Right-Page Folio Crossfades
  useEffect(() => {
    if (!isPlayingAudio || viewMode !== "reader") return;

    lastWallClockMsRef.current = typeof performance !== "undefined" ? performance.now() : Date.now();

    const intervalId = setInterval(() => {
      const nowMs = typeof performance !== "undefined" ? performance.now() : Date.now();
      const dtSec = Math.min(0.25, Math.max(0, (nowMs - lastWallClockMsRef.current) / 1000));
      lastWallClockMsRef.current = nowMs;

      const masterEl = getMasterAudioEl();
      let tSec = virtualClockRef.current;

      if (
        storybook.masterAudioUrl &&
        masterEl &&
        !masterEl.paused &&
        !masterEl.ended &&
        Number.isFinite(masterEl.currentTime)
      ) {
        tSec = masterEl.currentTime;
        virtualClockRef.current = tSec;
      } else {
        tSec = virtualClockRef.current + dtSec;
        virtualClockRef.current = tSec;
      }

      setPlaybackTimeSec(tSec);

      const totalDur = storybook.totalDurationSeconds || 113.25;
      const titleTurnStartSec = Math.max(1.45, (storybook.titleCardEndSec ?? 2.6) - 0.4);

      // 1. Opening Title Card (0.0s .. 2.2s) -> Spine-Hinged Page Turn & Pop-Up Diorama Unfold
      if (tSec < titleTurnStartSec) {
        if (!showOpeningTitleCardRef.current) {
          showOpeningTitleCardRef.current = true;
          setShowOpeningTitleCard(true);
        }
        return;
      } else if (showOpeningTitleCardRef.current) {
        showOpeningTitleCardRef.current = false;
        setShowOpeningTitleCard(false);
        setIsPageTurning(true);
        setIsDioramaUnfolding(true);
        setTimeout(() => setIsPageTurning(false), 650);
        setTimeout(() => setIsDioramaUnfolding(false), 1350);
      }

      // 2. Determine active folio index `targetPageIdx` from `pages[pIdx].startSec`
      const pages = storybook.pages || [];
      let targetPageIdx = 0;
      for (let pIdx = 0; pIdx < pages.length; pIdx++) {
        const pStart = pages[pIdx].startSec ?? 0;
        if (tSec >= pStart) {
          targetPageIdx = pIdx;
        } else {
          break;
        }
      }

      if (targetPageIdx !== currentPageIdxRef.current) {
        const prevPage = pages[currentPageIdxRef.current];
        const nextPage = pages[targetPageIdx];
        const prevSceneIdx = prevPage?.sceneIdx ?? currentPageIdxRef.current;
        const nextSceneIdx = nextPage?.sceneIdx ?? targetPageIdx;

        currentPageIdxRef.current = targetPageIdx;
        setCurrentPageIdx(targetPageIdx);
        setManualPlateIdx(null);

        if (prevSceneIdx === nextSceneIdx) {
          // Same visual scene (e.g., Pride & Prejudice Folios I.1 -> I.2 -> I.3):
          // Crossfade ONLY the right-hand text page while the left-hand 3D Pop-Up Diorama stays steady
          setIsRightFolioFading(true);
          setTimeout(() => setIsRightFolioFading(false), 450);
        } else {
          // New visual scene (e.g., Alice Scene I -> Scene II):
          // Full spine-hinged page turn + 3D Pop-Up Diorama unfold
          setIsPageTurning(true);
          setIsDioramaUnfolding(true);
          setTimeout(() => setIsPageTurning(false), 650);
          setTimeout(() => setIsDioramaUnfolding(false), 1350);
        }
      }

      // 3. Determine active turn index `targetLineIdx` within `pages[targetPageIdx]`
      //    (-1 = pre-speech future_ink, 0..N-1 = active turn ink_rgb, 999 = post-speech past_ink)
      const fLines = pages[targetPageIdx]?.dialogueLines || [];
      let targetLineIdx = -1;

      if (fLines.length > 0) {
        const firstStart = fLines[0].startSec ?? 5.4;
        if (tSec >= firstStart) {
          let kActive = 0;
          for (let k = 0; k < fLines.length; k++) {
            if (tSec >= (fLines[k].startSec ?? 0)) {
              kActive = k;
            } else {
              break;
            }
          }
          const curTurn = fLines[kActive];
          if (kActive === fLines.length - 1 && tSec >= (curTurn.endSec ?? 99999)) {
            targetLineIdx = 999;
          } else {
            targetLineIdx = kActive;
          }
        }
      }

      if (targetLineIdx !== activeLineIdxRef.current) {
        activeLineIdxRef.current = targetLineIdx;
        setActiveLineIdx(targetLineIdx);

        // If this is a custom commissioned book without a single masterAudioUrl, speak the active turn
        if (
          !storybook.masterAudioUrl &&
          targetLineIdx >= 0 &&
          targetLineIdx < fLines.length
        ) {
          const turnKey = `${storybook.id}_${targetPageIdx}_${targetLineIdx}`;
          if (lastSpokenTurnKeyRef.current !== turnKey) {
            lastSpokenTurnKeyRef.current = turnKey;
            const line = fLines[targetLineIdx];
            if (line.audioDataUrl && masterEl) {
              masterEl.src = line.audioDataUrl;
              masterEl.play().catch(() => {});
            } else if (typeof window !== "undefined" && "speechSynthesis" in window) {
              try {
                window.speechSynthesis.cancel();
                const utter = new SpeechSynthesisUtterance(
                  line.ttsText || line.text.replace(/[“”"]/g, "")
                );
                utter.rate = 0.98;
                window.speechSynthesis.speak(utter);
              } catch {}
            }
          }
        }
      }

      // 4. Stop cleanly at end of chapter
      if (tSec >= totalDur) {
        stopAllPlayback();
      }
    }, 80);

    return () => clearInterval(intervalId);
  }, [isPlayingAudio, viewMode, storybook]);

  // Seek directly to a specific folio & turn (and continue auto-narrating from there)
  const seekToFolioAndTurn = (pageIdx: number, lineIdx: number) => {
    const pages = storybook.pages || [];
    const targetPage = pages[pageIdx] || pages[0];
    const lines = targetPage?.dialogueLines || [];
    const safeLineIdx = Math.max(0, Math.min(lineIdx, Math.max(0, lines.length - 1)));
    const targetLine = lines[safeLineIdx];
    const targetSec = targetLine?.startSec ?? targetPage?.startSec ?? 5.4;

    const prevSceneIdx = pages[currentPageIdx]?.sceneIdx ?? currentPageIdx;
    const nextSceneIdx = targetPage?.sceneIdx ?? pageIdx;

    setShowOpeningTitleCard(false);
    showOpeningTitleCardRef.current = false;
    setManualPlateIdx(null);

    if (pageIdx !== currentPageIdx) {
      if (prevSceneIdx === nextSceneIdx) {
        setIsRightFolioFading(true);
        setTimeout(() => setIsRightFolioFading(false), 450);
      } else {
        setIsPageTurning(true);
        setIsDioramaUnfolding(true);
        setTimeout(() => setIsPageTurning(false), 650);
        setTimeout(() => setIsDioramaUnfolding(false), 1350);
      }
    }

    currentPageIdxRef.current = pageIdx;
    activeLineIdxRef.current = safeLineIdx;
    setCurrentPageIdx(pageIdx);
    setActiveLineIdx(safeLineIdx);

    virtualClockRef.current = targetSec;
    lastWallClockMsRef.current = typeof performance !== "undefined" ? performance.now() : Date.now();
    setPlaybackTimeSec(targetSec);

    const masterEl = getMasterAudioEl();
    if (storybook.masterAudioUrl && masterEl) {
      const currentSrc = masterEl.getAttribute("data-book-src") || "";
      if (currentSrc !== storybook.masterAudioUrl) {
        masterEl.src = storybook.masterAudioUrl;
        masterEl.setAttribute("data-book-src", storybook.masterAudioUrl);
      }
      try {
        masterEl.currentTime = targetSec;
      } catch {}
      masterEl.play().catch(() => {});
    }
    setIsPlayingAudio(true);
  };

  // Turn the leaf from the Title & Contents Folio directly into a bound volume AND auto-narrate!
  const handleOpenExistingBook = (book: Storybook, startFromTitleCard: boolean = true) => {
    stopAllPlayback();
    const normalized = ensureBookTimeline(book);
    setStorybook(normalized);
    setCurrentPageIdx(0);
    setActiveLineIdx(-1);
    setManualPlateIdx(null);
    setIsPageTurning(true);
    setViewMode("reader");
    setTimeout(() => {
      setIsPageTurning(false);
    }, 650);

    // Automatically begin narrating the volume from t = 0.0s (Title Card -> Page Turn -> Highlighted Narration)
    startBookNarration(normalized, startFromTitleCard ? 0 : 5.4, startFromTitleCard);
  };

  // Turn back to the Title & Commission Folio
  const handleCloseBookToCover = () => {
    stopAllPlayback();
    setShowOpeningTitleCard(false);
    setShowTitleCardModal(false);
    setIsPageTurning(true);
    setViewMode("cover");
    setTimeout(() => {
      setIsPageTurning(false);
    }, 650);
  };

  // Toggle Pause / Resume Narration
  const handleToggleNarration = () => {
    const masterEl = getMasterAudioEl();
    if (isPlayingAudio) {
      stopAllPlayback();
    } else {
      const resumeSec =
        playbackTimeSec >= (storybook.totalDurationSeconds || 113) - 1
          ? 0
          : playbackTimeSec;
      if (storybook.masterAudioUrl && masterEl) {
        const currentSrc = masterEl.getAttribute("data-book-src") || "";
        if (currentSrc !== storybook.masterAudioUrl) {
          masterEl.src = storybook.masterAudioUrl;
          masterEl.setAttribute("data-book-src", storybook.masterAudioUrl);
        }
        try {
          masterEl.currentTime = resumeSec;
        } catch {}
        masterEl.play().catch(() => {});
      }
      virtualClockRef.current = resumeSec;
      lastWallClockMsRef.current = typeof performance !== "undefined" ? performance.now() : Date.now();
      setIsPlayingAudio(true);
    }
  };

  // Cycle through the current folio's plates (3D pop-up diorama -> 2D watercolour plate -> character sheet)
  const handleCyclePlate = () => {
    if (plates.length <= 1) return;
    setManualPlateIdx((resolvedPlateIdx + 1) % plates.length);
  };

  // Commission a new Storybook via the Gemini Managed Agent (`antigravity-preview-09-2026` / `gemini-4-argon`)
  const handleCommissionStorybook = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    stopAllPlayback();
    setAgentError(null);
    setAgentLogs([]);
    setActiveStageIdx(0);
    setActiveStageLabel("Booting Managed Agent Sandbox");

    if (apiKeyInput.trim()) {
      try {
        if (typeof window !== "undefined" && window.localStorage) {
          window.localStorage.setItem("FOLIO_GEMINI_API_KEY", apiKeyInput.trim());
        }
      } catch {
        // Null-origin sandbox blocks localStorage
      }
    }

    setIsPageTurning(true);
    setViewMode("crafting");
    setIsRunningAgent(true);
    setTimeout(() => {
      setIsPageTurning(false);
    }, 650);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const result = await runManagedAgentStorybook({
        prompt: commissionPrompt,
        paletteKey: selectedPaletteKey,
        visualStyle,
        pageCount: 3,
        narratorVoice,
        agentName,
        modelName,
        apiKey: apiKeyInput.trim(),
        environmentId,
        previousInteractionId: interactionId,
        sessionId: `session_${Date.now()}`,
        signal: controller.signal,
        onLog: (entry) => {
          setAgentLogs((prev) => [...prev, entry]);
        },
        onStageChange: (stageIdx, stageLabel) => {
          setActiveStageIdx(stageIdx);
          setActiveStageLabel(stageLabel);
        },
        onCreated: (id, envId) => {
          setInteractionId(id);
          if (envId) setEnvironmentId(envId);
        },
      });

      const normalized = ensureBookTimeline(result.storybook);
      setStorybook(normalized);
      setLibrary((prev) => {
        const exists = prev.some((b) => b.id === normalized.id);
        return exists ? prev : [normalized, ...prev];
      });
      setCurrentPageIdx(0);
      setActiveLineIdx(-1);
      setManualPlateIdx(null);
      setIsRunningAgent(false);
      setIsPageTurning(true);
      setViewMode("reader");
      setTimeout(() => {
        setIsPageTurning(false);
      }, 650);

      // Automatically begin narrating the newly commissioned edition!
      startBookNarration(normalized, 0, true);
    } catch (err: any) {
      if (err?.name === "AbortError") {
        setIsRunningAgent(false);
        setViewMode("cover");
        return;
      }
      setAgentError(err?.message || "Failed to run Managed Agent");
      setIsRunningAgent(false);
    }
  };

  // Synthesize real Gemini Flash TTS WAV for the current Folio
  const handleSynthesizeFolioWav = async () => {
    setIsSynthesizingAudio(true);
    setStatusNote("Synthesizing 24 kHz WAV via Gemini Flash TTS…");
    try {
      const wavDataUri = await synthesizeStudioPageAudio(
        dialogueLines,
        currentPage.narrativeText,
        narratorVoice
      );
      const masterEl = getMasterAudioEl();
      if (masterEl) {
        masterEl.src = wavDataUri;
        masterEl.setAttribute("data-book-src", wavDataUri);
        masterEl.play().catch(() => {});
      }
      setIsPlayingAudio(true);
      setStatusNote("Playing mastered 24 kHz Gemini TTS folio audio");
      setTimeout(() => setStatusNote(null), 4000);
    } catch {
      setStatusNote("Playing mastered multi-voice & Lyria 3.5 edition audio");
      handleToggleNarration();
      setTimeout(() => setStatusNote(null), 4000);
    } finally {
      setIsSynthesizingAudio(false);
    }
  };

  // Repaint current plate using `gemini-3.1-flash-lite-image`
  const handleRepaintCurrentPlate = async () => {
    setIsRegeneratingPlate(true);
    setStatusNote("Engraving 16:9 plate on #F6F2EA cream paper…");
    try {
      const newDataUrl = await generateStudioIllustration(
        `${currentPlate.illustrationPrompt}. ${storybook.visualStyle}. Flat 2D illustration on warm cream archival paper (#F6F2EA), 16:9, no text, no borders.`,
        "16:9"
      );
      const updatedPages = storybook.pages.map((p, idx) => {
        if (idx !== currentPageIdx) return p;
        const updatedPlates = (p.plates || []).map((pl, pIdx) =>
          pIdx === resolvedPlateIdx ? { ...pl, imageUrl: newDataUrl } : pl
        );
        return {
          ...p,
          imageUrl: newDataUrl,
          plates: updatedPlates,
        };
      });
      setStorybook({ ...storybook, pages: updatedPages });
      setStatusNote("Plate engraved on #F6F2EA archival paper");
      setTimeout(() => setStatusNote(null), 3500);
    } catch {
      setStatusNote("Set GEMINI_API_KEY in Colophon to engrave plates live");
      setTimeout(() => setStatusNote(null), 3500);
    } finally {
      setIsRegeneratingPlate(false);
    }
  };

  // Keyboard navigation in Reader mode (←/→/↑/↓ for turns & folios, Space for play/pause)
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (viewMode !== "reader" || showTitleCardModal || showAgentSpecModal) return;
      if (
        document.activeElement?.tagName === "INPUT" ||
        document.activeElement?.tagName === "TEXTAREA" ||
        document.activeElement?.tagName === "SELECT"
      ) {
        return;
      }
      if (e.key === "ArrowDown" || e.key === "ArrowRight") {
        e.preventDefault();
        if (showOpeningTitleCard) {
          seekToFolioAndTurn(0, 0);
        } else if (activeLineIdx < dialogueLines.length - 1) {
          seekToFolioAndTurn(currentPageIdx, Math.max(0, activeLineIdx + 1));
        } else if (currentPageIdx < storybook.pages.length - 1) {
          seekToFolioAndTurn(currentPageIdx + 1, 0);
        }
      } else if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
        e.preventDefault();
        if (activeLineIdx > 0 && activeLineIdx < 999) {
          seekToFolioAndTurn(currentPageIdx, activeLineIdx - 1);
        } else if (currentPageIdx > 0) {
          const prevLines = storybook.pages[currentPageIdx - 1]?.dialogueLines || [];
          seekToFolioAndTurn(currentPageIdx - 1, Math.max(0, prevLines.length - 1));
        }
      } else if (e.key === " ") {
        e.preventDefault();
        handleToggleNarration();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [
    viewMode,
    activeLineIdx,
    currentPageIdx,
    dialogueLines.length,
    storybook,
    isPlayingAudio,
    showOpeningTitleCard,
    showTitleCardModal,
    showAgentSpecModal,
  ]);

  const formattedBookHeaderLeft = (
    storybook.bookHeaderLeft ||
    `BOOK ${storybook.roman || "I"}  ·  ${storybook.author.toUpperCase()}`
  ).replace(/\s*·\s*/g, "  ·  ");

  const latestLogs = agentLogs.slice(-6);

  const renderLanguageSwitcher = () => (
    <div
      className="folio-lang-toggle"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
      }}
    >
      <button
        type="button"
        onClick={() => handleToggleLanguage("ko")}
        style={{
          background: "transparent",
          border: "none",
          cursor: "pointer",
          fontFamily: "var(--font-cinzel)",
          fontSize: "12px",
          letterSpacing: "0.08em",
          padding: "1px 4px",
          color: language === "ko" ? "var(--folio-accent)" : "var(--folio-muted)",
          fontWeight: language === "ko" ? 700 : 400,
          textDecoration: language === "ko" ? "underline" : "none",
          textUnderlineOffset: "3px",
        }}
        title="한국어로 전환"
      >
        한국어
      </button>
      <span style={{ color: "var(--folio-rule)", fontSize: "11px" }}>/</span>
      <button
        type="button"
        onClick={() => handleToggleLanguage("en")}
        style={{
          background: "transparent",
          border: "none",
          cursor: "pointer",
          fontFamily: "var(--font-cinzel)",
          fontSize: "12px",
          letterSpacing: "0.08em",
          padding: "1px 4px",
          color: language === "en" ? "var(--folio-accent)" : "var(--folio-muted)",
          fontWeight: language === "en" ? 700 : 400,
          textDecoration: language === "en" ? "underline" : "none",
          textUnderlineOffset: "3px",
        }}
        title="Switch to English"
      >
        English
      </button>
    </div>
  );

  return (
    <div style={paletteCssVars} className="archival-paper-surface">
      {/* ====================================================================
          STATE 1: OPEN-BOOK TITLE & COMMISSION FOLIO SPREAD (HOME PAGE)
          Uses the exact #F6F2EA cream paper, #D5CBB8 1px rules, and 52.917%
          spine geometry as the finished agent output (zero pills or boxes)
          ==================================================================== */}
      {viewMode === "cover" && (
        <div className="austen-spread-viewport">
          <div
            className={`austen-open-book ${
              isPageTurning ? "folio-page-turning" : ""
            }`}
          >
            {/* ==============================================================
                VERSO (LEFT PAGE): FINE-PRESS TITLE PAGE & TABLE OF CONTENTS
                (Typography ladder from render_title_card in render_audiobook_video.py)
                ============================================================== */}
            <div className="austen-left-page">
              <div className="austen-running-bar">
                <span>{t.pressName}</span>
                <div style={{ display: "flex", alignItems: "baseline", gap: "14px" }}>
                  {renderLanguageSwitcher()}
                  <span>{t.era}</span>
                </div>
              </div>

              <div className="folio-title-verso">
                <div className="folio-title-block">
                  <div
                    style={{
                      fontFamily: "var(--font-cinzel)",
                      fontSize: "15px",
                      letterSpacing: "0.153em",
                      color: "var(--folio-accent)",
                      textTransform: "uppercase",
                      marginBottom: "12px",
                    }}
                  >
                    {t.tagline}
                  </div>

                  <h1
                    style={{
                      fontFamily: "var(--font-cormorant)",
                      fontSize: "clamp(42px, 3.6vw, 62px)",
                      fontWeight: 500,
                      color: "var(--folio-ink)",
                      margin: "0 0 12px 0",
                      lineHeight: 1.06,
                    }}
                  >
                    {t.mainTitle}
                  </h1>

                  <div
                    style={{
                      fontFamily: "var(--font-cinzel)",
                      fontSize: "15px",
                      letterSpacing: "0.12em",
                      color: "var(--folio-muted)",
                      textTransform: "uppercase",
                      whiteSpace: "pre",
                    }}
                  >
                    {t.subBadge}
                  </div>

                  {/* Fine-Press Diamond Rule (y=282 in render_title_card) */}
                  <div className="folio-diamond-rule">
                    <div className="folio-diamond-rule-line" />
                    <div className="folio-diamond-rule-gem" />
                    <div className="folio-diamond-rule-line" />
                  </div>

                  <div
                    style={{
                      fontFamily: "var(--font-garamond)",
                      fontStyle: "italic",
                      fontSize: "clamp(21px, 1.55vw, 27px)",
                      color: "var(--folio-ink)",
                    }}
                  >
                    {t.heroSubtitle}
                  </div>
                </div>

                {/* Classic Typographic Table of Contents (replaces boxed cards) */}
                <div className="folio-contents-section">
                  <div
                    className="austen-turn-rubric"
                    style={{
                      color: "var(--folio-accent)",
                      marginBottom: "10px",
                    }}
                  >
                    {t.contentsRubric}
                  </div>

                  <div className="folio-contents-list">
                    {library.map((book, idx) => {
                      const bookTitle =
                        language === "ko"
                          ? KOREAN_BOOK_METAS[book.id]?.title || book.title
                          : book.title;
                      const bookAuthor =
                        language === "ko"
                          ? KOREAN_BOOK_METAS[book.id]?.author || book.author
                          : book.author;
                      return (
                        <button
                          key={book.id}
                          type="button"
                          onClick={() => handleOpenExistingBook(book, true)}
                          className="folio-contents-row"
                        >
                          <span className="folio-contents-roman">
                            {book.roman || ROMAN_NUMERALS[idx] || "I"}
                          </span>
                          <span className="folio-contents-title">{bookTitle}</span>
                          <span className="folio-contents-leader" />
                          <span className="folio-contents-meta">
                            {bookAuthor}, {book.year || "1813"}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              <div className="austen-footer-bar">
                <span>{t.footerLeft}</span>
                <span>{t.footerRight}</span>
              </div>
            </div>

            {/* ==============================================================
                RECTO (RIGHT PAGE): COMMISSION FOLIO ("BOOK VI")
                Mirrors the exact speaker band & 3-state literary body of Reader
                ============================================================== */}
            <div className="austen-right-page">
              <div className="austen-running-bar">
                <span>{t.commissionHeader}</span>
                <div style={{ display: "flex", alignItems: "baseline", gap: "12px" }}>
                  {renderLanguageSwitcher()}
                  <span>{t.commissionChapter}</span>
                </div>
              </div>

              <div className="austen-speaker-band">
                <div>
                  <span
                    className="austen-speaker-name"
                    style={{ color: "var(--folio-accent)" }}
                  >
                    {t.authorSpeaker}
                  </span>
                  <span className="austen-speaker-role">
                    {t.authorRole}
                  </span>
                </div>
              </div>

              <form
                onSubmit={handleCommissionStorybook}
                className="austen-folio-body"
              >
                {/* Turn 1: Borderless Manuscript Inscription Surface */}
                <div className="austen-turn-block state-active">
                  <label
                    htmlFor="fairytale-prompt"
                    className="austen-turn-rubric"
                    style={{ display: "block", cursor: "pointer" }}
                  >
                    {t.inscription}
                  </label>
                  <textarea
                    id="fairytale-prompt"
                    rows={3}
                    value={commissionPrompt}
                    onChange={(e) => setCommissionPrompt(e.target.value)}
                    placeholder={t.inscriptionPlaceholder}
                    className="folio-manuscript-textarea"
                  />
                </div>

                {/* Turn 2: Continuous Italic Seed Run (zero pills, zero boxes) */}
                <div className="austen-turn-block state-past">
                  <div className="austen-turn-rubric">{t.presetRubric}</div>
                  <p className="austen-turn-text" style={{ lineHeight: 1.5 }}>
                    {activeFairytalePrompts.map((item, idx) => {
                      const isSelected = commissionPrompt === item.prompt;
                      return (
                        <React.Fragment key={item.id}>
                          {idx > 0 && (
                            <span
                              style={{
                                color: "var(--folio-muted)",
                                fontStyle: "normal",
                              }}
                            >
                              {"  ·  "}
                            </span>
                          )}
                          <button
                            type="button"
                            onClick={() => {
                              setCommissionPrompt(item.prompt);
                              if ("paletteKey" in item && item.paletteKey) {
                                setSelectedPaletteKey(item.paletteKey as string);
                              }
                            }}
                            className={`folio-seed-link ${
                              isSelected ? "is-selected" : ""
                            }`}
                          >
                            {item.title}
                          </button>
                        </React.Fragment>
                      );
                    })}
                  </p>
                </div>

                {/* Turn 3: Inline Colophon Sentence & Typographic Inscription Link */}
                <div className="austen-turn-block state-active">
                  <div className="austen-turn-rubric">
                    {language === "ko" ? "장본 명세 (EDITION COLOPHON)" : "EDITION COLOPHON"}
                  </div>
                  <p
                    className="austen-turn-text"
                    style={{
                      fontStyle: "italic",
                      fontSize: "clamp(18px, 1.2vw, 21px)",
                      color: "var(--folio-muted)",
                    }}
                  >
                    {language === "ko" ? "장본: " : "Bound in "}
                    <select
                      aria-label="Edition palette"
                      value={selectedPaletteKey}
                      onChange={(e) => setSelectedPaletteKey(e.target.value)}
                      className="folio-inline-select"
                    >
                      {Object.entries(EDITION_PALETTES).map(([key, info]) => (
                        <option key={key} value={key}>
                          {info.label}
                        </option>
                      ))}
                    </select>
                    {language === "ko" ? "  ·  낭독: " : "  ·  read by "}
                    <select
                      aria-label="Primary narrator voice"
                      value={narratorVoice}
                      onChange={(e) => setNarratorVoice(e.target.value)}
                      className="folio-inline-select"
                    >
                      {GEMINI_TTS_VOICES.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.label}
                        </option>
                      ))}
                    </select>
                    {language === "ko" ? "  ·  삽화: " : "  ·  plates in "}
                    <select
                      aria-label="Illustration wash style"
                      value={visualStyle}
                      onChange={(e) => setVisualStyle(e.target.value)}
                      className="folio-inline-select"
                    >
                      {VISUAL_STYLE_PRESETS.map((preset) => (
                        <option key={preset.id} value={preset.value}>
                          {preset.label}
                        </option>
                      ))}
                    </select>
                    .
                  </p>

                  <div
                    style={{
                      display: "flex",
                      justifyContent: "flex-end",
                      marginTop: "18px",
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => handleCommissionStorybook()}
                      className="folio-commission-link"
                    >
                      {t.commissionBtn} &nbsp;&rarr;
                    </button>
                  </div>
                </div>
              </form>

              <div className="austen-footer-bar">
                <div
                  className="austen-progress-filament"
                  style={{ width: "33.3%" }}
                />
                <span>GEMINI MANAGED AGENT</span>
                <span>{language === "ko" ? "제VI.1쪽" : "FOLIO VI.1"}</span>
              </div>
            </div>
          </div>

          {/* Subtle Outer Margin Line below the bottom rule */}
          <div className="austen-margin-bar">
            <div />
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              <button
                type="button"
                onClick={() => handleOpenExistingBook(INITIAL_SHOWCASE_STORYBOOK, true)}
                className="austen-margin-link"
              >
                {language === "ko"
                  ? "오만과 편견 (1813) 바로 열람 및 낭독 시작 →"
                  : "OPEN & AUTO-NARRATE PRIDE AND PREJUDICE (1813) →"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ====================================================================
          STATE 2: ILLUMINATOR'S OPEN FOLIO SPREAD WHILE MANAGED AGENT CRAFTS
          Uses the exact same two-page spread and 3-state paragraph ink
          ==================================================================== */}
      {viewMode === "crafting" && (
        <div className="austen-spread-viewport">
          <div
            className={`austen-open-book ${
              isPageTurning ? "folio-page-turning" : ""
            }`}
          >
            {/* LEFT PAGE: Matted 16:9 Stage Box being engraved */}
            <div className="austen-left-page">
              <div className="austen-running-bar">
                <span>
                  {language === "ko"
                    ? "제VI권 · GEMINI 매니지드 에이전트"
                    : "BOOK VI  ·  GEMINI MANAGED AGENT"}
                </span>
                <div style={{ display: "flex", alignItems: "baseline", gap: "14px" }}>
                  {renderLanguageSwitcher()}
                  <span>{t.era}</span>
                </div>
              </div>

              <div className="austen-plate-mat">
                <div
                  className="austen-plate-stage"
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "24px 28px",
                    textAlign: "center",
                    overflow: "hidden",
                  }}
                >
                  <div>
                    <div
                      style={{
                        fontFamily: "var(--font-cinzel)",
                        fontSize: "12px",
                        letterSpacing: "0.153em",
                        color: "var(--folio-accent)",
                        textTransform: "uppercase",
                        marginBottom: "8px",
                      }}
                    >
                      {agentName.toUpperCase()}  ·  {modelName.toUpperCase()}
                    </div>

                    <div
                      style={{
                        fontFamily: "var(--font-garamond)",
                        fontStyle: "italic",
                        fontSize: "clamp(19px, 1.35vw, 23px)",
                        color: "var(--folio-ink)",
                        maxWidth: "560px",
                        lineHeight: 1.32,
                      }}
                    >
                      {activeStageLabel ||
                        (language === "ko"
                          ? "아카이브 용지 위에 판화를 각인하고 있습니다…"
                          : "The plate is being engraved upon archival paper…")}
                    </div>

                    <div
                      className="folio-diamond-rule"
                      style={{ maxWidth: "240px", margin: "12px auto" }}
                    >
                      <div className="folio-diamond-rule-line" />
                      <div className="folio-diamond-rule-gem" />
                      <div className="folio-diamond-rule-line" />
                    </div>
                  </div>

                  <div
                    style={{
                      width: "100%",
                      textAlign: "left",
                      display: "flex",
                      flexDirection: "column",
                      gap: "5px",
                      borderTop: "1px solid var(--folio-rule)",
                      paddingTop: "10px",
                    }}
                  >
                    {latestLogs.map((log) => (
                      <div
                        key={log.id}
                        style={{
                          fontFamily: "var(--font-garamond)",
                          fontSize: "14px",
                          lineHeight: 1.28,
                          color: "var(--folio-ink)",
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        <span
                          style={{
                            fontFamily: "var(--font-cinzel)",
                            fontSize: "10.5px",
                            letterSpacing: "0.08em",
                            color: "var(--folio-accent)",
                            marginRight: "8px",
                          }}
                        >
                          {log.timestamp}
                        </span>
                        <span style={{ fontWeight: 500 }}>{log.title}</span>
                        {log.detail ? (
                          <span
                            style={{
                              fontStyle: "italic",
                              color: "var(--folio-muted)",
                            }}
                          >
                            {"  —  "}
                            {log.detail.replace(/\s+/g, " ").slice(0, 110)}
                          </span>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="austen-plate-caption-row">
                  <span className="austen-plate-number">
                    {environmentId
                      ? `ENV · ${environmentId.slice(0, 10).toUpperCase()}`
                      : "SANDBOX · LIVE"}
                  </span>
                  <span className="austen-plate-caption">
                    {interactionId
                      ? `Interaction ${interactionId.slice(0, 14)}…`
                      : "Streaming from /v1beta/interactions"}
                  </span>
                </div>
              </div>

              <div className="austen-footer-bar">
                <span>
                  {language === "ko" ? "일러스트 오디오북 판본" : "ILLUSTRATED AUDIOBOOK EDITION"}
                </span>
                <span>SANDBOX · GEMINI-API-CLI</span>
              </div>
            </div>

            {/* RIGHT PAGE: 5 Pipeline Stages as 3-State Literary Paragraphs */}
            <div className="austen-right-page">
              <div className="austen-running-bar">
                <span>{language === "ko" ? "새로운 장본 의뢰" : "A NEW COMMISSION"}</span>
                <span>{t.commissionChapter}</span>
              </div>

              <div className="austen-speaker-band">
                <div>
                  <span
                    className="austen-speaker-name"
                    style={{ color: "var(--folio-accent)" }}
                  >
                    {language === "ko" ? "삽화가 및 편집장" : "THE ILLUSTRATOR"}
                  </span>
                  <span className="austen-speaker-role">
                    {language === "ko"
                      ? `  —  제${ROMAN_NUMERALS[activeStageIdx] || "I"}단계 (총 5단계)`
                      : `  —  Stage ${ROMAN_NUMERALS[activeStageIdx] || "I"} of V`}
                  </span>
                </div>
              </div>

              <div className="austen-folio-body">
                {activePipelineStages.map((st) => {
                  const turnStateClass =
                    st.index === activeStageIdx
                      ? "state-active"
                      : st.index < activeStageIdx
                      ? "state-past"
                      : "state-future";
                  return (
                    <div
                      key={st.index}
                      className={`austen-turn-block ${turnStateClass}`}
                    >
                      <div className="austen-turn-rubric">{st.code}</div>
                      <p className="austen-turn-text">{st.title}</p>
                    </div>
                  );
                })}

                {agentError && (
                  <div className="austen-turn-block state-active">
                    <div
                      className="austen-turn-rubric"
                      style={{ color: "#9E332B" }}
                    >
                      {language === "ko" ? "샌드박스 알림" : "SANDBOX NOTICE"}
                    </div>
                    <p
                      className="austen-turn-text"
                      style={{ color: "#9E332B", fontStyle: "italic" }}
                    >
                      {agentError}
                    </p>
                  </div>
                )}
              </div>

              <div className="austen-footer-bar">
                <div
                  className="austen-progress-filament"
                  style={{ width: `${((activeStageIdx + 1) / 5) * 100}%` }}
                />
                <span>{language === "ko" ? "제I경" : "SCENE I"}</span>
                <span>{language === "ko" ? "제VI.1쪽" : "FOLIO VI.1"}</span>
              </div>
            </div>
          </div>

          <div className="austen-margin-bar">
            <span>
              {environmentId
                ? `SANDBOX ${environmentId.slice(0, 12)}`
                : language === "ko"
                ? "가상 샌드박스 컨테이너 프로비저닝 중"
                : "PROVISIONING SANDBOX CONTAINER"}
            </span>
            <button
              type="button"
              onClick={() => abortControllerRef.current?.abort()}
              className="austen-margin-link"
            >
              {t.cancelBtn}
            </button>
          </div>
        </div>
      )}

      {/* ====================================================================
          STATE 3: THE JANE AUSTEN TWO-PAGE OPEN FOLIO SPREAD (READER & PLAYER)
          Pixel-faithful to classic_novels_opening_chapters.mp4:
          - 0.0s .. 2.2s: Full-Frame Fine-Press Chapter Title Card with Character Sheet
          - 2.2s .. 5.4s: 3D Spine-Hinged Page Turn & Pop-Up Diorama Unfold (all turns in state-future)
          - 5.4s .. end: Real-Time Synchronized 3-State Paragraph Highlighting & Automatic Folio Crossfades
          ==================================================================== */}
      {viewMode === "reader" && (
        <div className="austen-spread-viewport">
          {showOpeningTitleCard ? (
            /* ================================================================
               STAGE A (0.0s .. 2.2s): FULL-FRAME CHAPTER TITLE CARD
               Matches render_title_card in render_audiobook_video.py
               ================================================================ */
            <div
              className="austen-opening-title-card"
              onClick={() => seekToFolioAndTurn(0, 0)}
              title="Click to turn immediately to Folio I.1"
            >
              <div className="austen-opening-title-inner">
                <div>
                  <div
                    style={{
                      fontFamily: "var(--font-cinzel)",
                      fontSize: "15px",
                      letterSpacing: "0.153em",
                      color: "var(--folio-accent)",
                      textTransform: "uppercase",
                      marginBottom: "10px",
                    }}
                  >
                    BOOK {storybook.roman || "I"} &nbsp;·&nbsp;{" "}
                    {storybook.genreFooterLeft || "REGENCY SOCIAL SATIRE"}
                  </div>

                  <h1
                    style={{
                      fontFamily: "var(--font-cormorant)",
                      fontSize: "clamp(46px, 4.1vw, 66px)",
                      fontWeight: 500,
                      color: "var(--folio-ink)",
                      margin: "0 0 8px 0",
                      lineHeight: 1.04,
                    }}
                  >
                    {storybook.title}
                  </h1>

                  <div
                    style={{
                      fontFamily: "var(--font-cinzel)",
                      fontSize: "16px",
                      letterSpacing: "0.12em",
                      color: "var(--folio-muted)",
                      textTransform: "uppercase",
                    }}
                  >
                    {storybook.author} &nbsp;·&nbsp; {storybook.year || "1813"}
                  </div>

                  <div
                    className="folio-diamond-rule"
                    style={{ maxWidth: "420px", margin: "16px auto" }}
                  >
                    <div className="folio-diamond-rule-line" />
                    <div className="folio-diamond-rule-gem" />
                    <div className="folio-diamond-rule-line" />
                  </div>

                  <div
                    style={{
                      fontFamily: "var(--font-garamond)",
                      fontStyle: "italic",
                      fontSize: "clamp(21px, 1.5vw, 25px)",
                      color: "var(--folio-ink)",
                    }}
                  >
                    {storybook.subtitle} &mdash;{" "}
                    {storybook.settingFooterRight || "Longbourn, Hertfordshire"}
                  </div>
                </div>

                {/* Matted 16:9 Character Reference Sheet Plate */}
                <div
                  style={{
                    backgroundColor: "var(--folio-card)",
                    border: "1px solid var(--folio-rule)",
                    padding: "14px 12px",
                    maxWidth: "740px",
                    width: "100%",
                    margin: "14px auto",
                  }}
                >
                  <div
                    style={{
                      aspectRatio: "16 / 9",
                      border: "1px solid var(--folio-rule)",
                      overflow: "hidden",
                      backgroundColor: "var(--folio-paper)",
                    }}
                  >
                    <img
                      src={
                        storybook.charSheetImageUrl ||
                        storybook.coverImageUrl ||
                        "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/01_pride_and_prejudice_char_sheet.jpg"
                      }
                      alt={`${storybook.title} Character Reference Sheet`}
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                        display: "block",
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div
                    style={{
                      fontFamily: "var(--font-cinzel)",
                      fontSize: "13px",
                      letterSpacing: "0.129em",
                      color: "var(--folio-muted)",
                      textTransform: "uppercase",
                      marginBottom: "6px",
                    }}
                  >
                    ILLUSTRATED EDITION &nbsp;·&nbsp; GEMINI 3.8 FLASH TTS CAST &nbsp;·&nbsp; LYRIA 3.5 SCORE
                  </div>

                  <div
                    style={{
                      fontFamily: "var(--font-garamond)",
                      fontStyle: "italic",
                      fontSize: "19.5px",
                      color: "var(--folio-ink)",
                    }}
                  >
                    {storybook.characters
                      .map((c) => `${c.name} (${c.voiceName})`)
                      .join("   ·   ")}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* ================================================================
               STAGE B & C (2.2s .. end): TWO-PAGE OPEN FOLIO SPREAD
               Left Page: 3D Pop-Up Diorama Stage (unfolds on scene open, steady across same-scene folios)
               Right Page: 3-State Synchronized Literary Narration & Dialogue Turns
               ================================================================ */
            <div
              className={`austen-open-book ${
                isPageTurning ? "folio-page-turning" : ""
              }`}
            >
              {/* ==============================================================
                  LEFT PAGE: VISUAL PLATE FOLIO
                  BOOK I · JANE AUSTEN | 1813
                  Matted 16:9 Stage: PLATE I OF III | Longbourn Morning Room
                  REGENCY SOCIAL SATIRE | LONGBOURN, HERTFORDSHIRE
                  ============================================================== */}
              <div className="austen-left-page">
                <div className="austen-running-bar">
                  <span>
                    {language === "ko"
                      ? `제${storybook.roman || "I"}권  ·  ${
                          KOREAN_BOOK_METAS[storybook.id]?.author || storybook.author
                        }`
                      : formattedBookHeaderLeft}
                  </span>
                  <span>{storybook.year || "1813"}</span>
                </div>

                {/* Centered Matted 16:9 Stage Box (#EFE9DC Card Mat + #D5CBB8 1px Rule) */}
                <div className="austen-plate-mat">
                  <div
                    className={`austen-plate-stage ${
                      isDioramaUnfolding ? "folio-diorama-unfolding" : ""
                    }`}
                    onClick={handleCyclePlate}
                    title="Click plate to cycle between 3D Pop-Up Diorama, 2D Watercolour Plate, and Character Sheet"
                  >
                    <img
                      src={
                        currentPlate?.imageDataUrl ||
                        currentPlate?.imageUrl ||
                        currentPage?.dioramaUrl ||
                        currentPage?.imageUrl ||
                        storybook.coverImageUrl
                      }
                      alt={currentPlate?.title || currentPage?.imageCaption}
                    />
                  </div>

                  {/* Plate Caption Row inside Mat */}
                  <div className="austen-plate-caption-row">
                    <button
                      type="button"
                      onClick={handleCyclePlate}
                      className="austen-plate-number"
                      title="Click to cycle plate view"
                    >
                      {language === "ko"
                        ? `판화 ${currentSceneRoman} / ${totalScenesRoman}`
                        : canonicalPlateLabel}
                    </button>
                    <span className="austen-plate-caption">
                      {currentPlate?.title || currentPage?.imageCaption}
                    </span>
                  </div>
                </div>

                {/* Left Page Running Footer */}
                <div className="austen-footer-bar">
                  <span>
                    {language === "ko"
                      ? KOREAN_BOOK_METAS[storybook.id]?.genre ||
                        storybook.genreFooterLeft ||
                        "리젠시 시대 풍자극"
                      : storybook.genreFooterLeft || "REGENCY SOCIAL SATIRE"}
                  </span>
                  <span>
                    {language === "ko"
                      ? KOREAN_BOOK_METAS[storybook.id]?.setting ||
                        storybook.settingFooterRight ||
                        "롱본, 하트퍼드셔"
                      : storybook.settingFooterRight || "LONGBOURN, HERTFORDSHIRE"}
                  </span>
                </div>
              </div>

              {/* RIGHT PAGE: LITERARY NARRATION & DIALOGUE FOLIO */}
              <div
                className={`austen-right-page ${
                  isRightFolioFading ? "folio-right-page-fading" : ""
                }`}
              >
                <div className="austen-running-bar">
                  <span>
                    {language === "ko"
                      ? KOREAN_BOOK_METAS[storybook.id]?.title || storybook.title
                      : storybook.title.toUpperCase()}
                  </span>
                  <div style={{ display: "flex", alignItems: "baseline", gap: "12px" }}>
                    {renderLanguageSwitcher()}
                    <span>
                      {currentPage?.chapterTitle ||
                        (language === "ko" ? "제I장" : "CHAPTER I")}
                    </span>
                  </div>
                </div>

                {/* Active Speaker Subheader Band */}
                <div className="austen-speaker-band">
                  <div>
                    <span
                      className="austen-speaker-name"
                      style={{
                        color:
                          activeLineIdx >= 0 &&
                          activeLineIdx < 999 &&
                          activeLine?.isDialogue
                            ? "var(--folio-accent)"
                            : "var(--folio-muted)",
                      }}
                    >
                      {activeLineIdx >= 0 && activeLineIdx < 999
                        ? activeLine?.speakerLabel ||
                          activeLine?.speaker?.toUpperCase() ||
                          (language === "ko" ? "해설자" : "NARRATOR")
                        : (language === "ko" ? "해설자" : "NARRATOR")}
                    </span>
                    <span className="austen-speaker-role">
                      {"  —  "}
                      {activeLineIdx >= 0 && activeLineIdx < 999
                        ? activeLine?.voiceRoleLabel ||
                          (activeLine?.isDialogue
                            ? t.characterDialogue
                            : t.narrationProse)
                        : t.narrationProse}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={handleToggleNarration}
                    className={`austen-margin-link ${
                      isPlayingAudio ? "is-active" : ""
                    }`}
                    style={{ fontSize: "11px" }}
                    title="Toggle synchronized audiobook narration"
                  >
                    {formatTimecode(playbackTimeSec)} / {formatTimecode(totalDurSec)}{" "}
                    &nbsp;·&nbsp; {isPlayingAudio ? t.pause : t.play}
                  </button>
                </div>

                {/* Right-Page Literary Body: 3-State Paragraph Ink Highlighting */}
                <div className="austen-folio-body">
                  {dialogueLines.map((line, idx) => {
                    const prevSpeaker =
                      idx > 0 ? dialogueLines[idx - 1]?.speaker : null;
                    const showRubric =
                      Boolean(line.isDialogue) && line.speaker !== prevSpeaker;

                    const turnStateClass =
                      activeLineIdx === -1
                        ? "state-future"
                        : activeLineIdx === 999
                        ? "state-past"
                        : idx === activeLineIdx
                        ? "state-active"
                        : idx < activeLineIdx
                        ? "state-past"
                        : "state-future";

                    return (
                      <div
                        key={idx}
                        onClick={() => seekToFolioAndTurn(currentPageIdx, idx)}
                        className={`austen-turn-block ${turnStateClass}`}
                        title="Click paragraph to seek narration here"
                      >
                        {showRubric && (
                          <div className="austen-turn-rubric">
                            {line.speakerLabel || line.speaker.toUpperCase()}
                          </div>
                        )}
                        <p className="austen-turn-text">{line.text}</p>
                      </div>
                    );
                  })}
                </div>

                {/* Right Page Running Footer */}
                <div className="austen-footer-bar">
                  <div
                    className="austen-progress-filament"
                    style={{
                      width: `${Math.min(100, Math.max(0, chapterProgress * 100))}%`,
                    }}
                  />
                  <span>
                    {language === "ko"
                      ? `제${currentSceneRoman}경`
                      : currentPage?.sceneLabel || "SCENE I"}
                  </span>
                  <span
                    onClick={() =>
                      seekToFolioAndTurn(
                        (currentPageIdx + 1) % storybook.pages.length,
                        0
                      )
                    }
                    style={{ cursor: "pointer" }}
                    title="Click to turn folio leaf"
                  >
                    {language === "ko"
                      ? `제${storybook.roman || "I"}.${currentPageIdx + 1}쪽`
                      : currentPage?.folioLabel ||
                        `FOLIO ${storybook.roman || "I"}.${currentPageIdx + 1}`}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Ghosted Outer Margin Line */}
          <div className="austen-margin-bar">
            <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
              <button
                type="button"
                onClick={handleCloseBookToCover}
                className="austen-margin-link"
              >
                {language === "ko" ? "← 목차 및 새로운 의뢰" : "← CONTENTS & COMMISSION"}
              </button>
              <span>·</span>
              <button
                type="button"
                onClick={handleToggleNarration}
                className={`austen-margin-link ${
                  isPlayingAudio ? "is-active" : ""
                }`}
              >
                {isPlayingAudio
                  ? (language === "ko" ? "일시정지" : "PAUSE NARRATION")
                  : (language === "ko" ? "낭독 이어듣기" : "RESUME NARRATION")}
              </button>
              <span>·</span>
              <button
                type="button"
                onClick={() => startBookNarration(storybook, 0, true)}
                className="austen-margin-link"
              >
                {language === "ko" ? "처음부터 다시 듣기" : "REPLAY FROM TITLE"}
              </button>
              <span>·</span>
              <button
                type="button"
                onClick={handleSynthesizeFolioWav}
                disabled={isSynthesizingAudio}
                className="austen-margin-link"
              >
                {isSynthesizingAudio
                  ? (language === "ko" ? "합성 중…" : "SYNTHESIZING…")
                  : (language === "ko" ? "24kHz 음성 재합성" : "LIVE TTS WAV")}
              </button>
              <span>·</span>
              <button
                type="button"
                onClick={handleCyclePlate}
                className="austen-margin-link"
              >
                {language === "ko"
                  ? `삽화 전환 (${resolvedPlateIdx + 1}/${plates.length})`
                  : `CYCLE PLATE (${resolvedPlateIdx + 1}/${plates.length})`}
              </button>
              <span>·</span>
              <button
                type="button"
                onClick={handleRepaintCurrentPlate}
                disabled={isRegeneratingPlate}
                className="austen-margin-link"
              >
                {isRegeneratingPlate
                  ? (language === "ko" ? "판화 제작 중…" : "ENGRAVING…")
                  : (language === "ko" ? "판화 재각인" : "ENGRAVE PLATE")}
              </button>
              {statusNote && (
                <>
                  <span>·</span>
                  <span
                    style={{
                      fontFamily: "var(--font-garamond)",
                      fontStyle: "italic",
                      textTransform: "none",
                      letterSpacing: "normal",
                      fontSize: "14px",
                      color: "var(--folio-accent)",
                    }}
                  >
                    {statusNote}
                  </span>
                </>
              )}
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
              <button
                type="button"
                onClick={() =>
                  currentPageIdx > 0 &&
                  seekToFolioAndTurn(currentPageIdx - 1, 0)
                }
                disabled={currentPageIdx === 0 && !showOpeningTitleCard}
                className="austen-margin-link"
              >
                {language === "ko" ? "‹ 이전 쪽" : "‹ PREV FOLIO"}
              </button>
              <span>
                {storybook.pages.map((p, pIdx) => (
                  <React.Fragment key={p.pageNumber}>
                    {pIdx > 0 && " · "}
                    <button
                      type="button"
                      onClick={() => seekToFolioAndTurn(pIdx, 0)}
                      className={`austen-margin-link ${
                        pIdx === currentPageIdx && !showOpeningTitleCard
                          ? "is-active"
                          : ""
                      }`}
                    >
                      {`${storybook.roman || "I"}.${pIdx + 1}`}
                    </button>
                  </React.Fragment>
                ))}
              </span>
              <button
                type="button"
                onClick={() =>
                  currentPageIdx < storybook.pages.length - 1 &&
                  seekToFolioAndTurn(currentPageIdx + 1, 0)
                }
                disabled={currentPageIdx >= storybook.pages.length - 1}
                className="austen-margin-link"
              >
                {language === "ko" ? "다음 쪽 ›" : "NEXT FOLIO ›"}
              </button>
              <span>·</span>
              <button
                type="button"
                onClick={() => setShowTitleCardModal(true)}
                className="austen-margin-link"
              >
                {language === "ko" ? "표제지" : "TITLE LEAF"}
              </button>
              <span>·</span>
              <button
                type="button"
                onClick={() => setShowAgentSpecModal(true)}
                className="austen-margin-link"
              >
                {language === "ko" ? "에이전트 명세" : "COLOPHON"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ====================================================================
          LEAF OVERLAY 1: FINE-PRESS CHAPTER TITLE CARD & CHARACTER SHEET
          (Matches 01_pride_and_prejudice_preview_title.png / render_title_card)
          ==================================================================== */}
      {showTitleCardModal && (
        <div
          className="folio-modal-backdrop"
          onClick={() => setShowTitleCardModal(false)}
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(30, 27, 24, 0.35)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "24px",
            zIndex: 50,
          }}
        >
          <div
            className="folio-modal-card"
            onClick={(e) => e.stopPropagation()}
            style={{
              backgroundColor: "var(--folio-paper)",
              border: "1px solid var(--folio-rule)",
              padding: "6px",
              maxWidth: "1020px",
              width: "100%",
            }}
          >
            <div
              className="folio-modal-inner"
              style={{
                border: "1px solid var(--folio-rule)",
                padding: "28px 36px",
                textAlign: "center",
                position: "relative",
              }}
            >
              <button
                type="button"
                onClick={() => setShowTitleCardModal(false)}
                className="austen-margin-link"
                style={{
                  position: "absolute",
                  top: "16px",
                  right: "20px",
                }}
              >
                CLOSE &times;
              </button>

              <div
                style={{
                  fontFamily: "var(--font-cinzel)",
                  fontSize: "14px",
                  letterSpacing: "0.153em",
                  color: "var(--folio-accent)",
                  textTransform: "uppercase",
                  marginBottom: "8px",
                }}
              >
                BOOK {storybook.roman || "I"} &nbsp;·&nbsp;{" "}
                {storybook.genreFooterLeft || "REGENCY SOCIAL SATIRE"}
              </div>

              <h2
                style={{
                  fontFamily: "var(--font-cormorant)",
                  fontSize: "52px",
                  fontWeight: 500,
                  color: "var(--folio-ink)",
                  margin: "0 0 8px 0",
                }}
              >
                {storybook.title}
              </h2>

              <div
                style={{
                  fontFamily: "var(--font-cinzel)",
                  fontSize: "15px",
                  letterSpacing: "0.12em",
                  color: "var(--folio-muted)",
                  textTransform: "uppercase",
                }}
              >
                {storybook.author} &nbsp;·&nbsp; {storybook.year || "1813"}
              </div>

              <div className="folio-diamond-rule" style={{ maxWidth: "360px" }}>
                <div className="folio-diamond-rule-line" />
                <div className="folio-diamond-rule-gem" />
                <div className="folio-diamond-rule-line" />
              </div>

              <div
                style={{
                  fontFamily: "var(--font-garamond)",
                  fontStyle: "italic",
                  fontSize: "22px",
                  color: "var(--folio-ink)",
                  marginBottom: "18px",
                }}
              >
                {storybook.subtitle} &mdash;{" "}
                {storybook.settingFooterRight || "Longbourn, Hertfordshire"}
              </div>

              {/* Matted 16:9 Character Reference Sheet Plate */}
              <div
                style={{
                  backgroundColor: "var(--folio-card)",
                  border: "1px solid var(--folio-rule)",
                  padding: "14px 12px",
                  maxWidth: "680px",
                  margin: "0 auto 18px",
                }}
              >
                <div
                  style={{
                    aspectRatio: "16 / 9",
                    border: "1px solid var(--folio-rule)",
                    overflow: "hidden",
                    backgroundColor: "var(--folio-paper)",
                  }}
                >
                  <img
                    src={
                      storybook.charSheetImageUrl ||
                      storybook.coverImageUrl ||
                      "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/01_pride_and_prejudice_char_sheet.jpg"
                    }
                    alt={`${storybook.title} Character Reference Sheet`}
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                      display: "block",
                    }}
                  />
                </div>
              </div>

              <div
                style={{
                  fontFamily: "var(--font-cinzel)",
                  fontSize: "12px",
                  letterSpacing: "0.129em",
                  color: "var(--folio-muted)",
                  textTransform: "uppercase",
                  marginBottom: "6px",
                }}
              >
                ILLUSTRATED EDITION &nbsp;·&nbsp; GEMINI FLASH TTS CAST &nbsp;·&nbsp; LYRIA 3.5 SCORE
              </div>

              <div
                style={{
                  fontFamily: "var(--font-garamond)",
                  fontStyle: "italic",
                  fontSize: "18.5px",
                  color: "var(--folio-ink)",
                }}
              >
                {storybook.characters
                  .map((c) => `${c.name} (${c.voiceName})`)
                  .join("   ·   ")}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ====================================================================
          LEAF OVERLAY 2: EDITION COLOPHON & MANAGED AGENT CONFIGURATION
          ==================================================================== */}
      {showAgentSpecModal && (
        <div
          className="folio-modal-backdrop"
          onClick={() => setShowAgentSpecModal(false)}
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(30, 27, 24, 0.35)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "24px",
            zIndex: 50,
          }}
        >
          <div
            className="folio-modal-sheet"
            onClick={(e) => e.stopPropagation()}
            style={{
              backgroundColor: "var(--folio-paper)",
              border: "1px solid var(--folio-rule)",
              padding: "24px 32px",
              maxWidth: "860px",
              width: "100%",
              maxHeight: "88vh",
              overflowY: "auto",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "baseline",
                borderBottom: "1px solid var(--folio-rule)",
                paddingBottom: "12px",
                marginBottom: "18px",
              }}
            >
              <div>
                <div
                  style={{
                    fontFamily: "var(--font-cinzel)",
                    fontSize: "12px",
                    letterSpacing: "0.129em",
                    color: "var(--folio-accent)",
                  }}
                >
                  COLOPHON &amp; GEMINI MANAGED AGENT ARCHITECTURE
                </div>
                <h3
                  style={{
                    fontFamily: "var(--font-cormorant)",
                    fontSize: "28px",
                    fontWeight: 500,
                    margin: "4px 0 0",
                  }}
                >
                  {agentName} ({modelName}) + classic-audiobooks Pipeline
                </h3>
              </div>

              <button
                type="button"
                onClick={() => setShowAgentSpecModal(false)}
                className="austen-margin-link"
              >
                CLOSE &times;
              </button>
            </div>

            <div
              className="folio-colophon-grid"
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr",
                gap: "16px",
                marginBottom: "18px",
              }}
            >
              <div>
                <label
                  style={{
                    display: "block",
                    fontFamily: "var(--font-cinzel)",
                    fontSize: "11px",
                    letterSpacing: "0.114em",
                    color: "var(--folio-muted)",
                    marginBottom: "4px",
                  }}
                >
                  MANAGED AGENT ID
                </label>
                <input
                  type="text"
                  value={agentName}
                  onChange={(e) => setAgentName(e.target.value)}
                  style={{
                    width: "100%",
                    backgroundColor: "transparent",
                    border: "none",
                    borderBottom: "1px solid var(--folio-rule)",
                    padding: "6px 2px",
                    fontFamily: "var(--font-mono)",
                    fontSize: "12px",
                    color: "var(--folio-ink)",
                    outline: "none",
                  }}
                />
              </div>
              <div>
                <label
                  style={{
                    display: "block",
                    fontFamily: "var(--font-cinzel)",
                    fontSize: "11px",
                    letterSpacing: "0.114em",
                    color: "var(--folio-muted)",
                    marginBottom: "4px",
                  }}
                >
                  AGENT MODEL (ARGON)
                </label>
                <input
                  type="text"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  style={{
                    width: "100%",
                    backgroundColor: "transparent",
                    border: "none",
                    borderBottom: "1px solid var(--folio-rule)",
                    padding: "6px 2px",
                    fontFamily: "var(--font-mono)",
                    fontSize: "12px",
                    color: "var(--folio-ink)",
                    outline: "none",
                  }}
                />
              </div>
              <div>
                <label
                  style={{
                    display: "block",
                    fontFamily: "var(--font-cinzel)",
                    fontSize: "11px",
                    letterSpacing: "0.114em",
                    color: "var(--folio-muted)",
                    marginBottom: "4px",
                  }}
                >
                  GEMINI API KEY
                </label>
                <input
                  type="password"
                  value={apiKeyInput}
                  onChange={(e) => {
                    setApiKeyInput(e.target.value);
                    try {
                      if (typeof window !== "undefined" && window.localStorage) {
                        window.localStorage.setItem(
                          "FOLIO_GEMINI_API_KEY",
                          e.target.value.trim()
                        );
                      }
                    } catch {
                      // Null-origin sandbox blocks localStorage
                    }
                  }}
                  placeholder="Uses server env or enter key…"
                  style={{
                    width: "100%",
                    backgroundColor: "transparent",
                    border: "none",
                    borderBottom: "1px solid var(--folio-rule)",
                    padding: "6px 2px",
                    fontFamily: "var(--font-mono)",
                    fontSize: "12px",
                    color: "var(--folio-ink)",
                    outline: "none",
                  }}
                />
              </div>
            </div>

            <div style={{ marginBottom: "14px" }}>
              <div
                style={{
                  fontFamily: "var(--font-cinzel)",
                  fontSize: "11px",
                  letterSpacing: "0.114em",
                  color: "var(--folio-muted)",
                  marginBottom: "6px",
                }}
              >
                GEMINI-API-CLI BOOTSTRAP COMMAND IN SANDBOX
              </div>
              <pre
                style={{
                  backgroundColor: "var(--folio-card)",
                  border: "1px solid var(--folio-rule)",
                  padding: "10px 12px",
                  fontFamily: "var(--font-mono)",
                  fontSize: "11.5px",
                  color: "var(--folio-muted)",
                  overflowX: "auto",
                  margin: 0,
                }}
              >
                {GEMINI_API_CLI_INSTALL_CMD}
              </pre>
            </div>

            <div>
              <div
                style={{
                  fontFamily: "var(--font-cinzel)",
                  fontSize: "11px",
                  letterSpacing: "0.114em",
                  color: "var(--folio-muted)",
                  marginBottom: "6px",
                }}
              >
                MOUNTED /.AGENTS/AGENTS.MD &amp; CLASSIC-AUDIOBOOKS SCRIPTS
              </div>
              <pre
                style={{
                  backgroundColor: "var(--folio-card)",
                  border: "1px solid var(--folio-rule)",
                  padding: "12px",
                  fontFamily: "var(--font-mono)",
                  fontSize: "11.5px",
                  color: "var(--folio-muted)",
                  whiteSpace: "pre-wrap",
                  maxHeight: "280px",
                  overflowY: "auto",
                  margin: 0,
                }}
              >
                {AGENTS_MD_CONTENT}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
