"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. The README's Tool Inventory is the spec for
all three.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings

# Words that say nothing about the item itself, dropped before scoring.
STOPWORDS = {
    "a", "an", "and", "any", "for", "i", "im", "in", "is", "looking", "me",
    "my", "of", "on", "or", "size", "some", "something", "the", "to", "under",
    "want", "with",
}


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _size_pieces(size: str) -> set[str]:
    return {piece for piece in re.split(r"[\s/()]+", size.lower()) if piece}


def _size_matches(asked: str, listing_size: str) -> bool:
    """Every piece of the asked size must appear among the listing's pieces."""
    if listing_size.lower().startswith("one size"):
        return True
    return _size_pieces(asked) <= _size_pieces(listing_size)


def _searchable_words(listing: dict) -> set[str]:
    text = " ".join([
        listing["title"],
        listing["description"],
        listing["category"],
        *listing["style_tags"],
        *listing["colors"],
    ])
    return set(_words(text))


def format_price(price: float) -> str:
    return f"${price:.0f}" if price == int(price) else f"${price:.2f}"


def _describe_item(item: dict) -> str:
    lines = [
        f"Title: {item['title']}",
        f"Description: {item['description']}",
        f"Category: {item['category']}",
        f"Style tags: {', '.join(item['style_tags'])}",
        f"Colors: {', '.join(item['colors'])}",
        f"Size: {item['size']}",
        f"Condition: {item['condition']}",
        f"Price: {format_price(item['price'])}",
        f"Platform: {item['platform']}",
    ]
    if item.get("brand"):
        lines.append(f"Brand: {item['brand']}")
    return "\n".join(lines)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Filter listings by price and size, then rank by keyword overlap.

    Args:
        description: keywords such as "vintage graphic tee". Case-insensitive;
                     STOPWORDS are dropped.
        size:        None skips size filtering. Otherwise the asked size and
                     the listing size are split on spaces, "/" and parentheses,
                     and every asked piece must appear among the listing's
                     pieces. "M" matches "S/M"; "S" does not match "US 9".
                     Listings whose size starts with "One Size" always match.
        max_price:   None skips price filtering. Otherwise price <= max_price.

    Returns:
        At most config.SEARCH_RESULT_LIMIT full listing dicts, highest score
        first, ties in data-file order. The score is how many distinct
        description keywords appear in the listing's title, description,
        category, style_tags, and colors. Zero-score listings are dropped.
        Returns [] when nothing matches. Never None, never raises.
    """
    keywords = {word for word in _words(description) if word not in STOPWORDS}

    scored = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size and not _size_matches(size, listing["size"]):
            continue
        score = len(keywords & _searchable_words(listing))
        if score > 0:
            scored.append((score, listing))

    # list.sort is stable, so equal scores keep data-file order.
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[:config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

OUTFIT_SYSTEM = (
    "You are a thrift stylist. Be concrete and brief. Plain text, no markdown "
    "headings."
)


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Ask the model for one or two outfits built around a thrifted item.

    Args:
        new_item: one listing dict, as returned by search_listings.
        wardrobe: {"items": [...]}; each item has id, name, category, colors,
                  style_tags, notes (notes may be None). May be empty.

    Returns:
        The model's suggestion as a str. With wardrobe items, the outfits name
        the user's pieces by their `name`. With an empty wardrobe it asks for
        general styling advice instead, rather than raising or returning "".
        Raises generate.ModelUnavailable if the model can't be reached.
    """
    items = wardrobe.get("items", [])

    if not items:
        prompt = (
            "Someone is thinking about buying this thrifted item but has not "
            "saved any of their own clothes yet.\n\n"
            f"{_describe_item(new_item)}\n\n"
            "Suggest one or two outfits built around it, describing the kinds "
            "of pieces that would pair well (cut, color, shoes, layers). Keep "
            "it under 120 words."
        )
        return generate(prompt, system=OUTFIT_SYSTEM)

    wardrobe_lines = []
    for piece in items:
        line = (
            f"- {piece['name']} ({piece['category']}; "
            f"colors: {', '.join(piece['colors'])}; "
            f"style: {', '.join(piece['style_tags'])})"
        )
        if piece.get("notes"):
            line += f" - {piece['notes']}"
        wardrobe_lines.append(line)

    prompt = (
        "Someone is thinking about buying this thrifted item:\n\n"
        f"{_describe_item(new_item)}\n\n"
        "Here is what they already own:\n"
        + "\n".join(wardrobe_lines)
        + "\n\nSuggest one or two complete outfits that combine the new item "
        "with pieces they own. Name each owned piece exactly as written in "
        "the list. Keep it under 120 words."
    )
    return generate(prompt, system=OUTFIT_SYSTEM)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

FIT_CARD_SYSTEM = (
    "You write short, casual social media captions about thrift finds. They "
    "read like a real person posting, not a product description. The poster "
    "is the shopper who found the item and is showing off how they styled "
    "it, not the seller."
)


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Ask the model for a caption someone would actually post about the find.

    Args:
        outfit:   the suggestion string from suggest_outfit.
        new_item: the same listing dict that went into suggest_outfit.

    Returns:
        A two-to-four sentence caption str that mentions the item's title,
        price, and platform once each. Brand is in the prompt only when it
        isn't None. If `outfit` is empty or whitespace, the model is not called
        and a message starting with "No fit card:" is returned instead.
        Raises generate.ModelUnavailable if the model can't be reached.
    """
    if not outfit or not outfit.strip():
        return (
            "No fit card: the outfit suggestion was empty, so there was "
            "nothing to write a caption about."
        )

    price = format_price(new_item["price"])
    prompt = (
        "Write a caption for a post about this thrift find.\n\n"
        f"{_describe_item(new_item)}\n\n"
        f"How it's being styled:\n{outfit.strip()}\n\n"
        "Rules:\n"
        "- Two to four sentences.\n"
        f'- Mention the title exactly once, written exactly as: "{new_item["title"]}"\n'
        f"- Mention the price exactly once, written as {price}. No other dollar amounts.\n"
        f"- Mention the platform ({new_item['platform']}) exactly once.\n"
        "- No hashtags.\n"
        "- Be specific about the vibe of the outfit."
    )
    return generate(prompt, system=FIT_CARD_SYSTEM)
