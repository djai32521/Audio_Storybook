export type Language = "ko" | "en";

export interface I18nText {
  pressName: string;
  era: string;
  tagline: string;
  mainTitle: string;
  subBadge: string;
  heroSubtitle: string;
  contentsRubric: string;
  footerLeft: string;
  footerRight: string;
  commissionHeader: string;
  commissionChapter: string;
  authorSpeaker: string;
  authorRole: string;
  inscription: string;
  inscriptionPlaceholder: string;
  presetRubric: string;
  folioBinding: string;
  illustrationStyle: string;
  narratorVoice: string;
  apiKeyLabel: string;
  apiKeyPlaceholder: string;
  commissionBtn: string;
  commissionSub: string;
  cancelBtn: string;
  terminalLogs: string;
  play: string;
  pause: string;
  prevTurn: string;
  nextTurn: string;
  cyclePlate: string;
  repaint: string;
  synthWav: string;
  titleCard: string;
  agentSpec: string;
  closeBook: string;
  shortcuts: string;
  narrationProse: string;
  characterDialogue: string;
  musicEnabled: string;
  musicMuted: string;
  plate: string;
  of: string;
  craftingTitle: string;
  craftingSubtitle: string;
  modalClose: string;
  agentSpecTitle: string;
  agentSpecSubtitle: string;
  pipelineStagesTitle: string;
}

export const TRANSLATIONS: Record<Language, I18nText> = {
  ko: {
    pressName: "더 폴리오 & 보이스 프레스",
    era: "2026년 (MMXXVI)",
    tagline: "일러스트 오디오북 서재",
    mainTitle: "오디오 스토리북",
    subBadge: "일러스트 · 보이스 · 챔버 스코어 · GEMINI",
    heroSubtitle: "다섯 권의 고전 양장본, 그리고 당신을 위한 여섯 번째 빈 서책",
    contentsRubric: "목차 — 도서를 클릭하면 열람 및 오디오 낭독이 시작됩니다",
    footerLeft: "제I권 – 제V권",
    footerRight: "클래식 오디오북 서재",
    commissionHeader: "제VI권 · 새로운 의뢰",
    commissionChapter: "제I장",
    authorSpeaker: "원작자",
    authorRole: "  — 당신만의 의뢰서 작성",
    inscription: "원고 및 줄거리 입력 (INSCRIPTION)",
    inscriptionPlaceholder: "Gemini 에이전트가 삽화, 다중 음성 낭독, 챔버 음악을 창작할 동화 줄거리나 고전 문학 챕터를 입력하세요…",
    presetRubric: "추천 동화 프리셋 선택 (SELECT A FAIRYTALE PRESET)",
    folioBinding: "장본 판형 및 색상 테마 (FOLIO BINDING)",
    illustrationStyle: "삽화 화풍 (ILLUSTRATION STYLE)",
    narratorVoice: "대표 낭독자 음성 (NARRATOR VOICE)",
    apiKeyLabel: "GEMINI API 키 (선택 사항 — 직접 키 입력 시 우선 적용)",
    apiKeyPlaceholder: "AI Studio API 키 입력 (미입력 시 내장 환경 키 자동 사용)",
    commissionBtn: "제VI권 양장본 제작 의뢰하기",
    commissionSub: "Gemini 4 Argon & API CLI 기반 자율 제작 파이프라인 가동",
    cancelBtn: "제작 취소 후 목차로 돌아가기",
    terminalLogs: "에이전트 터미널 실행 로그",
    play: "낭독 재생",
    pause: "일시정지",
    prevTurn: "이전 문장",
    nextTurn: "다음 문장",
    cyclePlate: "삽화 전환",
    repaint: "판화 재각인",
    synthWav: "24kHz 음성 재합성",
    titleCard: "표제지",
    agentSpec: "에이전트 명세서",
    closeBook: "책 덮기",
    shortcuts: "단축키: [스페이스] 재생/정지 · [←/→] 문장 이동 · [P] 삽화 전환 · [ESC] 책 덮기",
    narrationProse: "해설 낭독",
    characterDialogue: "등장인물 대사",
    musicEnabled: "배경음악 켜짐",
    musicMuted: "배경음악 꺼짐",
    plate: "판화",
    of: "/",
    craftingTitle: "에이전트가 서책을 장본하고 있습니다",
    craftingSubtitle: "문학 각색, 1810년대 수채화 판화, 다중 음성 낭독, 챔버 스코어를 실시간으로 합성합니다",
    modalClose: "닫기 (ESC)",
    agentSpecTitle: "제미나이 매니지드 에이전트 아키텍처 명세서",
    agentSpecSubtitle: "Google Gemini 모델 카탈로그와 Gemini API CLI 기반의 자율 창작 시스템",
    pipelineStagesTitle: "에이전트 5단계 파이프라인 진행 상태",
  },
  en: {
    pressName: "THE FOLIO & VOICE PRESS",
    era: "MMXXVI",
    tagline: "AN ILLUSTRATED AUDIOBOOK LIBRARY",
    mainTitle: "Audio Storybooks",
    subBadge: "ILLUSTRATED · VOICED · SCORED · GEMINI",
    heroSubtitle: "Five volumes bound, and a sixth left blank for you",
    contentsRubric: "CONTENTS — CLICK ANY VOLUME TO OPEN & AUTO-NARRATE",
    footerLeft: "VOLUMES I – V",
    footerRight: "THE CLASSIC LIBRARY",
    commissionHeader: "BOOK VI · A NEW COMMISSION",
    commissionChapter: "CHAPTER I",
    authorSpeaker: "THE AUTHOR",
    authorRole: "  — Your Commission",
    inscription: "INSCRIPTION",
    inscriptionPlaceholder: "Inscribe a fairytale, characters, or literary chapter for the Gemini Managed Agent to illustrate, voice, and score…",
    presetRubric: "OR CHOOSE A FAIRYTALE PRESET",
    folioBinding: "FOLIO BINDING",
    illustrationStyle: "ILLUSTRATION STYLE",
    narratorVoice: "NARRATOR VOICE",
    apiKeyLabel: "GEMINI API KEY (OPTIONAL)",
    apiKeyPlaceholder: "AI Studio API key (falls back to built-in environment key)",
    commissionBtn: "COMMISSION FOLIO EDITION",
    commissionSub: "Spawns autonomous pipeline across Gemini model catalog",
    cancelBtn: "Cancel & Return to Contents",
    terminalLogs: "AGENT TERMINAL LOGS",
    play: "PLAY",
    pause: "PAUSE",
    prevTurn: "PREV TURN",
    nextTurn: "NEXT TURN",
    cyclePlate: "CYCLE PLATE",
    repaint: "REPAINT",
    synthWav: "SYNTHESIZE TTS",
    titleCard: "TITLE CARD",
    agentSpec: "AGENT SPEC",
    closeBook: "CLOSE BOOK",
    shortcuts: "[SPACE] Play/Pause · [←/→] Seek Turns · [P] Cycle Plates · [ESC] Close Book",
    narrationProse: "Literary Narration",
    characterDialogue: "Character Dialogue",
    musicEnabled: "Music On",
    musicMuted: "Music Muted",
    plate: "PLATE",
    of: "OF",
    craftingTitle: "The Managed Agent is Binding Your Edition",
    craftingSubtitle: "Generating dramaturgical folios, 1810s watercolour plates, multi-voice dialogue, and Lyria chamber score in real-time.",
    modalClose: "Close (ESC)",
    agentSpecTitle: "GEMINI MANAGED AGENT ARCHITECTURE",
    agentSpecSubtitle: "Autonomous fine-press publishing across the Gemini model catalog and Gemini API CLI",
    pipelineStagesTitle: "Managed Agent Pipeline Stages",
  },
};

export interface KoreanBookMeta {
  title: string;
  author: string;
  genre: string;
  setting: string;
  tagline: string;
}

export const KOREAN_BOOK_METAS: Record<string, KoreanBookMeta> = {
  "01_pride_and_prejudice": {
    title: "오만과 편견",
    author: "제인 오스틴",
    genre: "리젠시 시대 풍자극",
    setting: "롱본, 하트퍼드셔",
    tagline: "제I권 · 제1장 — 롱본, 하트퍼드셔",
  },
  "02_hound_of_the_baskervilles": {
    title: "바스커빌 가문의 개",
    author: "아서 코난 도일",
    genre: "빅토리아 추리 스릴러",
    setting: "런던 베이커가 221B",
    tagline: "제II권 · 제1장 — 런던 베이커가 221B",
  },
  "03_alice_in_wonderland": {
    title: "이상한 나라의 앨리스",
    author: "루이스 캐럴",
    genre: "빅토리아 판타지 우화",
    setting: "토끼 굴 밑",
    tagline: "제III권 · 제1장 — 토끼 굴 속으로",
  },
  "04_the_time_machine": {
    title: "타임머신",
    author: "H. G. 웰스",
    genre: "에드워드 초기 SF",
    setting: "런던 리치먼드",
    tagline: "제IV권 · 제1장 — 시간 여행자의 흡연실",
  },
  "05_tom_sawyer": {
    title: "톰 소여의 모험",
    author: "마크 트웨인",
    genre: "미국 목가적 모험담",
    setting: "미주리주 세인트피터즈버그",
    tagline: "제V권 · 제1장 — 미주리주 세인트피터즈버그",
  },
};

export const KOREAN_FAIRYTALE_PROMPTS = [
  {
    id: "clockwork-nightingale",
    title: "시계 장인의 유리 꾀꼬리",
    subtitle: "1815년 제네바 호숫가의 리젠시 동화",
    prompt:
      "1815년 제네바 호숫가의 고요한 시계 공방에서, 조용한 시계공의 딸이 골동품 오르골 안에 숨겨진 정교한 유리 세공 꾀꼬리를 발견합니다. 새벽에 태엽을 감으면 새는 눈 덮인 산 아래 잠긴 겨울 정원에 관한 수수께끼 노래를 부릅니다.",
  },
  {
    id: "lantern-of-the-moors",
    title: "속삭이는 늪지의 등대지기",
    subtitle: "빅토리아 시대 황야의 전설",
    prompt:
      "안개 낀 가을 저녁, 속삭이는 늪지의 돌둑길에서 노년의 등대지기와 젊은 식물학자가 잊혀진 도서관을 가리키는 황동 나침반을 든 예의 바른 여우를 마주칩니다.",
  },
  {
    id: "paper-astronomer",
    title: "종이 천문학자의 계단",
    subtitle: "세 개의 폴리오로 펼쳐지는 천체 우화",
    prompt:
      "오래된 풍차 안 촛불 켜진 천문대에서 천문학자가 종이로 별자리를 접습니다. 종이 별자리는 덧창을 빠져나와 날아가며 달이 뜰 적절한 시각을 두고 북풍과 온화하게 논쟁합니다.",
  },
  {
    id: "bramble-post-office",
    title: "찔레나무 울타리 우체국",
    subtitle: "목가적인 숲속 동화",
    prompt:
      "오래된 산사나무 울타리 뿌리 아래에서 부지런한 겨울잠쥐 우체국장과 황토색 리넨 앞치마를 두른 소녀가 사계절에게 보낼 연체 편지들을 정성스레 분류합니다.",
  },
];

export const KOREAN_PIPELINE_STAGES = [
  {
    index: 0,
    code: "제I단계 · 샌드박스 및 GEMINI-API-CLI",
    title:
      "Gemini Managed Agent 가상 샌드박스를 프로비저닝하고 작업 공간에 최신 gemini-api-cli 도구를 설치합니다.",
  },
  {
    index: 1,
    code: "제II단계 · 극작 및 폴리오 스펙",
    title:
      "원작 텍스트를 인물별 대사와 지문으로 구성된 3개 폴리오로 분할 각색하고 시대적 인물 묘사를 설계합니다.",
  },
  {
    index: 2,
    code: "제III단계 · 아카이브 판화 및 팝업 디오라마",
    title:
      "16:9 등장인물 레퍼런스 시트와 #F6F2EA 크림 양지 위에 3개의 1810년대 펜화 수채화 판화를 채색합니다.",
  },
  {
    index: 3,
    code: "제IV단계 · 다중 음성 보컬 낭독",
    title:
      "자연스러운 호흡과 룸 톤을 반영하여 인물별 24kHz 고음질 음성 및 낭독을 합성하고 마스터링합니다.",
  },
  {
    index: 4,
    code: "제V단계 · 챔버 스코어 작곡 및 제본",
    title:
      "Lyria 3.5 어쿠스틱 챔버 스코어를 작곡하고 3개의 폴리오를 완성된 펼침면으로 제본합니다.",
  },
];
