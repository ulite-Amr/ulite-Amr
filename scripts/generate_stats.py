import os
import requests
from datetime import datetime

USERNAME = "ulite-Amr"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

# Gruvbox Hard palette
GRV = {
    "bg":      "#1d2021",
    "bg0":     "#282828",
    "bg1":     "#3c3836",
    "bg2":     "#504945",
    "bg3":     "#665c54",
    "fg":      "#ebdbb2",
    "fg2":     "#d5c4a1",
    "fg3":     "#bdae93",
    "gray":    "#a89984",
    "dim":     "#7c6f64",
    "yellow":  "#fabd2f",
    "orange":  "#fe8019",
    "red":     "#fb4934",
    "green":   "#b8bb26",
    "aqua":    "#8ec07c",
    "blue":    "#83a598",
    "purple":  "#d3869b",
}

LANG_COLORS = {
    "Kotlin":      "#7F52FF",
    "Java":        "#b07219",
    "Rust":        "#dea584",
    "Python":      "#3572A5",
    "Swift":       "#F05138",
    "JavaScript":  "#f1e05a",
    "TypeScript":  "#3178c6",
    "C++":         "#f34b7d",
    "C":           "#9b9b9b",
    "Go":          "#00ADD8",
    "Shell":       "#89e051",
    "HTML":        "#e34c26",
    "CSS":         "#563d7c",
    "TOML":        "#9c4221",
    "Makefile":    "#427819",
    "CMake":       "#DA3434",
    "Dart":        "#00B4AB",
    "Ruby":        "#701516",
}

FALLBACK = [
    GRV["yellow"], GRV["orange"], GRV["red"],
    GRV["green"],  GRV["aqua"],   GRV["blue"], GRV["purple"],
]


def get_language_stats():
    langs_size = {}
    langs_repos = {}
    query = """
    query($username: String!) {
      user(login: $username) {
        repositories(first: 100, isFork: false, ownerAffiliations: OWNER) {
          nodes {
            name
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges { size node { name } }
            }
          }
        }
        repositoriesContributedTo(first: 100, contributionTypes: [COMMIT, PULL_REQUEST]) {
          nodes {
            name
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges { size node { name } }
            }
          }
        }
      }
    }
    """
    try:
        resp = requests.post(
            "https://api.github.com/graphql",
            headers=HEADERS,
            json={"query": query, "variables": {"username": USERNAME}},
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("data", {}).get("user"):
            def process(repos):
                for repo in repos or []:
                    name = repo.get("name", "Unknown")
                    for edge in (repo.get("languages") or {}).get("edges", []):
                        lang = edge["node"]["name"]
                        sz = edge["size"]
                        langs_size[lang] = langs_size.get(lang, 0) + sz
                        langs_repos.setdefault(lang, set()).add(name)
            process(result["data"]["user"]["repositories"]["nodes"])
            process(result["data"]["user"]["repositoriesContributedTo"]["nodes"])
    except Exception as e:
        print(f"GraphQL error: {e}")
    return langs_size, langs_repos


def fmt_bytes(b):
    if b >= 1_000_000:
        return f"{b / 1_000_000:.1f} MB"
    if b >= 1_000:
        return f"{b / 1_000:.0f} kB"
    return f"{b} B"


def esc(s):
    """Escape special XML characters in text content."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(langs_size, langs_repos, top_n=6):
    ranked = sorted(langs_size.items(), key=lambda x: -x[1])[:top_n]
    total = sum(b for _, b in ranked)
    if not total:
        return ""

    # ── Layout constants ───────────────────────────────────────────
    W      = 460
    PAD    = 26
    INNER  = W - PAD * 2   # 408

    # Font stack: system fonts only — safe for GitHub's Camo proxy
    FONT   = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
    MONO   = "ui-monospace,'Cascadia Code','Segoe UI Mono','Roboto Mono',monospace"

    # Section heights
    HDR_H      = 50    # header area
    SEG_BAR_H  = 10    # stacked proportion bar
    SEG_BAR_Y  = HDR_H + 4
    DIV_Y      = SEG_BAR_Y + SEG_BAR_H + 14
    ITEM_H     = 54    # fixed per-language row height
    FOOTER_H   = 38

    content_H = len(ranked) * ITEM_H
    H = DIV_Y + 10 + content_H + FOOTER_H

    now = datetime.now().strftime("%b %Y")
    total_repos = sum(len(v) for v in langs_repos.values())
    total_bytes = sum(b for _, b in ranked)

    lines = []

    # ── SVG open ───────────────────────────────────────────────────
    lines.append(
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'fill="none" xmlns="http://www.w3.org/2000/svg">'
    )

    # ── Defs: clip path for stacked bar rounded corners ───────────
    lines.append(
        f'<defs>'
        f'<clipPath id="segClip">'
        f'<rect x="{PAD}" y="{SEG_BAR_Y}" width="{INNER}" height="{SEG_BAR_H}" rx="5"/>'
        f'</clipPath>'
        f'</defs>'
    )

    # ── Background & border ───────────────────────────────────────
    lines.append(f'<rect width="{W}" height="{H}" rx="14" fill="{GRV["bg"]}"/>')
    # Subtle inner border
    lines.append(
        f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="13.5" '
        f'stroke="{GRV["bg2"]}" stroke-opacity=".7"/>'
    )

    # ── Header ────────────────────────────────────────────────────
    # Accent bar
    lines.append(
        f'<rect x="{PAD}" y="16" width="3" height="20" rx="1.5" fill="{GRV["yellow"]}"/>'
    )
    # Title
    lines.append(
        f'<text x="{PAD + 12}" y="30" '
        f'font-family="{FONT}" font-size="13" font-weight="700" '
        f'fill="{GRV["yellow"]}" letter-spacing="2.5">'
        f'LANGUAGES'
        f'</text>'
    )
    # Subtitle on second line
    lines.append(
        f'<text x="{PAD + 12}" y="44" '
        f'font-family="{FONT}" font-size="10" '
        f'fill="{GRV["dim"]}">'
        f'{len(ranked)} languages · {total_repos} repos · {fmt_bytes(total_bytes)}'
        f'</text>'
    )

    # ── Stacked proportion bar ────────────────────────────────────
    # Background track
    lines.append(
        f'<rect x="{PAD}" y="{SEG_BAR_Y}" width="{INNER}" height="{SEG_BAR_H}" '
        f'rx="5" fill="{GRV["bg1"]}"/>'
    )
    # Colored segments (clipped to rounded rect)
    cx = PAD
    for i, (lang, count) in enumerate(ranked):
        color = LANG_COLORS.get(lang, FALLBACK[i % len(FALLBACK)])
        seg_w = round(INNER * count / total, 2)
        lines.append(
            f'<rect x="{cx}" y="{SEG_BAR_Y}" width="{seg_w}" height="{SEG_BAR_H}" '
            f'fill="{color}" clip-path="url(#segClip)"/>'
        )
        cx += seg_w

    # ── Divider ───────────────────────────────────────────────────
    lines.append(
        f'<line x1="{PAD}" y1="{DIV_Y}" x2="{W - PAD}" y2="{DIV_Y}" '
        f'stroke="{GRV["bg2"]}" stroke-opacity=".55"/>'
    )

    # ── Language rows ─────────────────────────────────────────────
    row_y = DIV_Y + 10

    BAR_H     = 4   # progress bar height
    DOT_R     = 5   # language dot radius
    NAME_X    = PAD + DOT_R * 2 + 8
    PCT_X     = W - PAD
    BAR_Y_OFF = 22  # bar offset from row_y
    INFO_Y_OFF = BAR_Y_OFF + BAR_H + 12  # info text offset

    for i, (lang, count) in enumerate(ranked):
        pct   = count / total
        color = LANG_COLORS.get(lang, FALLBACK[i % len(FALLBACK)])
        bar_w = round(INNER * pct, 2)
        repos = langs_repos.get(lang, set())

        center_y = row_y + 12  # vertical center for dot & name baseline

        # Language color dot
        lines.append(
            f'<circle cx="{PAD + DOT_R}" cy="{center_y - 2}" r="{DOT_R}" fill="{color}"/>'
        )

        # Language name
        lines.append(
            f'<text x="{NAME_X}" y="{center_y + 2}" '
            f'font-family="{FONT}" font-size="13" font-weight="600" '
            f'fill="{GRV["fg"]}">{esc(lang)}</text>'
        )

        # Percentage — colored to match language
        lines.append(
            f'<text x="{PCT_X}" y="{center_y + 2}" '
            f'font-family="{MONO}" font-size="12" font-weight="700" '
            f'fill="{color}" text-anchor="end">{pct * 100:.1f}%</text>'
        )

        # Progress bar track
        lines.append(
            f'<rect x="{PAD}" y="{row_y + BAR_Y_OFF}" '
            f'width="{INNER}" height="{BAR_H}" rx="2" fill="{GRV["bg1"]}"/>'
        )

        # Progress bar fill
        lines.append(
            f'<rect x="{PAD}" y="{row_y + BAR_Y_OFF}" '
            f'width="{bar_w}" height="{BAR_H}" rx="2" fill="{color}" opacity=".9"/>'
        )

        # Info line: size · N repos
        repo_count = len(repos)
        info = f"{fmt_bytes(count)}  ·  {repo_count} repo{'s' if repo_count != 1 else ''}"
        lines.append(
            f'<text x="{PAD}" y="{row_y + INFO_Y_OFF}" '
            f'font-family="{MONO}" font-size="9.5" fill="{GRV["dim"]}">{info}</text>'
        )

        # Dashed separator (skip after last row)
        if i < len(ranked) - 1:
            sep_y = row_y + ITEM_H - 4
            lines.append(
                f'<line x1="{PAD}" y1="{sep_y}" x2="{W - PAD}" y2="{sep_y}" '
                f'stroke="{GRV["bg1"]}" stroke-dasharray="3 5" opacity=".6"/>'
            )

        row_y += ITEM_H

    # ── Footer ────────────────────────────────────────────────────
    fy = H - FOOTER_H + 10

    # Footer divider
    lines.append(
        f'<line x1="{PAD}" y1="{fy - 2}" x2="{W - PAD}" y2="{fy - 2}" '
        f'stroke="{GRV["bg2"]}" stroke-opacity=".4"/>'
    )

    # Timestamp (left)
    lines.append(
        f'<text x="{PAD}" y="{fy + 16}" '
        f'font-family="{MONO}" font-size="9.5" fill="{GRV["dim"]}">'
        f'updated {now}'
        f'</text>'
    )

    # Username (right)
    lines.append(
        f'<text x="{W - PAD}" y="{fy + 16}" '
        f'font-family="{MONO}" font-size="9.5" fill="{GRV["dim"]}" text-anchor="end">'
        f'@{esc(USERNAME)}'
        f'</text>'
    )

    lines.append('</svg>')
    return "\n".join(lines)


if __name__ == "__main__":
    print(f"Fetching language stats for @{USERNAME}…")
    langs_size, langs_repos = get_language_stats()

    if not langs_size:
        print("✗ No language data — check GITHUB_TOKEN and username.")
    else:
        svg = build_svg(langs_size, langs_repos)
        os.makedirs("assets", exist_ok=True)
        out = "assets/languages.svg"
        with open(out, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"✓ {out} generated  ({len(svg):,} bytes)")
