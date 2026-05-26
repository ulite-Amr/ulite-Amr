import os

import requests

USERNAME = "ulite-Amr"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

# Gruvbox palette
GRV = {
    "bg": "#282828",
    "bg1": "#3c3836",
    "bg2": "#504945",
    "fg": "#ebdbb2",
    "gray": "#a89984",
    "dimgray": "#7c6f64",
    "yellow": "#fabd2f",
    "orange": "#fe8019",
    "red": "#fb4934",
    "green": "#b8bb26",
    "aqua": "#8ec07c",
    "blue": "#83a598",
    "purple": "#d3869b",
}

LANG_COLORS = {
    "Kotlin": "#7F52FF",
    "Java": "#b07219",
    "Rust": "#dea584",
    "Python": "#3572A5",
    "Swift": "#F05138",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "C++": "#f34b7d",
    "C": "#555555",
    "Shell": "#89e051",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "TOML": "#9c4221",
    "Makefile": "#427819",
    "CMake": "#DA3434",
}

FALLBACK = [
    GRV["yellow"],
    GRV["orange"],
    GRV["red"],
    GRV["green"],
    GRV["aqua"],
    GRV["blue"],
    GRV["purple"],
]


def get_language_stats() -> dict[str, int]:
    langs: dict[str, int] = {}
    page = 1
    while True:
        resp = requests.get(
            f"https://api.github.com/users/{USERNAME}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "type": "owner"},
            timeout=15,
        )
        repos = resp.json()
        if not isinstance(repos, list) or not repos:
            break
        for repo in repos:
            if repo.get("fork"):
                continue
            lr = requests.get(repo["languages_url"], headers=HEADERS, timeout=15)
            for lang, count in lr.json().items():
                langs[lang] = langs.get(lang, 0) + count
        if len(repos) < 100:
            break
        page += 1
    return langs


def build_svg(langs: dict[str, int], top_n: int = 6) -> str:
    ranked = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:top_n]
    total = sum(b for _, b in ranked)
    if total == 0:
        return ""

    W, PAD = 380, 20
    ITEM_H, TITLE_H = 38, 44
    BAR_H = 6
    H = TITLE_H + len(ranked) * ITEM_H + PAD
    BAR_W = W - PAD * 2
    FONT = "'JetBrains Mono','Fira Code','Courier New',monospace"

    out = [
        f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" \
fill="none" xmlns="http://www.w3.org/2000/svg">
<rect width="{W}" height="{H}" rx="8" fill="{GRV["bg"]}"/>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="7.5" stroke="{GRV["bg2"]}"/>
<rect x="{PAD}" y="16" width="3" height="14" rx="1.5" fill="{GRV["yellow"]}"/>
<text x="{PAD + 10}" y="27" font-family={FONT!r} font-size="12" \
font-weight="700" fill="{GRV["yellow"]}" letter-spacing="2">LANGUAGES</text>
<line x1="{PAD}" y1="36" x2="{W - PAD}" y2="36" stroke="{GRV["bg2"]}"/>"""
    ]

    for i, (lang, count) in enumerate(ranked):
        pct = count / total
        color = LANG_COLORS.get(lang, FALLBACK[i % len(FALLBACK)])
        y = TITLE_H + i * ITEM_H
        bar_fill = round(BAR_W * pct, 1)

        out.append(f"""
<circle cx="{PAD + 5}" cy="{y + 10}" r="4" fill="{color}"/>
<text x="{PAD + 16}" y="{y + 14}" font-family={FONT!r} \
font-size="11.5" fill="{GRV["fg"]}">{lang}</text>
<text x="{W - PAD}" y="{y + 14}" font-family={FONT!r} \
font-size="10.5" fill="{GRV["gray"]}" text-anchor="end">{pct * 100:.1f}%</text>
<rect x="{PAD}" y="{y + 20}" width="{BAR_W}" height="{BAR_H}" rx="3" fill="{GRV["bg1"]}"/>
<rect x="{PAD}" y="{y + 20}" width="{bar_fill}" height="{BAR_H}" rx="3" \
fill="{color}" opacity="0.85"/>""")

    out.append("\n</svg>")
    return "".join(out)


if __name__ == "__main__":
    print(f"Fetching stats for {USERNAME}...")
    data = get_language_stats()
    top = dict(sorted(data.items(), key=lambda x: x[1], reverse=True)[:6])
    print(f"Top languages: {top}")

    svg = build_svg(data)
    if svg:
        os.makedirs("assets", exist_ok=True)
        with open("assets/languages.svg", "w") as f:
            f.write(svg)
        print("✓ assets/languages.svg generated")
    else:
        print("✗ No language data found")
