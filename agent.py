"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re
import trace

from generate import ModelUnavailable
from mcp_client import call_tool
from tools import create_fit_card, format_price, suggest_outfit

# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── search over MCP ───────────────────────────────────────────────────────────

def search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]:
    """
    search_listings now lives behind MCP (mcp_server.py). Same inputs, same
    list of listing dicts back; this is the only place the agent reaches it.
    """
    return call_tool("search_listings", {
        "description": description,
        "size": size,
        "max_price": max_price,
    })


def _item_label(item: dict) -> str:
    """One listing as 'id: title ($price, platform)' for the trace."""
    return f"{item['id']}: {item['title']} (${item['price']}, {item['platform']})"


# ── query parsing ─────────────────────────────────────────────────────────────

# "under $30", "below 30", "less than $30.50", "up to $30", "max $30", or a
# bare "$30".
_PRICE = re.compile(
    r"(?:\b(?:under|below|less than|up to|max)\s*\$?\s*|\$\s*)(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
# "size M", "in size S/M", "size 8.5", "size US 8", "size W30".
_SIZE = re.compile(
    r"(?:\bin\s+)?\bsize\s+((?:us\s+)?[a-z0-9.]+(?:/[a-z0-9.]+)?)",
    re.IGNORECASE,
)


def parse_query(query: str) -> dict:
    """
    Pull a price ceiling and a size out of the query with regex. Whatever is
    left becomes the description.

    Returns {"description": str, "size": str or None, "max_price": float or None}.
    """
    text = query

    max_price = None
    price_match = _PRICE.search(text)
    if price_match:
        max_price = float(price_match.group(1))
        text = text[:price_match.start()] + " " + text[price_match.end():]

    size = None
    size_match = _SIZE.search(text)
    if size_match:
        size = size_match.group(1).rstrip(".").upper()
        text = text[:size_match.start()] + " " + text[size_match.end():]

    description = " ".join(re.sub(r"[^\w\s'-]", " ", text).split())
    return {"description": description, "size": size, "max_price": max_price}


# ── the empty-search message ──────────────────────────────────────────────────

def no_results_message(parsed: dict) -> str:
    """
    Say what was searched and which filter to loosen.

    Re-runs search_listings with each filter removed (no model calls) so the
    suggestion names the filter that is actually blocking results.
    """
    description, size, max_price = parsed["description"], parsed["size"], parsed["max_price"]

    searched = f"'{description}'" if description else "your search"
    if size:
        searched += f" in size {size}"
    if max_price is not None:
        searched += f" at {format_price(max_price)} or less"
    opening = f"Nothing matched {searched}."

    if max_price is not None:
        without_price = search_listings(description, size, None)
        if without_price:
            cheapest = min(listing["price"] for listing in without_price)
            return (
                f"{opening} Without the price limit there are "
                f"{len(without_price)} matches, the cheapest at "
                f"{format_price(cheapest)}. Try raising your budget."
            )

    if size:
        without_size = search_listings(description, None, max_price)
        if without_size:
            return (
                f"{opening} Without the size there are {len(without_size)} "
                f"matches. Try a different size, or leave the size out."
            )

    if size and max_price is not None and search_listings(description):
        return (
            f"{opening} It only matches with both the size and the price "
            f"limit removed. Try leaving the size out and raising your budget."
        )

    return (
        f"{opening} No listing matches those words even without a size or "
        f"price limit. Try naming the kind of item (tee, jacket, jeans, "
        f"sneakers) or a style (vintage, y2k, streetwear)."
    )


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    Each pass of the loop runs one step and picks the next one from what that
    step put in the session:

        parse → search_listings ─┬─ [] → error message, stop
                                 └─ results → selected_item = first result
                                              → suggest_outfit → create_fit_card → stop

    Every tool reads its inputs back out of the session, not from the previous
    call's return value.

    ─────────────────────────────────────────────────────────────────────────
    Unit 4 added two things: one trace.step() call per step (see trace.py), and
    a ModelUnavailable handler that turns a model that can't be reached into a
    message in session["error"] instead of a stack trace.
    """
    session = new_session(query, wardrobe)

    next_step = "parse"
    iterations = 0
    try:
        while next_step != "done":
            iterations += 1
            trace.check_iterations(iterations)

            if next_step == "parse":
                session["parsed"] = parse_query(session["query"])
                parsed = session["parsed"]
                trace.step(
                    "parse_query",
                    inputs=repr(session["query"]),
                    returned=(
                        f"description={parsed['description']!r}, "
                        f"size={parsed['size']!r}, max_price={parsed['max_price']!r}"
                    ),
                )
                next_step = "search_listings"

            elif next_step == "search_listings":
                session["search_results"] = search_listings(**session["parsed"])
                # The branch: nothing found means stop here, before any model call.
                if not session["search_results"]:
                    session["error"] = no_results_message(session["parsed"])
                    note = "branch: empty, stopping before suggest_outfit"
                    next_step = "done"
                else:
                    session["selected_item"] = session["search_results"][0]
                    note = "branch: results found, selected the first one"
                    next_step = "suggest_outfit"
                trace.step(
                    "search_listings (via MCP)",
                    inputs=str(session["parsed"]),
                    returned=session["search_results"],
                    note=note,
                )

            elif next_step == "suggest_outfit":
                item = session["selected_item"]
                session["outfit_suggestion"] = suggest_outfit(item, session["wardrobe"])
                trace.step(
                    "suggest_outfit",
                    inputs=(
                        f"new_item={_item_label(item)}, "
                        f"wardrobe={len(session['wardrobe']['items'])} items"
                    ),
                    returned=session["outfit_suggestion"],
                )
                next_step = "create_fit_card"

            elif next_step == "create_fit_card":
                item = session["selected_item"]
                session["fit_card"] = create_fit_card(session["outfit_suggestion"], item)
                trace.step(
                    "create_fit_card",
                    inputs=f"outfit={session['outfit_suggestion'][:40]!r}…, new_item={_item_label(item)}",
                    returned=session["fit_card"],
                )
                next_step = "done"

    except ModelUnavailable as exc:
        # A model call (suggest_outfit or create_fit_card) could not reach the
        # model. Stop with a message instead of a stack trace; the search
        # already worked, so say so.
        item = session["selected_item"]
        found = f" It did find {item['title']}, so your search is fine." if item else ""
        reason = str(exc)
        if reason.startswith("Couldn't reach the model:"):
            # generate._explain's catch-all text, which carries the provider's
            # raw error (e.g. a 503 JSON body). Don't show that to a user.
            reason = "The model service is busy or temporarily down. Wait a minute and try again."
        session["error"] = (
            f"FitFindr couldn't reach the model, so it couldn't style the item "
            f"or write a fit card.{found} {reason}"
        )
        trace.step("model unavailable", note="stopping, no fit card")

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
