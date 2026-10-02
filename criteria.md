# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
The successful path depends on two model calls, one for the outfit and one
for the fit card. I chose 4 of 5 rather than 5 of 5 because a model call can
fail or return an empty response even when search finds a listing. One miss
still needs a diagnosis; more than one means the full flow is not reliable
enough for my target.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
My search specification returns `[]` when nothing matches, and the loop can
check that result before either model call. This path depends on a fixed
branch rule, so I expect 5 of 5. There is no stricter success rate, and a
lower target would allow the agent to generate an outfit without an item.

---

## 3. The selected item reaches the outfit tool unchanged

<!-- YOU WRITE THIS ONE.

     How would you know that the item your search found is the same item the
     next tool received? Name something countable or observable.

     This is the criterion people find hardest, because state failure doesn't
     look like state failure — it looks like a tool problem. Something that
     compares session["selected_item"] against what actually reached
     suggest_outfit is the shape you're after. -->
For a query that matches at least one listing, the first listing in
`session["search_results"]`, `session["selected_item"]`, and the actual
`new_item` argument received by `suggest_outfit` have the same `id` and equal
values for every listing field, in 5 of 5 tries. A missing tool call counts
as a failure. Check the captured tool input against the session, rather than
guessing from the outfit's wording.

**Why this target:**
The loop only needs to store one listing and pass it to the next tool. That
handoff does not depend on the model's wording, so I expect it to work in all
five tries. There is no stricter success rate than 5 of 5; accepting fewer
would allow the agent to style an item the user did not select.

---

## 4. The fit card is short and includes the listing facts

<!-- YOU WRITE THIS ONE.

     The fit card calls a model, so the same input can produce different words
     each time. That's not a bug — it's the nature of the tool. So what would
     make it acceptable?

     Think about what you'd actually be unhappy to see. A caption that never
     mentions the price? Two different items producing the same opening
     sentence? A card longer than a caption anyone would post? Any of those can
     be turned into a number. -->
Run the same matching query five times with caching off. In at least 4 of
5 tries, the returned fit card has 2 to 4 sentences and mentions the selected
item's full title, correct price, and platform exactly once each. A missing
card fails. Use these rules to score every card:

- For the title, compare case-insensitively, collapse repeated whitespace,
  and treat all dash characters as a plain hyphen. All words on both sides
  of the title's dash must remain in the same order. Changing the dash is
  allowed; dropping the subtitle is a failure. Count complete title matches
  in the entire card.
- For the platform, count case-insensitive whole-word matches in the entire
  card, including hashtags. `ThredUp` and `thredUp` match. `on Depop` plus
  `#depop` counts as two mentions and fails.
- For the price, accept only a dollar sign immediately followed by the
  listing's numeric price, either with exactly two decimal places or, for
  a whole-dollar price, with no decimal places. For a price of 24, only
  `$24` and `$24.00` qualify; `24 bucks` does not. The card must contain
  exactly one dollar amount, and it must match the listing's price.
- For sentence counting, first remove hashtags. Split at `.`, `!`, or `?`,
  treating consecutive punctuation as one separator and ignoring a period
  between two digits. Count each resulting segment that contains at least
  one letter or digit, including a final segment with no closing punctuation.
  Emoji-only segments do not count, and line breaks do not split sentences.
  These are the counting rules for this test, including abbreviations.

**Why this target:**
My tool specification asks for a short caption with these three listing
facts, so this checks whether the card is useful without requiring a fixed
script. Dash style and capitalization do not change the listing facts, so
I allow those differences. I chose 4 of 5 rather than 5 of 5 because the model can occasionally
repeat a fact or miss the sentence limit even with the same input. Those
misses should still be recorded and investigated.

---

## 5. The search respects my budget

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. Speed, the empty
     wardrobe path, what happens when the model can't be reached, whether the
     search respects a price ceiling — anything, as long as it names a number
     or an observable outcome. -->
For `vintage graphic tee under $30`, the agent records
`session["parsed"]["max_price"]` as 30, returns at least one search result,
and every returned listing plus `session["selected_item"]` has a price of
$30 or less, in 5 of 5 tries. An empty result or missing selected item fails,
so returning nothing cannot pass the budget check.

**Why this target:**
I care about getting recommendations I can afford. The listings already have
numeric prices, and my search specification uses an inclusive price ceiling,
so this is a direct comparison rather than a model judgment. I chose 5 of 5
because there is no stricter success rate, and allowing one over-budget
result would break the limit I explicitly asked for.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
