# Google AI Studio와 Gemini Managed Agent로 나만의 고전 오디오 스토리북 만들기: 5단계 자율 제작 파이프라인 완벽 가이드

> **핵심 요약 (AI Overview / AEO Snippet)**  
> 본 가이드는 **Google AI Studio**의 최신 자율 에이전트 기술인 **Gemini Managed Agent (Antigravity Preview / Gemini 4 Argon)** 및 **Gemini API CLI**를 결합하여, 텍스트 입력 한 번으로 **3D 팝업 디오라마 삽화**, **24kHz 다중 배역 성우 낭독(Multi-Voice TTS)**, **어쿠스틱 챔버 스코어(Lyria 3.5)**가 완벽히 결합된 **고전 오디오 동화책(Audio Storybook)**을 자동으로 제작하는 전 과정을 상세한 실전 코드와 함께 다룹니다.

---

## 📌 목차 (Table of Contents)
1. [프로젝트 개요: 왜 오디오 스토리북인가?](#1-프로젝트-개요-왜-오디오-스토리북인가)
2. [Google AI Studio와 Gemini Managed Agent 아키텍처](#2-google-ai-studio와-gemini-managed-agent-아키텍처)
3. [5단계 자율 제작 파이프라인 (5-Stage Autonomous Pipeline)](#3-5단계-자율-제작-파이프라인-5-stage-autonomous-pipeline)
4. [핵심 기술 구현 및 실전 코드 예시](#4-핵심-기술-구현-및-실전-코드-예시)
   - 4.1. [Gemini Flash TTS 기반 다중 배역 24kHz 음성 합성](#41-gemini-flash-tts-기반-다중-배역-24khz-음성-합성)
   - 4.2. [1810년대 리젠시 양장본 수채화 및 3D 디오라마 프롬프트 엔지니어링](#42-1810년대-리젠시-양장본-수채화-및-3d-디오라마-프롬프트-엔지니어링)
   - 4.3. [Express SSE(Server-Sent Events) 스트리밍 에이전트 프록시](#43-express-sseserver-sent-events-스트리밍-에이전트-프록시)
   - 4.4. [80ms 정밀 오디오 타임라인 동기화 및 3단계 문단 잉크 하이라이팅](#44-80ms-정밀-오디오-타임라인-동기화-및-3단계-문단-잉크-하이라이팅)
   - 4.5. [한국어/영어 완벽 다국어(i18n) 지원 구조](#45-한국어영어-완벽-다국어i18n-지원-구조)
5. [GitHub 배포 및 GitHub Pages 정적 호스팅 최적화](#5-github-배포-및-github-pages-정적-호스팅-최적화)
6. [자주 묻는 질문 (AEO / FAQ 섹션)](#6-자주-묻는-질문-aeo--faq-섹션)
7. [마무리 및 소스 코드 저장소](#7-마무리-및-소스-코드-저장소)

---

## 1. 프로젝트 개요: 왜 오디오 스토리북인가?

전통적인 전자책(e-Book)이나 단조로운 단일 성우 TTS 오디오북은 독자의 몰입감을 이끌어내는 데 한계가 있었습니다. 특히 어린이를 위한 그림 동화책이나 《오만과 편견》, 《셜록 홈즈》와 같은 고전 문학은 **화자별 개성 있는 음성 연기**, **시대적 배경을 담은 고풍스러운 삽화**, 그리고 **감정을 고조시키는 배경음악**이 결합될 때 비로소 진정한 감동을 전달합니다.

우리가 구축한 **오디오 스토리북 스튜디오 (Audio Storybooks)**는 **Google AI Studio**와 최신 **Gemini 모델 카탈로그**를 단일 오케스트레이션 엔진으로 결합하여, 사용자가 한 문장의 아이디어나 고전 소설 챕터만 입력하면 다음 요소들을 전자동으로 제작합니다:

- **1810년대 영국 양장본 책(Folio) 펼침면 UI**: #F6F2EA 크림 양지 질감과 52.917% 책등(Spine) 제본선 구현
- **다중 배역 성우 낭독 (Multi-Voice TTS)**: 해설자(Kore, Fenrir)와 인물별(Aoede, Charon, Puck 등) 개별 음성 연기
- **16:9 수채화 삽화 및 3D 팝업 디오라마**: 장인 정신이 깃든 펜화와 부드러운 수채화 워시
- **Lyria 3.5 어쿠스틱 챔버 스코어**: 첼로, 바이올린, 하프시코드 기반의 시대 맞춤형 클래식 연주곡
- **초정밀 실시간 문단 하이라이팅**: 오디오 재생 시간(ms)에 맞춰 말하고 있는 문장만 선명한 잉크(100%)로 밝혀주는 3-State 인터랙션

---

## 2. Google AI Studio와 Gemini Managed Agent 아키텍처

### 2.1. 모델 카탈로그 매핑 (Multi-Model Federation)
단일 LLM에 모든 작업을 맡기는 대신, 작업 특성에 최적화된 Gemini 모델들을 에이전트가 오케스트레이션합니다:

| 역할 (Role) | 투입 모델 (Model) | 실행 도구 및 라이브러리 | 주요 출력물 |
| :--- | :--- | :--- | :--- |
| **에이전트 총괄 오케스트레이터** | `antigravity-preview-09-2026` / `gemini-4-argon` | Gemini Managed Agent Interactions API | 가상 샌드박스 제어, 파이프라인 상태 머신 관리 |
| **작업 공간 CLI 런타임** | `gemini-api-cli` | GitHub 공식 배포 바이너리 | 샌드박스 내 파일 입출력 및 파이썬 스크립트 실행 |
| **극작 각색 및 대본 설계** | `gemini-2.5-pro` / `gemini-3.8-flash` | `@google/genai` (generateContent) | 3개 폴리오 분할, 지문 및 대사 JSON 타임라인 생성 |
| **아카이브 수채화 판화 생성** | `gemini-3.1-flash-lite-image` / Imagen 3 | Gemini Image Modality API | 16:9 규격 수채화 삽화 및 3D 디오라마 에셋 |
| **다중 배역 24kHz 음성 합성** | `gemini-3.8-flash-tts` / Gemini TTS | Gemini Audio GenAI SDK | 인물별 음색(Voice ID) 지정 24kHz 무압축 WAV |
| **클래식 배경음악 작곡** | `lyria-3.5` / Lyria Audio Engine | Lyria Music Generation Pipeline | 챕터 분위기에 맞춘 어쿠스틱 챔버 스코어 MP3 |

### 2.2. 전체 시스템 아키텍처 흐름도
```
+-------------------------------------------------------------------------+
|                              사용자 인터페이스                          |
|    - 한국어/영문 바이링구얼 전환 지원 (기본: 한국어)                    |
|    - 1810s 앤티크 양장본 펼침면 (Left: 판화 / Right: 본문 및 하이라이트) |
|    - 60fps / 80ms 오디오 타임라인 동기화 렌더러                        |
+-------------------------------------------------------------------------+
                                    │
                                    ▼ (SSE 스트리밍 요청)
+-------------------------------------------------------------------------+
|                  Express Backend API Proxy (server.ts)                  |
|    - /api/agent (Managed Agent 세션 및 SSE 이벤트 브로드캐스트)         |
|    - /api/tts (Gemini 24kHz Flash TTS 실시간 음성 합성)                |
|    - /api/environments (가상 샌드박스 파일 다운로드 및 재생성)          |
+-------------------------------------------------------------------------+
                                    │
                                    ▼ (Google AI Studio Interactions API)
+-------------------------------------------------------------------------+
|                 Gemini Managed Agent (Antigravity Sandbox)               |
|  [STAGE 1] 컨테이너 샌드박스 프로비저닝 & gemini-api-cli 설치           |
|  [STAGE 2] dramaturgy-spec: 소설 원작 텍스트 분석 및 3개 폴리오 각색    |
|  [STAGE 3] illustration-generation: 16:9 수채화 판화 3점 & 디오라마 각인|
|  [STAGE 4] multi-voice-tts: 인물별 음성 매칭 및 24kHz 보컬 마스터링    |
|  [STAGE 5] lyria-chamber-score: 어쿠스틱 챔버 스코어 작곡 및 바인딩     |
+-------------------------------------------------------------------------+
```

---

## 3. 5단계 자율 제작 파이프라인 (5-Stage Autonomous Pipeline)

Gemini Managed Agent가 동작하는 표준 5단계 라이프사이클은 다음과 같습니다:

1. **STAGE I · 샌드박스 환경 프로비저닝 (Sandbox & CLI Setup)**  
   - 전용 가상 컨테이너가 시작되고 최신 `gemini-api-cli` 도구가 설치됩니다.
   - 사전 등록된 도메인 스킬(`dramaturgy-spec`, `tts-generation`, `music-generation`)이 인라인 소스로 워크스페이스에 마운트됩니다.

2. **STAGE II · 극작 각색 및 폴리오 명세서 (Dramaturgy & Folio Spec)**  
   - 입력된 줄거리나 고전 챕터를 분석하여 정확히 **3개의 연속된 펼침면(Folio)**으로 구조화합니다.
   - 화자(Speaker), 대사(Dialogue) 여부, 시대상에 어울리는 감정 톤 및 예상 발화 시간(Duration)을 산출합니다.

3. **STAGE III · 아카이브 16:9 판화 및 팝업 디오라마 채색 (Archival Plates & Diorama)**  
   - 등장인물 레퍼런스 시트(Character Sheet)를 먼저 렌더링하여 인물들의 외모 일관성을 유지합니다.
   - 배경 색상(#F6F2EA 크림지)과 세피아 딥펜 라인, 세이지 그린 워시가 조화를 이루는 고품격 16:9 삽화 3점을 생성합니다.

4. **STAGE IV · 다중 음성 보컬 낭독 합성 (Multi-Voice Performance)**  
   - 여성 해설자 `Kore`, 중후한 남성 노신사 `Charon`, 장난기 어린 소년 `Puck`, 생동감 넘치는 여주인공 `Aoede` 등의 음성 프리셋을 캐릭터별로 자동 매핑합니다.
   - 문장 간 자연스러운 호흡(0.36초~0.48초)과 문맥상 쉼표를 고려하여 24kHz WAV로 합성 및 믹싱합니다.

5. **STAGE V · 챔버 스코어 작곡 및 최종 제본 (Chamber Score & Binding)**  
   - 이야기의 분위기(Regency Social Satire, Victorian Mystery, Celestial Fable 등)에 최적화된 어쿠스틱 현악 챔버곡을 작곡합니다.
   - 오디오 타임라인 매니페스트(`startSec`, `endSec`)와 결합하여 웹 브라우저에서 바로 열람할 수 있는 완성된 스토리북으로 제본(Binding)합니다.

---

## 4. 핵심 기술 구현 및 실전 코드 예시

### 4.1. Gemini Flash TTS 기반 다중 배역 24kHz 음성 합성

Google GenAI SDK(`@google/genai`)를 활용하여 각 대사별 화자의 성격에 맞는 보이스를 호출하고 브라우저에서 재생 가능한 무압축 PCM 24kHz WAV 포맷으로 변환하는 코드입니다:

```typescript
// src/services/storybookAgentService.ts (발췌)
import { GoogleGenAI } from "@google/genai";
import { DialogueLine } from "../types";

/**
 * 24kHz 16-bit Mono PCM raw 바이트를 표준 브라우저 지원 WAV 포맷으로 패키징하는 헬퍼 함수
 */
function createWavBlobFromPcm16(pcmBytes: Uint8Array, sampleRate: number = 24000): Blob {
  const wavHeader = new ArrayBuffer(44);
  const view = new DataView(wavHeader);
  const totalDataLen = pcmBytes.length;

  // RIFF 청크 헤더
  view.setUint32(0, 0x52494646, false); // "RIFF"
  view.setUint32(4, 36 + totalDataLen, true);
  view.setUint32(8, 0x57415645, false); // "WAVE"

  // fmt 하위 청크
  view.setUint32(12, 0x666d7420, false); // "fmt "
  view.setUint32(16, 16, true);          // 하위 청크 크기 (16)
  view.setUint16(20, 1, true);           // PCM 오디오 포맷
  view.setUint16(22, 1, true);           // 모노 채널 (1)
  view.setUint32(24, sampleRate, true);  // 샘플 레이트 (24000 Hz)
  view.setUint32(28, sampleRate * 2, true); // 바이트 레이트 (SampleRate * 2 bytes)
  view.setUint16(32, 2, true);           // 블록 정렬 (16-bit Mono = 2)
  view.setUint16(34, 16, true);          // 샘플당 비트 수 (16)

  // data 하위 청크
  view.setUint32(36, 0x64617461, false); // "data"
  view.setUint32(40, totalDataLen, true);

  return new Blob([wavHeader, pcmBytes], { type: "audio/wav" });
}

/**
 * 페이지 내 다중 대사를 인물별 음성으로 Gemini Flash TTS를 호출하여 합성
 */
export async function synthesizeStudioPageAudio(
  lines: DialogueLine[],
  fallbackText: string,
  narratorVoice: string = "Kore"
): Promise<string> {
  const ai = new GoogleGenAI();
  const chunks: Uint8Array[] = [];

  for (const line of lines) {
    const textToSpeak = line.ttsText || line.text;
    const selectedVoice = line.voiceName || narratorVoice || "Kore";

    // Gemini 2.5 Flash Audio 합성 요청
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: [{ role: "user", parts: [{ text: textToSpeak }] }],
      config: {
        responseModalities: ["AUDIO"],
        speechConfig: {
          voiceConfig: {
            prebuiltVoiceConfig: { voiceName: selectedVoice }
          }
        }
      }
    });

    const candidate = response.candidates?.[0];
    const audioPart = candidate?.content?.parts?.find(p => p.inlineData?.mimeType?.startsWith("audio/"));
    if (audioPart?.inlineData?.data) {
      const binaryString = atob(audioPart.inlineData.data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      chunks.push(bytes);
    }
  }

  // 전체 오디오 청크 병합 후 WAV 데이터 URI 반환
  const totalLength = chunks.reduce((acc, c) => acc + c.length, 0);
  const combined = new Uint8Array(totalLength);
  let offset = 0;
  for (const chunk of chunks) {
    combined.set(chunk, offset);
    offset += chunk.length;
  }

  const wavBlob = createWavBlobFromPcm16(combined, 24000);
  return URL.createObjectURL(wavBlob);
}
```

---

### 4.2. 1810년대 리젠시 양장본 수채화 및 3D 디오라마 프롬프트 엔지니어링

AI 생성 이미지가 현대풍 디지털 일러스트로 변질(AI Slop)되는 것을 방지하기 위해 엄격한 **네거티브 제약(Negative Constraints)**과 **역사적 화풍 앵커링(Historical Anchoring)**을 프롬프트에 주입합니다:

```typescript
// 화풍 템플릿 프롬프트 정의
export const REGENCY_WATERCOLOUR_PROMPT_TEMPLATE = (sceneDescription: string) => `
1810s Regency fine dip-pen sepia ink line drawing with delicate muted watercolour wash
(sage green, warm ochre, dusty rose, and sepia ink) on warm cream archival rag paper (#F6F2EA).
Historical period setting, authentic Regency garments, generous negative space, hand-coloured book illustration.

Scene details: ${sceneDescription}

Strict aesthetic guidelines:
- No glossy 3D renders, no modern anime, no hyper-saturated digital gradients.
- Fine-press book illustration inspired by Arthur Rackham and Hugh Thomson.
- Visible archival paper grain texture (#F6F2EA warm cream background).
- 16:9 cinematic aspect ratio stage box framing.
`.trim();
```

---

### 4.3. Express SSE(Server-Sent Events) 스트리밍 에이전트 프록시

클라이언트와 AI Studio 간의 실시간 진행 상황(로그, 파이프라인 단계, 코드 실행 결과)을 유실 없이 전달하기 위해 Server-Sent Events(SSE) 파이프라인을 구축했습니다:

```typescript
// server.ts (발췌)
app.post("/api/agent", async (req, res) => {
  // SSE 응답 헤더 설정
  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
  });

  const sendEvent = (event: string, data: any) => {
    res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
  };

  const sessionId = req.body.sessionId || `sess_${Date.now()}`;
  const abortController = new AbortController();
  activeInteractions.set(sessionId, abortController);

  try {
    sendEvent("stage", { stageIdx: 0, label: "가상 샌드박스 프로비저닝 중…" });

    // Google AI Studio Managed Agent 인터랙션 생성
    const interaction = await createInteraction({
      agent: "antigravity-preview-09-2026",
      model: "gemini-4-argon",
      input: req.body.prompt,
      signal: abortController.signal
    });

    sendEvent("created", { id: interaction.id, envId: interaction.environmentId });

    // 에이전트 터미널 실행 로그 실시간 스트리밍
    for await (const chunk of streamInteraction(interaction.id)) {
      if (chunk.logEntry) {
        sendEvent("log", chunk.logEntry);
      }
      if (chunk.stageUpdate) {
        sendEvent("stage", chunk.stageUpdate);
      }
    }

    sendEvent("done", { success: true });
  } catch (err: any) {
    sendEvent("error", { message: err?.message || "에이전트 실행 실패" });
  } finally {
    activeInteractions.delete(sessionId);
    res.end();
  }
});
```

---

### 4.4. 80ms 정밀 오디오 타임라인 동기화 및 3단계 문단 잉크 하이라이팅

비디오나 오디오 재생 시 현재 낭독 중인 문장만 100% 잉크로 강조하고, 이미 읽은 문장은 50%, 아직 읽지 않은 문장은 38% 투명도로 처리하여 독서의 시각적 리듬을 살립니다:

```typescript
// src/App.tsx 80ms 렌더 루프 및 상태 계산 로직
useEffect(() => {
  if (!isPlayingAudio || viewMode !== "reader") return;

  const intervalId = setInterval(() => {
    const masterEl = getMasterAudioEl();
    const tSec = masterEl && !masterEl.paused ? masterEl.currentTime : virtualClockRef.current;
    setPlaybackTimeSec(tSec);

    // 현재 재생 시각(tSec)에 해당하는 대사 라인(idx) 탐색
    const lines = currentPage?.dialogueLines || [];
    let currentLineIdx = -1;

    for (let idx = 0; idx < lines.length; idx++) {
      const line = lines[idx];
      if (tSec >= line.startSec! && tSec <= line.endSec!) {
        currentLineIdx = idx;
        break;
      }
    }
    setActiveLineIdx(currentLineIdx);
  }, 80);

  return () => clearInterval(intervalId);
}, [isPlayingAudio, viewMode, currentPage]);
```

**CSS 문단 3-상태 스타일링:**
```css
/* 읽기 전 문장: 흐릿한 38% 아카이브 잉크 */
.austen-turn-block.state-future {
  opacity: 0.38;
  transition: opacity 0.35s ease;
}

/* 현재 낭독 중인 문장: 선명한 100% 잉크 및 세이지 그린 화자 루브릭 */
.austen-turn-block.state-active {
  opacity: 1.0;
  transform: translateX(4px);
  transition: all 0.25s ease-out;
}

/* 이미 읽은 문장: 차분한 50% 잉크 */
.austen-turn-block.state-past {
  opacity: 0.52;
  transition: opacity 0.35s ease;
}
```

---

### 4.5. 한국어/영어 완벽 다국어(i18n) 지원 구조

국내 사용자를 위해 **기본 언어를 한국어(`ko`)**로 설정하고, 앤티크 양장본 헤더 바에서 클릭 한 번으로 영문(`en`)과 한국어를 전환할 수 있는 번역 시스템(`src/data/translations.ts`)을 통합했습니다.

- 고전 도서 제목 한국어 현지화:
  - 《오만과 편견》 (제인 오스틴, 1813년)
  - 《바스커빌 가문의 개》 (아서 코난 도일, 1902년)
  - 《이상한 나라의 앨리스》 (루이스 캐럴, 1865년)
  - 《타임머신》 (H. G. 웰스, 1895년)
  - 《톰 소여의 모험》 (마크 트웨인, 1876년)
- 동화 의뢰 프리셋 한국어 제공:
  - 《시계 장인의 유리 꾀꼬리》 (1815년 제네바 호숫가의 리젠시 동화)
  - 《속삭이는 늪지의 등대지기》 (빅토리아 시대 황야의 전설)
  - 《종이 천문학자의 계단》 (세 개의 폴리오로 펼쳐지는 천체 우화)
  - 《찔레나무 울타리 우체국》 (목가적인 숲속 동화)

---

## 5. GitHub 배포 및 GitHub Pages 정적 호스팅 최적화

GitHub Pages는 저장소 하위 경로(예: `/Audio_Storybook/`)에 배포되므로, Vite 빌드 시 번들 파일 링크가 깨지지 않도록 상대 경로(`base: './'`) 설정이 필수적입니다.

### 5.1. Vite 상대 경로 설정 (`vite.config.ts`)
```typescript
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  base: './', // 상대 경로로 설정하여 GitHub Pages 서브디렉터리 404 완벽 방지
  plugins: [react(), tailwindcss()],
});
```

### 5.2. 자동 배포 GitHub Actions 워크플로우 (`.github/workflows/deploy.yml`)
`main` 브랜치에 코드가 푸시될 때마다 GitHub Pages에 자동으로 무중단 배포됩니다:
```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: write
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install dependencies
        run: npm ci || npm install

      - name: Build project
        run: npm run build

      - name: Setup Pages
        uses: actions/configure-pages@v5

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: './dist'

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

---

## 6. 자주 묻는 질문 (AEO / FAQ 섹션)

### Q1. Google AI Studio의 Managed Agent란 무엇인가요?
> **A:** Gemini Managed Agent는 단순한 단답형 LLM 호출이 아닌, 전용 가상 샌드박스 컨테이너 내에서 **파일 생성, CLI 툴 실행, 다단계 태스크 계획 및 복구**를 자율적으로 수행하는 차세대 에이전트 런타임입니다. 본 프로젝트에서는 `gemini-4-argon` 오케스트레이터가 대본 작성부터 삽화, 음성, 음악 합성까지의 전 파이프라인을 관리합니다.

### Q2. 제작된 오디오북의 음성 품질과 지연 시간은 어느 정도인가요?
> **A:** Gemini 2.5/3.8 Flash Audio 모델을 통해 **24kHz 무압축 Studio급 WAV**로 합성되며, 문장당 평균 1초 내외의 빠른 레이턴시로 생성됩니다. 3개 폴리오 분량의 챕터 전체 마스터링에는 약 10~20초가 소요됩니다.

### Q3. GitHub Pages와 같은 완전한 정적 호스팅 환경에서도 실행되나요?
> **A:** 네! 서버 백엔드 연결이 어려운 정적 호스팅 환경에서는 클라이언트 측 `@google/genai` 브라우저 SDK 및 Web Speech API, 사전 생성된 클래식 라이브러리(오만과 편견, 셜록 홈즈 등)의 고음질 마스터 음원이 즉시 동작하도록 지능형 폴백(Fallback) 구조가 구현되어 있습니다.

### Q4. 상업적 이용 및 라이선스는 어떻게 되나요?
> **A:** 본 프로젝트에 수록된 고전 작품들은 프로젝트 구텐베르크(Project Gutenberg)의 퍼블릭 도메인 원작에 기반하며, Gemini 모델이 생성한 에셋은 Google Cloud 및 AI Studio의 이용 약관을 준수합니다.

---

## 7. 마무리 및 소스 코드 저장소

Google AI Studio와 Gemini 생태계는 멀티모달 생성 기술을 개별 API 호출 수준에서 **완전 자율형 멀티 에이전트 파이프라인**으로 혁신하고 있습니다. 단순한 텍스트 챗봇을 넘어, 시각과 청각, 문학적 서사가 융합된 나만의 고전 오디오북 스튜디오를 직접 경험해보세요!

- 🌐 **GitHub Pages 실시간 라이브 데모**: [https://djai32521.github.io/Audio_Storybook/](https://djai32521.github.io/Audio_Storybook/)
- 💻 **GitHub 오픈소스 저장소**: [https://github.com/djai32521/Audio_Storybook](https://github.com/djai32521/Audio_Storybook)

---
*Tags: #GoogleAIStudio #Gemini #ManagedAgent #GeminiAPI #오디오북 #AI스토리북 #AEO #GEO #SEO #React #TypeScript #WebAudio #TTS*
