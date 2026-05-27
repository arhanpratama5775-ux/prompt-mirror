# prompt-mirror

ever looked at your chatgpt history and thought "wow i really asked that huh"

yeah me too. that's basically why this exists.

---

the idea is simple. you export your AI conversations, feed them into this thing, and it gives you a mirror report. not a score, not a grade, just a mirror. shows you what you've been asking about, when you ask, how you ask, and what patterns are hiding in there.

> "the unexamined life is not worth living" - socrates

sounds dramatic for a CLI tool but hear me out. most of us talk to AI every day and never look back at what we actually said. we ask questions, get answers, move on. but stack up 800+ conversations and you start seeing things. like how 40% of your prompts are about coding and 0% are about your actual life. or how you keep asking "should I..." instead of deciding for yourself.

> "know thyself" - some ancient greek at a temple

that's what this does. it doesn't judge. it just shows you what's already there.

---

### what you get

```
==================================================
           YOUR MIRROR REPORT
==================================================

OVERVIEW:
  Total conversations: 847
  Total prompts by you: 2,341
  Date range: Jan 2025 - May 2026

YOUR TOP 5 TOPICS:
  1. Coding & Programming (42%)
  2. Writing & Content (18%)
  3. Learning & Research (15%)
  4. Decision Making (12%)
  5. Creative Projects (8%)

WHEN YOU ASK:
  Evening (18-24): 412 prompts
  Morning (6-12): 318 prompts
  Night (0-6): 203 prompts

PATTERNS DETECTED:
  - You ask "how" questions 3x more than "why" questions
  - Over 40% of prompts are about Coding & Programming
  - You ask "should" questions frequently (18% of prompts)

REFLECTION QUESTIONS:
  1. You've spent 200+ prompts on coding & programming.
     Is this aligned with your priorities?
  2. Only 5% of prompts about personal life. Intentional?
  3. Are you outsourcing decisions you could make yourself?
  4. What would you ask if AI didn't exist?
  5. What did you learn this month that you still remember?

==================================================
```

a mirror, not a judgment. use it however you want.

---

### install

```bash
git clone https://github.com/arhanpratama5775-ux/prompt-mirror.git
cd prompt-mirror
pip install -e .

# or with everything
pip install -e ".[all]"
```

optional stuff:
- `[viz]` charts n visualizations (needs matplotlib)
- `[pdf]` export to pdf (needs reportlab)
- `[all]` all of the above

---

### how to use

**step 1: export your conversations**

| platform | how |
|----------|-----|
| chatgpt | settings > data controls > export data |
| claude | settings > export data |
| gemini | settings > export your data |

**step 2: run it**

```bash
prompt-mirror analyze ~/Downloads/conversations.json

# with your timezone
prompt-mirror analyze ~/Downloads/conversations.json --timezone "Asia/Jakarta"

# save to file
prompt-mirror analyze ~/Downloads/conversations.json --output report.txt

# different formats
prompt-mirror analyze ~/Downloads/conversations.json --format json --output report.json
prompt-mirror analyze ~/Downloads/conversations.json --format markdown --output report.md
```

**step 3: stare at the mirror**

you'll see:
- what topics you ask about most
- when you're most active
- how you frame your questions
- behavioral patterns you might not notice
- reflection questions to think about

---

### other commands

```bash
# trend analysis over time
prompt-mirror trend conversations.json

# charts
prompt-mirror visualize conversations.json --output charts/

# pdf report
prompt-mirror analyze conversations.json --format pdf --output report.pdf

# list topics
prompt-mirror topics

# quick stats
prompt-mirror stats conversations.json --timezone "Asia/Jakarta"

# export guide
prompt-mirror guide
```

---

### adding your own topics

by default there's 10 topics built in (coding, writing, learning, etc). but maybe that's not you. maybe you're a gamer who asks AI about elden ring builds at 3am. maybe you're a crypto degen asking about memecoins. i don't judge.

here's how to add your own. open `prompt_mirror/analyzer.py` and find the `TOPIC_KEYWORDS` dictionary. it looks like this:

```python
TOPIC_KEYWORDS = {
    "Coding & Programming": [
        "code", "function", "error", "bug", ...
    ],
    "Writing & Content": [
        "write", "article", "blog", ...
    ],
    # ... more topics
}
```

just add your own at the bottom, before the closing `}`:

```python
    # your custom topics go here
    "Gaming": [
        "game", "gaming", "fps", "rpg", "build", "strategy",
        "boss", "level", "quest", "rank", "match", "lobby",
        "steam", "console", "controller", "co-op", "mmorpg",
        "elden ring", "valorant", "minecraft", "fortnite", "gta"
    ],
    "Finance & Trading": [
        "stock", "crypto", "bitcoin", "ethereum", "trading",
        "invest", "portfolio", "dividend", "market", "price",
        "bull", "bear", "coin", "token", "defi", "nft",
        "saham", "reksadana", "deposito", "bumn"
    ],
    "Music": [
        "music", "song", "guitar", "piano", "chord", "beat",
        "melody", "lyrics", "album", "spotify", "genre",
        "produce", "mix", "master", "vocal", "bass", "drum"
    ],
    "Fitness & Health": [
        "workout", "gym", "exercise", "diet", "calories",
        "protein", "cardio", "weight", "muscle", " reps",
        "set", "squat", "deadlift", "bench", "run", "yoga"
    ],
    "Cooking & Food": [
        "recipe", "cook", "bake", "ingredient", "meal",
        "dish", "sauce", "season", "taste", "oven",
        "fry", "grill", "chop", "saut\u00e9", "nasi goreng"
    ],
```

a few tips so you don't break things:

1. **order matters.** topics are checked top to bottom, first match wins. so if you put "Problem Solving" before "Gaming", a prompt like "help me fix my game strategy" will get tagged as Problem Solving, not Gaming. put your specific topics above the generic ones.

2. **use lowercase keywords.** the matching is case-insensitive so just write them in lowercase, no need to yell.

3. **keep keywords unique per topic.** don't put "build" in both Gaming and Coding. well, you can, but whichever topic comes first will steal all the "build" prompts. that's just how it works. life isn't fair.

4. **word boundaries.** the tool matches whole words, so "art" won't accidentally match "start". you're safe. unless you add "art" as a keyword and wonder why "artificial" doesn't trigger it. that's why, it needs to be a whole word.

5. **you can also remove topics** you don't care about. just delete the entry from the dictionary. if you never ask about "Planning & Organization" then why keep it around taking up space.

6. **run `prompt-mirror topics`** after editing to verify your changes show up correctly.

that's it. go make this tool yours.

---

### some thoughts on why this matters

> "we are what we repeatedly do" - aristotle

your conversation patterns are habits. some help you grow, some just help the algorithm. did you pick them, or did they pick you?

> "until you make the unconscious conscious, it will direct your life and you will call it fate" - jung

this one hits different when you see it in your own data. those patterns in your AI chats? they're unconscious habits. they'll steer you whether you look at them or not.

> "man is condemned to be free" - sartre

every "should I..." you throw at AI is a moment where you're handing your freedom to a machine. not saying don't ask. just saying notice when you're doing it.

> "he who knows others is wise; he who knows himself is enlightened" - lao tzu

> "we shape our tools and thereafter our tools shape us" - mcluhan

ai isn't just a tool anymore. it changes how you think, what you ask, what you value. when you talk to it every day, you're being shaped. the question is whether you're shaping yourself on purpose.

> "the chains of habit are too light to be felt until they are too heavy to be broken" - samuel johnson

> "between stimulus and response there is a space. in that space is our power to choose our response" - viktor frankl

> "the ignorant man is not the one who does not know, but the one who does not know that he does not know" - al-ghazali

> "a person's intelligence is measured by the questions they ask, not the answers they give" - ibn khaldun

this tool doesn't analyze AI's answers. it analyzes your questions. because the quality of your questions shows the depth of your thinking. at least that's what ibn khaldun would say and i'm not gonna argue with him.

> "you have power over your mind, not outside events" - marcus aurelius

> "it is not things that disturb us, but our judgments about things" - epictetus

> "the only way to deal with an unfree world is to become so absolutely free that your very existence is an act of rebellion" - camus

> "the knowledge of anything, since all things have causes, is not acquired or complete unless it is known by its causes" - ibn sina

> "real knowledge is to know the extent of one's ignorance" - confucius

---

### privacy

everything runs locally. no api calls, no data collection, your conversations never leave your machine. period.

| file | what it is | has your data? |
|------|-----------|----------------|
| mirror-report.txt/json/md | the report | yes |
| charts/*.png | visualizations | yes, aggregated |
| *.pdf | pdf reports | yes |
| trends.txt/json | trend analysis | yes |

delete when done:
```bash
rm -rf mirror-report.* charts/ *.pdf trends.*
```

---

### troubleshooting

**"Invalid timezone 'XXX'"** use IANA format like `Asia/Jakarta`, `America/New_York`, not `WIB` or `GMT+7`

**"No conversations found"** make sure the export is valid JSON, path is correct, and format is supported (chatgpt/claude/gemini)

**"File too large (500MB+)"** split it or export only recent conversations

**"reportlab is required"** run `pip install -e ".[pdf]"`

**"matplotlib is required"** run `pip install -e ".[viz]"`

---

### who's this for

| if you are | this might help you |
|------------|-------------------|
| someone who uses AI a lot | see what you've actually been doing |
| prompt engineer | understand your patterns |
| self-improver type | examine unconscious habits |
| researcher | analyze human-AI interaction |
| philosophy nerd | apply old wisdom to new tech |
| someone who asks "should I..." too much | yeah this one's for you |

---

### full command reference

```bash
prompt-mirror analyze <file> [options]
  --format, -f    text, json, markdown, pdf
  --output, -o    output file path
  --timezone, -tz your timezone
  --no-color      no colored output

prompt-mirror trend <file> [options]
  --format, -f    text, json
  --output, -o    output file path
  --timezone, -tz your timezone

prompt-mirror visualize <file> [options]
  --output, -o    output directory
  --summary       single summary image

prompt-mirror topics
prompt-mirror stats <file> [options]
  --timezone, -tz your timezone
prompt-mirror guide
```

---

### use it programmatically

```python
from prompt_mirror.parser import ConversationParser
from prompt_mirror.analyzer import PromptAnalyzer

parser = ConversationParser()
conversations = parser.parse('conversations.json', local_timezone='Asia/Jakarta')

analyzer = PromptAnalyzer()
result = analyzer.analyze(conversations)

print(f"Total prompts: {result.total_user_prompts}")
print(f"Top topic: {result.topics[0].name}")
print(f"Patterns: {[p.description for p in result.patterns]}")
```

---

### contributing

yeah sure, why not. check [CONTRIBUTING.md](CONTRIBUTING.md).

### license

MIT. do whatever.

---

> "life can only be understood backwards; but it must be lived forwards" - kierkegaard
