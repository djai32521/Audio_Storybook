export interface StorybookPalette {
  paper: string;      // e.g. "#F6F2EA"
  card: string;       // e.g. "#EFE9DC"
  ink: string;        // e.g. "#1E1B18"
  muted: string;      // e.g. "#7A7267"
  accent: string;     // e.g. "#4A6B53"
  rule: string;       // e.g. "#D5CBB8"
  coverCloth?: string; // e.g. "#3E5A47"
  coverSpine?: string; // e.g. "#2B3F31"
}

export interface CharacterVoice {
  id: string;
  name: string;
  role: string;
  description: string;
  voiceName: "Charon" | "Kore" | "Puck" | "Fenrir" | "Aoede" | "Zephyr" | "Leda" | "Orus" | "Iapetus" | string;
  voiceStyle: string;
}

export interface DialogueLine {
  speaker: string;
  speakerLabel?: string;   // e.g. "MRS. BENNET" or "NARRATOR"
  voiceRoleLabel?: string; // e.g. "Character Dialogue" or "Literary Narration"
  isDialogue?: boolean;    // true for spoken character lines, false for narrator prose
  voiceName: string;
  voiceStyle?: string;
  stylePrompt?: string;
  text: string;
  ttsText?: string;
  plateIndex?: number;
  startSec?: number;
  endSec?: number;
  durationSeconds?: number;
  pauseAfterSeconds?: number;
  audioDataUrl?: string;
}

export interface StoryPlate {
  plateNumberRoman: string; // e.g. "I", "II", "III"
  plateLabel?: string;      // e.g. "PLATE I OF I" or "PLATE I OF III"
  title: string;            // e.g. "Longbourn Morning Room"
  illustrationPrompt: string;
  imageUrl?: string;
  imageDataUrl?: string;
  dioramaUrl?: string;
}

export interface StorybookPage {
  pageNumber: number;
  sceneIdx?: number;   // 0, 1, 2
  sceneLabel?: string; // e.g. "SCENE I"
  folioLabel?: string; // e.g. "FOLIO I.1"
  chapterTitle: string; // e.g. "CHAPTER I"
  dropCap?: string;
  narrativeText: string;
  dialogueLines: DialogueLine[];
  plates?: StoryPlate[];
  illustrationPrompt: string;
  imageCaption: string;
  imageUrl?: string;
  imageDataUrl?: string;
  dioramaUrl?: string;
  audioUrl?: string;
  audioDataUrl?: string;
  startSec?: number;
  endSec?: number;
  durationSeconds?: number;
}

export interface StorybookModelsUsed {
  orchestrator: string;
  cli: string;
  writer: string;
  illustrator: string;
  narrator: string;
  composer: string;
}

export interface Storybook {
  id: string;
  roman?: string;             // e.g. "I"
  bookHeaderLeft?: string;    // e.g. "BOOK I  ·  JANE AUSTEN"
  year?: string;              // e.g. "1813"
  genreFooterLeft?: string;   // e.g. "REGENCY SOCIAL SATIRE"
  settingFooterRight?: string;// e.g. "LONGBOURN, HERTFORDSHIRE"
  title: string;              // e.g. "Pride and Prejudice"
  subtitle: string;           // e.g. "Chapter I"
  author: string;             // e.g. "Jane Austen"
  palette?: StorybookPalette;
  sourceType?: "classic-adaptation" | "original-story";
  gutenbergId?: number;
  visualStyle: string;
  mood: string;
  musicPrompt: string;
  charSheetPrompt?: string;
  charSheetImageUrl?: string;
  coverImagePrompt: string;
  coverImageUrl?: string;
  coverImageDataUrl?: string;
  backgroundMusicUrl?: string;
  backgroundMusicDataUrl?: string;
  masterAudioUrl?: string;
  fullAudiobookUrl?: string;
  fullAudiobookDataUrl?: string;
  titleCardEndSec?: number;
  totalDurationSeconds?: number;
  modelsUsed: StorybookModelsUsed;
  characters: CharacterVoice[];
  pages: StorybookPage[];
}

export interface AgentLogEntry {
  id: string;
  timestamp: string;
  type: "status" | "thinking" | "tool_call" | "tool_result" | "text" | "error";
  title: string;
  detail?: string;
  isError?: boolean;
}

export interface ClassicPreset {
  id: string;
  title: string;
  author: string;
  year: string;
  gutenbergId: number;
  tagline: string;
  defaultPrompt: string;
  visualStyle: string;
  narratorVoice: string;
  accentColor: string;
  palette: StorybookPalette;
}
