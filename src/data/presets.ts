import { ClassicPreset, Storybook, StorybookPalette } from "../types";

export const EDITION_PALETTES: Record<string, { label: string; palette: StorybookPalette }> = {
  regency: {
    label: "Regency Sage (Jane Austen)",
    palette: {
      paper: "#F6F2EA",
      card: "#EFE9DC",
      ink: "#1E1B18",
      muted: "#7A7267",
      accent: "#4A6B53",
      rule: "#D5CBB8",
      coverCloth: "#3D5845",
      coverSpine: "#2B3F31",
    },
  },
  victorian: {
    label: "Baker Street Amber (Conan Doyle)",
    palette: {
      paper: "#F2EDE2",
      card: "#E8E1D3",
      ink: "#181A1B",
      muted: "#6E6A63",
      accent: "#9E6B2E",
      rule: "#CFC6B4",
      coverCloth: "#5A3E28",
      coverSpine: "#3E2A1B",
    },
  },
  wonderland: {
    label: "Wonderland Crimson (Lewis Carroll)",
    palette: {
      paper: "#F8F5EE",
      card: "#F0EBE0",
      ink: "#1C2026",
      muted: "#72767D",
      accent: "#9E332B",
      rule: "#D8D0C1",
      coverCloth: "#6E2B26",
      coverSpine: "#4C1D19",
    },
  },
  chronos: {
    label: "Astral Brass (H. G. Wells)",
    palette: {
      paper: "#F0F2F4",
      card: "#E4E8EC",
      ink: "#18222C",
      muted: "#64707D",
      accent: "#B38628",
      rule: "#C8D0D8",
      coverCloth: "#2E3D4F",
      coverSpine: "#1F2936",
    },
  },
  americana: {
    label: "Pastoral Terracotta (Mark Twain)",
    palette: {
      paper: "#F6EFE4",
      card: "#EDE3D3",
      ink: "#261E19",
      muted: "#7A6D61",
      accent: "#B85733",
      rule: "#D6C8B4",
      coverCloth: "#6B3B28",
      coverSpine: "#4A281B",
    },
  },
};

export const VISUAL_STYLE_PRESETS = [
  {
    id: "regency-wash",
    label: "1810s Regency Pen-and-Ink & Sepia Watercolour Wash",
    value:
      "1810s Regency fine dip-pen sepia ink line drawing with delicate muted watercolour wash (sage green, warm ochre, dusty rose, and sepia ink) on warm cream archival paper (#F6F2EA)",
  },
  {
    id: "rackham-fairytale",
    label: "Golden-Age Fairytale Pen-and-Ink & Botanical Wash",
    value:
      "Golden-Age fairytale pen-and-ink line drawing with muted sage, ochre, and sepia watercolour wash on warm cream archival laid paper (#F6F2EA), generous negative space",
  },
  {
    id: "victorian-engraving",
    label: "Late-Victorian Fine Dip-Pen & Warm Bistre Wash",
    value:
      "Late-Victorian fine dip-pen ink illustration with warm amber-ochre and charcoal watercolour wash on archival rag paper",
  },
  {
    id: "pastoral-storybook",
    label: "Pastoral Woodcut & Muted Watercolour Folio",
    value:
      "Minimalist fine-press editorial book illustration on warm cream archival paper with delicate ink linework and soft pastoral watercolour wash",
  },
];

export const GEMINI_TTS_VOICES = [
  { id: "Kore", label: "Kore — Poised Literary Narrator" },
  { id: "Aoede", label: "Aoede — Animated & Expressive" },
  { id: "Charon", label: "Charon — Dry Baritone Gentleman" },
  { id: "Fenrir", label: "Fenrir — Warm Observant Narrator" },
  { id: "Orus", label: "Orus — Crisp Intellectual Lead" },
  { id: "Leda", label: "Leda — Curious Storybook Heroine" },
  { id: "Puck", label: "Puck — Nimble & Spirited" },
  { id: "Iapetus", label: "Iapetus — Skeptical Debater" },
];

export const FAIRYTALE_COMMISSION_PROMPTS = [
  {
    id: "clockwork-nightingale",
    title: "The Clockmaker’s Glass Nightingale",
    subtitle: "An 1815 Regency Fairytale of Lake Geneva",
    paletteKey: "regency",
    prompt:
      "A quiet clockmaker's daughter in an 1815 lakeside workshop discovers a miniature spun-glass nightingale hidden inside an antique music box. When wound at dawn, the bird sings a riddle about a sunken winter garden beneath the mountains.",
  },
  {
    id: "lantern-of-the-moors",
    title: "The Lantern-Keeper of Whispering Fen",
    subtitle: "A Victorian Moorland Folk Tale",
    paletteKey: "victorian",
    prompt:
      "On a misty autumn evening along the stone causeway of Whispering Fen, an elderly lantern-keeper and a young botanist encounter a polite fox carrying a brass compass that points toward forgotten libraries.",
  },
  {
    id: "paper-astronomer",
    title: "The Paper Astronomer’s Staircase",
    subtitle: "A Celestial Fable in Three Folios",
    paletteKey: "chronos",
    prompt:
      "In a candlelit observatory built inside an old windmill, an astronomer folds paper constellations that drift up through the shutters and argue gently with the North Wind about the proper time for moonrise.",
  },
  {
    id: "bramble-post-office",
    title: "The Bramble-Hedge Post Office",
    subtitle: "A Pastoral Woodland Fairytale",
    paletteKey: "wonderland",
    prompt:
      "Beneath the roots of an ancient hawthorn hedge, a diligent dormouse postmaster and a girl in an ochre linen pinafore sort overdue letters addressed to the four seasons.",
  },
];

export const CLASSIC_LITERATURE_PRESETS: ClassicPreset[] = [
  {
    id: "01_pride_and_prejudice",
    title: "Pride and Prejudice",
    author: "Jane Austen",
    year: "1813",
    gutenbergId: 1342,
    tagline: "Book I · Chapter I — Longbourn, Hertfordshire",
    defaultPrompt:
      "Adapt Chapter I of Jane Austen's Pride and Prejudice ('It is a truth universally acknowledged...') into a 3-folio illustrated fine-press edition set in Longbourn, Hertfordshire, with Narrator (Kore), Mrs. Bennet (Aoede), and Mr. Bennet (Charon).",
    visualStyle: VISUAL_STYLE_PRESETS[0].value,
    narratorVoice: "Kore",
    accentColor: "#4A6B53",
    palette: EDITION_PALETTES.regency.palette,
  },
  {
    id: "02_hound_of_the_baskervilles",
    title: "The Hound of the Baskervilles",
    author: "Arthur Conan Doyle",
    year: "1902",
    gutenbergId: 2852,
    tagline: "Book II · Chapter I — 221B Baker Street, London",
    defaultPrompt:
      "Adapt Chapter I ('Mr. Sherlock Holmes') of Arthur Conan Doyle's The Hound of the Baskervilles into a 3-folio illustrated edition with Dr. Watson (Fenrir) and Sherlock Holmes (Orus).",
    visualStyle: VISUAL_STYLE_PRESETS[2].value,
    narratorVoice: "Fenrir",
    accentColor: "#9E6B2E",
    palette: EDITION_PALETTES.victorian.palette,
  },
  {
    id: "03_alice_in_wonderland",
    title: "Alice’s Adventures in Wonderland",
    author: "Lewis Carroll",
    year: "1865",
    gutenbergId: 11,
    tagline: "Book III · Chapter I — Down the Rabbit-Hole",
    defaultPrompt:
      "Adapt Chapter I ('Down the Rabbit-Hole') of Lewis Carroll's Alice's Adventures in Wonderland into a 3-folio illustrated edition with Narrator (Kore), Alice (Leda), and The White Rabbit (Puck).",
    visualStyle: VISUAL_STYLE_PRESETS[1].value,
    narratorVoice: "Kore",
    accentColor: "#9E332B",
    palette: EDITION_PALETTES.wonderland.palette,
  },
  {
    id: "04_the_time_machine",
    title: "The Time Machine",
    author: "H. G. Wells",
    year: "1895",
    gutenbergId: 35,
    tagline: "Book IV · Chapter I — The Time Traveller’s Smoking-Room",
    defaultPrompt:
      "Adapt Chapter I ('Introduction') of H. G. Wells's The Time Machine into a 3-folio illustrated edition with Narrator (Fenrir), The Time Traveller (Orus), Filby (Iapetus), and The Psychologist (Charon).",
    visualStyle: VISUAL_STYLE_PRESETS[2].value,
    narratorVoice: "Fenrir",
    accentColor: "#B38628",
    palette: EDITION_PALETTES.chronos.palette,
  },
  {
    id: "05_tom_sawyer",
    title: "The Adventures of Tom Sawyer",
    author: "Mark Twain",
    year: "1876",
    gutenbergId: 74,
    tagline: "Book V · Chapter I — St. Petersburg, Missouri",
    defaultPrompt:
      "Adapt Chapter I ('Y-o-u-u Tom—Aunt Polly Decides Upon Her Duty') of Mark Twain's The Adventures of Tom Sawyer into a 3-folio illustrated edition with Narrator (Charon), Aunt Polly (Aoede), and Tom Sawyer (Puck).",
    visualStyle: VISUAL_STYLE_PRESETS[3].value,
    narratorVoice: "Charon",
    accentColor: "#B85733",
    palette: EDITION_PALETTES.americana.palette,
  },
];

const DEFAULT_MODELS_USED = {
  orchestrator: "antigravity-preview-09-2026 (gemini-4-argon)",
  cli: "gemini-api-cli (github.com/google-gemini/gemini-api-cli)",
  writer: "gemini-4-argon / books_spec.py",
  illustrator: "gemini-3.1-flash-lite-image + generate_popup_assets.py",
  narrator: "gemini-3.8-flash-tts + voice_mastering.py",
  composer: "lyria-3.5 + generate_and_mix_music.py",
};

/**
 * All 5 Classic Opening Chapters with exact millisecond timelines and 3D Pop-Up Dioramas
 * from classic-audiobooks-main/audio/timeline_manifest.json
 */
export const PRIDE_AND_PREJUDICE_STORYBOOK: Storybook = {
  "id": "01_pride_and_prejudice",
  "roman": "I",
  "bookHeaderLeft": "BOOK I  ·  JANE AUSTEN",
  "year": "1813",
  "genreFooterLeft": "REGENCY SOCIAL SATIRE",
  "settingFooterRight": "LONGBOURN, HERTFORDSHIRE",
  "title": "Pride and Prejudice",
  "subtitle": "Chapter I",
  "author": "Jane Austen",
  "palette": {
    "paper": "#F6F2EA",
    "card": "#EFE9DC",
    "ink": "#1E1B18",
    "muted": "#7A7267",
    "accent": "#4A6B53",
    "rule": "#D5CBB8",
    "coverCloth": "#3D5845",
    "coverSpine": "#2B3F31"
  },
  "sourceType": "classic-adaptation",
  "gutenbergId": 1342,
  "visualStyle": "Regency Social Satire — Longbourn, Hertfordshire",
  "mood": "Regency Social Satire — Longbourn, Hertfordshire",
  "musicPrompt": "Acoustic chamber score for Pride and Prejudice (1813)",
  "charSheetPrompt": "Anonymous period character reference sheet for Pride and Prejudice",
  "charSheetImageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/01_pride_and_prejudice_char_sheet.jpg",
  "coverImagePrompt": "Longbourn Morning Room",
  "coverImageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/01_pride_and_prejudice_diorama_scene_1.png",
  "backgroundMusicUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/music/01_pride_and_prejudice_lyria.mp3",
  "masterAudioUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/master/01_pride_and_prejudice.mp4",
  "titleCardEndSec": 2.6,
  "totalDurationSeconds": 113.2516,
  "modelsUsed": {
    "orchestrator": "antigravity-preview-09-2026 (gemini-4-argon)",
    "cli": "gemini-api-cli (github.com/google-gemini/gemini-api-cli)",
    "writer": "gemini-4-argon / books_spec.py",
    "illustrator": "gemini-3.1-flash-lite-image + generate_popup_assets.py",
    "narrator": "gemini-3.8-flash-tts + voice_mastering.py",
    "composer": "lyria-3.5 + generate_and_mix_music.py"
  },
  "characters": [
    {
      "id": "austen_narrator",
      "name": "Narrator",
      "role": "Literary Narration",
      "description": "Austen Regency Narrator",
      "voiceName": "Kore",
      "voiceStyle": "poised, dry literary irony, measured pace"
    },
    {
      "id": "mrs_bennet",
      "name": "Mrs. Bennet",
      "role": "Character Dialogue",
      "description": "Mrs. Bennet (Pride and Prejudice)",
      "voiceName": "Aoede",
      "voiceStyle": "eager, animated"
    },
    {
      "id": "mr_bennet",
      "name": "Mr. Bennet",
      "role": "Character Dialogue",
      "description": "Mr. Bennet (Pride and Prejudice)",
      "voiceName": "Charon",
      "voiceStyle": "dry, calm, deadpan amusement"
    }
  ],
  "pages": [
    {
      "pageNumber": 1,
      "sceneIdx": 0,
      "sceneLabel": "SCENE I",
      "folioLabel": "FOLIO I.1",
      "chapterTitle": "CHAPTER I",
      "startSec": 2.6,
      "endSec": 44.2218,
      "narrativeText": "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife. However little known the feelings or views of such a man may be on his first entering a neighbourhood, this truth is so well fixed in the minds of the surrounding families, that he is considered as the rightful property of some one or other of their daughters. “My dear Mr. Bennet,” said his lady to him one day, “have you heard that Netherfield Park is let at last?” Mr. Bennet replied that he had not.",
      "illustrationPrompt": "Longbourn Morning Room",
      "imageCaption": "Longbourn Morning Room",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/01_pride_and_prejudice_diorama_scene_1.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/01_pride_and_prejudice_diorama_scene_1.png",
      "plates": [
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "Longbourn Morning Room",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — Longbourn Morning Room",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/01_pride_and_prejudice_diorama_scene_1.png"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "Longbourn Morning Room (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — Longbourn Morning Room",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/01_pride_and_prejudice_scene_1.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "Pride and Prejudice — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/01_pride_and_prejudice_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Kore",
          "voiceStyle": "poised, dry literary irony, measured pace",
          "text": "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.",
          "ttsText": "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.",
          "durationSeconds": 9.1063,
          "startSec": 5.4,
          "endSec": 14.5063,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Kore",
          "voiceStyle": "calm, observant literary narration",
          "text": "However little known the feelings or views of such a man may be on his first entering a neighbourhood, this truth is so well fixed in the minds of the surrounding families, that he is considered as the rightful property of some one or other of their daughters.",
          "ttsText": "However little known the feelings or views of such a man may be on his first entering a neighbourhood, this truth is so well fixed in the minds of the surrounding families, that he is considered as the rightful property of some one or other of their daughters.",
          "durationSeconds": 16.5481,
          "startSec": 14.9863,
          "endSec": 31.5345,
          "plateIndex": 0
        },
        {
          "speaker": "Mrs. Bennet",
          "speakerLabel": "MRS. BENNET",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Aoede",
          "voiceStyle": "eager, animated",
          "text": "“My dear Mr. Bennet,”",
          "ttsText": "My dear Mr. Bennet,",
          "durationSeconds": 1.6571,
          "startSec": 32.0545,
          "endSec": 33.7116,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Kore",
          "voiceStyle": "calm literary narration",
          "text": "said his lady to him one day,",
          "ttsText": "said his lady to him one day,",
          "durationSeconds": 2.5768,
          "startSec": 33.8716,
          "endSec": 36.4484,
          "plateIndex": 0
        },
        {
          "speaker": "Mrs. Bennet",
          "speakerLabel": "MRS. BENNET",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Aoede",
          "voiceStyle": "eager, expectant, pronounce Netherfield like NETH-er-field",
          "text": "“have you heard that Netherfield Park is let at last?”",
          "ttsText": "have you heard that Netherfield Park is let at last?",
          "durationSeconds": 3.9755,
          "startSec": 36.6284,
          "endSec": 40.6038,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Kore",
          "voiceStyle": "dry, matter-of-fact narration",
          "text": "Mr. Bennet replied that he had not.",
          "ttsText": "Mr. Bennet replied that he had not.",
          "durationSeconds": 2.798,
          "startSec": 41.0238,
          "endSec": 43.8218,
          "plateIndex": 0
        }
      ]
    },
    {
      "pageNumber": 2,
      "sceneIdx": 0,
      "sceneLabel": "SCENE I",
      "folioLabel": "FOLIO I.2",
      "chapterTitle": "CHAPTER I",
      "startSec": 44.2218,
      "endSec": 65.0917,
      "narrativeText": "“But it is,” returned she; “for Mrs. Long has just been here, and she told me all about it.” Mr. Bennet made no answer. “Do not you want to know who has taken it?” cried his wife, impatiently. “You want to tell me, and I have no objection to hearing it.” This was invitation enough.",
      "illustrationPrompt": "Longbourn Morning Room",
      "imageCaption": "Longbourn Morning Room",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/01_pride_and_prejudice_diorama_scene_1.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/01_pride_and_prejudice_diorama_scene_1.png",
      "plates": [
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "Longbourn Morning Room",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — Longbourn Morning Room",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/01_pride_and_prejudice_diorama_scene_1.png"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "Longbourn Morning Room (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — Longbourn Morning Room",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/01_pride_and_prejudice_scene_1.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "Pride and Prejudice — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/01_pride_and_prejudice_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "Mrs. Bennet",
          "speakerLabel": "MRS. BENNET",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Aoede",
          "voiceStyle": "insistent, gossipy excitement",
          "text": "“But it is,” returned she; “for Mrs. Long has just been here, and she told me all about it.”",
          "ttsText": "But it is, for Mrs. Long has just been here, and she told me all about it.",
          "durationSeconds": 5.1707,
          "startSec": 44.6718,
          "endSec": 49.8425,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Kore",
          "voiceStyle": "quiet, deadpan literary narration",
          "text": "Mr. Bennet made no answer.",
          "ttsText": "Mr. Bennet made no answer.",
          "durationSeconds": 2.3373,
          "startSec": 50.2625,
          "endSec": 52.5998,
          "plateIndex": 0
        },
        {
          "speaker": "Mrs. Bennet",
          "speakerLabel": "MRS. BENNET",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Aoede",
          "voiceStyle": "impatient, pressing",
          "text": "“Do not you want to know who has taken it?”",
          "ttsText": "Do not you want to know who has taken it?",
          "durationSeconds": 2.46,
          "startSec": 53.0798,
          "endSec": 55.5399,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Kore",
          "voiceStyle": "calm literary narration",
          "text": "cried his wife, impatiently.",
          "ttsText": "cried his wife, impatiently.",
          "durationSeconds": 1.9852,
          "startSec": 55.7199,
          "endSec": 57.705,
          "plateIndex": 0
        },
        {
          "speaker": "Mr. Bennet",
          "speakerLabel": "MR. BENNET",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Charon",
          "voiceStyle": "dry, calm, deadpan amusement",
          "text": "“You want to tell me, and I have no objection to hearing it.”",
          "ttsText": "YOU want to tell me, and I have no objection to hearing it.",
          "durationSeconds": 3.8546,
          "startSec": 58.085,
          "endSec": 61.9396,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Kore",
          "voiceStyle": "dry, understated wit",
          "text": "This was invitation enough.",
          "ttsText": "This was invitation enough.",
          "durationSeconds": 2.3321,
          "startSec": 62.3596,
          "endSec": 64.6917,
          "plateIndex": 0
        }
      ]
    },
    {
      "pageNumber": 3,
      "sceneIdx": 0,
      "sceneLabel": "SCENE I",
      "folioLabel": "FOLIO I.3",
      "chapterTitle": "CHAPTER I",
      "startSec": 65.0917,
      "endSec": 113.2516,
      "narrativeText": "“Why, my dear, you must know, Mrs. Long says that Netherfield is taken by a young man of large fortune from the north of England; that he came down on Monday in a chaise and four to see the place, and was so much delighted with it that he agreed with Mr. Morris immediately.” “What is his name?” “Bingley.” “Is he married or single?” “Oh, single, my dear, to be sure! A single man of large fortune; four or five thousand a year. What a fine thing for our girls!” “How so? How can it affect them?” “My dear Mr. Bennet, how can you be so tiresome? You must know that I am thinking of his marrying one of them.”",
      "illustrationPrompt": "Longbourn Morning Room",
      "imageCaption": "Longbourn Morning Room",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/01_pride_and_prejudice_diorama_scene_1.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/01_pride_and_prejudice_diorama_scene_1.png",
      "plates": [
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "Longbourn Morning Room",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — Longbourn Morning Room",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/01_pride_and_prejudice_diorama_scene_1.png"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "Longbourn Morning Room (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — Longbourn Morning Room",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/01_pride_and_prejudice_scene_1.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "Pride and Prejudice — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/01_pride_and_prejudice_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "Mrs. Bennet",
          "speakerLabel": "MRS. BENNET",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Aoede",
          "voiceStyle": "animated, delighted gossip, pronounce chaise like shayz",
          "text": "“Why, my dear, you must know, Mrs. Long says that Netherfield is taken by a young man of large fortune from the north of England; that he came down on Monday in a chaise and four to see the place, and was so much delighted with it that he agreed with Mr. Morris immediately.”",
          "ttsText": "Why, my dear, you must know, Mrs. Long says that Netherfield is taken by a young man of large fortune from the north of England; that he came down on Monday in a chaise and four to see the place, and was so much delighted with it that he agreed with Mr. Morris immediately.",
          "durationSeconds": 18.4486,
          "startSec": 65.5417,
          "endSec": 83.9903,
          "plateIndex": 0
        },
        {
          "speaker": "Mr. Bennet",
          "speakerLabel": "MR. BENNET",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Charon",
          "voiceStyle": "calm, unhurried",
          "text": "“What is his name?”",
          "ttsText": "What is his name?",
          "durationSeconds": 1.421,
          "startSec": 84.4103,
          "endSec": 85.8313,
          "plateIndex": 0
        },
        {
          "speaker": "Mrs. Bennet",
          "speakerLabel": "MRS. BENNET",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Aoede",
          "voiceStyle": "decisive, pleased",
          "text": "“Bingley.”",
          "ttsText": "Bingley.",
          "durationSeconds": 0.8525,
          "startSec": 86.1513,
          "endSec": 87.0038,
          "plateIndex": 0
        },
        {
          "speaker": "Mr. Bennet",
          "speakerLabel": "MR. BENNET",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Charon",
          "voiceStyle": "calm, mildly curious",
          "text": "“Is he married or single?”",
          "ttsText": "Is he married or single?",
          "durationSeconds": 2.1685,
          "startSec": 87.3238,
          "endSec": 89.4923,
          "plateIndex": 0
        },
        {
          "speaker": "Mrs. Bennet",
          "speakerLabel": "MRS. BENNET",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Aoede",
          "voiceStyle": "joyful, triumphant enthusiasm",
          "text": "“Oh, single, my dear, to be sure! A single man of large fortune; four or five thousand a year. What a fine thing for our girls!”",
          "ttsText": "Oh, single, my dear, to be sure! A single man of large fortune; four or five thousand a year. What a fine thing for our girls!",
          "durationSeconds": 9.8468,
          "startSec": 89.8123,
          "endSec": 99.6592,
          "plateIndex": 0
        },
        {
          "speaker": "Mr. Bennet",
          "speakerLabel": "MR. BENNET",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Charon",
          "voiceStyle": "dry, feigned innocence",
          "text": "“How so? How can it affect them?”",
          "ttsText": "How so? How can it affect them?",
          "durationSeconds": 3.3353,
          "startSec": 100.0392,
          "endSec": 103.3745,
          "plateIndex": 0
        },
        {
          "speaker": "Mrs. Bennet",
          "speakerLabel": "MRS. BENNET",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Aoede",
          "voiceStyle": "exasperated, emphatic",
          "text": "“My dear Mr. Bennet, how can you be so tiresome? You must know that I am thinking of his marrying one of them.”",
          "ttsText": "My dear Mr. Bennet, how can you be so tiresome? You must know that I am thinking of his marrying one of them.",
          "durationSeconds": 7.0971,
          "startSec": 103.7545,
          "endSec": 110.8516,
          "plateIndex": 0
        }
      ]
    }
  ]
};

export const BASKERVILLES_STORYBOOK: Storybook = {
  "id": "02_hound_of_the_baskervilles",
  "roman": "II",
  "bookHeaderLeft": "BOOK II  ·  ARTHUR CONAN DOYLE",
  "year": "1902",
  "genreFooterLeft": "VICTORIAN DETECTIVE MYSTERY",
  "settingFooterRight": "221B BAKER STREET, LONDON",
  "title": "The Hound of the Baskervilles",
  "subtitle": "Chapter I · Mr. Sherlock Holmes",
  "author": "Arthur Conan Doyle",
  "palette": {
    "paper": "#F2EDE2",
    "card": "#E8E1D3",
    "ink": "#181A1B",
    "muted": "#6E6A63",
    "accent": "#9E6B2E",
    "rule": "#CFC6B4",
    "coverCloth": "#3D5845",
    "coverSpine": "#2B3F31"
  },
  "sourceType": "classic-adaptation",
  "gutenbergId": 2852,
  "visualStyle": "Victorian Detective Mystery — 221B Baker Street, London",
  "mood": "Victorian Detective Mystery — 221B Baker Street, London",
  "musicPrompt": "Acoustic chamber score for The Hound of the Baskervilles (1902)",
  "charSheetPrompt": "Anonymous period character reference sheet for The Hound of the Baskervilles",
  "charSheetImageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/02_hound_of_the_baskervilles_char_sheet.jpg",
  "coverImagePrompt": "221B Baker Street",
  "coverImageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/02_hound_of_the_baskervilles_diorama_scene_1.png",
  "backgroundMusicUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/music/01_pride_and_prejudice_lyria.mp3",
  "masterAudioUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/master/02_hound_of_the_baskervilles.mp4",
  "titleCardEndSec": 2.6,
  "totalDurationSeconds": 113.6167,
  "modelsUsed": {
    "orchestrator": "antigravity-preview-09-2026 (gemini-4-argon)",
    "cli": "gemini-api-cli (github.com/google-gemini/gemini-api-cli)",
    "writer": "gemini-4-argon / books_spec.py",
    "illustrator": "gemini-3.1-flash-lite-image + generate_popup_assets.py",
    "narrator": "gemini-3.8-flash-tts + voice_mastering.py",
    "composer": "lyria-3.5 + generate_and_mix_music.py"
  },
  "characters": [
    {
      "id": "dr_watson",
      "name": "Dr. Watson (narrator)",
      "role": "Literary Narration",
      "description": "Dr. John Watson (Baskervilles)",
      "voiceName": "Fenrir",
      "voiceStyle": "warm, measured Victorian literary narration"
    },
    {
      "id": "sherlock_holmes",
      "name": "Sherlock Holmes",
      "role": "Character Dialogue",
      "description": "Sherlock Holmes (Baskervilles)",
      "voiceName": "Orus",
      "voiceStyle": "crisp, sudden, inquisitive"
    }
  ],
  "pages": [
    {
      "pageNumber": 1,
      "sceneIdx": 0,
      "sceneLabel": "SCENE I",
      "folioLabel": "FOLIO II.1",
      "chapterTitle": "CHAPTER I · MR. SHERLOCK HOLMES",
      "startSec": 2.6,
      "endSec": 46.5117,
      "narrativeText": "Mr. Sherlock Holmes, who was usually very late in the mornings, save upon those not infrequent occasions when he was up all night, was seated at the breakfast table. I stood upon the hearth-rug and picked up the stick which our visitor had left behind him the night before. It was a fine, thick piece of wood, bulbous-headed, of the sort which is known as a “Penang lawyer.” Just under the head was a broad silver band nearly an inch across. “To James Mortimer, M.R.C.S., from his friends of the C.C.H.,” was engraved upon it, with the date “1884.” “Well, Watson, what do you make of it?”",
      "illustrationPrompt": "221B Baker Street",
      "imageCaption": "221B Baker Street",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/02_hound_of_the_baskervilles_diorama_scene_1.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/02_hound_of_the_baskervilles_diorama_scene_1.png",
      "plates": [
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "221B Baker Street",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — 221B Baker Street",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/02_hound_of_the_baskervilles_diorama_scene_1.png"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "221B Baker Street (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — 221B Baker Street",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/02_hound_of_the_baskervilles_scene_1.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "The Hound of the Baskervilles — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/02_hound_of_the_baskervilles_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "Dr. Watson (narrator)",
          "speakerLabel": "DR. WATSON (NARRATOR)",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Fenrir",
          "voiceStyle": "warm, measured Victorian literary narration",
          "text": "Mr. Sherlock Holmes, who was usually very late in the mornings, save upon those not infrequent occasions when he was up all night, was seated at the breakfast table.",
          "ttsText": "Mr. Sherlock Holmes, who was usually very late in the mornings, save upon those not infrequent occasions when he was up all night, was seated at the breakfast table.",
          "durationSeconds": 10.085,
          "startSec": 5.4,
          "endSec": 15.485,
          "plateIndex": 0
        },
        {
          "speaker": "Dr. Watson (narrator)",
          "speakerLabel": "DR. WATSON (NARRATOR)",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Fenrir",
          "voiceStyle": "observant narration, pronounce Penang like peh-NANG",
          "text": "I stood upon the hearth-rug and picked up the stick which our visitor had left behind him the night before. It was a fine, thick piece of wood, bulbous-headed, of the sort which is known as a “Penang lawyer.”",
          "ttsText": "I stood upon the hearth-rug and picked up the stick which our visitor had left behind him the night before. It was a fine, thick piece of wood, bulbous-headed, of the sort which is known as a Penang lawyer.",
          "durationSeconds": 13.0325,
          "startSec": 15.905,
          "endSec": 28.9375,
          "plateIndex": 0
        },
        {
          "speaker": "Dr. Watson (narrator)",
          "speakerLabel": "DR. WATSON (NARRATOR)",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Fenrir",
          "voiceStyle": "measured, clear articulation",
          "text": "Just under the head was a broad silver band nearly an inch across. “To James Mortimer, M.R.C.S., from his friends of the C.C.H.,” was engraved upon it, with the date “1884.”",
          "ttsText": "Just under the head was a broad silver band nearly an inch across. To James Mortimer, M. R. C. S., from his friends of the C. C. H., was engraved upon it, with the date eighteen eighty-four.",
          "durationSeconds": 14.4483,
          "startSec": 29.3575,
          "endSec": 43.8058,
          "plateIndex": 0
        },
        {
          "speaker": "Sherlock Holmes",
          "speakerLabel": "SHERLOCK HOLMES",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Orus",
          "voiceStyle": "crisp, sudden, inquisitive",
          "text": "“Well, Watson, what do you make of it?”",
          "ttsText": "Well, Watson, what do you make of it?",
          "durationSeconds": 1.826,
          "startSec": 44.2858,
          "endSec": 46.1118,
          "plateIndex": 0
        }
      ]
    },
    {
      "pageNumber": 2,
      "sceneIdx": 0,
      "sceneLabel": "SCENE I",
      "folioLabel": "FOLIO II.2",
      "chapterTitle": "CHAPTER I · MR. SHERLOCK HOLMES",
      "startSec": 46.5117,
      "endSec": 71.2623,
      "narrativeText": "Holmes was sitting with his back to me, and I had given him no sign of my occupation. “How did you know what I was doing? I believe you have eyes in the back of your head.” “I have, at least, a well-polished, silver-plated coffee-pot in front of me. But, tell me, Watson, what do you make of our visitor’s stick? Let me hear you reconstruct the man by an examination of it.”",
      "illustrationPrompt": "221B Baker Street",
      "imageCaption": "221B Baker Street",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/02_hound_of_the_baskervilles_diorama_scene_1.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/02_hound_of_the_baskervilles_diorama_scene_1.png",
      "plates": [
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "221B Baker Street",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — 221B Baker Street",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/02_hound_of_the_baskervilles_diorama_scene_1.png"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "221B Baker Street (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — 221B Baker Street",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/02_hound_of_the_baskervilles_scene_1.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "The Hound of the Baskervilles — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/02_hound_of_the_baskervilles_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "Dr. Watson (narrator)",
          "speakerLabel": "DR. WATSON (NARRATOR)",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Fenrir",
          "voiceStyle": "quietly astonished narration",
          "text": "Holmes was sitting with his back to me, and I had given him no sign of my occupation.",
          "ttsText": "Holmes was sitting with his back to me, and I had given him no sign of my occupation.",
          "durationSeconds": 5.4828,
          "startSec": 46.9618,
          "endSec": 52.4445,
          "plateIndex": 0
        },
        {
          "speaker": "Dr. Watson",
          "speakerLabel": "DR. WATSON",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Fenrir",
          "voiceStyle": "surprised, wry",
          "text": "“How did you know what I was doing? I believe you have eyes in the back of your head.”",
          "ttsText": "How did you know what I was doing? I believe you have eyes in the back of your head.",
          "durationSeconds": 4.8447,
          "startSec": 52.8045,
          "endSec": 57.6492,
          "plateIndex": 0
        },
        {
          "speaker": "Sherlock Holmes",
          "speakerLabel": "SHERLOCK HOLMES",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Orus",
          "voiceStyle": "dry intellectual amusement, inviting",
          "text": "“I have, at least, a well-polished, silver-plated coffee-pot in front of me. But, tell me, Watson, what do you make of our visitor’s stick? Let me hear you reconstruct the man by an examination of it.”",
          "ttsText": "I have, at least, a well-polished, silver-plated coffee-pot in front of me. But, tell me, Watson, what do you make of our visitor's stick? Let me hear you reconstruct the man by an examination of it.",
          "durationSeconds": 12.8331,
          "startSec": 58.0292,
          "endSec": 70.8623,
          "plateIndex": 0
        }
      ]
    },
    {
      "pageNumber": 3,
      "sceneIdx": 0,
      "sceneLabel": "SCENE I",
      "folioLabel": "FOLIO II.3",
      "chapterTitle": "CHAPTER I · MR. SHERLOCK HOLMES",
      "startSec": 71.2623,
      "endSec": 113.6167,
      "narrativeText": "“I think that Dr. Mortimer is a successful, elderly medical man, well-esteemed since those who know him give him this mark of their appreciation.” “Good!” said Holmes. “Excellent!” “I think also that the probability is in favour of his being a country practitioner who does a great deal of his visiting on foot.” “Why so?” “Because this stick, though originally a very handsome one, has been so knocked about that I can hardly imagine a town practitioner carrying it. The thick-iron ferrule is worn down, so it is evident that he has done a great amount of walking with it.” “Perfectly sound!” said Holmes.",
      "illustrationPrompt": "221B Baker Street",
      "imageCaption": "221B Baker Street",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/02_hound_of_the_baskervilles_diorama_scene_1.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/02_hound_of_the_baskervilles_diorama_scene_1.png",
      "plates": [
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "221B Baker Street",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — 221B Baker Street",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/02_hound_of_the_baskervilles_diorama_scene_1.png"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "221B Baker Street (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — 221B Baker Street",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/02_hound_of_the_baskervilles_scene_1.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "The Hound of the Baskervilles — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/02_hound_of_the_baskervilles_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "Dr. Watson",
          "speakerLabel": "DR. WATSON",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Fenrir",
          "voiceStyle": "thoughtful, deliberate deduction",
          "text": "“I think that Dr. Mortimer is a successful, elderly medical man, well-esteemed since those who know him give him this mark of their appreciation.”",
          "ttsText": "I think that Doctor Mortimer is a successful, elderly medical man, well-esteemed since those who know him give him this mark of their appreciation.",
          "durationSeconds": 10.2986,
          "startSec": 71.7123,
          "endSec": 82.0109,
          "plateIndex": 0
        },
        {
          "speaker": "Sherlock Holmes",
          "speakerLabel": "SHERLOCK HOLMES",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Orus",
          "voiceStyle": "crisp, encouraging approval",
          "text": "“Good!” said Holmes. “Excellent!”",
          "ttsText": "Good! Excellent!",
          "durationSeconds": 1.7514,
          "startSec": 82.3309,
          "endSec": 84.0823,
          "plateIndex": 0
        },
        {
          "speaker": "Dr. Watson",
          "speakerLabel": "DR. WATSON",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Fenrir",
          "voiceStyle": "confident, reasoned",
          "text": "“I think also that the probability is in favour of his being a country practitioner who does a great deal of his visiting on foot.”",
          "ttsText": "I think also that the probability is in favour of his being a country practitioner who does a great deal of his visiting on foot.",
          "durationSeconds": 7.7399,
          "startSec": 84.4423,
          "endSec": 92.1822,
          "plateIndex": 0
        },
        {
          "speaker": "Sherlock Holmes",
          "speakerLabel": "SHERLOCK HOLMES",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Orus",
          "voiceStyle": "keen, brisk",
          "text": "“Why so?”",
          "ttsText": "Why so?",
          "durationSeconds": 0.9828,
          "startSec": 92.4822,
          "endSec": 93.465,
          "plateIndex": 0
        },
        {
          "speaker": "Dr. Watson",
          "speakerLabel": "DR. WATSON",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Fenrir",
          "voiceStyle": "assured, analytical, pronounce ferrule like FER-uhl",
          "text": "“Because this stick, though originally a very handsome one, has been so knocked about that I can hardly imagine a town practitioner carrying it. The thick-iron ferrule is worn down, so it is evident that he has done a great amount of walking with it.”",
          "ttsText": "Because this stick, though originally a very handsome one, has been so knocked about that I can hardly imagine a town practitioner carrying it. The thick-iron ferrule is worn down, so it is evident that he has done a great amount of walking with it.",
          "durationSeconds": 15.7332,
          "startSec": 93.785,
          "endSec": 109.5181,
          "plateIndex": 0
        },
        {
          "speaker": "Sherlock Holmes",
          "speakerLabel": "SHERLOCK HOLMES",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Orus",
          "voiceStyle": "warm, satisfied approval",
          "text": "“Perfectly sound!” said Holmes.",
          "ttsText": "Perfectly sound!",
          "durationSeconds": 1.3585,
          "startSec": 109.8581,
          "endSec": 111.2167,
          "plateIndex": 0
        }
      ]
    }
  ]
};

export const ALICE_STORYBOOK: Storybook = {
  "id": "03_alice_in_wonderland",
  "roman": "III",
  "bookHeaderLeft": "BOOK III  ·  LEWIS CARROLL",
  "year": "1865",
  "genreFooterLeft": "SURREAL VICTORIAN FANTASY",
  "settingFooterRight": "THE RIVERBANK & THE DEEP WELL",
  "title": "Alice’s Adventures in Wonderland",
  "subtitle": "Chapter I · Down the Rabbit-Hole",
  "author": "Lewis Carroll",
  "palette": {
    "paper": "#F8F5EE",
    "card": "#F0EBE0",
    "ink": "#1C2026",
    "muted": "#72767D",
    "accent": "#9E332B",
    "rule": "#D8D0C1",
    "coverCloth": "#3D5845",
    "coverSpine": "#2B3F31"
  },
  "sourceType": "classic-adaptation",
  "gutenbergId": 11,
  "visualStyle": "Surreal Victorian Fantasy — The Riverbank & The Deep Well",
  "mood": "Surreal Victorian Fantasy — The Riverbank & The Deep Well",
  "musicPrompt": "Acoustic chamber score for Alice’s Adventures in Wonderland (1865)",
  "charSheetPrompt": "Anonymous period character reference sheet for Alice’s Adventures in Wonderland",
  "charSheetImageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/03_alice_in_wonderland_char_sheet.jpg",
  "coverImagePrompt": "On the Sunny Riverbank",
  "coverImageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/03_alice_in_wonderland_diorama_scene_1.png",
  "backgroundMusicUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/music/01_pride_and_prejudice_lyria.mp3",
  "masterAudioUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/master/03_alice_in_wonderland.mp4",
  "titleCardEndSec": 2.6,
  "totalDurationSeconds": 119.1983,
  "modelsUsed": {
    "orchestrator": "antigravity-preview-09-2026 (gemini-4-argon)",
    "cli": "gemini-api-cli (github.com/google-gemini/gemini-api-cli)",
    "writer": "gemini-4-argon / books_spec.py",
    "illustrator": "gemini-3.1-flash-lite-image + generate_popup_assets.py",
    "narrator": "gemini-3.8-flash-tts + voice_mastering.py",
    "composer": "lyria-3.5 + generate_and_mix_music.py"
  },
  "characters": [
    {
      "id": "carroll_narrator",
      "name": "Narrator",
      "role": "Literary Narration",
      "description": "Carroll Wonderland Narrator",
      "voiceName": "Kore",
      "voiceStyle": "warm, unhurried storybook narration"
    },
    {
      "id": "alice",
      "name": "Alice",
      "role": "Character Dialogue",
      "description": "Alice (Wonderland)",
      "voiceName": "Leda",
      "voiceStyle": "drowsy, wondering"
    },
    {
      "id": "white_rabbit",
      "name": "The White Rabbit",
      "role": "Character Dialogue",
      "description": "The White Rabbit (Wonderland)",
      "voiceName": "Puck",
      "voiceStyle": "hurried, flustered British gentlemanly urgency, clear spoken voice"
    }
  ],
  "pages": [
    {
      "pageNumber": 1,
      "sceneIdx": 0,
      "sceneLabel": "SCENE I",
      "folioLabel": "FOLIO III.1",
      "chapterTitle": "CHAPTER I · DOWN THE RABBIT-HOLE",
      "startSec": 2.6,
      "endSec": 50.1364,
      "narrativeText": "Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it, “and what is the use of a book,” thought Alice, “without pictures or conversations?” So she was considering in her own mind (as well as she could, for the hot day made her feel very sleepy and stupid), whether the pleasure of making a daisy-chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her.",
      "illustrationPrompt": "On the Sunny Riverbank",
      "imageCaption": "On the Sunny Riverbank",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/03_alice_in_wonderland_diorama_scene_1.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/03_alice_in_wonderland_diorama_scene_1.png",
      "plates": [
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "On the Sunny Riverbank",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — On the Sunny Riverbank",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/03_alice_in_wonderland_diorama_scene_1.png"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "On the Sunny Riverbank (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — On the Sunny Riverbank",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/03_alice_in_wonderland_scene_1.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "Alice’s Adventures in Wonderland — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/03_alice_in_wonderland_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Kore",
          "voiceStyle": "warm, unhurried storybook narration",
          "text": "Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it,",
          "ttsText": "Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeked into the book her sister was reading, but it had no pictures or conversations in it,",
          "durationSeconds": 15.4405,
          "startSec": 5.4,
          "endSec": 20.8405,
          "plateIndex": 0
        },
        {
          "speaker": "Alice",
          "speakerLabel": "ALICE",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Leda",
          "voiceStyle": "drowsy, wondering",
          "text": "“and what is the use of a book,”",
          "ttsText": "and what is the use of a book,",
          "durationSeconds": 2.9375,
          "startSec": 21.0605,
          "endSec": 23.998,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Kore",
          "voiceStyle": "gentle narration",
          "text": "thought Alice,",
          "ttsText": "thought Alice,",
          "durationSeconds": 1.2603,
          "startSec": 24.158,
          "endSec": 25.4183,
          "plateIndex": 0
        },
        {
          "speaker": "Alice",
          "speakerLabel": "ALICE",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Leda",
          "voiceStyle": "curious, earnest",
          "text": "“without pictures or conversations?”",
          "ttsText": "without pictures or conversations?",
          "durationSeconds": 2.7828,
          "startSec": 25.5783,
          "endSec": 28.3611,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Kore",
          "voiceStyle": "dreamy, then brightening with gentle surprise",
          "text": "So she was considering in her own mind (as well as she could, for the hot day made her feel very sleepy and stupid), whether the pleasure of making a daisy-chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her.",
          "ttsText": "So she was considering in her own mind, as well as she could, for the hot day made her feel very sleepy and stupid, whether the pleasure of making a daisy-chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her.",
          "durationSeconds": 20.8953,
          "startSec": 28.8411,
          "endSec": 49.7364,
          "plateIndex": 0
        }
      ]
    },
    {
      "pageNumber": 2,
      "sceneIdx": 0,
      "sceneLabel": "SCENE I",
      "folioLabel": "FOLIO III.2",
      "chapterTitle": "CHAPTER I · DOWN THE RABBIT-HOLE",
      "startSec": 50.1364,
      "endSec": 90.1015,
      "narrativeText": "There was nothing so very remarkable in that; nor did Alice think it so very much out of the way to hear the Rabbit say to itself, “Oh dear! Oh dear! I shall be late!” But when the Rabbit actually took a watch out of its waistcoat-pocket, and looked at it, and then hurried on, Alice started to her feet, for it flashed across her mind that she had never before seen a rabbit with either a waistcoat-pocket, or a watch to take out of it, and burning with curiosity, she ran across the field after it, and fortunately was just in time to see it pop down a large rabbit-hole under the hedge.",
      "illustrationPrompt": "On the Sunny Riverbank",
      "imageCaption": "On the Sunny Riverbank",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/03_alice_in_wonderland_diorama_scene_1.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/03_alice_in_wonderland_diorama_scene_1.png",
      "plates": [
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "On the Sunny Riverbank",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — On the Sunny Riverbank",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/03_alice_in_wonderland_diorama_scene_1.png"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "On the Sunny Riverbank (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — On the Sunny Riverbank",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/03_alice_in_wonderland_scene_1.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "Alice’s Adventures in Wonderland — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/03_alice_in_wonderland_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Kore",
          "voiceStyle": "light, playful storybook narration",
          "text": "There was nothing so very remarkable in that; nor did Alice think it so very much out of the way to hear the Rabbit say to itself,",
          "ttsText": "There was nothing so VERY remarkable in that; nor did Alice think it so VERY much out of the way to hear the Rabbit say to itself,",
          "durationSeconds": 9,
          "startSec": 50.5864,
          "endSec": 59.5864,
          "plateIndex": 0
        },
        {
          "speaker": "The White Rabbit",
          "speakerLabel": "THE WHITE RABBIT",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Puck",
          "voiceStyle": "hurried, flustered British gentlemanly urgency, clear spoken voice",
          "text": "“Oh dear! Oh dear! I shall be late!”",
          "ttsText": "Oh dear! Oh dear! I shall be late!",
          "durationSeconds": 2.0747,
          "startSec": 59.8064,
          "endSec": 61.8811,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Kore",
          "voiceStyle": "animated, building wonder and momentum",
          "text": "But when the Rabbit actually took a watch out of its waistcoat-pocket, and looked at it, and then hurried on, Alice started to her feet, for it flashed across her mind that she had never before seen a rabbit with either a waistcoat-pocket, or a watch to take out of it, and burning with curiosity, she ran across the field after it, and fortunately was just in time to see it pop down a large rabbit-hole under the hedge.",
          "ttsText": "But when the Rabbit actually took a watch out of its waistcoat-pocket, and looked at it, and then hurried on, Alice started to her feet, for it flashed across her mind that she had never before seen a rabbit with either a waistcoat-pocket, or a watch to take out of it, and burning with curiosity, she ran across the field after it, and fortunately was just in time to see it pop down a large rabbit-hole under the hedge.",
          "durationSeconds": 27.2504,
          "startSec": 62.3011,
          "endSec": 89.5515,
          "plateIndex": 0
        }
      ]
    },
    {
      "pageNumber": 3,
      "sceneIdx": 1,
      "sceneLabel": "SCENE II",
      "folioLabel": "FOLIO III.3",
      "chapterTitle": "CHAPTER I · DOWN THE RABBIT-HOLE",
      "startSec": 90.1015,
      "endSec": 119.1983,
      "narrativeText": "In another moment down went Alice after it, never once considering how in the world she was to get out again. The rabbit-hole went straight on like a tunnel for some way, and then dipped suddenly down, so suddenly that Alice had not a moment to think about stopping herself before she found herself falling down a very deep well.",
      "illustrationPrompt": "Down the Deep Well",
      "imageCaption": "Down the Deep Well",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/03_alice_in_wonderland_diorama_scene_3.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/03_alice_in_wonderland_diorama_scene_3.png",
      "plates": [
        {
          "plateNumberRoman": "II",
          "plateLabel": "PLATE II OF III",
          "title": "Down the Deep Well",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — Down the Deep Well",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/03_alice_in_wonderland_diorama_scene_3.png"
        },
        {
          "plateNumberRoman": "II",
          "plateLabel": "PLATE II OF III",
          "title": "Down the Deep Well (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — Down the Deep Well",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/03_alice_in_wonderland_scene_2.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "Alice’s Adventures in Wonderland — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/03_alice_in_wonderland_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Kore",
          "voiceStyle": "expressive, graceful, wondering",
          "text": "In another moment down went Alice after it, never once considering how in the world she was to get out again. The rabbit-hole went straight on like a tunnel for some way, and then dipped suddenly down, so suddenly that Alice had not a moment to think about stopping herself before she found herself falling down a very deep well.",
          "ttsText": "In another moment down went Alice after it, never once considering how in the world she was to get out again. The rabbit-hole went straight on like a tunnel for some way, and then dipped suddenly down, so suddenly that Alice had not a moment to think about stopping herself before she found herself falling down a very deep well.",
          "durationSeconds": 23.8968,
          "startSec": 92.9015,
          "endSec": 116.7983,
          "plateIndex": 0
        }
      ]
    }
  ]
};

export const TIME_MACHINE_STORYBOOK: Storybook = {
  "id": "04_the_time_machine",
  "roman": "IV",
  "bookHeaderLeft": "BOOK IV  ·  H. G. WELLS",
  "year": "1895",
  "genreFooterLeft": "PHILOSOPHICAL SCIENCE FICTION",
  "settingFooterRight": "THE TIME TRAVELLER’S SMOKING-ROOM, LONDON",
  "title": "The Time Machine",
  "subtitle": "Chapter I · Introduction",
  "author": "H. G. Wells",
  "palette": {
    "paper": "#F0F2F4",
    "card": "#E4E8EC",
    "ink": "#18222C",
    "muted": "#64707D",
    "accent": "#B38628",
    "rule": "#C8D0D8",
    "coverCloth": "#3D5845",
    "coverSpine": "#2B3F31"
  },
  "sourceType": "classic-adaptation",
  "gutenbergId": 35,
  "visualStyle": "Philosophical Science Fiction — The Time Traveller’s Smoking-Room, London",
  "mood": "Philosophical Science Fiction — The Time Traveller’s Smoking-Room, London",
  "musicPrompt": "Acoustic chamber score for The Time Machine (1895)",
  "charSheetPrompt": "Anonymous period character reference sheet for The Time Machine",
  "charSheetImageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/04_the_time_machine_char_sheet.jpg",
  "coverImagePrompt": "The Firelit Smoking-Room",
  "coverImageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/04_the_time_machine_diorama_scene_1.png",
  "backgroundMusicUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/music/01_pride_and_prejudice_lyria.mp3",
  "masterAudioUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/master/04_the_time_machine.mp4",
  "titleCardEndSec": 2.6,
  "totalDurationSeconds": 116.1795,
  "modelsUsed": {
    "orchestrator": "antigravity-preview-09-2026 (gemini-4-argon)",
    "cli": "gemini-api-cli (github.com/google-gemini/gemini-api-cli)",
    "writer": "gemini-4-argon / books_spec.py",
    "illustrator": "gemini-3.1-flash-lite-image + generate_popup_assets.py",
    "narrator": "gemini-3.8-flash-tts + voice_mastering.py",
    "composer": "lyria-3.5 + generate_and_mix_music.py"
  },
  "characters": [
    {
      "id": "wells_narrator",
      "name": "Narrator",
      "role": "Literary Narration",
      "description": "Hillyer Narrator (The Time Machine)",
      "voiceName": "Fenrir",
      "voiceStyle": "reflective literary narration, pronounce recondite like REK-uhn-dite"
    },
    {
      "id": "time_traveller",
      "name": "The Time Traveller",
      "role": "Character Dialogue",
      "description": "The Time Traveller (Wells)",
      "voiceName": "Orus",
      "voiceStyle": "lucid, engaged, intellectually assured"
    },
    {
      "id": "filby",
      "name": "Filby",
      "role": "Character Dialogue",
      "description": "Filby (The Time Machine)",
      "voiceName": "Iapetus",
      "voiceStyle": "skeptical, wryly challenging"
    },
    {
      "id": "psychologist",
      "name": "The Psychologist",
      "role": "Character Dialogue",
      "description": "The Psychologist (The Time Machine)",
      "voiceName": "Charon",
      "voiceStyle": "calm, matter-of-fact agreement"
    }
  ],
  "pages": [
    {
      "pageNumber": 1,
      "sceneIdx": 0,
      "sceneLabel": "SCENE I",
      "folioLabel": "FOLIO IV.1",
      "chapterTitle": "CHAPTER I · INTRODUCTION",
      "startSec": 2.6,
      "endSec": 48.5188,
      "narrativeText": "The Time Traveller (for so it will be convenient to speak of him) was expounding a recondite matter to us. His grey eyes shone and twinkled, and his usually pale face was flushed and animated. The fire burnt brightly, and the soft radiance of the incandescent lights in the lilies of silver caught the bubbles that flashed and passed in our glasses. And he put it to us in this way—marking the points with a lean forefinger. “You must follow me carefully. I shall have to controvert one or two ideas that are almost universally accepted. The geometry, for instance, they taught you at school is founded on a misconception.”",
      "illustrationPrompt": "The Firelit Smoking-Room",
      "imageCaption": "The Firelit Smoking-Room",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/04_the_time_machine_diorama_scene_1.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/04_the_time_machine_diorama_scene_1.png",
      "plates": [
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "The Firelit Smoking-Room",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — The Firelit Smoking-Room",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/04_the_time_machine_diorama_scene_1.png"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "The Firelit Smoking-Room (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — The Firelit Smoking-Room",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/04_the_time_machine_scene_1.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "The Time Machine — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/04_the_time_machine_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Fenrir",
          "voiceStyle": "reflective literary narration, pronounce recondite like REK-uhn-dite",
          "text": "The Time Traveller (for so it will be convenient to speak of him) was expounding a recondite matter to us. His grey eyes shone and twinkled, and his usually pale face was flushed and animated.",
          "ttsText": "The Time Traveller, for so it will be convenient to speak of him, was expounding a recondite matter to us. His grey eyes shone and twinkled, and his usually pale face was flushed and animated.",
          "durationSeconds": 14.1061,
          "startSec": 5.4,
          "endSec": 19.5061,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Fenrir",
          "voiceStyle": "warm, atmospheric narration",
          "text": "The fire burnt brightly, and the soft radiance of the incandescent lights in the lilies of silver caught the bubbles that flashed and passed in our glasses. And he put it to us in this way—marking the points with a lean forefinger.",
          "ttsText": "The fire burnt brightly, and the soft radiance of the incandescent lights in the lilies of silver caught the bubbles that flashed and passed in our glasses. And he put it to us in this way, marking the points with a lean forefinger.",
          "durationSeconds": 16.1114,
          "startSec": 19.9461,
          "endSec": 36.0575,
          "plateIndex": 0
        },
        {
          "speaker": "The Time Traveller",
          "speakerLabel": "THE TIME TRAVELLER",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Orus",
          "voiceStyle": "lucid, engaged, intellectually assured",
          "text": "“You must follow me carefully. I shall have to controvert one or two ideas that are almost universally accepted. The geometry, for instance, they taught you at school is founded on a misconception.”",
          "ttsText": "You must follow me carefully. I shall have to controvert one or two ideas that are almost universally accepted. The geometry, for instance, they taught you at school is founded on a misconception.",
          "durationSeconds": 11.5813,
          "startSec": 36.5375,
          "endSec": 48.1188,
          "plateIndex": 0
        }
      ]
    },
    {
      "pageNumber": 2,
      "sceneIdx": 0,
      "sceneLabel": "SCENE I",
      "folioLabel": "FOLIO IV.2",
      "chapterTitle": "CHAPTER I · INTRODUCTION",
      "startSec": 48.5188,
      "endSec": 75.9462,
      "narrativeText": "“Is not that rather a large thing to expect us to begin upon?” said Filby, an argumentative person with red hair. “I do not mean to ask you to accept anything without reasonable ground for it. You know of course that a mathematical line, a line of thickness nil, has no real existence. Neither has a mathematical plane. These things are mere abstractions.” “That is all right,” said the Psychologist.",
      "illustrationPrompt": "The Firelit Smoking-Room",
      "imageCaption": "The Firelit Smoking-Room",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/04_the_time_machine_diorama_scene_1.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/04_the_time_machine_diorama_scene_1.png",
      "plates": [
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "The Firelit Smoking-Room",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — The Firelit Smoking-Room",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/04_the_time_machine_diorama_scene_1.png"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "The Firelit Smoking-Room (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — The Firelit Smoking-Room",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/04_the_time_machine_scene_1.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "The Time Machine — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/04_the_time_machine_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "Filby",
          "speakerLabel": "FILBY",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Iapetus",
          "voiceStyle": "skeptical, wryly challenging",
          "text": "“Is not that rather a large thing to expect us to begin upon?”",
          "ttsText": "Is not that rather a large thing to expect us to begin upon?",
          "durationSeconds": 4.3246,
          "startSec": 48.9688,
          "endSec": 53.2934,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Fenrir",
          "voiceStyle": "calm narration, pronounce Filby like FIL-bee",
          "text": "said Filby, an argumentative person with red hair.",
          "ttsText": "said Filby, an argumentative person with red hair.",
          "durationSeconds": 3.9717,
          "startSec": 53.4734,
          "endSec": 57.4451,
          "plateIndex": 0
        },
        {
          "speaker": "The Time Traveller",
          "speakerLabel": "THE TIME TRAVELLER",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Orus",
          "voiceStyle": "precise, persuasive",
          "text": "“I do not mean to ask you to accept anything without reasonable ground for it. You know of course that a mathematical line, a line of thickness nil, has no real existence. Neither has a mathematical plane. These things are mere abstractions.”",
          "ttsText": "I do not mean to ask you to accept anything without reasonable ground for it. You know of course that a mathematical line, a line of thickness nil, has no real existence. Neither has a mathematical plane. These things are mere abstractions.",
          "durationSeconds": 14.2301,
          "startSec": 57.8451,
          "endSec": 72.0752,
          "plateIndex": 0
        },
        {
          "speaker": "The Psychologist",
          "speakerLabel": "THE PSYCHOLOGIST",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Charon",
          "voiceStyle": "calm, matter-of-fact agreement",
          "text": "“That is all right,”",
          "ttsText": "That is all right,",
          "durationSeconds": 1.6198,
          "startSec": 72.4352,
          "endSec": 74.055,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Fenrir",
          "voiceStyle": "measured narration",
          "text": "said the Psychologist.",
          "ttsText": "said the Psychologist.",
          "durationSeconds": 1.3112,
          "startSec": 74.235,
          "endSec": 75.5462,
          "plateIndex": 0
        }
      ]
    },
    {
      "pageNumber": 3,
      "sceneIdx": 0,
      "sceneLabel": "SCENE I",
      "folioLabel": "FOLIO IV.3",
      "chapterTitle": "CHAPTER I · INTRODUCTION",
      "startSec": 75.9462,
      "endSec": 116.1795,
      "narrativeText": "“Nor, having only length, breadth, and thickness, can a cube have a real existence.” “There I object,” said Filby. “Of course a solid body may exist. All real things—” “So most people think. But wait a moment. Can an instantaneous cube exist? Can a cube that does not last for any time at all, have a real existence?” Filby became pensive. “Clearly,” the Time Traveller proceeded, “any real body must have extension in four directions: it must have Length, Breadth, Thickness, and—Duration.”",
      "illustrationPrompt": "The Firelit Smoking-Room",
      "imageCaption": "The Firelit Smoking-Room",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/04_the_time_machine_diorama_scene_1.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/04_the_time_machine_diorama_scene_1.png",
      "plates": [
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "The Firelit Smoking-Room",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — The Firelit Smoking-Room",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/04_the_time_machine_diorama_scene_1.png"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "The Firelit Smoking-Room (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — The Firelit Smoking-Room",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/04_the_time_machine_scene_1.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "The Time Machine — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/04_the_time_machine_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "The Time Traveller",
          "speakerLabel": "THE TIME TRAVELLER",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Orus",
          "voiceStyle": "deliberate, provocative",
          "text": "“Nor, having only length, breadth, and thickness, can a cube have a real existence.”",
          "ttsText": "Nor, having only length, breadth, and thickness, can a cube have a real existence.",
          "durationSeconds": 5.4175,
          "startSec": 76.3962,
          "endSec": 81.8137,
          "plateIndex": 0
        },
        {
          "speaker": "Filby",
          "speakerLabel": "FILBY",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Iapetus",
          "voiceStyle": "blunt, objecting",
          "text": "“There I object,” said Filby. “Of course a solid body may exist. All real things—”",
          "ttsText": "There I object. Of course a solid body may exist. All real things—",
          "durationSeconds": 5.9867,
          "startSec": 82.1737,
          "endSec": 88.1604,
          "plateIndex": 0
        },
        {
          "speaker": "The Time Traveller",
          "speakerLabel": "THE TIME TRAVELLER",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Orus",
          "voiceStyle": "quietly intense, pointed question",
          "text": "“So most people think. But wait a moment. Can an instantaneous cube exist? Can a cube that does not last for any time at all, have a real existence?”",
          "ttsText": "So most people think. But wait a moment. Can an instantaneous cube exist? Can a cube that does not last for any time at all, have a real existence?",
          "durationSeconds": 11.9812,
          "startSec": 88.4404,
          "endSec": 100.4216,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Fenrir",
          "voiceStyle": "quiet narration, pronounce Filby like FIL-bee",
          "text": "Filby became pensive.",
          "ttsText": "Filby became pensive.",
          "durationSeconds": 2.0086,
          "startSec": 100.8416,
          "endSec": 102.8502,
          "plateIndex": 0
        },
        {
          "speaker": "The Time Traveller",
          "speakerLabel": "THE TIME TRAVELLER",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Orus",
          "voiceStyle": "measured, resonant revelation",
          "text": "“Clearly,” the Time Traveller proceeded, “any real body must have extension in four directions: it must have Length, Breadth, Thickness, and—Duration.”",
          "ttsText": "Clearly, any real body must have extension in four directions: it must have Length, Breadth, Thickness, and <short pause> Duration.",
          "durationSeconds": 10.5493,
          "startSec": 103.2302,
          "endSec": 113.7795,
          "plateIndex": 0
        }
      ]
    }
  ]
};

export const TOM_SAWYER_STORYBOOK: Storybook = {
  "id": "05_tom_sawyer",
  "roman": "V",
  "bookHeaderLeft": "BOOK V  ·  MARK TWAIN",
  "year": "1876",
  "genreFooterLeft": "MISSISSIPPI RIVER AMERICANA",
  "settingFooterRight": "ST. PETERSBURG, MISSOURI",
  "title": "The Adventures of Tom Sawyer",
  "subtitle": "Chapter I · Y-o-u-u Tom—Aunt Polly Decides Upon Her Duty",
  "author": "Mark Twain",
  "palette": {
    "paper": "#F6EFE4",
    "card": "#EDE3D3",
    "ink": "#261E19",
    "muted": "#7A6D61",
    "accent": "#B85733",
    "rule": "#D6C8B4",
    "coverCloth": "#3D5845",
    "coverSpine": "#2B3F31"
  },
  "sourceType": "classic-adaptation",
  "gutenbergId": 74,
  "visualStyle": "Mississippi River Americana — St. Petersburg, Missouri",
  "mood": "Mississippi River Americana — St. Petersburg, Missouri",
  "musicPrompt": "Acoustic chamber score for The Adventures of Tom Sawyer (1876)",
  "charSheetPrompt": "Anonymous period character reference sheet for The Adventures of Tom Sawyer",
  "charSheetImageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/05_tom_sawyer_char_sheet.jpg",
  "coverImagePrompt": "Inside Aunt Polly’s Cottage",
  "coverImageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/05_tom_sawyer_diorama_scene_1.png",
  "backgroundMusicUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/music/01_pride_and_prejudice_lyria.mp3",
  "masterAudioUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/master/05_tom_sawyer.mp4",
  "titleCardEndSec": 2.6,
  "totalDurationSeconds": 101.3691,
  "modelsUsed": {
    "orchestrator": "antigravity-preview-09-2026 (gemini-4-argon)",
    "cli": "gemini-api-cli (github.com/google-gemini/gemini-api-cli)",
    "writer": "gemini-4-argon / books_spec.py",
    "illustrator": "gemini-3.1-flash-lite-image + generate_popup_assets.py",
    "narrator": "gemini-3.8-flash-tts + voice_mastering.py",
    "composer": "lyria-3.5 + generate_and_mix_music.py"
  },
  "characters": [
    {
      "id": "aunt_polly",
      "name": "Aunt Polly",
      "role": "Character Dialogue",
      "description": "Aunt Polly (Tom Sawyer)",
      "voiceName": "Aoede",
      "voiceStyle": "calling out firmly across a quiet house"
    },
    {
      "id": "twain_narrator",
      "name": "Narrator",
      "role": "Literary Narration",
      "description": "Twain Missouri Narrator",
      "voiceName": "Charon",
      "voiceStyle": "dry, unhurried storytelling"
    },
    {
      "id": "tom_sawyer",
      "name": "Tom Sawyer",
      "role": "Character Dialogue",
      "description": "Tom Sawyer (Twain)",
      "voiceName": "Puck",
      "voiceStyle": "innocent, sheepish"
    }
  ],
  "pages": [
    {
      "pageNumber": 1,
      "sceneIdx": 0,
      "sceneLabel": "SCENE I",
      "folioLabel": "FOLIO V.1",
      "chapterTitle": "CHAPTER I · Y-O-U-U TOM—AUNT POLLY DECIDES UPON HER DUTY",
      "startSec": 2.6,
      "endSec": 37.3975,
      "narrativeText": "“TOM!” No answer. “What’s gone with that boy, I wonder? You TOM!” No answer. The old lady pulled her spectacles down and looked over them about the room; then she put them up and looked out under them. She seldom or never looked through them for so small a thing as a boy; they were her state pair, the pride of her heart, and were built for “style,” not service—she could have seen through a pair of stove-lids just as well.",
      "illustrationPrompt": "Inside Aunt Polly’s Cottage",
      "imageCaption": "Inside Aunt Polly’s Cottage",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/05_tom_sawyer_diorama_scene_1.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/05_tom_sawyer_diorama_scene_1.png",
      "plates": [
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "Inside Aunt Polly’s Cottage",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — Inside Aunt Polly’s Cottage",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/05_tom_sawyer_diorama_scene_1.png"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "Inside Aunt Polly’s Cottage (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — Inside Aunt Polly’s Cottage",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/05_tom_sawyer_scene_1.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "The Adventures of Tom Sawyer — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/05_tom_sawyer_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "Aunt Polly",
          "speakerLabel": "AUNT POLLY",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Aoede",
          "voiceStyle": "calling out firmly across a quiet house",
          "text": "“TOM!”",
          "ttsText": "TOM!",
          "durationSeconds": 0.8508,
          "startSec": 5.4,
          "endSec": 6.2508,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Charon",
          "voiceStyle": "dry, unhurried storytelling",
          "text": "No answer.",
          "ttsText": "No answer.",
          "durationSeconds": 0.9582,
          "startSec": 6.6708,
          "endSec": 7.629,
          "plateIndex": 0
        },
        {
          "speaker": "Aunt Polly",
          "speakerLabel": "AUNT POLLY",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Aoede",
          "voiceStyle": "speaking to herself in puzzled exasperation, then calling out clearly across the room",
          "text": "“What’s gone with that boy, I wonder? You TOM!”",
          "ttsText": "What's gone with that boy, I wonder? You TOM!",
          "durationSeconds": 4.1315,
          "startSec": 8.049,
          "endSec": 12.1805,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Charon",
          "voiceStyle": "warm, wry, affectionate humor",
          "text": "No answer. The old lady pulled her spectacles down and looked over them about the room; then she put them up and looked out under them. She seldom or never looked through them for so small a thing as a boy; they were her state pair, the pride of her heart, and were built for “style,” not service—she could have seen through a pair of stove-lids just as well.",
          "ttsText": "No answer. The old lady pulled her spectacles down and looked over them about the room; then she put them up and looked out under them. She seldom or never looked through them for so small a thing as a boy; they were her state pair, the pride of her heart, and were built for style, not service—she could have seen through a pair of stove-lids just as well.",
          "durationSeconds": 24.397,
          "startSec": 12.6005,
          "endSec": 36.9975,
          "plateIndex": 0
        }
      ]
    },
    {
      "pageNumber": 2,
      "sceneIdx": 0,
      "sceneLabel": "SCENE I",
      "folioLabel": "FOLIO V.2",
      "chapterTitle": "CHAPTER I · Y-O-U-U TOM—AUNT POLLY DECIDES UPON HER DUTY",
      "startSec": 37.3975,
      "endSec": 71.9021,
      "narrativeText": "There was a slight noise behind her and she turned just in time to seize a small boy by the slack of his roundabout and arrest his flight. “There! I might ’a’ thought of that closet. What you been doing in there?” “Nothing.” “Nothing! Look at your hands. And look at your mouth. What is that truck?” “I don’t know, aunt.” “Well, I know. It’s jam—that’s what it is. Forty times I’ve said if you didn’t let that jam alone I’d skin you. Hand me that switch.”",
      "illustrationPrompt": "Inside Aunt Polly’s Cottage",
      "imageCaption": "Inside Aunt Polly’s Cottage",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/05_tom_sawyer_diorama_scene_1.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/05_tom_sawyer_diorama_scene_1.png",
      "plates": [
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "Inside Aunt Polly’s Cottage",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — Inside Aunt Polly’s Cottage",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/05_tom_sawyer_diorama_scene_1.png"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "PLATE I OF III",
          "title": "Inside Aunt Polly’s Cottage (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — Inside Aunt Polly’s Cottage",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/05_tom_sawyer_scene_1.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "The Adventures of Tom Sawyer — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/05_tom_sawyer_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Charon",
          "voiceStyle": "lively narrative pacing",
          "text": "There was a slight noise behind her and she turned just in time to seize a small boy by the slack of his roundabout and arrest his flight.",
          "ttsText": "There was a slight noise behind her and she turned just in time to seize a small boy by the slack of his roundabout and arrest his flight.",
          "durationSeconds": 10.6105,
          "startSec": 37.8475,
          "endSec": 48.458,
          "plateIndex": 0
        },
        {
          "speaker": "Aunt Polly",
          "speakerLabel": "AUNT POLLY",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Aoede",
          "voiceStyle": "sharp, triumphant, suspicious",
          "text": "“There! I might ’a’ thought of that closet. What you been doing in there?”",
          "ttsText": "There! I might a thought of that closet. What you been doing in there?",
          "durationSeconds": 4.3233,
          "startSec": 48.838,
          "endSec": 53.1613,
          "plateIndex": 0
        },
        {
          "speaker": "Tom Sawyer",
          "speakerLabel": "TOM SAWYER",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Puck",
          "voiceStyle": "innocent, sheepish",
          "text": "“Nothing.”",
          "ttsText": "Nothing.",
          "durationSeconds": 0.9653,
          "startSec": 53.4613,
          "endSec": 54.4265,
          "plateIndex": 0
        },
        {
          "speaker": "Aunt Polly",
          "speakerLabel": "AUNT POLLY",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Aoede",
          "voiceStyle": "scolding, incredulous",
          "text": "“Nothing! Look at your hands. And look at your mouth. What is that truck?”",
          "ttsText": "Nothing! Look at your hands. And look at your mouth. What IS that truck?",
          "durationSeconds": 5.591,
          "startSec": 54.7265,
          "endSec": 60.3176,
          "plateIndex": 0
        },
        {
          "speaker": "Tom Sawyer",
          "speakerLabel": "TOM SAWYER",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Puck",
          "voiceStyle": "meek, feigning ignorance",
          "text": "“I don’t know, aunt.”",
          "ttsText": "I don't know, aunt.",
          "durationSeconds": 1.88,
          "startSec": 60.6176,
          "endSec": 62.4976,
          "plateIndex": 0
        },
        {
          "speaker": "Aunt Polly",
          "speakerLabel": "AUNT POLLY",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Aoede",
          "voiceStyle": "stern, exasperated authority",
          "text": "“Well, I know. It’s jam—that’s what it is. Forty times I’ve said if you didn’t let that jam alone I’d skin you. Hand me that switch.”",
          "ttsText": "Well, I know. It's jam—that's what it is. Forty times I've said if you didn't let that jam alone I'd skin you. Hand me that switch.",
          "durationSeconds": 8.5545,
          "startSec": 62.7976,
          "endSec": 71.3521,
          "plateIndex": 0
        }
      ]
    },
    {
      "pageNumber": 3,
      "sceneIdx": 1,
      "sceneLabel": "SCENE II",
      "folioLabel": "FOLIO V.3",
      "chapterTitle": "CHAPTER I · Y-O-U-U TOM—AUNT POLLY DECIDES UPON HER DUTY",
      "startSec": 71.9021,
      "endSec": 101.3691,
      "narrativeText": "The switch hovered in the air—the peril was desperate— “My! Look behind you, aunt!” The old lady whirled round, and snatched her skirts out of danger. The lad fled on the instant, scrambled up the high board-fence, and disappeared over it. His aunt Polly stood surprised a moment, and then broke into a gentle laugh.",
      "illustrationPrompt": "Over the High Board-Fence",
      "imageCaption": "Over the High Board-Fence",
      "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/05_tom_sawyer_diorama_scene_3.png",
      "dioramaUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/05_tom_sawyer_diorama_scene_3.png",
      "plates": [
        {
          "plateNumberRoman": "II",
          "plateLabel": "PLATE II OF III",
          "title": "Over the High Board-Fence",
          "illustrationPrompt": "3D Multi-Plane Pop-Up Diorama — Over the High Board-Fence",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/dioramas/05_tom_sawyer_diorama_scene_3.png"
        },
        {
          "plateNumberRoman": "II",
          "plateLabel": "PLATE II OF III",
          "title": "Over the High Board-Fence (2D Archival Watercolour Plate)",
          "illustrationPrompt": "2D Archival Watercolour Plate — Over the High Board-Fence",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/05_tom_sawyer_scene_2.jpg"
        },
        {
          "plateNumberRoman": "I",
          "plateLabel": "CHARACTER SHEET",
          "title": "The Adventures of Tom Sawyer — Anonymous Period Character Sheet",
          "illustrationPrompt": "16:9 Character & Style Reference Sheet",
          "imageUrl": "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/illustrations/05_tom_sawyer_char_sheet.jpg"
        }
      ],
      "dialogueLines": [
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Charon",
          "voiceStyle": "mock-dramatic suspense",
          "text": "The switch hovered in the air—the peril was desperate—",
          "ttsText": "The switch hovered in the air... the peril was desperate...",
          "durationSeconds": 5.2885,
          "startSec": 74.7021,
          "endSec": 79.9907,
          "plateIndex": 0
        },
        {
          "speaker": "Tom Sawyer",
          "speakerLabel": "TOM SAWYER",
          "voiceRoleLabel": "Character Dialogue",
          "isDialogue": true,
          "voiceName": "Puck",
          "voiceStyle": "urgent, startled warning",
          "text": "“My! Look behind you, aunt!”",
          "ttsText": "My! Look behind you, aunt!",
          "durationSeconds": 1.7624,
          "startSec": 80.3107,
          "endSec": 82.073,
          "plateIndex": 0
        },
        {
          "speaker": "Narrator",
          "speakerLabel": "NARRATOR",
          "voiceRoleLabel": "Literary Narration",
          "isDialogue": false,
          "voiceName": "Charon",
          "voiceStyle": "brisk action, softening into warm affectionate amusement",
          "text": "The old lady whirled round, and snatched her skirts out of danger. The lad fled on the instant, scrambled up the high board-fence, and disappeared over it. His aunt Polly stood surprised a moment, and then broke into a gentle laugh.",
          "ttsText": "The old lady whirled round, and snatched her skirts out of danger. The lad fled on the instant, scrambled up the high board-fence, and disappeared over it. His aunt Polly stood surprised a moment, and then broke into a gentle laugh.",
          "durationSeconds": 16.556,
          "startSec": 82.413,
          "endSec": 98.9691,
          "plateIndex": 0
        }
      ]
    }
  ]
};

export const INITIAL_SHOWCASE_STORYBOOK: Storybook = PRIDE_AND_PREJUDICE_STORYBOOK;

export const ALL_CLASSIC_STORYBOOKS: Storybook[] = [
  PRIDE_AND_PREJUDICE_STORYBOOK,
  BASKERVILLES_STORYBOOK,
  ALICE_STORYBOOK,
  TIME_MACHINE_STORYBOOK,
  TOM_SAWYER_STORYBOOK,
];

/**
 * Generates fine-press Regency / Fairytale pen-and-ink & watercolour SVG plates
 * on warm archival paper (#F6F2EA) when creating a bespoke fairytale storybook
 * without an external image API key.
 */
function createFairytalePlateSvgDataUri(
  variant: "char-sheet" | "scene-1" | "scene-2" | "scene-3",
  palette: StorybookPalette,
  caption: string
): string {
  const { paper, card, ink, muted, accent, rule } = palette;
  let artwork = "";

  if (variant === "char-sheet") {
    artwork = `
      <!-- Subtle center fold and ground wash -->
      <ellipse cx="448" cy="430" rx="280" ry="22" fill="${card}" opacity="0.85"/>
      <!-- Left figure in three-quarter profile facing right -->
      <g transform="translate(275, 110)">
        <ellipse cx="45" cy="315" rx="46" ry="8" fill="${rule}" opacity="0.55"/>
        <!-- Coat & skirts -->
        <path d="M22,92 L68,92 L82,235 L14,235 Z" fill="${accent}" fill-opacity="0.28" stroke="${ink}" stroke-width="1.6"/>
        <path d="M32,92 L58,92 L62,175 L28,175 Z" fill="${card}" stroke="${ink}" stroke-width="1.3"/>
        <!-- Legs & boots -->
        <path d="M32,235 L30,305 M58,235 L62,305" stroke="${ink}" stroke-width="2.2" stroke-linecap="round"/>
        <!-- Head & collar facing right -->
        <circle cx="46" cy="56" r="22" fill="${paper}" stroke="${ink}" stroke-width="1.6"/>
        <path d="M30,42 Q46,24 64,42" fill="none" stroke="${ink}" stroke-width="1.8"/>
        <circle cx="54" cy="53" r="1.8" fill="${ink}"/>
        <path d="M66,56 L72,60 L65,63" fill="none" stroke="${ink}" stroke-width="1.4"/>
        <!-- Arm holding open notebook/chronicle -->
        <path d="M55,115 L92,142 L106,132" fill="none" stroke="${ink}" stroke-width="1.8"/>
        <rect x="98" y="114" width="28" height="22" rx="2" transform="rotate(-12 98 114)" fill="${paper}" stroke="${ink}" stroke-width="1.5"/>
      </g>
      <!-- Right figure in three-quarter profile facing left -->
      <g transform="translate(525, 118)">
        <ellipse cx="45" cy="307" rx="52" ry="9" fill="${rule}" opacity="0.55"/>
        <!-- Empire-waist gown with botanical wash -->
        <path d="M24,88 L66,88 L94,298 L-4,298 Z" fill="${accent}" fill-opacity="0.18" stroke="${ink}" stroke-width="1.6"/>
        <path d="M20,122 L70,122" stroke="${accent}" stroke-width="3"/>
        <!-- Shawl & bodice -->
        <path d="M18,88 Q45,112 72,88 L78,168 Q45,148 12,168 Z" fill="${card}" stroke="${ink}" stroke-width="1.4"/>
        <!-- Head facing left -->
        <circle cx="44" cy="52" r="21" fill="${paper}" stroke="${ink}" stroke-width="1.6"/>
        <path d="M30,34 Q52,22 66,46 Q72,58 62,68" fill="${card}" stroke="${ink}" stroke-width="1.4"/>
        <circle cx="36" cy="50" r="1.8" fill="${ink}"/>
        <path d="M24,52 L19,56 L25,59" fill="none" stroke="${ink}" stroke-width="1.4"/>
        <!-- Expressive hand gesture toward left figure -->
        <path d="M26,112 L-14,132 L-28,125" fill="none" stroke="${ink}" stroke-width="1.7"/>
      </g>
    `;
  } else if (variant === "scene-1") {
    artwork = `
      <!-- Tall Georgian/Fairytale arched sash windows on distant back wall -->
      <rect x="0" y="0" width="896" height="360" fill="${paper}"/>
      <rect x="0" y="360" width="896" height="144" fill="${card}" opacity="0.65"/>
      <line x1="0" y1="360" x2="896" y2="360" stroke="${rule}" stroke-width="1.5"/>
      <!-- Sunlit window left & right -->
      <g stroke="${ink}" stroke-width="1.3" fill="${paper}">
        <rect x="110" y="36" width="150" height="250" fill="#FDFBF5"/>
        <line x1="185" y1="36" x2="185" y2="286"/>
        <line x1="110" y1="120" x2="260" y2="120"/>
        <line x1="110" y1="204" x2="260" y2="204"/>
        <rect x="636" y="36" width="150" height="250" fill="#FDFBF5"/>
        <line x1="711" y1="36" x2="711" y2="286"/>
        <line x1="636" y1="120" x2="786" y2="120"/>
        <line x1="636" y1="204" x2="786" y2="204"/>
      </g>
      <!-- Sage drapes -->
      <path d="M88,28 L126,28 L116,356 L82,356 Z" fill="${accent}" fill-opacity="0.26" stroke="${ink}" stroke-width="1.3"/>
      <path d="M248,28 L282,28 L288,356 L256,356 Z" fill="${accent}" fill-opacity="0.26" stroke="${ink}" stroke-width="1.3"/>
      <path d="M614,28 L648,28 L640,356 L608,356 Z" fill="${accent}" fill-opacity="0.26" stroke="${ink}" stroke-width="1.3"/>
      <path d="M774,28 L808,28 L814,356 L782,356 Z" fill="${accent}" fill-opacity="0.26" stroke="${ink}" stroke-width="1.3"/>
      <!-- Center die-cut pedestal table with lantern/music box -->
      <g filter="drop-shadow(6px 6px 5px rgba(30,27,24,0.18))">
        <path d="M388,292 L508,292 L508,312 L462,312 L462,422 L496,448 L400,448 L434,422 L434,312 L388,312 Z" fill="${paper}" stroke="${paper}" stroke-width="9" stroke-linejoin="round"/>
        <ellipse cx="448" cy="302" rx="64" ry="12" fill="${card}" stroke="${ink}" stroke-width="1.6"/>
        <path d="M442,314 L442,420 L412,446 M454,314 L454,420 L484,446" fill="none" stroke="${ink}" stroke-width="2"/>
        <!-- Spun-glass dome & songbird centerpiece -->
        <path d="M428,296 L428,262 A20,20 0 0,1 468,262 L468,296 Z" fill="#FDFBF5" stroke="${ink}" stroke-width="1.4"/>
        <circle cx="448" cy="276" r="6" fill="${accent}" fill-opacity="0.55" stroke="${ink}" stroke-width="1.2"/>
      </g>
      <!-- Left & Right die-cut cardstock standees with white paper margin -->
      <g filter="drop-shadow(7px 7px 6px rgba(30,27,24,0.22))">
        <path d="M180,158 C195,135 235,135 245,162 L272,452 L162,452 Z" fill="${paper}" stroke="${paper}" stroke-width="10" stroke-linejoin="round"/>
        <circle cx="214" cy="176" r="19" fill="${paper}" stroke="${ink}" stroke-width="1.6"/>
        <path d="M192,205 L238,205 L262,442 L172,442 Z" fill="${accent}" fill-opacity="0.24" stroke="${ink}" stroke-width="1.6"/>
        <path d="M228,228 L268,244" stroke="${ink}" stroke-width="1.7"/>
      </g>
      <g filter="drop-shadow(7px 7px 6px rgba(30,27,24,0.22))">
        <path d="M645,168 C660,145 700,145 715,172 L732,452 L626,452 Z" fill="${paper}" stroke="${paper}" stroke-width="10" stroke-linejoin="round"/>
        <circle cx="678" cy="184" r="19" fill="${paper}" stroke="${ink}" stroke-width="1.6"/>
        <path d="M652,212 L704,212 L718,365 L640,365 Z" fill="${card}" stroke="${ink}" stroke-width="1.6"/>
        <path d="M660,365 L656,442 M696,365 L700,442" stroke="${ink}" stroke-width="2.2"/>
      </g>
    `;
  } else if (variant === "scene-2") {
    artwork = `
      <!-- Arched conservatory / library gallery -->
      <rect x="0" y="0" width="896" height="370" fill="${paper}"/>
      <rect x="0" y="370" width="896" height="134" fill="${card}" opacity="0.6"/>
      <line x1="0" y1="370" x2="896" y2="370" stroke="${rule}" stroke-width="1.5"/>
      <!-- Bookcases & arched Botanical window -->
      <rect x="70" y="42" width="210" height="328" fill="${card}" stroke="${ink}" stroke-width="1.4"/>
      <line x1="70" y1="120" x2="280" y2="120" stroke="${ink}" stroke-width="1.2"/>
      <line x1="70" y1="200" x2="280" y2="200" stroke="${ink}" stroke-width="1.2"/>
      <line x1="70" y1="280" x2="280" y2="280" stroke="${ink}" stroke-width="1.2"/>
      <path d="M358,370 L358,130 A90,90 0 0,1 538,130 L538,370 Z" fill="#FDFBF5" stroke="${ink}" stroke-width="1.5"/>
      <!-- Die-cut standees in conversation -->
      <g filter="drop-shadow(7px 7px 6px rgba(30,27,24,0.22))">
        <path d="M250,165 L335,165 L350,452 L235,452 Z" fill="${paper}" stroke="${paper}" stroke-width="10" stroke-linejoin="round"/>
        <circle cx="292" cy="188" r="19" fill="${paper}" stroke="${ink}" stroke-width="1.6"/>
        <path d="M268,215 L318,215 L338,442 L250,442 Z" fill="${accent}" fill-opacity="0.25" stroke="${ink}" stroke-width="1.6"/>
      </g>
      <g filter="drop-shadow(7px 7px 6px rgba(30,27,24,0.22))">
        <path d="M555,165 L645,165 L660,452 L540,452 Z" fill="${paper}" stroke="${paper}" stroke-width="10" stroke-linejoin="round"/>
        <circle cx="600" cy="188" r="19" fill="${paper}" stroke="${ink}" stroke-width="1.6"/>
        <path d="M572,215 L628,215 L642,442 L558,442 Z" fill="${card}" stroke="${ink}" stroke-width="1.6"/>
      </g>
    `;
  } else {
    artwork = `
      <!-- Starlit / Sunlit garden terrace -->
      <rect x="0" y="0" width="896" height="350" fill="${paper}"/>
      <rect x="0" y="350" width="896" height="154" fill="${card}" opacity="0.65"/>
      <line x1="0" y1="350" x2="896" y2="350" stroke="${rule}" stroke-width="1.5"/>
      <circle cx="448" cy="145" r="78" fill="#FDFBF5" stroke="${rule}" stroke-width="1.2"/>
      <!-- Classical balustrade -->
      <line x1="80" y1="310" x2="816" y2="310" stroke="${ink}" stroke-width="1.6"/>
      <g filter="drop-shadow(7px 7px 6px rgba(30,27,24,0.22))">
        <path d="M395,160 L500,160 L522,454 L375,454 Z" fill="${paper}" stroke="${paper}" stroke-width="10" stroke-linejoin="round"/>
        <circle cx="448" cy="186" r="20" fill="${paper}" stroke="${ink}" stroke-width="1.6"/>
        <path d="M418,214 L478,214 L506,442 L390,442 Z" fill="${accent}" fill-opacity="0.26" stroke="${ink}" stroke-width="1.6"/>
      </g>
    `;
  }

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 896 504" width="896" height="504">
    <rect width="896" height="504" fill="${paper}"/>
    <!-- Center vertical pop-up book spine fold crease -->
    <line x1="448" y1="0" x2="448" y2="504" stroke="${rule}" stroke-width="1.5" opacity="0.65"/>
    ${artwork}
    <rect x="0.5" y="0.5" width="895" height="503" fill="none" stroke="${rule}" stroke-width="1"/>
  </svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

/**
 * Dynamically creates a complete 3-Folio Jane Austen-style Illustrated Edition
 * for any user fairytale or custom prompt when running in offline/demo sandbox mode.
 */
export function createBespokeFairytaleStorybook(
  userPrompt: string,
  visualStyle: string,
  narratorVoice: string,
  paletteKey: string = "regency"
): Storybook {
  const cleanPrompt = userPrompt.trim() || FAIRYTALE_COMMISSION_PROMPTS[0].prompt;
  const matchedStarter = FAIRYTALE_COMMISSION_PROMPTS.find(
    (p) => cleanPrompt.toLowerCase().includes(p.title.toLowerCase().slice(0, 12)) || cleanPrompt === p.prompt
  );

  const pal = EDITION_PALETTES[paletteKey]?.palette || EDITION_PALETTES.regency.palette;

  // Derive a literary title & setting from the user's prompt
  const words = cleanPrompt.replace(/[^\w\s'-]/g, " ").split(/\s+/).filter(Boolean);
  const title = matchedStarter
    ? matchedStarter.title
    : words.length <= 7
    ? cleanPrompt
    : `The Chronicle of ${words.slice(0, 4).map((w) => w[0].toUpperCase() + w.slice(1).toLowerCase()).join(" ")}`;

  const charSheetUri = createFairytalePlateSvgDataUri("char-sheet", pal, "Character Reference Sheet");
  const scene1Uri = createFairytalePlateSvgDataUri("scene-1", pal, "The Morning Workshop");
  const scene2Uri = createFairytalePlateSvgDataUri("scene-2", pal, "The Riddle of the Key");
  const scene3Uri = createFairytalePlateSvgDataUri("scene-3", pal, "The Hidden Conservatory");

  return {
    id: `custom_${Date.now()}`,
    roman: "I",
    bookHeaderLeft: "BOOK I  ·  FOLIO & VOICE PRESS",
    year: "1815",
    genreFooterLeft: "ILLUSTRATED FAIRYTALE FOLIO",
    settingFooterRight: "CHAMBER EDITION · GEMINI MANAGED AGENT",
    title,
    subtitle: "Chapter I",
    author: "Gemini Managed Agent (gemini-4-argon)",
    palette: pal,
    sourceType: "original-story",
    visualStyle,
    mood: "Warm archival paper fairytale, delicate pen-and-ink linework, chamber strings",
    musicPrompt:
      "Warm Regency chamber string quartet and pianoforte in D major — resonant cello and contrabass arco and pizzicato foundation, warm viola and mellow violin.",
    charSheetPrompt:
      "Minimalist editorial book illustration character reference sheet on clean warm cream archival paper (#F6F2EA). Two full-length period figures standing side by side in three-quarter profile facing each other, with zero proper names or text labels.",
    charSheetImageUrl: charSheetUri,
    coverImagePrompt: cleanPrompt,
    coverImageUrl: scene1Uri,
    backgroundMusicUrl: "https://www.gstatic.com/aistudio/starter-apps/audio-storybooks/music/01_pride_and_prejudice_lyria.mp3",
    totalDurationSeconds: 92.4,
    modelsUsed: DEFAULT_MODELS_USED,
    characters: [
      {
        id: "narrator",
        name: "Narrator",
        role: "Literary Narration",
        description: "Poised, warm storybook narrator",
        voiceName: narratorVoice || "Kore",
        voiceStyle: "poised, warm storybook narration",
      },
      {
        id: "clara",
        name: "Clara",
        role: "Character Dialogue",
        description: "Observant, spirited heroine",
        voiceName: "Aoede",
        voiceStyle: "eager, wondering, expressive",
      },
      {
        id: "master_aldous",
        name: "Master Aldous",
        role: "Character Dialogue",
        description: "Dry, kindly master craftsman with unhurried wit",
        voiceName: "Charon",
        voiceStyle: "dry, calm, affectionate amusement",
      },
    ],
    pages: [
      {
        pageNumber: 1,
        sceneLabel: "SCENE I",
        folioLabel: "FOLIO I.1",
        chapterTitle: "CHAPTER I",
        narrativeText: cleanPrompt,
        illustrationPrompt: `Scene I for: ${cleanPrompt}`,
        imageCaption: "The Sunlit Workshop",
        imageUrl: scene1Uri,
        dioramaUrl: scene1Uri,
        plates: [
          {
            plateNumberRoman: "I",
            plateLabel: "PLATE I OF III",
            title: "The Sunlit Workshop",
            illustrationPrompt: "3D Multi-Plane Pop-Up Diorama — Scene I",
            imageUrl: scene1Uri,
          },
          {
            plateNumberRoman: "I",
            plateLabel: "CHARACTER SHEET",
            title: "Anonymous Character Reference Sheet",
            illustrationPrompt: "16:9 Character & Style Reference Sheet on #F6F2EA paper",
            imageUrl: charSheetUri,
          },
        ],
        dialogueLines: [
          {
            speaker: "Narrator",
            speakerLabel: "NARRATOR",
            voiceRoleLabel: "Literary Narration",
            isDialogue: false,
            voiceName: narratorVoice || "Kore",
            text: `It was a truth long whispered in the valley, though seldom set down in ink: ${cleanPrompt}`,
            durationSeconds: 11.2,
          },
          {
            speaker: "Clara",
            speakerLabel: "CLARA",
            voiceRoleLabel: "Character Dialogue",
            isDialogue: true,
            voiceName: "Aoede",
            text: "“Look closely at the brass escapement, Master Aldous—it has begun to turn of its own accord!”",
            durationSeconds: 5.4,
          },
          {
            speaker: "Narrator",
            speakerLabel: "NARRATOR",
            voiceRoleLabel: "Literary Narration",
            isDialogue: false,
            voiceName: narratorVoice || "Kore",
            text: "said she, setting her candle beside the tall sash window.",
            durationSeconds: 3.1,
          },
          {
            speaker: "Master Aldous",
            speakerLabel: "MASTER ALDOUS",
            voiceRoleLabel: "Character Dialogue",
            isDialogue: true,
            voiceName: "Charon",
            text: "“Impossible Things, my dear child, rarely wait for our permission before beginning their work.”",
            durationSeconds: 5.8,
          },
        ],
      },
      {
        pageNumber: 2,
        sceneLabel: "SCENE II",
        folioLabel: "FOLIO I.2",
        chapterTitle: "CHAPTER I",
        narrativeText:
          "As the chime settled across the floorboards, a delicate map unfolded from beneath the velvet lining.",
        illustrationPrompt: `Scene II for: ${cleanPrompt}`,
        imageCaption: "The Unfolded Charter",
        imageUrl: scene2Uri,
        dioramaUrl: scene2Uri,
        plates: [
          {
            plateNumberRoman: "II",
            plateLabel: "PLATE II OF III",
            title: "The Unfolded Charter",
            illustrationPrompt: "3D Multi-Plane Pop-Up Diorama — Scene II",
            imageUrl: scene2Uri,
          },
          {
            plateNumberRoman: "I",
            plateLabel: "CHARACTER SHEET",
            title: "Anonymous Character Reference Sheet",
            illustrationPrompt: "16:9 Character & Style Reference Sheet",
            imageUrl: charSheetUri,
          },
        ],
        dialogueLines: [
          {
            speaker: "Narrator",
            speakerLabel: "NARRATOR",
            voiceRoleLabel: "Literary Narration",
            isDialogue: false,
            voiceName: narratorVoice || "Kore",
            text: "As the silver chime settled across the oak floorboards, a folded leaf of laid paper slipped from beneath the velvet lining.",
            durationSeconds: 8.4,
          },
          {
            speaker: "Clara",
            speakerLabel: "CLARA",
            voiceRoleLabel: "Character Dialogue",
            isDialogue: true,
            voiceName: "Aoede",
            text: "“Do not you wish to read what is inscribed along the margin?”",
            durationSeconds: 3.9,
          },
          {
            speaker: "Master Aldous",
            speakerLabel: "MASTER ALDOUS",
            voiceRoleLabel: "Character Dialogue",
            isDialogue: true,
            voiceName: "Charon",
            text: "“You have already held it to the light, and I have no objection to hearing it aloud.”",
            durationSeconds: 4.8,
          },
          {
            speaker: "Narrator",
            speakerLabel: "NARRATOR",
            voiceRoleLabel: "Literary Narration",
            isDialogue: false,
            voiceName: narratorVoice || "Kore",
            text: "This was encouragement enough.",
            durationSeconds: 2.4,
          },
        ],
      },
      {
        pageNumber: 3,
        sceneLabel: "SCENE III",
        folioLabel: "FOLIO I.3",
        chapterTitle: "CHAPTER I",
        narrativeText:
          "Before the last note of the chamber quartet had faded, the garden doors stood open to the morning.",
        illustrationPrompt: `Scene III for: ${cleanPrompt}`,
        imageCaption: "The Morning Conservatory",
        imageUrl: scene3Uri,
        dioramaUrl: scene3Uri,
        plates: [
          {
            plateNumberRoman: "III",
            plateLabel: "PLATE III OF III",
            title: "The Morning Conservatory",
            illustrationPrompt: "3D Multi-Plane Pop-Up Diorama — Scene III",
            imageUrl: scene3Uri,
          },
          {
            plateNumberRoman: "I",
            plateLabel: "CHARACTER SHEET",
            title: "Anonymous Character Reference Sheet",
            illustrationPrompt: "16:9 Character & Style Reference Sheet",
            imageUrl: charSheetUri,
          },
        ],
        dialogueLines: [
          {
            speaker: "Clara",
            speakerLabel: "CLARA",
            voiceRoleLabel: "Character Dialogue",
            isDialogue: true,
            voiceName: "Aoede",
            text: "“Every line of the riddle points toward the old conservatory beyond the orchard!”",
            durationSeconds: 5.2,
          },
          {
            speaker: "Master Aldous",
            speakerLabel: "MASTER ALDOUS",
            voiceRoleLabel: "Character Dialogue",
            isDialogue: true,
            voiceName: "Charon",
            text: "“Then fetch your cloak, my dear. It would be most impolite to keep a fairytale waiting.”",
            durationSeconds: 5.6,
          },
          {
            speaker: "Narrator",
            speakerLabel: "NARRATOR",
            voiceRoleLabel: "Literary Narration",
            isDialogue: false,
            voiceName: narratorVoice || "Kore",
            text: "And so they stepped out across the dewy terrace, while the morning sun gilded the edges of the open book.",
            durationSeconds: 7.5,
          },
        ],
      },
    ],
  };
}
