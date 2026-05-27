import os
import requests
from datetime import datetime
USERNAME = "ulite-Amr"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}
# ── Gruvbox dark palette ──────────────────────────────────────────
GRV = {
    "bg":       "#282828",
    "bg1":      "#3c3836",
    "bg2":      "#504945",
    "fg":       "#ebdbb2",
    "gray":     "#a89984",
    "dimgray":  "#7c6f64",
    "yellow":   "#fabd2f",
    "orange":   "#fe8019",
    "red":      "#fb4934",
    "green":    "#b8bb26",
    "aqua":     "#8ec07c",
    "blue":     "#83a598",
    "purple":   "#d3869b",
}
LANG_COLORS = {
    "Kotlin":    "#7F52FF",
    "Java":      "#b07219",
    "Rust":      "#dea584",
    "Python":    "#3572A5",
    "Swift":     "#F05138",
    "JavaScript":"#f1e05a",
    "TypeScript":"#3178c6",
    "C++":       "#f34b7d",
    "C":         "#555555",
    "Shell":     "#89e051",
    "HTML":      "#e34c26",
    "CSS":       "#563d7c",
    "TOML":      "#9c4221",
    "Makefile":  "#427819",
    "CMake":     "#DA3434",
}
FALLBACK = [GRV["yellow"], GRV["orange"], GRV["red"],
            GRV["green"], GRV["aqua"], GRV["blue"], GRV["purple"]]
def get_language_stats() -> tuple[dict[str, int], dict[str, list[tuple[str, int]]]]:
    langs_size: dict[str, int] = {}
    langs_repos: dict[str, list[tuple[str, int]]] = {}
    query = """
    query($username: String!) {
      user(login: $username) {
        repositories(first: 100, isFork: false, ownerAffiliations: OWNER) {
          nodes {
            name
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges { size  node { name } }
            }
          }
        }
        repositoriesContributedTo(first: 100, contributionTypes: [COMMIT, PULL_REQUEST]) {
          nodes {
            name
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges { size  node { name } }
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
                        langs_repos.setdefault(lang, []).append((name, sz))
            process(result["data"]["user"]["repositories"]["nodes"])
            process(result["data"]["user"]["repositoriesContributedTo"]["nodes"])
    except Exception as e:
        print(f"Error: {e}")
    return langs_size, langs_repos
def fmt_bytes(b: int) -> str:
    if b >= 1_000_000:
        return f"{b / 1_000_000:.1f} MB"
    if b >= 1_000:
        return f"{b / 1_000:.0f} kB"
    return f"{b} B"
def build_svg(langs_size: dict[str, int],
               langs_repos: dict[str, list[tuple[str, int]]],
               top_n: int = 6) -> str:
    ranked = sorted(langs_size.items(), key=lambda x: -x[1])[:top_n]
    total = sum(b for _, b in ranked)
    if not total:
        return ""
    W, PAD = 400, 22
    TITLE_H = 48
    BAR_H = 5
    BAR_W = W - PAD * 2
    FONT = "'JetBrains Mono','Fira Code','Courier New',monospace"
    FOOTER_H = 42
    BLOCK_GAP = 22
    # Height calculation
    H = TITLE_H + PAD
    for lang, _ in ranked:
        n = min(len(langs_repos.get(lang, [])), 2)
        H += 34 + n * 14 + BLOCK_GAP
    H += FOOTER_H
    now = datetime.now().strftime("%b %Y")
    out = [
        f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{GRV["bg1"]}" stop-opacity="0"/>
    <stop offset="100%" stop-color="{GRV["bg1"]}" stop-opacity="1"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{H}" rx="10" fill="{GRV["bg"]}"/>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="9.5" stroke="{GRV["bg2"]}"/>
<rect x="{PAD}" y="18" width="3" height="14" rx="1.5" fill="{GRV["yellow"]}"/>
<text x="{PAD+10}" y="28" font-family={FONT!r} font-size="12" font-weight="700" fill="{GRV["yellow"]}" letter-spacing="2">LANGUAGES</text>
<line x1="{PAD}" y1="40" x2="{W-PAD}" y2="40" stroke="{GRV["bg2"]}"/>'''
    ]
    y = TITLE_H
    for i, (lang, count) in enumerate(ranked):
        pct = count / total
        color = LANG_COLORS.get(lang, FALLBACK[i % 7])
        bar_w = round(BAR_W * pct, 1)
        # ── Left accent bar ────────────────────────────────────────
        out.append(f'''
<rect x="{PAD}" y="{y}" width="3" height="28" rx="1.5" fill="{color}" opacity="0.5"/>''')
        # ── Language name ──────────────────────────────────────────
        out.append(f'''
<text x="{PAD+12}" y="{y+11}" font-family={FONT!r} font-size="13" font-weight="600" fill="{GRV["fg"]}">{lang}</text>''')
        # ── Byte count & percentage (right side) ───────────────────
        out.append(f'''
<text x="{W-PAD-82}" y="{y+11}" font-family={FONT!r} font-size="10" fill="{GRV["dimgray"]}" text-anchor="end">{fmt_bytes(count)}</text>
<text x="{W-PAD}" y="{y+11}" font-family={FONT!r} font-size="11" fill="{GRV["gray"]}" text-anchor="end">{pct*100:.1f}%</text>''')
        # ── Progress bar ───────────────────────────────────────────
        out.append(f'''
<rect x="{PAD}" y="{y+18}" width="{BAR_W}" height="{BAR_H}" rx="2.5" fill="{GRV["bg1"]}"/>
<rect x="{PAD}" y="{y+18}" width="{bar_w}" height="{BAR_H}" rx="2.5" fill="{color}" opacity="0.85"/>''')
        # ── Repositories ───────────────────────────────────────────
        repos = sorted(langs_repos.get(lang, []), key=lambda x: -x[1])
        ry = y + 32
        for ri, (rname, _) in enumerate(repos[:2]):
            out.append(f'''
<text x="{PAD+14}" y="{ry+ri*14}" font-family={FONT!r} font-size="9.5" fill="{GRV["gray"]}">└─ {rname}</text>''')
        extra = len(repos) - 2
        if extra > 0:
            rx_pos = PAD + 14
            ry_pos = ry + 2 * 14 - 7
            out.append(f'''
<rect x="{rx_pos}" y="{ry_pos}" width="20" height="13" rx="3" fill="{GRV["bg1"]}"/>
<text x="{rx_pos+10}" y="{ry_pos+10}" font-family={FONT!r} font-size="8.5" font-weight="600" fill="{GRV["gray"]}" text-anchor="middle">+{extra}</text>''')
        # ── Subtle separator ───────────────────────────────────────
        nlines = min(len(repos), 2)
        sep = y + 32 + nlines * 14 + 11
        out.append(f'''
<line x1="{PAD}" y1="{sep}" x2="{W-PAD}" y2="{sep}" stroke="{GRV["bg1"]}" stroke-dasharray="2 3" opacity="0.6"/>''')
        y += 34 + nlines * 14 + BLOCK_GAP
    # ── Footer ─────────────────────────────────────────────────────
    fy = H - FOOTER_H + 14
    total_repos = sum(len(r) for r in langs_repos.values())
    out.append(f'''
<line x1="{PAD}" y1="{fy-4}" x2="{W-PAD}" y2="{fy-4}" stroke="url(#g)" stroke-width="1"/>
<text x="{PAD}" y="{fy+8}" font-family={FONT!r} font-size="9" fill="{GRV["dimgray"]}">{total_repos} repositories · updated {now}</text>
<text x="{W-PAD}" y="{fy+8}" font-family={FONT!r} font-size="9" fill="{GRV["dimgray"]}" text-anchor="end">github.com/{USERNAME}</text>''')
    out.append("\n</svg>")
    return "".join(out)
if __name__ == "__main__":
    print(f"Fetching stats for {USERNAME}...")
    langs_size, langs_repos = get_language_stats()
    svg = build_svg(langs_size, langs_repos)
    if svg:
        os.makedirs("assets", exist_ok=True)
        with open("assets/languages.svg", "w") as f:
            f.write(svg)
        print("✓ assets/languages.svg generated")
    else:
        print("✗ No language data")
