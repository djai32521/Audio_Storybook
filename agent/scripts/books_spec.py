#!/usr/bin/env python3
"""Master specification for the 5-book Classic Public Domain Novels Video Audiobook.

Covers:
- 15 custom voices designed via Gemini 3.8 Flash TTS Voice Design (POST /v1beta/voices)
- Verbatim opening passages from Project Gutenberg Chapter I sources
- Pronunciation & restrained acting metadata (speech_metadata.style)
- Character & Style Reference Sheet prompts + 3 minimal scene illustration prompts per book
  for Nano Banana 2 Lite (gemini-3.1-flash-lite-image)
- Fine-press editorial color tokens per book (Folio Society / Penguin Classics aesthetic)
"""

VOICES_SPEC = {
    # Book 1: Pride and Prejudice (Jane Austen, 1813)
    "austen_narrator": {
        "display_name": "Austen Regency Narrator",
        "voice_id": "Kore",
        "persona_style": "Poised, cultivated British Received Pronunciation female literary narrator in her late 30s, warm clarity and dry Regency wit",
        "gender": "female",
        "language_code": "en-GB",
        "prompt": (
            "A poised, intelligent British woman in her early 40s with a cultivated"
            " Received Pronunciation accent, speaking with dry literary wit, warm"
            " clarity, and unhurried audiobook composure."
        ),
    },
    "mrs_bennet": {
        "display_name": "Mrs. Bennet (Pride and Prejudice)",
        "voice_id": "Aoede",
        "persona_style": "Animated, expressive Regency British matron in her late 40s, refined Southern English accent, eager social warmth",
        "gender": "female",
        "language_code": "en-GB",
        "prompt": (
            "An animated, excitable British matron in her late 40s with a slightly"
            " higher-pitched, refined Southern English voice, speaking with eager"
            " social urgency and gossipy warmth."
        ),
    },
    "mr_bennet": {
        "display_name": "Mr. Bennet (Pride and Prejudice)",
        "voice_id": "Charon",
        "persona_style": "Dry, sardonic older British gentleman in his mid-50s, resonant low Received Pronunciation baritone, unhurried deadpan amusement",
        "gender": "male",
        "language_code": "en-GB",
        "prompt": (
            "A dry, sardonic British gentleman in his mid-50s with a resonant, low"
            " baritone voice, speaking with quiet deadpan amusement and unhurried"
            " restraint."
        ),
    },
    # Book 2: The Hound of the Baskervilles (Arthur Conan Doyle, 1902)
    "dr_watson": {
        "display_name": "Dr. John Watson (Baskervilles)",
        "voice_id": "Fenrir",
        "persona_style": "Warm, steady, articulate British gentleman and physician in his early 40s, classic educated London Received Pronunciation baritone",
        "gender": "male",
        "language_code": "en-GB",
        "prompt": (
            "A warm, steady, trustworthy British physician and former army officer in"
            " his early 40s with a classic educated London accent, speaking with"
            " grounded observation and earnest curiosity."
        ),
    },
    "sherlock_holmes": {
        "display_name": "Sherlock Holmes (Baskervilles)",
        "voice_id": "Orus",
        "persona_style": "Crisp, incisive, aristocratic British detective in his early 40s, sharp analytical Received Pronunciation tenor-baritone",
        "gender": "male",
        "language_code": "en-GB",
        "prompt": (
            "A crisp, incisive British detective in his early 40s with a focused,"
            " resonant tenor-baritone voice, speaking with cool analytical precision"
            " and dry intellectual relish."
        ),
    },
    # Book 3: Alice's Adventures in Wonderland (Lewis Carroll, 1865)
    "carroll_narrator": {
        "display_name": "Carroll Wonderland Narrator",
        "voice_id": "Kore",
        "persona_style": "Warm, articulate British storyteller in her late 30s, gentle Oxford Received Pronunciation accent, lyrical storybook clarity",
        "gender": "female",
        "language_code": "en-GB",
        "prompt": (
            "A warm, articulate British storyteller in her late 30s with a gentle"
            " Oxford accent, speaking with lyrical clarity, quiet wonder, and"
            " restrained storybook elegance."
        ),
    },
    "alice": {
        "display_name": "Alice (Wonderland)",
        "voice_id": "Leda",
        "persona_style": "Youthful, bright-voiced young British girl, clear natural Southern English Received Pronunciation accent, earnest curiosity and wonder",
        "gender": "female",
        "language_code": "en-GB",
        "prompt": (
            "A youthful, bright-voiced British woman in her early 20s with a clear,"
            " natural Southern English accent, speaking with earnest wonder and"
            " curious imagination."
        ),
    },
    "white_rabbit": {
        "display_name": "The White Rabbit (Wonderland)",
        "voice_id": "Puck",
        "persona_style": "Fussy, flustered British gentleman in a hurry, brisk articulate Received Pronunciation tenor, anxious polite urgency with clear full-voiced diction",
        "gender": "male",
        "language_code": "en-GB",
        "prompt": (
            "A fussy, flustered British gentleman in a hurry with a brisk, articulate"
            " Received Pronunciation tenor voice, speaking with anxious polite urgency."
        ),
    },
    # Book 4: The Time Machine (H. G. Wells, 1895)
    "wells_narrator": {
        "display_name": "Hillyer Narrator (The Time Machine)",
        "voice_id": "Fenrir",
        "persona_style": "Thoughtful, educated Victorian British gentleman in his late 30s, calm measured London Received Pronunciation baritone",
        "gender": "male",
        "language_code": "en-GB",
        "prompt": (
            "A thoughtful, educated British gentleman in his late 30s with a calm,"
            " measured Victorian London voice, narrating with quiet intellectual"
            " fascination."
        ),
    },
    "time_traveller": {
        "display_name": "The Time Traveller (Wells)",
        "voice_id": "Orus",
        "persona_style": "Intense, articulate British scientist and inventor in his late 30s, clear energetic Received Pronunciation baritone, lucid conviction",
        "gender": "male",
        "language_code": "en-GB",
        "prompt": (
            "An intense, articulate British scientist and inventor in his late 30s"
            " with a clear, energetic baritone voice, speaking with lucid conviction"
            " and quiet visionary urgency."
        ),
    },
    "filby": {
        "display_name": "Filby (The Time Machine)",
        "voice_id": "Iapetus",
        "persona_style": "Skeptical, grounded Scottish-inflected British gentleman in his 40s, warm resonant baritone, blunt common sense",
        "gender": "male",
        "language_code": "en-GB",
        "prompt": (
            "A skeptical, blunt Scottish-inflected British gentleman in his 40s with"
            " a warm, gravelly voice, speaking with grounded common sense."
        ),
    },
    "psychologist": {
        "display_name": "The Psychologist (The Time Machine)",
        "voice_id": "Charon",
        "persona_style": "Calm, dry British academic in his late 40s, measured scholarly Received Pronunciation baritone",
        "gender": "male",
        "language_code": "en-GB",
        "prompt": (
            "A calm, dry British academic in his late 40s with a measured, soft-spoken"
            " scholarly voice."
        ),
    },
    # Book 5: The Adventures of Tom Sawyer (Mark Twain, 1876)
    "twain_narrator": {
        "display_name": "Twain Missouri Narrator",
        "voice_id": "Charon",
        "persona_style": "Warm, observant older American literary storyteller in his 60s, gentle 19th-century Missouri drawl, wry humor and unhurried cadence",
        "gender": "male",
        "language_code": "en-US",
        "prompt": (
            "A warm, observant older American literary storyteller in his 60s with a"
            " gentle 19th-century Missouri drawl, speaking with wry humor, unhurried"
            " cadence, and quiet warmth."
        ),
    },
    "aunt_polly": {
        "display_name": "Aunt Polly (Tom Sawyer)",
        "voice_id": "Aoede",
        "persona_style": "Warm, spirited older 19th-century Missouri woman in her 60s, natural rural Missouri folk accent, affectionate maternal authority",
        "gender": "female",
        "language_code": "en-US",
        "prompt": (
            "A spirited, affectionate, sharp-tongued older American woman in her 60s"
            " with a classic rural Missouri accent, speaking with exasperated"
            " maternal authority."
        ),
    },
    "tom_sawyer": {
        "display_name": "Tom Sawyer (Twain)",
        "voice_id": "Puck",
        "persona_style": "Youthful, lively American boy in 1840s Missouri, bright natural American voice, playful innocence and clear full-voiced diction",
        "gender": "male",
        "language_code": "en-US",
        "prompt": (
            "A youthful, bright-voiced American theatrical actor in his early 20s"
            " with a lively Missouri accent, speaking with quick-witted, playful"
            " innocence and high-pitched energy."
        ),
    },
}


BOOKS_SPEC = [
    {
        "id": "01_pride_and_prejudice",
        "roman": "I",
        "title": "Pride and Prejudice",
        "author": "Jane Austen",
        "year": "1813",
        "chapter_title": "Chapter I",
        "genre": "Regency Social Satire",
        "setting": "Longbourn, Hertfordshire",
        "palette": {
            "paper": "#F6F2EA",
            "card": "#EFE9DC",
            "ink": "#1E1B18",
            "muted": "#7A7267",
            "accent": "#4A6B53",  # Muted Regency sage
            "rule": "#D5CBB8",
        },
        "char_sheet_prompt": (
            "Minimalist editorial book illustration character reference sheet on clean"
            " warm cream archival paper (#F6F2EA). Delicate 1810s Regency pen-and-ink"
            " line drawing with sparse, subtle muted sage-green (#4A6B53) and warm"
            " sepia watercolor wash. Show two distinct full-length 1810s characters"
            " side by side with generous negative space: on the left, a dry, observant"
            " fifty-year-old 1810s English country gentleman with lean features,"
            " greying sideburns, a high white linen cravat, buff waistcoat, and"
            " tailored dark olive-brown wool cutaway coat and breeches, holding a"
            " small leather-bound book; on the right, an animated forty-five-year-old"
            " 1810s English country gentlewoman with soft curls under a lace morning"
            " cap, wearing a high-waisted sage-and-cream sprigged muslin Empire-waist"
            " gown with a light shawl. Clean fine-press ink linework, minimalist"
            " restraint, no text, no labels, no borders."
        ),
        "scenes": [
            {
                "id": "scene_1",
                "caption": "The Country Estate Morning Room",
                "prompt": (
                    "Using the exact character designs and minimalist 1810s Regency"
                    " pen-and-ink with sparse sage-green and warm sepia watercolor wash"
                    " style from the reference image: a book illustration on"
                    " warm cream archival paper (#F6F2EA)."
                    " In a sunlit 1810s English country-house morning room with a tall sash window,"
                    " the fifty-year-old country gentleman (lean features, greying sideburns,"
                    " dark olive-brown wool cutaway coat, high white linen cravat) sits calmly in a"
                    " wingback chair reading his small leather-bound book, while his forty-five-year-old"
                    " wife (in her high-waisted sage-and-cream sprigged muslin Empire-waist gown and"
                    " lace morning cap) enters eagerly beside him to announce news. Clean"
                    " ink lines, full architectural interior, no text."
                ),
            },
            {
                "id": "scene_2",
                "caption": "“The Neighboring Park is Let at Last”",
                "prompt": (
                    "Using the exact character designs and 1810s Regency pen-and-ink with"
                    " muted sage-green (#4A6B53) and warm sepia watercolor wash style"
                    " from the reference image: a full-scene Regency interior"
                    " illustration on warm cream archival paper (#F6F2EA). In the"
                    " country-house morning room with floor-to-ceiling Georgian bookshelves,"
                    " a carved marble fireplace, and sunlit Regency wainscoting, the"
                    " forty-five-year-old gentlewoman (high-waisted sage-and-cream sprigged muslin"
                    " Empire-waist gown and lace morning cap) stands beside the gentleman's wingback"
                    " armchair leaning forward with animated excitement to announce that the"
                    " neighboring country estate is let at last, while the fifty-year-old gentleman"
                    " (greying sideburns, high white linen cravat, olive-brown cutaway coat) holds his"
                    " small leather-bound book open in his lap and looks up with calm,"
                    " sardonic composure. Rich period interior architecture filling the"
                    " 16:9 composition, no borders, no text."
                ),
            },
            {
                "id": "scene_3",
                "caption": "The Neighbor’s Intelligence",
                "prompt": (
                    "Using the exact character designs and 1810s Regency pen-and-ink with"
                    " muted sage-green (#4A6B53) and warm sepia watercolor wash style"
                    " from the reference image: a full-scene Regency drawing-room"
                    " illustration on warm cream archival paper (#F6F2EA). Inside the"
                    " sunlit country-house drawing room featuring a striped Regency settee,"
                    " framed botanical prints on the wall, and tall draped sash windows"
                    " overlooking garden trees, the gentlewoman sits forward on the settee"
                    " gesturing animatedly with both empty hands as she recounts a neighbor's"
                    " morning visit, while the gentleman sits across from her in a curved"
                    " Regency library chair with legs crossed, listening with dry,"
                    " deadpan amusement. Complete period room environment, no borders,"
                    " no text."
                ),
            },
            {
                "id": "scene_4",
                "caption": "A Chaise and Four from the North",
                "prompt": (
                    "Using the exact character designs and 1810s Regency pen-and-ink with"
                    " muted sage-green (#4A6B53) and warm sepia watercolor wash style"
                    " from the reference image: a full-scene Regency interior and"
                    " window view on warm cream archival paper (#F6F2EA). Beside a tall"
                    " Georgian sash window in an English country house looking out over a"
                    " tree-lined gravel drive and rolling green hills, the gentlewoman"
                    " stands on the left pointing eagerly toward the window as"
                    " she describes a young gentleman of large fortune arriving on Monday"
                    " in a chaise and four, while her husband sits calmly on the right"
                    " in a Regency wooden armchair with his hands folded in his lap."
                    " Full period room with wainscoting and landscape view through the"
                    " window, anatomically accurate two arms per person, no borders,"
                    " no text."
                ),
            },
            {
                "id": "scene_5",
                "caption": "“A Single Man of Large Fortune”",
                "prompt": (
                    "Using the exact character designs and 1810s Regency pen-and-ink with"
                    " muted sage-green (#4A6B53) and warm sepia watercolor wash style"
                    " from the reference image: a full-scene Regency drawing-room"
                    " illustration on warm cream archival paper (#F6F2EA). Across a"
                    " polished round Regency mahogany tea table set with porcelain"
                    " teacups and a silver teapot in a sunlit panelled room with a"
                    " chandelier and fireplace, the gentlewoman raises her hands in"
                    " triumphant, exasperated insistence over her five daughters' marriage"
                    " prospects, while the gentleman stands with hands clasped behind his"
                    " olive-brown cutaway coat, inclining his head with dry irony. Full"
                    " architectural interior, no borders, no text."
                ),
            },
        ],
        "turns": [
            {
                "speaker": "austen_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 0,
                "page_idx": 0,
                "display_text": (
                    "It is a truth universally acknowledged, that a single man in"
                    " possession of a good fortune, must be in want of a wife."
                ),
                "tts_text": (
                    "It is a truth universally acknowledged, that a single man in"
                    " possession of a good fortune, must be in want of a wife."
                ),
                "style": "poised, dry literary irony, measured pace",
                "pause_after_ms": 480,
            },
            {
                "speaker": "austen_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 0,
                "page_idx": 0,
                "display_text": (
                    "However little known the feelings or views of such a man may be on"
                    " his first entering a neighbourhood, this truth is so well fixed"
                    " in the minds of the surrounding families, that he is considered"
                    " as the rightful property of some one or other of their daughters."
                ),
                "tts_text": (
                    "However little known the feelings or views of such a man may be on"
                    " his first entering a neighbourhood, this truth is so well fixed"
                    " in the minds of the surrounding families, that he is considered"
                    " as the rightful property of some one or other of their daughters."
                ),
                "style": "calm, observant literary narration",
                "pause_after_ms": 520,
            },
            {
                "speaker": "mrs_bennet",
                "label": "MRS. BENNET",
                "is_dialogue": True,
                "scene_idx": 1,
                "page_idx": 1,
                "display_text": "“My dear Mr. Bennet,”",
                "tts_text": "My dear Mr. Bennet,",
                "style": "eager, animated",
                "pause_after_ms": 160,
            },
            {
                "speaker": "austen_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 1,
                "page_idx": 1,
                "display_text": "said his lady to him one day,",
                "tts_text": "said his lady to him one day,",
                "style": "calm literary narration",
                "pause_after_ms": 180,
            },
            {
                "speaker": "mrs_bennet",
                "label": "MRS. BENNET",
                "is_dialogue": True,
                "scene_idx": 1,
                "page_idx": 1,
                "display_text": "“have you heard that Netherfield Park is let at last?”",
                "tts_text": "have you heard that Netherfield Park is let at last?",
                "style": "eager, expectant, pronounce Netherfield like NETH-er-field",
                "pause_after_ms": 420,
            },
            {
                "speaker": "austen_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 1,
                "page_idx": 1,
                "display_text": "Mr. Bennet replied that he had not.",
                "tts_text": "Mr. Bennet replied that he had not.",
                "style": "dry, matter-of-fact narration",
                "pause_after_ms": 400,
            },
            {
                "speaker": "mrs_bennet",
                "label": "MRS. BENNET",
                "is_dialogue": True,
                "scene_idx": 2,
                "page_idx": 2,
                "display_text": (
                    "“But it is,” returned she; “for Mrs. Long has just been here, and"
                    " she told me all about it.”"
                ),
                "tts_text": (
                    "But it is, for Mrs. Long has just been here, and she told me all"
                    " about it."
                ),
                "style": "insistent, gossipy excitement",
                "pause_after_ms": 420,
            },
            {
                "speaker": "austen_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 2,
                "page_idx": 2,
                "display_text": "Mr. Bennet made no answer.",
                "tts_text": "Mr. Bennet made no answer.",
                "style": "quiet, deadpan literary narration",
                "pause_after_ms": 480,
            },
            {
                "speaker": "mrs_bennet",
                "label": "MRS. BENNET",
                "is_dialogue": True,
                "scene_idx": 2,
                "page_idx": 2,
                "display_text": "“Do not you want to know who has taken it?”",
                "tts_text": "Do not you want to know who has taken it?",
                "style": "impatient, pressing",
                "pause_after_ms": 180,
            },
            {
                "speaker": "austen_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 2,
                "page_idx": 3,
                "display_text": "cried his wife, impatiently.",
                "tts_text": "cried his wife, impatiently.",
                "style": "calm literary narration",
                "pause_after_ms": 380,
            },
            {
                "speaker": "mr_bennet",
                "label": "MR. BENNET",
                "is_dialogue": True,
                "scene_idx": 2,
                "page_idx": 3,
                "display_text": "“You want to tell me, and I have no objection to hearing it.”",
                "tts_text": "YOU want to tell me, and I have no objection to hearing it.",
                "style": "dry, calm, deadpan amusement",
                "pause_after_ms": 420,
            },
            {
                "speaker": "austen_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 2,
                "page_idx": 3,
                "display_text": "This was invitation enough.",
                "tts_text": "This was invitation enough.",
                "style": "dry, understated wit",
                "pause_after_ms": 420,
            },
            {
                "speaker": "mrs_bennet",
                "label": "MRS. BENNET",
                "is_dialogue": True,
                "scene_idx": 3,
                "page_idx": 4,
                "display_text": (
                    "“Why, my dear, you must know, Mrs. Long says that Netherfield is"
                    " taken by a young man of large fortune from the north of England;"
                    " that he came down on Monday in a chaise and four to see the"
                    " place, and was so much delighted with it that he agreed with Mr."
                    " Morris immediately.”"
                ),
                "tts_text": (
                    "Why, my dear, you must know, Mrs. Long says that Netherfield is"
                    " taken by a young man of large fortune from the north of England;"
                    " that he came down on Monday in a chaise and four to see the"
                    " place, and was so much delighted with it that he agreed with Mr."
                    " Morris immediately."
                ),
                "style": "animated, delighted gossip, pronounce chaise like shayz",
                "pause_after_ms": 420,
            },
            {
                "speaker": "mr_bennet",
                "label": "MR. BENNET",
                "is_dialogue": True,
                "scene_idx": 3,
                "page_idx": 4,
                "display_text": "“What is his name?”",
                "tts_text": "What is his name?",
                "style": "calm, unhurried",
                "pause_after_ms": 320,
            },
            {
                "speaker": "mrs_bennet",
                "label": "MRS. BENNET",
                "is_dialogue": True,
                "scene_idx": 3,
                "page_idx": 4,
                "display_text": "“Bingley.”",
                "tts_text": "Bingley.",
                "style": "decisive, pleased",
                "pause_after_ms": 320,
            },
            {
                "speaker": "mr_bennet",
                "label": "MR. BENNET",
                "is_dialogue": True,
                "scene_idx": 3,
                "page_idx": 4,
                "display_text": "“Is he married or single?”",
                "tts_text": "Is he married or single?",
                "style": "calm, mildly curious",
                "pause_after_ms": 320,
            },
            {
                "speaker": "mrs_bennet",
                "label": "MRS. BENNET",
                "is_dialogue": True,
                "scene_idx": 4,
                "page_idx": 5,
                "display_text": (
                    "“Oh, single, my dear, to be sure! A single man of large fortune;"
                    " four or five thousand a year. What a fine thing for our girls!”"
                ),
                "tts_text": (
                    "Oh, single, my dear, to be sure! A single man of large fortune;"
                    " four or five thousand a year. What a fine thing for our girls!"
                ),
                "style": "joyful, triumphant enthusiasm",
                "pause_after_ms": 380,
            },
            {
                "speaker": "mr_bennet",
                "label": "MR. BENNET",
                "is_dialogue": True,
                "scene_idx": 4,
                "page_idx": 5,
                "display_text": "“How so? How can it affect them?”",
                "tts_text": "How so? How can it affect them?",
                "style": "dry, feigned innocence",
                "pause_after_ms": 380,
            },
            {
                "speaker": "mrs_bennet",
                "label": "MRS. BENNET",
                "is_dialogue": True,
                "scene_idx": 4,
                "page_idx": 5,
                "display_text": (
                    "“My dear Mr. Bennet, how can you be so tiresome? You must know"
                    " that I am thinking of his marrying one of them.”"
                ),
                "tts_text": (
                    "My dear Mr. Bennet, how can you be so tiresome? You must know"
                    " that I am thinking of his marrying one of them."
                ),
                "style": "exasperated, emphatic",
                "pause_after_ms": 600,
            },
        ],
    },
    {
        "id": "02_hound_of_the_baskervilles",
        "roman": "II",
        "title": "The Hound of the Baskervilles",
        "author": "Arthur Conan Doyle",
        "year": "1902",
        "chapter_title": "Chapter I · Mr. Sherlock Holmes",
        "genre": "Victorian Detective Mystery",
        "setting": "221B Baker Street, London",
        "palette": {
            "paper": "#F2EDE2",
            "card": "#E8E1D3",
            "ink": "#181A1B",
            "muted": "#6E6A63",
            "accent": "#9E6B2E",  # Warm Baker Street amber-ochre
            "rule": "#CFC6B4",
        },
        "char_sheet_prompt": (
            "Minimalist 1900 late-Victorian woodblock and scratchboard engraving"
            " character reference sheet on aged ivory archival paper (#F2EDE2). Crisp"
            " charcoal-black ink linework (#181A1B) with a single restrained warm"
            " amber-ochre accent (#9E6B2E) and wide negative space. Show two distinct"
            " full-length characters side by side: on the left, a tall, spare"
            " late-Victorian gentleman in his early forties with sharp grey eyes,"
            " straight dark hair brushed back, clean-shaven angular face, wearing a"
            " dark claret-brown velveteen indoor smoking jacket over a white wing"
            " collar, dark waistcoat and trousers (no hat, no cape); on the right, a"
            " sturdy, warm-faced late-Victorian gentleman in his forties with neatly"
            " parted sandy-brown hair and a trim moustache, wearing a brown"
            " three-piece tweed morning suit and holding a thick bulbous-headed wooden"
            " walking-stick with a broad silver-gold band below the handle. Minimalist"
            " fine-press printmaking style, no text, no labels, no borders."
        ),
        "scenes": [
            {
                "id": "scene_1",
                "caption": "The Visitor’s Walking-Stick",
                "prompt": (
                    "Using the exact character designs and charcoal-black"
                    " woodblock engraving with warm amber-ochre accent style from the"
                    " reference image: a book illustration on aged ivory"
                    " paper (#F2EDE2). In a 1900 late-Victorian metropolitan study,"
                    " the sturdy forty-year-old physician (neatly parted sandy-brown hair,"
                    " trim moustache, brown three-piece tweed morning suit) stands on the"
                    " hearth-rug examining the bulbous-headed wooden walking-stick with its"
                    " warm amber-gold metal band, while the tall spare investigator (sharp"
                    " angular profile, dark claret-brown velveteen smoking jacket) sits with"
                    " his back turned at the breakfast table. Atmospheric woodcut lines, no text."
                ),
            },
            {
                "id": "scene_2",
                "caption": "The Engraved Band (1884)",
                "prompt": (
                    "Using the exact character designs and charcoal-black Victorian"
                    " woodblock engraving with warm amber-ochre (#9E6B2E) accent style"
                    " from the reference image: a full-scene Victorian interior"
                    " woodcut on aged ivory paper (#F2EDE2). In the cluttered late-Victorian"
                    " sitting room with chemical flasks on a side table,"
                    " floor-to-ceiling bookshelves, and a glowing coal fireplace, the"
                    " sturdy physician stands near the tall sash window holding the thick"
                    " bulbous-headed tropical-hardwood walking-stick horizontally in both"
                    " hands, inspecting the gleaming warm amber-gold metal presentation"
                    " band just below its handle, while the tall spare investigator sits in"
                    " three-quarter rear view at the breakfast table in the background."
                    " Detailed Victorian woodblock printmaking filling the 16:9 frame,"
                    " no borders, no text."
                ),
            },
            {
                "id": "scene_3",
                "caption": "The Silver-Plated Coffee-Pot",
                "prompt": (
                    "Using the exact character designs and charcoal-black Victorian"
                    " woodblock engraving with warm amber-ochre (#9E6B2E) accent style"
                    " from the reference image: a full-scene Victorian interior"
                    " woodcut on aged ivory paper (#F2EDE2). At the late-Victorian"
                    " breakfast table set with a plain white linen tablecloth, porcelain"
                    " teacup, saucer, and silver toast-rack (no newspapers, no books,"
                    " no writing) before a tall bay window overlooking misty metropolitan"
                    " rooftops, the tall spare investigator (sharp angular profile,"
                    " dark velveteen smoking jacket) sits beside a gleaming well-polished"
                    " silver-plated coffee-pot, gesturing calmly toward its reflective"
                    " surface, while the sturdy physician stands behind him holding the"
                    " walking-stick in surprise. Full Victorian room environment, no"
                    " borders, no text anywhere."
                ),
            },
            {
                "id": "scene_4",
                "caption": "Reconstructing the Country Practitioner",
                "prompt": (
                    "Using the exact character designs and charcoal-black Victorian"
                    " woodblock engraving with warm amber-ochre (#9E6B2E) accent style"
                    " from the reference image: a full-scene Victorian interior"
                    " woodcut on aged ivory paper (#F2EDE2). In the book-lined"
                    " Victorian study with a violin resting on a side table and"
                    " framed anatomical prints on the wall, the sturdy physician sits forward in"
                    " a tufted leather armchair holding the bulbous-headed wooden"
                    " walking-stick across his knees as he reasons aloud, while"
                    " the tall spare investigator leans back in his armchair opposite the fireplace"
                    " with fingertips pressed together and an encouraging, keen"
                    " expression. Full Victorian room composition, no borders, no text."
                ),
            },
            {
                "id": "scene_5",
                "caption": "The Worn Iron Ferrule",
                "prompt": (
                    "Using the exact character designs and charcoal-black Victorian"
                    " woodblock engraving with warm amber-ochre (#9E6B2E) accent style"
                    " from the reference image: a full-scene Victorian interior"
                    " woodcut on aged ivory paper (#F2EDE2). Beside the hearth and"
                    " bookshelves of the Victorian study, the sturdy physician tilts the bottom tip"
                    " of the battered wooden walking-stick upward to demonstrate its"
                    " worn iron ferrule from country walking, while the tall spare investigator"
                    " stands beside the mantelpiece in his dark velveteen smoking jacket,"
                    " nodding in warm analytical satisfaction. Rich Victorian woodblock"
                    " interior filling the 16:9 canvas, no borders, no text."
                ),
            },
        ],
        "turns": [
            {
                "speaker": "dr_watson",
                "label": "DR. WATSON (NARRATOR)",
                "is_dialogue": False,
                "scene_idx": 0,
                "page_idx": 0,
                "display_text": (
                    "Mr. Sherlock Holmes, who was usually very late in the mornings,"
                    " save upon those not infrequent occasions when he was up all"
                    " night, was seated at the breakfast table."
                ),
                "tts_text": (
                    "Mr. Sherlock Holmes, who was usually very late in the mornings,"
                    " save upon those not infrequent occasions when he was up all"
                    " night, was seated at the breakfast table."
                ),
                "style": "warm, measured Victorian literary narration",
                "pause_after_ms": 420,
            },
            {
                "speaker": "dr_watson",
                "label": "DR. WATSON (NARRATOR)",
                "is_dialogue": False,
                "scene_idx": 0,
                "page_idx": 0,
                "display_text": (
                    "I stood upon the hearth-rug and picked up the stick which our"
                    " visitor had left behind him the night before. It was a fine,"
                    " thick piece of wood, bulbous-headed, of the sort which is known"
                    " as a “Penang lawyer.”"
                ),
                "tts_text": (
                    "I stood upon the hearth-rug and picked up the stick which our"
                    " visitor had left behind him the night before. It was a fine,"
                    " thick piece of wood, bulbous-headed, of the sort which is known"
                    " as a Penang lawyer."
                ),
                "style": "observant narration, pronounce Penang like peh-NANG",
                "pause_after_ms": 420,
            },
            {
                "speaker": "dr_watson",
                "label": "DR. WATSON (NARRATOR)",
                "is_dialogue": False,
                "scene_idx": 1,
                "page_idx": 1,
                "display_text": (
                    "Just under the head was a broad silver band nearly an inch"
                    " across. “To James Mortimer, M.R.C.S., from his friends of the"
                    " C.C.H.,” was engraved upon it, with the date “1884.”"
                ),
                "tts_text": (
                    "Just under the head was a broad silver band nearly an inch"
                    " across. To James Mortimer, M. R. C. S., from his friends of the"
                    " C. C. H., was engraved upon it, with the date eighteen"
                    " eighty-four."
                ),
                "style": "measured, clear articulation",
                "pause_after_ms": 480,
            },
            {
                "speaker": "sherlock_holmes",
                "label": "SHERLOCK HOLMES",
                "is_dialogue": True,
                "scene_idx": 1,
                "page_idx": 1,
                "display_text": "“Well, Watson, what do you make of it?”",
                "tts_text": "Well, Watson, what do you make of it?",
                "style": "crisp, sudden, inquisitive",
                "pause_after_ms": 420,
            },
            {
                "speaker": "dr_watson",
                "label": "DR. WATSON (NARRATOR)",
                "is_dialogue": False,
                "scene_idx": 2,
                "page_idx": 2,
                "display_text": (
                    "Holmes was sitting with his back to me, and I had given him no"
                    " sign of my occupation."
                ),
                "tts_text": (
                    "Holmes was sitting with his back to me, and I had given him no"
                    " sign of my occupation."
                ),
                "style": "quietly astonished narration",
                "pause_after_ms": 360,
            },
            {
                "speaker": "dr_watson",
                "label": "DR. WATSON",
                "is_dialogue": True,
                "scene_idx": 2,
                "page_idx": 2,
                "display_text": (
                    "“How did you know what I was doing? I believe you have eyes in"
                    " the back of your head.”"
                ),
                "tts_text": (
                    "How did you know what I was doing? I believe you have eyes in"
                    " the back of your head."
                ),
                "style": "surprised, wry",
                "pause_after_ms": 380,
            },
            {
                "speaker": "sherlock_holmes",
                "label": "SHERLOCK HOLMES",
                "is_dialogue": True,
                "scene_idx": 2,
                "page_idx": 2,
                "display_text": (
                    "“I have, at least, a well-polished, silver-plated coffee-pot in"
                    " front of me. But, tell me, Watson, what do you make of our"
                    " visitor’s stick? Let me hear you reconstruct the man by an"
                    " examination of it.”"
                ),
                "tts_text": (
                    "I have, at least, a well-polished, silver-plated coffee-pot in"
                    " front of me. But, tell me, Watson, what do you make of our"
                    " visitor's stick? Let me hear you reconstruct the man by an"
                    " examination of it."
                ),
                "style": "dry intellectual amusement, inviting",
                "pause_after_ms": 480,
            },
            {
                "speaker": "dr_watson",
                "label": "DR. WATSON",
                "is_dialogue": True,
                "scene_idx": 3,
                "page_idx": 3,
                "display_text": (
                    "“I think that Dr. Mortimer is a successful, elderly medical man,"
                    " well-esteemed since those who know him give him this mark of"
                    " their appreciation.”"
                ),
                "tts_text": (
                    "I think that Doctor Mortimer is a successful, elderly medical man,"
                    " well-esteemed since those who know him give him this mark of"
                    " their appreciation."
                ),
                "style": "thoughtful, deliberate deduction",
                "pause_after_ms": 320,
            },
            {
                "speaker": "sherlock_holmes",
                "label": "SHERLOCK HOLMES",
                "is_dialogue": True,
                "scene_idx": 3,
                "page_idx": 3,
                "display_text": "“Good!” said Holmes. “Excellent!”",
                "tts_text": "Good! Excellent!",
                "style": "crisp, encouraging approval",
                "pause_after_ms": 360,
            },
            {
                "speaker": "dr_watson",
                "label": "DR. WATSON",
                "is_dialogue": True,
                "scene_idx": 3,
                "page_idx": 3,
                "display_text": (
                    "“I think also that the probability is in favour of his being a"
                    " country practitioner who does a great deal of his visiting on"
                    " foot.”"
                ),
                "tts_text": (
                    "I think also that the probability is in favour of his being a"
                    " country practitioner who does a great deal of his visiting on"
                    " foot."
                ),
                "style": "confident, reasoned",
                "pause_after_ms": 300,
            },
            {
                "speaker": "sherlock_holmes",
                "label": "SHERLOCK HOLMES",
                "is_dialogue": True,
                "scene_idx": 3,
                "page_idx": 3,
                "display_text": "“Why so?”",
                "tts_text": "Why so?",
                "style": "keen, brisk",
                "pause_after_ms": 320,
            },
            {
                "speaker": "dr_watson",
                "label": "DR. WATSON",
                "is_dialogue": True,
                "scene_idx": 4,
                "page_idx": 4,
                "display_text": (
                    "“Because this stick, though originally a very handsome one, has"
                    " been so knocked about that I can hardly imagine a town"
                    " practitioner carrying it. The thick-iron ferrule is worn down,"
                    " so it is evident that he has done a great amount of walking with"
                    " it.”"
                ),
                "tts_text": (
                    "Because this stick, though originally a very handsome one, has"
                    " been so knocked about that I can hardly imagine a town"
                    " practitioner carrying it. The thick-iron ferrule is worn down,"
                    " so it is evident that he has done a great amount of walking with"
                    " it."
                ),
                "style": "assured, analytical, pronounce ferrule like FER-uhl",
                "pause_after_ms": 340,
            },
            {
                "speaker": "sherlock_holmes",
                "label": "SHERLOCK HOLMES",
                "is_dialogue": True,
                "scene_idx": 4,
                "page_idx": 4,
                "display_text": "“Perfectly sound!” said Holmes.",
                "tts_text": "Perfectly sound!",
                "style": "warm, satisfied approval",
                "pause_after_ms": 600,
            },
        ],
    },
    {
        "id": "03_alice_in_wonderland",
        "roman": "III",
        "title": "Alice’s Adventures in Wonderland",
        "author": "Lewis Carroll",
        "year": "1865",
        "chapter_title": "Chapter I · Down the Rabbit-Hole",
        "genre": "Surreal Victorian Fantasy",
        "setting": "The Riverbank & The Deep Well",
        "palette": {
            "paper": "#F8F5EE",
            "card": "#F0EBE0",
            "ink": "#1C2026",
            "muted": "#72767D",
            "accent": "#9E332B",  # Waistcoat carmine
            "rule": "#D8D0C1",
        },
        "char_sheet_prompt": (
            "Minimalist editorial book illustration character reference sheet on"
            " warm ivory paper (#F8F5EE). Delicate 1860s Victorian wood-engraving"
            " crosshatched black pen-and-ink linework with warm terracotta-ochre,"
            " soft olive-green, and russet-red watercolor accents. Show two distinct"
            " full-length characters side by side with generous empty paper space:"
            " on the left, a curious seven-year-old 1860s Victorian English girl with"
            " wavy shoulder-length dark chestnut-brown hair (no headband), wearing a"
            " simple 1860s summer dress in warm terracotta-ochre linen with short"
            " puffed sleeves, cream stockings, and buttoned ankle boots (NOT blonde,"
            " NOT wearing a blue dress or white apron); on the right, a"
            " naturalistically proportioned white English country rabbit with pink"
            " eyes, standing upright on hind legs, wearing a small buttoned"
            " russet-tweed waistcoat and holding a round brass pocket-watch on a"
            " chain. Minimalist, no text, no labels, no borders."
        ),
        "scenes": [
            {
                "id": "scene_1",
                "caption": "On the Drowsy Riverbank",
                "prompt": (
                    "Using the exact character designs and crosshatched"
                    " pen-and-ink with sparse porcelain-blue and carmine watercolor"
                    " style from the reference image: a book illustration on"
                    " warm ivory paper (#F8F5EE). A curious seven-year-old 1860s"
                    " Victorian English girl (wavy shoulder-length dark chestnut-brown"
                    " hair, simple terracotta-ochre linen summer dress with short puffed"
                    " sleeves, cream stockings, buttoned ankle boots) sits drowsily among"
                    " sparse daisies on a grassy riverbank beneath a willow branch, resting"
                    " her chin on her hand as she glances toward a plain open book."
                    " Delicate ink linework, no text."
                ),
            },
            {
                "id": "scene_2",
                "caption": "A White Rabbit with Pink Eyes",
                "prompt": (
                    "Using the exact character designs and crosshatched black"
                    " pen-and-ink with porcelain-blue (#4A7491) and carmine-red"
                    " (#9E332B) watercolor accents from the reference image: a"
                    " full-scene pastoral book illustration on warm ivory archival"
                    " paper (#F8F5EE). Across a sunlit English meadow of tall grass"
                    " and white field daisies beside a winding river and weeping willow"
                    " trees, the seven-year-old girl (wavy dark chestnut-brown hair,"
                    " terracotta-ochre linen dress) sits on the grassy"
                    " bank holding a half-woven daisy-chain, turning her head in"
                    " drowsy surprise as a naturalistically proportioned upright white"
                    " country rabbit with pink eyes in a small buttoned russet-tweed"
                    " waistcoat dashes past her along a meadow path. Full"
                    " pastoral landscape filling the 16:9 canvas, no borders, no text."
                ),
            },
            {
                "id": "scene_3",
                "caption": "The Waistcoat Pocket-Watch",
                "prompt": (
                    "Using the exact character designs and crosshatched"
                    " pen-and-ink with porcelain-blue and carmine watercolor"
                    " style from the reference image: a book illustration on"
                    " warm ivory paper (#F8F5EE). In the"
                    " foreground, the upright white country rabbit in its buttoned"
                    " russet-tweed waistcoat hurries past while peering"
                    " anxiously at a round brass pocket-watch held in its paw; in the"
                    " background, the seven-year-old girl in her terracotta-ochre linen"
                    " dress springs to her feet in sudden curiosity. Clean ink linework,"
                    " no text."
                ),
            },
            {
                "id": "scene_4",
                "caption": "Under the Hawthorn Hedge",
                "prompt": (
                    "Using the exact character designs and crosshatched black"
                    " pen-and-ink with porcelain-blue (#4A7491) and carmine-red"
                    " (#9E332B) watercolor accents from the reference image: a"
                    " full-scene storybook landscape illustration on warm ivory"
                    " archival paper (#F8F5EE). Across a sunlit English meadow bordered"
                    " by a tangled hawthorn hedge and ancient gnarled tree roots, the"
                    " seven-year-old girl in her terracotta-ochre linen dress runs"
                    " eagerly across the grass just in time to see the upright white"
                    " country rabbit in its russet-tweed waistcoat diving headfirst into"
                    " a large shadowy burrow beneath the roots of the hedge. Full pastoral"
                    " environment filling the 16:9 frame, no borders, no text."
                ),
            },
            {
                "id": "scene_5",
                "caption": "Falling Down the Deep Well",
                "prompt": (
                    "Using the exact character designs and crosshatched"
                    " pen-and-ink with porcelain-blue and carmine watercolor"
                    " style from the reference image: a book illustration on"
                    " warm ivory paper (#F8F5EE). The seven-year-old girl"
                    " (wavy dark chestnut-brown hair, terracotta-ochre linen dress"
                    " billowing gently upward) floats serenely down a vertical shaft"
                    " lined with floating wooden bookshelves, a terrestrial globe, and a"
                    " stoneware preserve crock on a shelf. Delicate crosshatched ink lines,"
                    " no text."
                ),
            },
        ],
        "turns": [
            {
                "speaker": "carroll_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 0,
                "page_idx": 0,
                "display_text": (
                    "Alice was beginning to get very tired of sitting by her sister on"
                    " the bank, and of having nothing to do: once or twice she had"
                    " peeped into the book her sister was reading, but it had no"
                    " pictures or conversations in it,"
                ),
                "tts_text": (
                    "Alice was beginning to get very tired of sitting by her sister on"
                    " the bank, and of having nothing to do: once or twice she had"
                    " peeked into the book her sister was reading, but it had no"
                    " pictures or conversations in it,"
                ),
                "style": "warm, unhurried storybook narration",
                "pause_after_ms": 220,
            },
            {
                "speaker": "alice",
                "label": "ALICE",
                "is_dialogue": True,
                "scene_idx": 0,
                "page_idx": 0,
                "display_text": "“and what is the use of a book,”",
                "tts_text": "and what is the use of a book,",
                "style": "drowsy, wondering",
                "pause_after_ms": 160,
            },
            {
                "speaker": "carroll_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 0,
                "page_idx": 0,
                "display_text": "thought Alice,",
                "tts_text": "thought Alice,",
                "style": "gentle narration",
                "pause_after_ms": 160,
            },
            {
                "speaker": "alice",
                "label": "ALICE",
                "is_dialogue": True,
                "scene_idx": 0,
                "page_idx": 0,
                "display_text": "“without pictures or conversations?”",
                "tts_text": "without pictures or conversations?",
                "style": "curious, earnest",
                "pause_after_ms": 480,
            },
            {
                "speaker": "carroll_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 1,
                "page_idx": 1,
                "display_text": (
                    "So she was considering in her own mind (as well as she could, for"
                    " the hot day made her feel very sleepy and stupid), whether the"
                    " pleasure of making a daisy-chain would be worth the trouble of"
                    " getting up and picking the daisies, when suddenly a White Rabbit"
                    " with pink eyes ran close by her."
                ),
                "tts_text": (
                    "So she was considering in her own mind, as well as she could, for"
                    " the hot day made her feel very sleepy and stupid, whether the"
                    " pleasure of making a daisy-chain would be worth the trouble of"
                    " getting up and picking the daisies, when suddenly a White Rabbit"
                    " with pink eyes ran close by her."
                ),
                "style": "dreamy, then brightening with gentle surprise",
                "pause_after_ms": 480,
            },
            {
                "speaker": "carroll_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 2,
                "page_idx": 2,
                "display_text": (
                    "There was nothing so very remarkable in that; nor did Alice think"
                    " it so very much out of the way to hear the Rabbit say to itself,"
                ),
                "tts_text": (
                    "There was nothing so VERY remarkable in that; nor did Alice think"
                    " it so VERY much out of the way to hear the Rabbit say to itself,"
                ),
                "style": "light, playful storybook narration",
                "pause_after_ms": 220,
            },
            {
                "speaker": "white_rabbit",
                "label": "THE WHITE RABBIT",
                "is_dialogue": True,
                "scene_idx": 2,
                "page_idx": 2,
                "display_text": "“Oh dear! Oh dear! I shall be late!”",
                "tts_text": "Oh dear! Oh dear! I shall be late!",
                "style": "hurried, flustered British gentlemanly urgency, clear spoken voice",
                "pause_after_ms": 420,
            },
            {
                "speaker": "carroll_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 3,
                "page_idx": 3,
                "display_text": (
                    "But when the Rabbit actually took a watch out of its"
                    " waistcoat-pocket, and looked at it, and then hurried on, Alice"
                    " started to her feet, for it flashed across her mind that she had"
                    " never before seen a rabbit with either a waistcoat-pocket, or a"
                    " watch to take out of it, and burning with curiosity, she ran"
                    " across the field after it, and fortunately was just in time to"
                    " see it pop down a large rabbit-hole under the hedge."
                ),
                "tts_text": (
                    "But when the Rabbit actually took a watch out of its"
                    " waistcoat-pocket, and looked at it, and then hurried on, Alice"
                    " started to her feet, for it flashed across her mind that she had"
                    " never before seen a rabbit with either a waistcoat-pocket, or a"
                    " watch to take out of it, and burning with curiosity, she ran"
                    " across the field after it, and fortunately was just in time to"
                    " see it pop down a large rabbit-hole under the hedge."
                ),
                "style": "animated, building wonder and momentum",
                "pause_after_ms": 480,
            },
            {
                "speaker": "carroll_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 4,
                "page_idx": 4,
                "display_text": (
                    "In another moment down went Alice after it, never once"
                    " considering how in the world she was to get out again. The"
                    " rabbit-hole went straight on like a tunnel for some way, and"
                    " then dipped suddenly down, so suddenly that Alice had not a"
                    " moment to think about stopping herself before she found herself"
                    " falling down a very deep well."
                ),
                "tts_text": (
                    "In another moment down went Alice after it, never once"
                    " considering how in the world she was to get out again. The"
                    " rabbit-hole went straight on like a tunnel for some way, and"
                    " then dipped suddenly down, so suddenly that Alice had not a"
                    " moment to think about stopping herself before she found herself"
                    " falling down a very deep well."
                ),
                "style": "expressive, graceful, wondering",
                "pause_after_ms": 600,
            },
        ],
    },
    {
        "id": "04_the_time_machine",
        "roman": "IV",
        "title": "The Time Machine",
        "author": "H. G. Wells",
        "year": "1895",
        "chapter_title": "Chapter I · Introduction",
        "genre": "Philosophical Science Fiction",
        "setting": "The Time Traveller’s Smoking-Room, London",
        "palette": {
            "paper": "#F0F2F4",
            "card": "#E4E8EC",
            "ink": "#18222C",
            "muted": "#64707D",
            "accent": "#B38628",  # Horological burnished brass
            "rule": "#C8D0D8",
        },
        "char_sheet_prompt": (
            "Minimalist architectural line and woodcut book illustration character"
            " reference sheet on pale slate-ivory paper (#F0F2F4). Clean Prussian-blue"
            " (#18222C) ink linework with warm burnished brass-gold (#B38628) accents"
            " and generous negative space. Show two distinct full-length 1895"
            " Victorian gentlemen side by side: on the left, a lean, pale-faced"
            " late-Victorian natural philosopher in his late thirties with tousled"
            " dark brown hair, bright grey eyes, and a short trim beard, wearing an"
            " unbuttoned dark charcoal waistcoat over a white linen shirt and dark"
            " trousers, raising one lean forefinger in explanation; on the right, an"
            " argumentative Victorian gentleman in his thirties with thick wavy"
            " auburn-red hair and a neat red moustache, wearing a warm brown wool"
            " frock coat and high collar, arms folded in sceptical debate. Minimalist"
            " fine-press illustration, no text, no labels, no borders."
        ),
        "scenes": [
            {
                "id": "scene_1",
                "caption": "The Firelit Smoking-Room",
                "prompt": (
                    "Using the exact character designs and Prussian-blue"
                    " ink linework with burnished brass-gold accent style from the"
                    " reference image: a book illustration on pale"
                    " slate-ivory paper (#F0F2F4). In an 1895"
                    " Victorian smoking-room illuminated by warm brass lily-shaped"
                    " lamps, the lean pale-faced natural philosopher (tousled"
                    " dark brown hair, short trim beard, unbuttoned dark charcoal waistcoat)"
                    " stands before the hearth raising a"
                    " lean forefinger as he addresses his seated guests. Clean"
                    " architectural line art, no text."
                ),
            },
            {
                "id": "scene_2",
                "caption": "A Misconception of Geometry",
                "prompt": (
                    "Using the exact character designs and Prussian-blue (#18222C) ink"
                    " linework with burnished brass-gold (#B38628) accent style from"
                    " the reference image: a full-scene Victorian interior engraving on"
                    " pale slate-ivory paper (#F0F2F4). Inside a"
                    " firelit 1895 Victorian smoking-room with tall bookcases, a glowing"
                    " hearth, and silver lily-shaped wall sconces, the argumentative"
                    " gentleman (thick wavy auburn-red hair and neat red moustache in a"
                    " warm brown wool frock coat) leans forward skeptically in a tufted"
                    " leather armchair holding a small glass, while the lean natural"
                    " philosopher (dark charcoal waistcoat with brass watch-chain) stands"
                    " beside an octagonal parlor table raising an open hand in lucid"
                    " argument. Complete Victorian room environment filling the 16:9 frame,"
                    " no borders, no text."
                ),
            },
            {
                "id": "scene_3",
                "caption": "Lines and Planes of Thickness Nil",
                "prompt": (
                    "Using the exact character designs and Prussian-blue (#18222C) ink"
                    " linework with burnished brass-gold (#B38628) accent style from"
                    " the reference image: a full-scene Victorian scientific parlor"
                    " illustration on pale slate-ivory paper (#F0F2F4). Around a"
                    " polished Victorian parlor table illuminated by warm brass lily"
                    " lamps, with brass astrolabes, horological instruments, and"
                    " bookshelves in the background, the lean natural philosopher leans forward"
                    " tracing clean golden geometric lines and planes in the air above"
                    " the table, while the auburn-haired debater and an older silver-haired"
                    " Victorian scholar in spectacles watch closely from their armchairs."
                    " Full architectural interior, no borders, no text."
                ),
            },
            {
                "id": "scene_4",
                "caption": "“Can an Instantaneous Cube Exist?”",
                "prompt": (
                    "Using the exact character designs and Prussian-blue (#18222C) ink"
                    " linework with burnished brass-gold (#B38628) accent style from"
                    " the reference image: a dramatic Victorian interior illustration"
                    " on pale slate-ivory paper (#F0F2F4). In the firelit study with"
                    " tall clockwork mechanisms and bookshelves in the background, the"
                    " lean natural philosopher in sharp profile holds his hands on either side of"
                    " a gleaming geometric burnished-brass wireframe cube resting on"
                    " the parlor table, while the auburn-haired debater leans across the table"
                    " raising a hand in blunt objection. Full room environment filling"
                    " the 16:9 canvas, no borders, no text."
                ),
            },
            {
                "id": "scene_5",
                "caption": "The Fourth Dimension: Duration",
                "prompt": (
                    "Using the exact character designs and Prussian-blue (#18222C) ink"
                    " linework with burnished brass-gold (#B38628) accent style from"
                    " the reference image: a visionary Victorian architectural woodcut"
                    " on pale slate-ivory paper (#F0F2F4). In the shadowy Victorian"
                    " smoking-room framed by subtle concentric brass horological rings"
                    " and a tall grandfather clock, the auburn-haired debater sits back pensively with chin"
                    " on hand while the lean natural philosopher stands illuminated by warm"
                    " golden light beside a miniature brass, ivory, and quartz clockwork"
                    " mechanism on the table, marking the fourth dimension of Duration."
                    " Rich architectural line art filling the 16:9 canvas, no borders,"
                    " no text."
                ),
            },
        ],
        "turns": [
            {
                "speaker": "wells_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 0,
                "page_idx": 0,
                "display_text": (
                    "The Time Traveller (for so it will be convenient to speak of him)"
                    " was expounding a recondite matter to us. His grey eyes shone and"
                    " twinkled, and his usually pale face was flushed and animated."
                ),
                "tts_text": (
                    "The Time Traveller, for so it will be convenient to speak of him,"
                    " was expounding a recondite matter to us. His grey eyes shone and"
                    " twinkled, and his usually pale face was flushed and animated."
                ),
                "style": "reflective literary narration, pronounce recondite like REK-uhn-dite",
                "pause_after_ms": 440,
            },
            {
                "speaker": "wells_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 0,
                "page_idx": 0,
                "display_text": (
                    "The fire burnt brightly, and the soft radiance of the"
                    " incandescent lights in the lilies of silver caught the bubbles"
                    " that flashed and passed in our glasses. And he put it to us in"
                    " this way—marking the points with a lean forefinger."
                ),
                "tts_text": (
                    "The fire burnt brightly, and the soft radiance of the"
                    " incandescent lights in the lilies of silver caught the bubbles"
                    " that flashed and passed in our glasses. And he put it to us in"
                    " this way, marking the points with a lean forefinger."
                ),
                "style": "warm, atmospheric narration",
                "pause_after_ms": 480,
            },
            {
                "speaker": "time_traveller",
                "label": "THE TIME TRAVELLER",
                "is_dialogue": True,
                "scene_idx": 1,
                "page_idx": 1,
                "display_text": (
                    "“You must follow me carefully. I shall have to controvert one or"
                    " two ideas that are almost universally accepted. The geometry,"
                    " for instance, they taught you at school is founded on a"
                    " misconception.”"
                ),
                "tts_text": (
                    "You must follow me carefully. I shall have to controvert one or"
                    " two ideas that are almost universally accepted. The geometry,"
                    " for instance, they taught you at school is founded on a"
                    " misconception."
                ),
                "style": "lucid, engaged, intellectually assured",
                "pause_after_ms": 420,
            },
            {
                "speaker": "filby",
                "label": "FILBY",
                "is_dialogue": True,
                "scene_idx": 1,
                "page_idx": 1,
                "display_text": "“Is not that rather a large thing to expect us to begin upon?”",
                "tts_text": "Is not that rather a large thing to expect us to begin upon?",
                "style": "skeptical, wryly challenging",
                "pause_after_ms": 180,
            },
            {
                "speaker": "wells_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 1,
                "page_idx": 1,
                "display_text": "said Filby, an argumentative person with red hair.",
                "tts_text": "said Filby, an argumentative person with red hair.",
                "style": "calm narration, pronounce Filby like FIL-bee",
                "pause_after_ms": 400,
            },
            {
                "speaker": "time_traveller",
                "label": "THE TIME TRAVELLER",
                "is_dialogue": True,
                "scene_idx": 2,
                "page_idx": 2,
                "display_text": (
                    "“I do not mean to ask you to accept anything without reasonable"
                    " ground for it. You know of course that a mathematical line, a"
                    " line of thickness nil, has no real existence. Neither has a"
                    " mathematical plane. These things are mere abstractions.”"
                ),
                "tts_text": (
                    "I do not mean to ask you to accept anything without reasonable"
                    " ground for it. You know of course that a mathematical line, a"
                    " line of thickness nil, has no real existence. Neither has a"
                    " mathematical plane. These things are mere abstractions."
                ),
                "style": "precise, persuasive",
                "pause_after_ms": 360,
            },
            {
                "speaker": "psychologist",
                "label": "THE PSYCHOLOGIST",
                "is_dialogue": True,
                "scene_idx": 2,
                "page_idx": 2,
                "display_text": "“That is all right,”",
                "tts_text": "That is all right,",
                "style": "calm, matter-of-fact agreement",
                "pause_after_ms": 180,
            },
            {
                "speaker": "wells_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 2,
                "page_idx": 2,
                "display_text": "said the Psychologist.",
                "tts_text": "said the Psychologist.",
                "style": "measured narration",
                "pause_after_ms": 380,
            },
            {
                "speaker": "time_traveller",
                "label": "THE TIME TRAVELLER",
                "is_dialogue": True,
                "scene_idx": 3,
                "page_idx": 3,
                "display_text": (
                    "“Nor, having only length, breadth, and thickness, can a cube have"
                    " a real existence.”"
                ),
                "tts_text": (
                    "Nor, having only length, breadth, and thickness, can a cube have"
                    " a real existence."
                ),
                "style": "deliberate, provocative",
                "pause_after_ms": 360,
            },
            {
                "speaker": "filby",
                "label": "FILBY",
                "is_dialogue": True,
                "scene_idx": 3,
                "page_idx": 3,
                "display_text": (
                    "“There I object,” said Filby. “Of course a solid body may exist."
                    " All real things—”"
                ),
                "tts_text": "There I object. Of course a solid body may exist. All real things—",
                "style": "blunt, objecting",
                "pause_after_ms": 280,
            },
            {
                "speaker": "time_traveller",
                "label": "THE TIME TRAVELLER",
                "is_dialogue": True,
                "scene_idx": 4,
                "page_idx": 4,
                "display_text": (
                    "“So most people think. But wait a moment. Can an instantaneous"
                    " cube exist? Can a cube that does not last for any time at all,"
                    " have a real existence?”"
                ),
                "tts_text": (
                    "So most people think. But wait a moment. Can an instantaneous"
                    " cube exist? Can a cube that does not last for any time at all,"
                    " have a real existence?"
                ),
                "style": "quietly intense, pointed question",
                "pause_after_ms": 420,
            },
            {
                "speaker": "wells_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 4,
                "page_idx": 4,
                "display_text": "Filby became pensive.",
                "tts_text": "Filby became pensive.",
                "style": "quiet narration, pronounce Filby like FIL-bee",
                "pause_after_ms": 380,
            },
            {
                "speaker": "time_traveller",
                "label": "THE TIME TRAVELLER",
                "is_dialogue": True,
                "scene_idx": 4,
                "page_idx": 4,
                "display_text": (
                    "“Clearly,” the Time Traveller proceeded, “any real body must have"
                    " extension in four directions: it must have Length, Breadth,"
                    " Thickness, and—Duration.”"
                ),
                "tts_text": (
                    "Clearly, any real body must have extension in four directions: it"
                    " must have Length, Breadth, Thickness, and <short pause> Duration."
                ),
                "style": "measured, resonant revelation",
                "pause_after_ms": 600,
            },
        ],
    },
    {
        "id": "05_tom_sawyer",
        "roman": "V",
        "title": "The Adventures of Tom Sawyer",
        "author": "Mark Twain",
        "year": "1876",
        "chapter_title": "Chapter I · Y-o-u-u Tom—Aunt Polly Decides Upon Her Duty",
        "genre": "Mississippi River Americana",
        "setting": "St. Petersburg, Missouri",
        "palette": {
            "paper": "#F6EFE4",
            "card": "#EDE3D3",
            "ink": "#261E19",
            "muted": "#7A6D61",
            "accent": "#B85733",  # Sun-baked terracotta
            "rule": "#D6C8B4",
        },
        "char_sheet_prompt": (
            "Minimalist 19th-century American woodcut and dip-pen book illustration"
            " character reference sheet on warm cotton-rag paper (#F6EFE4). Crisp"
            " walnut-brown ink linework (#261E19) with warm indigo-blue and"
            " sun-baked terracotta (#B85733) accents and wide negative space. Show"
            " two distinct full-length 1840s American frontier characters side by"
            " side: on the left, a tall, kindly sixty-year-old 1840s American"
            " frontier woman with grey hair pulled into a neat bun, small square"
            " brass spectacles pushed high up on her forehead, wearing a plain"
            " indigo-dyed homespun cotton ankle-length dress, a clean white linen"
            " apron, and black leather ankle shoes on her feet (wearing shoes, NOT"
            " barefoot); on the right, a wiry ten-year-old 1840s country boy with"
            " messy sun-bleached brown hair (no hat), wearing a short buttoned tan"
            " wool 'roundabout' jacket over a terracotta homespun shirt and"
            " rolled-up patched trousers with bare feet, his empty hands at his"
            " sides with dark berry-jam smudges on his cheeks and hands. Minimalist"
            " printmaking style, no text, no labels, no borders."
        ),
        "scenes": [
            {
                "id": "scene_1",
                "caption": "At the Garden Door",
                "prompt": (
                    "Using the exact character designs and walnut-brown"
                    " woodcut with sun-baked terracotta (#B85733) accent style from the"
                    " reference image: a full-bleed 16:9 horizontal book illustration"
                    " directly on warm cotton-rag paper (#F6EFE4) with NO borders and"
                    " NO rectangular frame. On the sunlit wooden back porch of an"
                    " 1840s American frontier clapboard cottage, the sixty-year-old woman"
                    " (grey hair in a bun, white linen apron over indigo-dyed homespun dress,"
                    " small round brass spectacles pushed up high on her forehead) stands holding a"
                    " corn-husk broom and calling out across a summer kitchen garden"
                    " filled with tall staked tomato vines, jimsonweed, and a whitewashed"
                    " board fence. Clean American regionalist woodcut print lines spanning the"
                    " full horizontal width, no border box, no text."
                ),
            },
            {
                "id": "scene_2",
                "caption": "The State Spectacles",
                "prompt": (
                    "Using the exact character designs and walnut-brown"
                    " woodcut with sun-baked terracotta (#B85733) accent style from the"
                    " reference image: a full-scene 1840s frontier kitchen interior"
                    " woodcut on warm cotton-rag paper (#F6EFE4) with no borders."
                    " Inside a sunlit clapboard kitchen with a cast-iron wood stove,"
                    " wooden table, and a pantry closet door standing slightly ajar in"
                    " the background, the sixty-year-old woman stands with both empty hands resting"
                    " on her hips over her clean white apron (holding nothing, no"
                    " utensils), tilting her head back to peer out under her small"
                    " round spectacles perched high on her forehead while a barefoot"
                    " ten-year-old country boy peeks stealthily from the shadowed pantry doorway. Full"
                    " room environment filling the 16:9 canvas, no borders, no text."
                ),
            },
            {
                "id": "scene_3",
                "caption": "Caught by the Roundabout",
                "prompt": (
                    "Using the exact character designs and walnut-brown"
                    " woodcut with sun-baked terracotta accent style from the"
                    " reference image: a book illustration on warm"
                    " cotton-rag paper (#F6EFE4). Beside an"
                    " open pantry door with a terracotta jam crock on the shelf, the"
                    " sixty-year-old woman holds the barefoot ten-year-old country boy by the collar of his short"
                    " tan wool roundabout jacket, pointing sternly at the berry-jam smudge"
                    " on his mouth while the boy looks up innocently. Woodcut"
                    " line art, no text."
                ),
            },
            {
                "id": "scene_4",
                "caption": "The Hovering Switch",
                "prompt": (
                    "Using the exact character designs and walnut-brown"
                    " woodcut with sun-baked terracotta (#B85733) accent style from the"
                    " reference image: a dramatic full-scene 1840s frontier kitchen"
                    " woodcut on warm cotton-rag paper (#F6EFE4) with no borders."
                    " Beside the open pantry lined with terracotta jam crocks and"
                    " wooden shelves, the stern sixty-year-old woman raises a slender birch switch"
                    " in one hand while holding the barefoot ten-year-old country boy by his short"
                    " roundabout jacket; the boy (with a berry-jam smudge by his"
                    " mouth) points urgently past the woman's shoulder with a startled"
                    " expression as if warning her of danger behind her. Full interior"
                    " composition filling the 16:9 canvas, no borders, no text."
                ),
            },
            {
                "id": "scene_5",
                "caption": "Over the High Board-Fence",
                "prompt": (
                    "Using the exact character designs and walnut-brown"
                    " woodcut with sun-baked terracotta accent style from the"
                    " reference image: a book illustration on warm"
                    " cotton-rag paper (#F6EFE4). The barefoot"
                    " ten-year-old country boy in his short roundabout jacket scrambles agilely over"
                    " the top of a high wooden board-fence in the background, gripping"
                    " the top wooden planks with both empty hands, while in the"
                    " foreground the sixty-year-old woman stands turned around with a single pair of"
                    " spectacles pushed up on her forehead, breaking into a gentle,"
                    " surprised smile. Clean woodcut printmaking, no text."
                ),
            },
        ],
        "turns": [
            {
                "speaker": "aunt_polly",
                "label": "AUNT POLLY",
                "is_dialogue": True,
                "scene_idx": 0,
                "page_idx": 0,
                "display_text": "“TOM!”",
                "tts_text": "TOM!",
                "style": "calling out firmly across a quiet house",
                "pause_after_ms": 420,
            },
            {
                "speaker": "twain_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 0,
                "page_idx": 0,
                "display_text": "No answer.",
                "tts_text": "No answer.",
                "style": "dry, unhurried storytelling",
                "pause_after_ms": 420,
            },
            {
                "speaker": "aunt_polly",
                "label": "AUNT POLLY",
                "is_dialogue": True,
                "scene_idx": 0,
                "page_idx": 0,
                "display_text": "“What’s gone with that boy, I wonder? You TOM!”",
                "tts_text": "What's gone with that boy, I wonder? You TOM!",
                "style": "speaking to herself in puzzled exasperation, then calling out clearly across the room",
                "pause_after_ms": 420,
            },
            {
                "speaker": "twain_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 1,
                "page_idx": 1,
                "display_text": (
                    "No answer. The old lady pulled her spectacles down and looked over"
                    " them about the room; then she put them up and looked out under"
                    " them. She seldom or never looked through them for so small a"
                    " thing as a boy; they were her state pair, the pride of her heart,"
                    " and were built for “style,” not service—she could have seen"
                    " through a pair of stove-lids just as well."
                ),
                "tts_text": (
                    "No answer. The old lady pulled her spectacles down and looked over"
                    " them about the room; then she put them up and looked out under"
                    " them. She seldom or never looked through them for so small a"
                    " thing as a boy; they were her state pair, the pride of her heart,"
                    " and were built for style, not service—she could have seen"
                    " through a pair of stove-lids just as well."
                ),
                "style": "warm, wry, affectionate humor",
                "pause_after_ms": 500,
            },
            {
                "speaker": "twain_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 2,
                "page_idx": 2,
                "display_text": (
                    "There was a slight noise behind her and she turned just in time to"
                    " seize a small boy by the slack of his roundabout and arrest his"
                    " flight."
                ),
                "tts_text": (
                    "There was a slight noise behind her and she turned just in time to"
                    " seize a small boy by the slack of his roundabout and arrest his"
                    " flight."
                ),
                "style": "lively narrative pacing",
                "pause_after_ms": 380,
            },
            {
                "speaker": "aunt_polly",
                "label": "AUNT POLLY",
                "is_dialogue": True,
                "scene_idx": 2,
                "page_idx": 2,
                "display_text": (
                    "“There! I might ’a’ thought of that closet. What you been doing"
                    " in there?”"
                ),
                "tts_text": "There! I might a thought of that closet. What you been doing in there?",
                "style": "sharp, triumphant, suspicious",
                "pause_after_ms": 300,
            },
            {
                "speaker": "tom_sawyer",
                "label": "TOM SAWYER",
                "is_dialogue": True,
                "scene_idx": 2,
                "page_idx": 2,
                "display_text": "“Nothing.”",
                "tts_text": "Nothing.",
                "style": "innocent, sheepish",
                "pause_after_ms": 300,
            },
            {
                "speaker": "aunt_polly",
                "label": "AUNT POLLY",
                "is_dialogue": True,
                "scene_idx": 3,
                "page_idx": 3,
                "display_text": (
                    "“Nothing! Look at your hands. And look at your mouth. What is"
                    " that truck?”"
                ),
                "tts_text": "Nothing! Look at your hands. And look at your mouth. What IS that truck?",
                "style": "scolding, incredulous",
                "pause_after_ms": 300,
            },
            {
                "speaker": "tom_sawyer",
                "label": "TOM SAWYER",
                "is_dialogue": True,
                "scene_idx": 3,
                "page_idx": 3,
                "display_text": "“I don’t know, aunt.”",
                "tts_text": "I don't know, aunt.",
                "style": "meek, feigning ignorance",
                "pause_after_ms": 300,
            },
            {
                "speaker": "aunt_polly",
                "label": "AUNT POLLY",
                "is_dialogue": True,
                "scene_idx": 3,
                "page_idx": 3,
                "display_text": (
                    "“Well, I know. It’s jam—that’s what it is. Forty times I’ve said"
                    " if you didn’t let that jam alone I’d skin you. Hand me that"
                    " switch.”"
                ),
                "tts_text": (
                    "Well, I know. It's jam—that's what it is. Forty times I've said"
                    " if you didn't let that jam alone I'd skin you. Hand me that"
                    " switch."
                ),
                "style": "stern, exasperated authority",
                "pause_after_ms": 420,
            },
            {
                "speaker": "twain_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 4,
                "page_idx": 4,
                "display_text": "The switch hovered in the air—the peril was desperate—",
                "tts_text": "The switch hovered in the air... the peril was desperate...",
                "style": "mock-dramatic suspense",
                "pause_after_ms": 320,
            },
            {
                "speaker": "tom_sawyer",
                "label": "TOM SAWYER",
                "is_dialogue": True,
                "scene_idx": 4,
                "page_idx": 4,
                "display_text": "“My! Look behind you, aunt!”",
                "tts_text": "My! Look behind you, aunt!",
                "style": "urgent, startled warning",
                "pause_after_ms": 340,
            },
            {
                "speaker": "twain_narrator",
                "label": "NARRATOR",
                "is_dialogue": False,
                "scene_idx": 4,
                "page_idx": 4,
                "display_text": (
                    "The old lady whirled round, and snatched her skirts out of"
                    " danger. The lad fled on the instant, scrambled up the high"
                    " board-fence, and disappeared over it. His aunt Polly stood"
                    " surprised a moment, and then broke into a gentle laugh."
                ),
                "tts_text": (
                    "The old lady whirled round, and snatched her skirts out of"
                    " danger. The lad fled on the instant, scrambled up the high"
                    " board-fence, and disappeared over it. His aunt Polly stood"
                    " surprised a moment, and then broke into a gentle laugh."
                ),
                "style": "brisk action, softening into warm affectionate amusement",
                "pause_after_ms": 600,
            },
        ],
    },
]

import re as _re

FORBIDDEN_WORDS = [
    # Book 1
    "bennet",
    "bingley",
    "darcy",
    "longbourn",
    "netherfield",
    "austen",
    "pride",
    "prejudice",
    "hertfordshire",
    # Book 2
    "holmes",
    "sherlock",
    "watson",
    "mortimer",
    "baskerville",
    "baskervilles",
    "baker street",
    "221b",
    "conan doyle",
    "paget",
    "charing cross",
    "penang",
    "devonshire",
    "grimpen",
    "london",
    # Book 3
    "alice",
    "dinah",
    "wonderland",
    "carroll",
    "tenniel",
    "oxfordshire",
    "oxford",
    # Book 4
    "time traveller",
    "time machine",
    "filby",
    "wells",
    "eloi",
    "morlock",
    "psychologist",
    "richmond",
    # Book 5
    "tom",
    "sawyer",
    "polly",
    "sid",
    "twain",
    "st. petersburg",
    "missouri",
    "rockwell kent",
    "huck",
    "finn",
    "harper",
]


def assert_no_forbidden_words(prompt: str, context: str = "") -> None:
    """Assert that an image generation prompt contains zero character names, book titles,
    author/illustrator names, or famous place names.
    """
    low = prompt.lower()
    for word in FORBIDDEN_WORDS:
        pattern = r"\b" + _re.escape(word.lower()) + r"\b"
        if _re.search(pattern, low):
            ctx_prefix = f"[{context}] " if context else ""
            raise ValueError(
                f"{ctx_prefix}Forbidden word '{word}' found in image prompt: {prompt!r}"
            )


def validate_books_spec_prompts() -> None:
    for book in BOOKS_SPEC:
        bid = book["id"]
        assert_no_forbidden_words(book["char_sheet_prompt"], f"{bid}.char_sheet_prompt")
        for sc in book.get("scenes", []):
            assert_no_forbidden_words(
                sc["prompt"], f"{bid}.scenes.{sc['id']}.prompt"
            )


validate_books_spec_prompts()

