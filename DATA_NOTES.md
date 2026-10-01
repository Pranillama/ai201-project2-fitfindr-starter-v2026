# Data Notes (Milestone 1)

What the tools will be reading, written down before speccing them.

## Listing fields (`data/listings.json`, 40 listings)

| Field | Type | Example |
|---|---|---|
| `id` | str | `lst_001` |
| `title` | str | `Vintage Levi's 501 Jeans - Medium Wash` |
| `description` | str | `Classic 501s in a perfect medium wash...` |
| `category` | str | `bottoms` |
| `style_tags` | list[str] | `['vintage', 'classic', 'denim', 'streetwear']` |
| `size` | str | `W30 L30` |
| `condition` | str | `good` |
| `price` | float | `38.0` |
| `colors` | list[str] | `['blue', 'indigo']` |
| `brand` | str or None | `Levi's` |
| `platform` | str | `depop` |

## Wardrobe item fields (`data/wardrobe_schema.json`)

| Field | Type | Example |
|---|---|---|
| `id` | str | `w_001` |
| `name` | str | `Baggy straight-leg jeans, dark wash` |
| `category` | str | `bottoms` |
| `colors` | list[str] | `['dark blue', 'indigo']` |
| `style_tags` | list[str] | `['denim', 'streetwear', 'baggy']` |
| `notes` | str | `High-waisted, sits above the hip` |

A wardrobe is a dict with one key, `items`. The example wardrobe has 10 items.
**An empty wardrobe is `{'items': []}`**: the key is present, the list is empty.

## What stood out

- **Categories:** tops 15, bottoms 10, outerwear 8, shoes 4, accessories 3.
- **Platforms:** depop 18, thredUp 11, poshmark 11.
- **Condition:** good 19, excellent 17, fair 4.
- **Price:** $12.00 to $75.00. 24 of 40 listings are $30 or under.
- **Brand is None on 32 of 40 listings.** Anything that assumes a brand will hit a blank most of the time.
- **Size has no single format.** Letter sizes (`S`, `M`, `L`, `XL`), ranges (`S/M`, `M/L`, `L/XL`), annotated sizes (`XL (oversized)`), `One Size` variants, shoe sizes (`US 7` to `US 9`), and waist/inseam (`W27` to `W32`, `W30 L30`). A plain substring test is wrong here: `"s" in "us 9"` and `"l" in "xl"` are both True. The size-match rule has to be decided in the Milestone 2 spec.
- **"Graphic tee" is not a field.** It appears only in title and description text, so keyword search has to look at free text, not just `category` or `style_tags`.

## Starter run

```
$ python app.py ask 'vintage graphic tee under $30'

  The planning loop isn't built yet - see the TODO in agent.py.

0 model calls this session
```

That is the expected starting position: it runs, and it does nothing yet.
