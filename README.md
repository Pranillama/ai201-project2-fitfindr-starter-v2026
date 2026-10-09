# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

A user asks for a thrift find in plain words, like `python app.py ask 'vintage graphic tee under $30'`, optionally with a size (`size M`) and a price ceiling. FitFindr pulls the description, size, and budget out of the query, searches 40 listings from Depop, ThredUp, and Poshmark, and picks the best match. It then suggests one or two outfits built from clothes the user already owns (or general styling advice if their wardrobe is empty) and writes a short caption they could post about the find. If nothing matches, it stops before calling the model and says which part of the search to change, such as raising the budget or dropping the size.



---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the 40 listings in `data/listings.json` (loaded with `utils/data_loader.load_listings`) by price and size, then ranks what is left by how many description keywords appear in each listing's `title`, `description`, `style_tags`, `category`, and `colors`, and keeps only listings that match more than half of the distinct keywords (`len(keywords) // 2 + 1`: 1 of 1, 2 of 2, 2 of 3, 3 of 4 or 5).
- **Inputs:**
  - `description` (str): keywords such as `"vintage graphic tee"`. Matched case-insensitively, with filler words (`under`, `size`, `in`, `a`, `the`, ...) dropped.
  - `size` (str or None): `None` skips size filtering. Otherwise the asked size and the listing's `size` are each split into pieces on spaces, `/`, and parentheses, and the listing matches when every piece of the asked size appears among the listing's pieces, case-insensitively. So `"M"` matches `M`, `S/M`, `M/L`; `"S"` does not match `US 9`; `"8"` and `"US 8"` match `US 8` but not `US 8.5`; `"W30"` matches `W30 L30`. Any listing whose size starts with `One Size` matches every size.
  - `max_price` (float or None): `None` skips price filtering. Otherwise keeps listings with `price <= max_price`.
- **Returns:** A `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` (10) listing dicts, highest keyword score first, ties kept in data-file order. Each dict is the full listing, unchanged: `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None), `platform`. Listings that match half the keywords or fewer are dropped (so a single shared word cannot carry a multi-word query).
- **When it has nothing:** Returns an empty list `[]`. Never `None`, never raises.

### `suggest_outfit`

- **What it does:** Asks the model (through `generate()`) for one or two outfits built around the new item, using pieces the user already owns.
- **Inputs:**
  - `new_item` (dict): one listing dict, as returned by `search_listings`.
  - `wardrobe` (dict): `{"items": [...]}`, where each item has `id`, `name`, `category`, `colors` (list), `style_tags` (list), `notes`.
- **Returns:** A non-empty `str` with one or two outfit suggestions that name wardrobe pieces by their `name`.
- **When it has nothing:** If `wardrobe["items"]` is empty (`{"items": []}`), it still calls the model, asks for general styling advice for the item instead, and returns that as a non-empty `str`. It never returns `""` and never raises for an empty wardrobe.

### `create_fit_card`

- **What it does:** Asks the model (through `generate()`) for a short caption someone would actually post about the find.
- **Inputs:**
  - `outfit` (str): the suggestion returned by `suggest_outfit`.
  - `new_item` (dict): the same listing dict that went into `suggest_outfit`.
- **Returns:** A `str` caption of two to four sentences that mentions the item's `title`, `price`, and `platform` once each and is specific about the vibe. `brand` goes into the prompt only when it is not `None`.
- **When it has nothing:** If `outfit` is empty or only whitespace, it does not call the model and returns a message string starting with `No fit card:` that says the outfit suggestion was missing. It never raises.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that repeats the description, size, and price ceiling that were searched and suggests which one to loosen, then return the session without calling `suggest_outfit` or `create_fit_card` (so `session["fit_card"]` stays `None`). Otherwise, put the first result in `session["selected_item"]` and go to `suggest_outfit`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::parse_query`. A price ceiling (`under $30`, `below 30`, `up to $30`, `max $30`, or a bare `$30`) becomes `max_price` (float). `size` followed by a size (`size M`, `in size S/M`, `size 8.5`, `size US 8`) becomes `size` (str, uppercased). Both matches are cut out of the query, punctuation is removed, and what is left becomes `description`. Anything not found is `None`. No model call.

**What moves through the session:** In order: `query` → `parsed` (`description`, `size`, `max_price`) → `search_results` (the list from `search_listings`) → `selected_item` (`search_results[0]`) → `outfit_suggestion` (from `suggest_outfit(selected_item, wardrobe)`) → `fit_card` (from `create_fit_card(outfit_suggestion, selected_item)`). Each tool reads its inputs back out of the session, not from the previous call. On the empty branch, `error` is set and `selected_item`, `outfit_suggestion`, and `fit_card` stay `None`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit 1
Pair the Y2K Baby Tee with the baggy straight-leg jeans, vintage black denim jacket, and chunky white sneakers. Add the black crossbody bag for an effortless everyday streetwear look that balances the fitted crop top with relaxed denim.

Outfit 2
Style the Y2K Baby Tee with the wide-leg khaki trousers, black combat boots, and the black cropped zip hoodie worn unzipped. Finish with the brown leather belt to tie the earth tones and grunge elements together.

  Fit card: Scored this Y2K Baby Tee — Butterfly Print for just $18 over on depop and I'm obsessed. I've been wearing it non-stop, either with baggy jeans and chunky sneakers for casual streetwear days, or toughened up with wide-leg trousers and combat boots. It's the ultimate little crop top to throw on when you want to look put together with zero effort.

2 model calls this session, 766 prompt + 183 output tokens
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Outfit One: Streetwear Casual
Pair the Vintage Levi's 501 Jeans with the white ribbed tank top tucked in. Layer on the oversized grey crewneck sweatshirt and finish with the chunky white sneakers and black crossbody bag.

Outfit Two: Edge and Vintage
Style the Vintage Levi's 501 Jeans with the brown leather belt. Add the black cropped zip hoodie and layer the vintage black denim jacket on top. Ground the look with the black combat boots.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Scored these Vintage Levi's 501 Jeans — Medium Wash on depop for only $38 and I'm obsessed with the knee fading. Just threw them on with my beat-up white sneakers for an effortless errand-running look. They fit like an absolute dream.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1: attacking my acceptance criteria (Milestone 3)**

- *What I asked for:* I wrote criteria 3, 4, and 5 myself, then gave all five to Claude and asked it to say exactly how it would test each one using only the sentence, without rewriting them.
- *What came back:* Criteria 3 and 5 could be tested as written, but criterion 4 (the fit card) could not. All 40 listing titles contain an em dash that the model might rewrite as a hyphen or drop along with the subtitle, a price like `$25.00` breaks a naive sentence count, and "mentions the platform exactly once" didn't say whether `on Depop` plus `#depop` counts as two mentions. It also pointed out that criteria 1 and 2 still had no reasons under them.
- *What I changed:* I added explicit scoring rules to criterion 4: titles compare case-insensitively with any dash treated as a hyphen but the subtitle required, platform mentions count hashtags, only `$N` or `$N.00` counts as a price and the card must contain exactly one dollar amount, and sentences are counted after removing hashtags without splitting on a period between digits. I also wrote the reasons for criteria 1 and 2.

**Moment 2: the fit card's voice (Milestone 4)**

- *What I asked for:* I had Claude build `create_fit_card` from my Tool Inventory spec and run it three times on the Levi's 501s with the cache off (`AI201_CACHE=0`), to check that the captions varied.
- *What came back:* The three captions were worded differently and each mentioned the title, `$38`, and `depop` once, but all three were written from the seller's point of view: "Grab them on my depop before I change my mind and keep them."
- *What I changed:* FitFindr's user is the shopper who found the item, not the person selling it, so I added a line to the system prompt in `tools.py` saying the poster is the shopper showing off how they styled the find, not the seller. The re-run captions read like a buyer's post: "Scored these Vintage Levi's 501 Jeans — Medium Wash on depop for only $38..."

**Moment 3: a failure I did not plan to trigger (Unit 4, Milestone 2 and 4)**

- *What I asked for:* I had Claude trigger my three failure modes, add a handler where one crashed, and add the trace calls. For the bad key it set a fake `GEMINI_API_KEY` on the command line, so my real key in `.env` was never edited or printed.
- *What came back:* The empty search and empty wardrobe already worked. The bad key escaped `run_agent` as a raised `ModelUnavailable`, so Claude added a handler that leaves `fit_card` as `None` and sets `session["error"]`. Later, two runs of `leather bomber under $20` hit a live `503 UNAVAILABLE` from the model, and my handler printed the provider's raw JSON error to the user.
- *What I changed:* I chose to clean up the message instead of leaving it. `agent.py::run_agent` now replaces the catch-all text with "The model service is busy or temporarily down. Wait a minute and try again.", and the bad-key message keeps its own hint. I left `generate.py` alone, so a 503 is still not retried (see What's Still Broken).

**Moment 4: scoring my criteria against the real runs (Unit 4, Milestones 3 to 5)**

- *What I asked for:* I asked Claude to score my five criteria from the run logs using my own rules, and to find the weak spot behind any misses.
- *What came back:* Criteria 1, 2 and 4 could be scored from the run log, but criterion 3 needs every field of the item that reached `suggest_outfit`, and the trace line only shows `id`, title, price and platform. Claude offered three options and I picked an inline capture command that wraps `suggest_outfit` and compares the full dict. Nothing was missed, so Claude pointed out that `leather bomber under $20` would pass criterion 1 while returning a $12 leather belt, because `search_listings` kept any listing with one matching keyword.
- *What I changed:* I kept every verdict as MET, wrote that my targets were partly too low, and made the one improvement the search rule (a listing must match more than half of the keywords). I measured it with a probe on two queries, because my five criteria were already at 5 of 5 and could not show it.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item reaches the outfit tool unchanged | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card is short and includes the listing facts | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. The search respects my budget | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

How each try was scored: `python run_eval.py --label before` ran every scenario five times with caching off and wrote `results/run_2026-10-08_1840_before.md`, which holds each try's session summary, outfit, fit card and trace. Criteria 1, 2 and 4 were scored from that file. Criterion 1 needs all four trace steps (`parse_query`, `search_listings (via MCP)`, `suggest_outfit`, `create_fit_card`) and a non-empty fit card. Criterion 2 needs a two-step trace that never reaches `suggest_outfit`, `fit_card` left `None`, and a message that names what to change. Criterion 4 was scored with the exact rules in `criteria.md`: sentences counted after removing hashtags, then title, platform and price each counted once; the per-try counts are in the criterion 4 paragraph below. Criteria 3 and 5 need more than the run log records (the full dict that reached `suggest_outfit`, and the price of every result), so they were scored by the capture command at the end of this section, which runs `agent.py::run_agent` five times per criterion with caching off and `suggest_outfit` wrapped to record its argument.

**Real output from one try** (try 1 of each criterion), pasted as text, naming the file and function that produced it:

**Criterion 1** - `agent.py::run_agent` (scenario "matching query completes", query `vintage graphic tee under $30`). All four steps ran and a fit card came back:

```
[1] parse_query
      in:  'vintage graphic tee under $30'
      out: description='vintage graphic tee', size=None, max_price=30.0
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: results found, selected the first one
[3] suggest_outfit
      in:  new_item=lst_002: Y2K Baby Tee — Butterfly Print ($18.0, depop), wardrobe=10 items
      out: Outfit 1 Pair the Y2K Baby Tee — Butterfly Print with baggy straight-leg jeans, dark wash. Layer the vintage b…
[4] create_fit_card
      in:  outfit='Outfit 1\nPair the Y2K Baby Tee — Butterf'…, new_item=lst_002: Y2K Baby Tee — Butterfly Print ($18.0, …
      out: Scored this Y2K Baby Tee — Butterfly Print on depop for only $18 and I am obsessed. I've been living in it pai…
```

Fit card (`tools.py::create_fit_card`): Scored this Y2K Baby Tee — Butterfly Print on depop for only $18 and I am obsessed. I've been living in it paired with baggy dark wash jeans and a black denim jacket for that ultimate 2000s street style. Such a lucky find!

**Criterion 2** - `agent.py::run_agent` and `agent.py::no_results_message` (query `designer ballgown size XXS under $5`). The trace stops at step 2 and `suggest_outfit` is never called:

```
[1] parse_query
      in:  'designer ballgown size XXS under $5'
      out: description='designer ballgown', size='XXS', max_price=5.0
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit
```

Message returned in `session["error"]`: Nothing matched 'designer ballgown' in size XXS at $5 or less. No listing matches those words even without a size or price limit. Try naming the kind of item (tee, jacket, jeans, sneakers) or a style (vintage, y2k, streetwear).

**Criterion 3** - capture command below (`agent.py::run_agent` with `suggest_outfit` wrapped), query `denim jacket under $50`, try 1:

```
CRITERION 3: query 'denim jacket under $50'
  try 1: PASS  calls_to_suggest_outfit=1  id search_results[0]=lst_007 selected_item=lst_007 received=lst_007  all fields equal=True
```

**Criterion 4** - `tools.py::create_fit_card` (scenario "fit card is short and has the listing facts", same query as criterion 1, listing `lst_002`, Y2K Baby Tee - Butterfly Print, $18, depop). Try 1 fit card:

```
Scored this Y2K Baby Tee — Butterfly Print on depop for only $18 and I am obsessed. I threw it on with baggy dark wash jeans, an unzipped zip hoodie, and chunky sneakers for the ultimate cozy streetwear vibe. Such an easy little graphic tee to throw on and go!
```

Scored with the `criteria.md` rules, per try (sentences / title count / platform count / dollar amounts): try 1: 3 / 1 / 1 / ['$18']; try 2: 3 / 1 / 1 / ['$18']; try 3: 2 / 1 / 1 / ['$18']; try 4: 3 / 1 / 1 / ['$18']; try 5: 3 / 1 / 1 / ['$18']. All five tries are within 2 to 4 sentences with each fact exactly once.

**Criterion 5** - capture command below, query `vintage graphic tee under $30`, try 1:

```
CRITERION 5: query 'vintage graphic tee under $30'
  try 1: PASS  parsed max_price=30.0  results=10  max result price=30.0  selected price=18.0
```

**Capture command for criteria 3 and 5** (run from the repo root with the virtual environment active, for example `python - < capture.py`). Full output of all ten tries follows it:

```python
import config
config.CACHE_ENABLED = False          # five real model answers, as in run_eval.py
import agent
from utils.data_loader import get_example_wardrobe

received = []                         # what suggest_outfit actually got as new_item
_real = agent.suggest_outfit
agent.suggest_outfit = lambda item, wardrobe: (received.append(item), _real(item, wardrobe))[1]

def tries(query):
    for n in range(1, 6):
        received.clear()
        s = agent.run_agent(query, get_example_wardrobe())
        yield n, s, list(received)

print("CRITERION 3: query 'denim jacket under $50'")
for n, s, got in tries("denim jacket under $50"):
    first = s["search_results"][0] if s["search_results"] else None
    ok = bool(got) and first is not None and first == s["selected_item"] == got[0]
    print(f"  try {n}: {'PASS' if ok else 'FAIL'}  calls_to_suggest_outfit={len(got)}  "
          f"id search_results[0]={first and first['id']} selected_item={s['selected_item'] and s['selected_item']['id']} "
          f"received={got[0]['id'] if got else None}  all fields equal={ok}")

print("CRITERION 5: query 'vintage graphic tee under $30'")
for n, s, got in tries("vintage graphic tee under $30"):
    prices = [r["price"] for r in s["search_results"]]
    sel = s["selected_item"]
    ok = (s["parsed"]["max_price"] == 30 and len(prices) >= 1 and sel is not None
          and all(p <= 30 for p in prices) and sel["price"] <= 30)
    print(f"  try {n}: {'PASS' if ok else 'FAIL'}  parsed max_price={s['parsed']['max_price']}  "
          f"results={len(prices)}  max result price={max(prices) if prices else None}  selected price={sel and sel['price']}")
```

```
CRITERION 3: query 'denim jacket under $50'
  try 1: PASS  calls_to_suggest_outfit=1  id search_results[0]=lst_007 selected_item=lst_007 received=lst_007  all fields equal=True
  try 2: PASS  calls_to_suggest_outfit=1  id search_results[0]=lst_007 selected_item=lst_007 received=lst_007  all fields equal=True
  try 3: PASS  calls_to_suggest_outfit=1  id search_results[0]=lst_007 selected_item=lst_007 received=lst_007  all fields equal=True
  try 4: PASS  calls_to_suggest_outfit=1  id search_results[0]=lst_007 selected_item=lst_007 received=lst_007  all fields equal=True
  try 5: PASS  calls_to_suggest_outfit=1  id search_results[0]=lst_007 selected_item=lst_007 received=lst_007  all fields equal=True
CRITERION 5: query 'vintage graphic tee under $30'
  try 1: PASS  parsed max_price=30.0  results=10  max result price=30.0  selected price=18.0
  try 2: PASS  parsed max_price=30.0  results=10  max result price=30.0  selected price=18.0
  try 3: PASS  parsed max_price=30.0  results=10  max result price=30.0  selected price=18.0
  try 4: PASS  parsed max_price=30.0  results=10  max result price=30.0  selected price=18.0
  try 5: PASS  parsed max_price=30.0  results=10  max result price=30.0  selected price=18.0
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | A matching query completes all three tools | 4 of 5 | MET (5/5) | Counted tries whose trace had all four steps (`parse_query`, `search_listings (via MCP)`, `suggest_outfit`, `create_fit_card`) and a non-empty fit card. Five of five did. |
| 2 | An impossible query stops before the second tool | 5 of 5 | MET (5/5) | All five traces end at step 2 with `[] (empty)`, `suggest_outfit` is never called, `fit_card` stays `None`, and the message names what to change ("Try naming the kind of item ... or a style"). |
| 3 | The selected item reaches the outfit tool unchanged | 5 of 5 | MET (5/5) | The capture command compared `search_results[0]`, `selected_item` and the `new_item` that `suggest_outfit` received. Same `id` (`lst_007`) and equal for every field in all five tries. |
| 4 | The fit card is short and includes the listing facts | 4 of 5 | MET (5/5) | Applied the `criteria.md` counting rules to each card: 2 to 4 sentences, full title once, `depop` once, one dollar amount equal to `$18`. All five passed (sentence counts 3, 3, 2, 3, 3). |
| 5 | The search respects my budget | 5 of 5 | MET (5/5) | The capture command checked `parsed["max_price"]` is 30, there is at least one result, and every result and the selected item cost $30 or less. Ten results each try, highest price $30. |

**Diagnoses**

Nothing was missed: all five criteria are MET at 5 of 5, so there is no miss to trace to a tool, the branch, the session or the model's output. I am not revising any criterion. Each one was measurable as written, and the fit card rules in `criteria.md` scored cleanly.

Were my targets too low? Partly, yes:

- **Criterion 1 is the one I would tighten.** It only asks for "a query that matches at least one listing", and a search that matches one keyword counts as a match. `leather bomber under $20` shows it: the only bomber costs $75, but the search returns `lst_014 Leather Belt - Brown, Braided` ($12) because `leather` alone gives it a score above zero (`search_listings` keeps anything with a keyword score greater than zero). A run like that would complete all three tools and return a fit card, so it would pass criterion 1 while giving the user the wrong item. That is a tool problem (`search_listings`: the score cutoff), and my criteria had no way to catch it because I only tested friendly queries.
- **Criteria 3 and 5 cannot vary.** They do not call a model, so five tries return the same result by design. Five of five on them says the code is consistent, not that five tries added information.
- **Criterion 4 and the model.** The fit card varies between tries, but all five opened with "Scored ...". My criterion does not mention openers, so it did not notice.
- **Outside the test.** After the 50-call run, the live model returned `503 UNAVAILABLE` on two separate queries. None of the 50 test calls hit one, so criterion 1's 4 of 5 was never tested against a model outage.

The pattern is a single weak spot, not several: the search cutoff in `search_listings` (a one-keyword match passes) and a test set of easy queries that never exercised it.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path** (`AI201_CACHE=0 python app.py ask 'vintage graphic tee under $30' --trace`, two real model calls)

```
[1] parse_query
      in:  'vintage graphic tee under $30'
      out: description='vintage graphic tee', size=None, max_price=30.0
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: results found, selected the first one
[3] suggest_outfit
      in:  new_item=lst_002: Y2K Baby Tee — Butterfly Print ($18.0, depop), wardrobe=10 items
      out: Outfit 1: Y2K Streetwear Pair the butterfly baby tee with the baggy straight-leg jeans, dark wash. Layer the b…
[4] create_fit_card
      in:  outfit='Outfit 1: Y2K Streetwear\nPair the butter'…, new_item=lst_002: Y2K Baby Tee — Butterfly Print ($18.0, …
      out: Manifesting pure 2000s energy with this Y2K Baby Tee — Butterfly Print I scored on depop for just $18! I’m obs…
```

**Empty search** (`python app.py ask 'designer ballgown size XXS under $5' --trace`)

```
[1] parse_query
      in:  'designer ballgown size XXS under $5'
      out: description='designer ballgown', size='XXS', max_price=5.0
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit
```

The empty run is two steps and stops at the branch; the happy run is four. Step 2 is the MCP call: `agent.py::search_listings` calls `mcp_client.call_tool`, which starts `mcp_server.py` and asks it for `search_listings`.

**On the MCP move:** I moved `search_listings` behind MCP. In `mcp_server.py` it is registered with `@mcp.tool()` (typed inputs `description: str`, `size: str | None`, `max_price: float | None`, and a description that names units and the empty case). In `agent.py`, `search_listings` is now a small wrapper that calls `mcp_client.call_tool("search_listings", {...})`, and both `run_agent` and `no_results_message` use it, so the tool is only reached through MCP. Nothing behaved differently: on three queries (6 results, 1 result, and an empty list) the MCP result was identical to the direct call, and the happy and impossible queries print the same text as before. The only visible change is speed, because each MCP call starts the server again.

**Failure modes triggered on purpose**

- Empty search (`python app.py ask 'designer ballgown size XXS under $5'`): already handled. It stops before `suggest_outfit` and says: "Nothing matched 'designer ballgown' in size XXS at $5 or less. No listing matches those words even without a size or price limit. Try naming the kind of item (tee, jacket, jeans, sneakers) or a style (vintage, y2k, streetwear)."
- Empty wardrobe (`python app.py ask 'vintage graphic tee under $30' --empty-wardrobe`): already handled. It returned general styling advice for the item and a fit card, no crash and no empty string. A `--trace` run of it shows `wardrobe=0 items` at step 3.
- Model unavailable (`GEMINI_API_KEY=not-a-real-key python app.py ask 'cropped leather jacket under $80'`, a query not asked before; I overrode the key for that one command instead of editing `.env`, which gives the same rejection and leaves the real key untouched). Before the fix, the failure escaped `run_agent` as a raised `ModelUnavailable` and `app.py` printed it as an exception line. After the fix, `run_agent` catches it, leaves `fit_card` as `None`, and puts this in `session["error"]`: "FitFindr couldn't reach the model, so it couldn't style the item or write a fit card. It did find Denim Jacket — Light Wash, Cropped, so your search is fine. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com."
  A second, unplanned trigger showed up later in the unit: the live model answered `503 UNAVAILABLE` ("high demand") on two runs of `leather bomber under $20`. The handler stopped cleanly, but `generate.py`'s catch-all text put the provider's raw JSON error in the message. `agent.py::run_agent` now replaces that case with "The model service is busy or temporarily down. Wait a minute and try again." (checked by raising the exact 503 text from a patched `generate`), and the bad-key message above is unchanged.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** One change, in `tools.py::search_listings`. Before, a listing was kept if it matched at least one description keyword. Now it is kept only if it matches more than half of the distinct keywords (`needed = len(keywords) // 2 + 1`, so 1 of 1, 2 of 2, 2 of 3, 3 of 4 or 5). Nothing else in the loop or the other two tools changed. The Tool Inventory above, the docstring in `tools.py` and the tool description in `mcp_server.py` were updated to say the same thing. The only other code change in this unit is the MCP move and the failure handlers from Milestone 2 (plus the 503 message wording, commit `22567f9`).

**Which failure it was meant to fix:** The diagnosis in Verdicts and Diagnoses: `search_listings` (a tool) passed any listing with a score above zero, so one shared word carried a multi-word query. `leather bomber under $20` returned `Leather Belt - Brown, Braided` ($12) because of `leather`, and the loop then styled the belt and wrote a fit card for it. The change should make the agent stop at the search with a message instead of producing a fit card for the wrong item.

### Run Log — After

`python run_eval.py --label after` wrote `results/run_2026-10-08_1922_after.md`: the same six scenarios as the before run, five tries each, caching off. Scored the same way as before (criteria 1, 2 and 4 from that file with the `criteria.md` rules; criteria 3 and 5 by re-running the capture command from Run Log - Before against the changed search).

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item reaches the outfit tool unchanged | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card is short and includes the listing facts | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. The search respects my budget | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Before and after, side by side: all five rows are 5 of 5 in both logs. Two details from the after run. First, in the "search respects the budget" scenario, try 4 stopped at `create_fit_card` because the live model returned 503 (the new "busy or temporarily down" message appeared as written, and `fit_card` was `None`). Criterion 5 is about the search, which had already returned five in-budget results in that try, so it is scored PASS from the capture command, not from that scenario's fit card. Second, the capture output after the change:

```
CRITERION 3: query 'denim jacket under $50'
  try 1: PASS  calls_to_suggest_outfit=1  id search_results[0]=lst_007 selected_item=lst_007 received=lst_007  all fields equal=True
  try 2: PASS  calls_to_suggest_outfit=1  id search_results[0]=lst_007 selected_item=lst_007 received=lst_007  all fields equal=True
  try 3: PASS  calls_to_suggest_outfit=1  id search_results[0]=lst_007 selected_item=lst_007 received=lst_007  all fields equal=True
  try 4: PASS  calls_to_suggest_outfit=1  id search_results[0]=lst_007 selected_item=lst_007 received=lst_007  all fields equal=True
  try 5: PASS  calls_to_suggest_outfit=1  id search_results[0]=lst_007 selected_item=lst_007 received=lst_007  all fields equal=True
CRITERION 5: query 'vintage graphic tee under $30'
  try 1: PASS  parsed max_price=30.0  results=5  max result price=26.0  selected price=18.0
  try 2: PASS  parsed max_price=30.0  results=5  max result price=26.0  selected price=18.0
  try 3: PASS  parsed max_price=30.0  results=5  max result price=26.0  selected price=18.0
  try 4: PASS  parsed max_price=30.0  results=5  max result price=26.0  selected price=18.0
  try 5: PASS  parsed max_price=30.0  results=5  max result price=26.0  selected price=18.0
```

The change moved the search results: `vintage graphic tee under $30` now returns 5 listings (highest price $26) instead of 10 (highest $30), and `denim jacket under $50` returns 1 instead of 7. The selected item did not change for either query.

**The probe.** The five criteria were already at 5 of 5, so they cannot show an improvement. To measure this change I ran the two queries that exposed the weakness through the same runner, `run_eval.py::run_once`, five tries each with caching off, before and after the change. The probe command (run from the repo root with the virtual environment active, for example `python - < probe.py`):

```python
import config
config.CACHE_ENABLED = False          # five real model answers, as in run_eval.py
from run_eval import run_once

PROBES = ["leather bomber under $20", "oversized wool coat under $90"]
for query in PROBES:
    print(f"PROBE: {query!r}")
    for n in range(1, 6):
        rec = run_once({"query": query, "wardrobe": "example"})
        s = rec["session"] or {}
        item = s.get("selected_item")
        if rec["crashed"]:
            outcome = "CRASHED " + rec["crashed"][:60]
        elif s.get("error") and item is None:
            outcome = "stopped at search: " + s["error"][:70] + "..."
        elif s.get("error"):
            outcome = f"stopped after search ({item['title']}): model unavailable"
        else:
            outcome = f"fit card for: {item['title']} (${item['price']})"
        print(f"  try {n}: results={len(s.get('search_results') or [])}  {outcome}")
```

Before the change (old `search_listings`):

```
PROBE: 'leather bomber under $20'
  try 1: results=1  fit card for: Leather Belt — Brown, Braided ($12.0)
  try 2: results=1  fit card for: Leather Belt — Brown, Braided ($12.0)
  try 3: results=1  fit card for: Leather Belt — Brown, Braided ($12.0)
  try 4: results=1  fit card for: Leather Belt — Brown, Braided ($12.0)
  try 5: results=1  fit card for: Leather Belt — Brown, Braided ($12.0)
PROBE: 'oversized wool coat under $90'
  try 1: results=5  fit card for: Oversized Flannel Shirt — Plaid Red/Black ($22.0)
  try 2: results=5  fit card for: Oversized Flannel Shirt — Plaid Red/Black ($22.0)
  try 3: results=5  fit card for: Oversized Flannel Shirt — Plaid Red/Black ($22.0)
  try 4: results=5  fit card for: Oversized Flannel Shirt — Plaid Red/Black ($22.0)
  try 5: results=5  fit card for: Oversized Flannel Shirt — Plaid Red/Black ($22.0)
```

After the change:

```
PROBE: 'leather bomber under $20'
  try 1: results=0  stopped at search: Nothing matched 'leather bomber' at $20 or less. Without the price lim...
  try 2: results=0  stopped at search: Nothing matched 'leather bomber' at $20 or less. Without the price lim...
  try 3: results=0  stopped at search: Nothing matched 'leather bomber' at $20 or less. Without the price lim...
  try 4: results=0  stopped at search: Nothing matched 'leather bomber' at $20 or less. Without the price lim...
  try 5: results=0  stopped at search: Nothing matched 'leather bomber' at $20 or less. Without the price lim...
PROBE: 'oversized wool coat under $90'
  try 1: results=0  stopped at search: Nothing matched 'oversized wool coat' at $90 or less. No listing match...
  try 2: results=0  stopped at search: Nothing matched 'oversized wool coat' at $90 or less. No listing match...
  try 3: results=0  stopped at search: Nothing matched 'oversized wool coat' at $90 or less. No listing match...
  try 4: results=0  stopped at search: Nothing matched 'oversized wool coat' at $90 or less. No listing match...
  try 5: results=0  stopped at search: Nothing matched 'oversized wool coat' at $90 or less. No listing match...
```

The empty-search messages after the change, in full: "Nothing matched 'leather bomber' at $20 or less. Without the price limit there are 1 matches, the cheapest at $75. Try raising your budget." and "Nothing matched 'oversized wool coat' at $90 or less. No listing matches those words even without a size or price limit. Try naming the kind of item (tee, jacket, jeans, sneakers) or a style (vintage, y2k, streetwear)."

**Did it help, and how do I know:** Yes, on the failure I diagnosed, and it did not move any of my five criteria. Before: on both probe queries, all 5 of 5 tries (10 of 10 runs) ended with a fit card for the wrong item (a leather belt for a bomber, a flannel shirt for a wool coat), and criterion 1 as written would have scored those PASS. After: 10 of 10 runs stop at the search with a message that says what to change, no model call is made, and `fit_card` stays `None`. The five criteria stayed at 5 of 5 because they were already at the ceiling, so the probe, not the table, is the evidence. Costs I can see: queries return fewer results (5 instead of 10 for the tee query, 1 instead of 7 for the denim jacket query), so a loosely worded query is more likely to come back empty. The rule is also a majority, not all keywords: `cropped leather jacket under $80` still matches the cropped denim jacket on two of its three words.

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

No criterion is missed: all five are 5 of 5 before and after. That says my targets were easy, not that FitFindr is finished. What is left, and what I would do:

- **Criterion 1 is still loose.** It only asks for a query that matches at least one listing. After the improvement, a match must cover more than half the keywords, but it is a majority, not all: `cropped leather jacket under $80` still selects `Denim Jacket - Light Wash, Cropped` (two of three words) ahead of the leather bomber. I would tighten the criterion to check that the selected item matches every keyword that names a kind of item, and add a probe for it. I stopped because the unit allows one improvement and tightening a target after seeing results is not a revision, so `criteria.md` is unchanged.
- **A 503 from the model is not retried.** The live model returned `503 UNAVAILABLE` on three runs (two probe runs and one try in the after run). `generate.py` only retries rate limits (429) and raises `ModelUnavailable` on anything else, so a short outage ends the run with the "busy" message. I would retry a 503 once or twice after a few seconds. I stopped because `generate.py` is the starter's adapter and the unit's only code changes were the MCP move and one improvement.
- **Fewer results.** The new rule returns 5 listings for `vintage graphic tee under $30` (was 10) and 1 for `denim jacket under $50` (was 7), so a loosely worded query is more likely to come back empty. The empty-search message helps, but I did not measure how often real queries now fail.
- **Ties and exact words.** When listings tie, the first in the data file wins, so `vintage graphic tee under $30` picks `Y2K Baby Tee` over `Graphic Tee - 2003 Tour Bootleg Style`, which also matches all three words. Matching is exact-word, so `tees` does not match `tee`. I would weight title matches and stem plurals. I did not touch these because no criterion measures them.
- **Criteria 3 and 5 cannot vary.** They never call the model, so five tries return the same answer. I would score them once on several different queries instead of five times on one.
- **Fit cards share an opener.** Eight of the ten fit cards in the two criterion 4 runs start with "Scored this ..." (the other two start "Found this ..."). Criterion 4 does not check openers, so it passed. I would add an opener rule to the criterion.
- **MCP.** Only `search_listings` moved. Each call starts `mcp_server.py` again, so a search is slower than a direct call, and the agent has no handler for an `MCPError` if the server will not start (it would show the error text from `mcp_client.py`). I did not move a second tool or add that handler.
- **Cosmetic.** `app.py` prints `$18.0` in the "Found:" line while the fit card says `$18`. I left it because it is not part of this unit.

**The MCP move, in one line:** `search_listings` is registered in `mcp_server.py` and `agent.py` calls it through `mcp_client.call_tool`; on three test queries the MCP result was identical to the direct call, and the only difference I saw was speed (see Loop Trace).

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
