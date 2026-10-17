#!/usr/bin/env python3
"""Generate the Character & Style Reference Sheet and 16 Scene Plates for
Voltaire's Candide (Chapters I-XII, Pages 1-53) using Nano Banana 2 Lite
(gemini-3.1-flash-lite-image).
"""

import base64
import concurrent.futures
import json
import os
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ILLUST_DIR = ROOT / "illustrations"
MODEL = "gemini-3.1-flash-lite-image"

STYLE_HEADER = (
    "18th-century French Rococo copperplate book-plate engraving and fine sepia-and-black"
    " quill ink etching with delicate, restrained hand-tinted watercolour wash (in the"
    " authentic 1778 fine-press style of Jean-Michel Moreau le Jeune and Charles Eisen)"
    " on warm cream laid cotton paper (#F6F1E6). Clean, uncluttered composition with"
    " generous open paper breathing room around the subjects. STRICTLY NO TEXT, NO"
    " LETTERS, NO CAPTIONS, NO NUMBERS, NO BORDERS, NO FRAMES inside the illustration."
)

CHAR_SHEET_PROMPT = (
    f"{STYLE_HEADER} A horizontal 16:9 four-character turn-around reference sheet standing"
    " side by side on a clean warm cream paper background: "
    "(1) Far left: CANDIDE, an earnest, open-faced young man of twenty with wide innocent"
    " eyes, powdered hair tied with a black ribbon at the nape, wearing an 18th-century"
    " sky-blue wool frock coat, cream waistcoat, buff knee breeches, white stockings, and"
    " buckled shoes. "
    "(2) Center-left: DOCTOR PANGLOSS, a tall, thin, pedantic 18th-century philosopher in"
    " his sixties with a long aquiline nose, small round spectacles, a curled white"
    " powdered periwig, and a deep burgundy velvet academic frock coat over a dark"
    " waistcoat, raising one index finger in a philosophical lecture gesture. "
    "(3) Center-right: LADY CUNÉGONDE, a graceful, rosy-cheeked young noblewoman of"
    " seventeen with dark chestnut curls, wearing an 18th-century warm rose-and-ochre"
    " silk gown with lace-trimmed sleeves. "
    "(4) Far right: THE OLD WOMAN (La Vieille), a weathered, sharp-eyed elderly woman in"
    " her seventies with a dignified posture, wearing a dark slate hooded shawl over an"
    " ochre and russet linen skirt, holding a walking staff. No text or labels anywhere."
)

SCENE_PROMPTS = {
    # Part 1: Chapters I-III (Westphalia, the Bulgarians, and Holland)
    "06_candide_p1_scene_1.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. In the sunlit stone hall of the Castle of Thunder-ten-Tronckh,"
        " DOCTOR PANGLOSS (in his burgundy academic coat, spectacles, and white periwig,"
        " raising one finger in a philosophical lecture) instructs young CANDIDE (in his"
        " sky-blue frock coat, listening with wide-eyed earnest attention) while young"
        " LADY CUNÉGONDE (in her rose-and-ochre silk gown) watches demurely nearby."
        " Minimal architectural background, no text."
    ),
    "06_candide_p1_scene_2.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. Young CANDIDE (in his sky-blue frock coat) and LADY CUNÉGONDE"
        " (in her rose-and-ochre silk gown) lean toward each other in tender innocent"
        " affection beside a tall painted 18th-century folding screen in the castle"
        " drawing room, as Cunégonde drops her lace handkerchief. Clean warm cream paper"
        " background, no text."
    ),
    "06_candide_p1_scene_3.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. Inside a snow-lit 18th-century German tavern, young CANDIDE"
        " (in his sky-blue frock coat) sits at a wooden table raising a pewter tankard"
        " as two tall recruiting soldiers in Prussian-blue 18th-century military coats"
        " and tall mitre caps toast him with tankards. Clean minimal background, no text."
    ),
    "06_candide_p1_scene_4.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. Along a quiet Dutch canal in Holland, a kind, soberly dressed"
        " Anabaptist merchant in a broad-brimmed black hat and dark brown coat extends a"
        " loaf of bread and a welcoming hand to travel-worn young CANDIDE (in his worn"
        " sky-blue frock coat). Clean minimal background, no text."
    ),
    # Part 2: Chapters IV-VI (Pangloss Found, Tempest, Lisbon Earthquake & Auto-da-fé)
    "06_candide_p2_scene_1.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. Outside a quiet Dutch stable, young CANDIDE (in his sky-blue"
        " frock coat) clasps the hands of a tattered, dishevelled DOCTOR PANGLOSS (in a"
        " worn burgundy coat and askew periwig, leaning on a wooden crutch) in shocked"
        " recognition and compassion. Clean minimal background, no text."
    ),
    "06_candide_p2_scene_2.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. An 18th-century three-masted wooden sailing ship with reefed"
        " canvas sails pitches on dark ink-crosshatched storm waves off the rocky coast"
        " of Lisbon under dramatic engraved storm clouds, while CANDIDE and DOCTOR"
        " PANGLOSS cling to the wooden rail on deck. Clean copperplate etching style, no text."
    ),
    "06_candide_p2_scene_3.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. Amid fallen classical stone blocks and rising dust of the 1755"
        " Lisbon earthquake, young CANDIDE (in his dusty sky-blue coat) sits propped"
        " against a stone step while DOCTOR PANGLOSS (in his burgundy coat and periwig)"
        " gestures grandly as he lectures on sufficient reason, holding a small jug of"
        " water. Minimal background, no text."
    ),
    "06_candide_p2_scene_4.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. In a stone courtyard in Lisbon after the Auto-da-fé, young"
        " CANDIDE (wearing a loose sleeveless tunic painted with decorative flames over"
        " his shirt) stands bewildered and sorrowful as THE OLD WOMAN (in her dark slate"
        " hooded shawl and ochre skirt, leaning on her staff) approaches him gently and"
        " beckons him to follow her. Minimal background, no text."
    ),
    # Part 3: Chapters VII-X (Reunion with Cunégonde, The Duel, and Flight to Cadiz)
    "06_candide_p3_scene_1.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. Inside a candlelit Portuguese country salon, young CANDIDE"
        " (in his sky-blue frock coat) gently lifts a translucent silk veil from the face"
        " of LADY CUNÉGONDE (in her rose-and-gold silk gown) in joyful astonishment,"
        " while THE OLD WOMAN (in her dark hooded shawl) watches beside a gilded sofa."
        " Clean minimal background, no text."
    ),
    "06_candide_p3_scene_2.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. Seated together on an 18th-century carved wooden settee"
        " beside a silver candelabrum, LADY CUNÉGONDE (in her rose-and-ochre silk gown)"
        " gestures expressively as she recounts her dramatic story to anspellbound"
        " CANDIDE (in his sky-blue frock coat). Clean warm cream paper background, no text."
    ),
    "06_candide_p3_scene_3.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. In the Lisbon apartment, young CANDIDE (in his sky-blue frock"
        " coat) stands holding a slender 18th-century steel rapier at his side with"
        " startled resolve, while LADY CUNÉGONDE clasps her hands in alarm and THE OLD"
        " WOMAN (in her dark hooded shawl) points urgently toward the door advising"
        " immediate flight. Clean minimal background, no text."
    ),
    "06_candide_p3_scene_4.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. Riding along a winding mountain path through the Sierra Morena"
        " toward Cadiz, young CANDIDE (in his sky-blue frock coat and tricorn hat) rides"
        " an Andalusian horse beside LADY CUNÉGONDE (in her rose gown and riding cloak)"
        " and THE OLD WOMAN (in her dark hooded shawl). Clean copperplate etching, no text."
    ),
    # Part 4: Chapters XI-XII (The History and Adventures of the Old Woman at Sea)
    "06_candide_p4_scene_1.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. On the sunlit wooden quarterdeck of an 18th-century Spanish"
        " sailing ship at sea with rigging and calm ocean waves behind them, THE OLD"
        " WOMAN (in her dark slate hooded shawl and ochre skirt) sits on a wooden sea"
        " chest recounting her life story to CANDIDE (in his sky-blue coat) and LADY"
        " CUNÉGONDE (in her rose gown). Clean minimal background, no text."
    ),
    "06_candide_p4_scene_2.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. An 18th-century Mediterranean coastal vista showing a"
        " lateen-sailed galley on sparkling blue-tinted engraved waves off the Italian"
        " coast of Gaeta, with classical palace arches on a distant sunlit headland."
        " Clean copperplate etching with delicate watercolour wash, no text."
    ),
    "06_candide_p4_scene_3.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. Beneath a grove of Mediterranean orange trees beside a small"
        " running brook, a young Italian noblewoman in torn 18th-century silk robes"
        " converses in astonishment with a Neapolitan courtier in a white linen coat."
        " Clean 18th-century copperplate etching and watercolour wash, no text."
    ),
    "06_candide_p4_scene_4.jpg": (
        f"{STYLE_HEADER} Match the exact character appearances and art style from the"
        " reference image. Standing together at the carved wooden rail of the sailing"
        " ship bound for Buenos Aires under a calm sunset sky, THE OLD WOMAN (in her"
        " dark hooded shawl) speaks with dry philosophical wisdom to CANDIDE (in his"
        " sky-blue frock coat) and LADY CUNÉGONDE (in her rose silk gown) as they gaze"
        " toward the horizon. Clean copperplate etching, no text."
    ),
}


def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key.startswith("AQ."):
        return key
    profile = Path.home() / ".profile"
    if profile.exists():
        for line in profile.read_text().splitlines():
            if line.strip().startswith("export GEMINI_API_KEY="):
                return line.strip().split("=", 1)[1].strip()
    if key:
        return key
    raise RuntimeError("GEMINI_API_KEY not found")


def call_nano_banana(prompt: str, out_path: Path, api_key: str, ref_img_b64: str | None = None, retries: int = 3) -> Path:
    if out_path.exists() and out_path.stat().st_size > 20_000:
        print(f"[SKIP] {out_path.name} already exists")
        return out_path

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    parts = []
    if ref_img_b64:
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": ref_img_b64}})
    parts.append({"text": prompt})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "16:9"},
        },
    }

    for attempt in range(1, retries + 1):
        try:
            print(f"[IMAGE] Generating {out_path.name} (attempt {attempt})...")
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for cand in data.get("candidates", []):
                for part in cand.get("content", {}).get("parts", []):
                    inl = part.get("inlineData")
                    if inl and inl.get("data"):
                        raw = base64.b64decode(inl["data"])
                        out_path.write_bytes(raw)
                        print(f"[OK] {out_path.name} ({len(raw)} bytes)")
                        return out_path
            raise RuntimeError(f"No image returned for {out_path.name}")
        except Exception as e:
            if attempt == retries:
                raise
            print(f"[RETRY {attempt}/{retries}] {out_path.name}: {e}")
            time.sleep(2.5 * attempt)
    raise RuntimeError(f"Failed {out_path.name}")


def main():
    ILLUST_DIR.mkdir(parents=True, exist_ok=True)
    api_key = get_api_key()

    char_sheet_path = ILLUST_DIR / "06_candide_char_sheet.jpg"
    call_nano_banana(CHAR_SHEET_PROMPT, char_sheet_path, api_key, ref_img_b64=None)
    ref_b64 = base64.b64encode(char_sheet_path.read_bytes()).decode("ascii")

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        futs = {
            ex.submit(call_nano_banana, prompt, ILLUST_DIR / fname, api_key, ref_b64): fname
            for fname, prompt in SCENE_PROMPTS.items()
        }
        for f in concurrent.futures.as_completed(futs):
            f.result()

    print("All 17 Candide illustrations generated successfully.")


if __name__ == "__main__":
    main()
