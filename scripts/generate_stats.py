import os
import requests
from datetime import datetime
USERNAME = "ulite-Amr"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}
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
def fmt_bytes(b):
    if b >= 1_000_000:
        return f"{b / 1_000_000:.1f}MB"
    if b >= 1_000:
        return f"{b / 1_000:.0f}kB"
    return f"{b}B"
def build_svg(langs_size, langs_repos, top_n=6):
    ranked = sorted(langs_size.items(), key=lambda x: -x[1])[:top_n]
    total = sum(b for _, b in ranked)
    if not total:
        return ""
    W, PAD = 420, 24
    FONT = "'JetBrains Mono','Fira Code','Courier New',monospace"
    BAR_H = 5
    BAR_W = W - PAD * 2
    BLOCK_GAP = 20
    # ── height ────────────────────────────────────────────────────
    H = 60  # header
    for lang, _ in ranked:
        n = min(len(langs_repos.get(lang, [])), 2)
        n_lines = n + (1 if n > 2 else 0)
        H += 38 + n_lines * 14 + BLOCK_GAP
    H += 44  # footer
    now = datetime.now().strftime("%b %Y")
    lines = [
        f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="bgGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#2a2a2a"/>
    <stop offset="100%" stop-color="{GRV["bg"]}"/>
  </linearGradient>
  <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{GRV["bg1"]}" stop-opacity="0"/>
    <stop offset="100%" stop-color="{GRV["bg1"]}" stop-opacity="1"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{H}" rx="12" fill="url(#bgGrad)"/>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="11.5" stroke="{GRV["bg2"]}"/>
<!-- Header -->
<rect x="{PAD}" y="20" width="3" height="16" rx="1.5" fill="{GRV["yellow"]}"/>
<text x="{PAD+12}" y="32" font-family={FONT!r} font-size="14" font-weight="700" fill="{GRV["yellow"]}" letter-spacing="2.5">LANGUAGES</text>
<text x="{W-PAD}" y="32" font-family={FONT!r} font-size="10" fill="{GRV["dimgray"]}" text-anchor="end">{len(ranked)} languages · {sum(len(v) for v in langs_repos.values())} repos</text>
<line x1="{PAD}" y1="46" x2="{W-PAD}" y2="46" stroke="{GRV["bg2"]}"/>'''
    ]
    y = 60
    for i, (lang, count) in enumerate(ranked):
        pct = count / total
        color = LANG_COLORS.get(lang, FALLBACK[i % 7])
        bar_w = round(BAR_W * pct, 1)
        # ── Language row ───────────────────────────────────────────
        lines.append(f'''
<circle cx="{PAD+5}" cy="{y+8}" r="4.5" fill="{color}" opacity=".9"/>
<text x="{PAD+18}" y="{y+12}" font-family={FONT!r} font-size="13" font-weight="600" fill="{GRV["fg"]}">{lang}</text>
<text x="{W-PAD}" y="{y+12}" font-family={FONT!r} font-size="13" font-weight="700" fill="{GRV["fg"]}" text-anchor="end">{pct*100:.1f}%</text>''')
        # ── Bar ────────────────────────────────────────────────────
        lines.append(f'''
<rect x="{PAD}" y="{y+18}" width="{BAR_W}" height="{BAR_H}" rx="3" fill="{GRV["bg1"]}"/>
<rect x="{PAD}" y="{y+18}" width="{bar_w}" height="{BAR_H}" rx="3" fill="{color}" opacity=".85"/>''')
        # ── Byte count under bar ───────────────────────────────────
        lines.append(f'''
<text x="{PAD}" y="{y+18+BAR_H+12}" font-family={FONT!r} font-size="9.5" fill="{GRV["dimgray"]}">{fmt_bytes(count)}</text>''')
        # ── Repos ─────────────────────────────────────────────────
        repos = sorted(langs_repos.get(lang, []), key=lambda x: -x[1])
        ry = y + 18 + BAR_H + 22
        for ri, (rname, _) in enumerate(repos[:2]):
            lines.append(f'''
<text x="{PAD+14}" y="{ry+ri*14}" font-family={FONT!r} font-size="9" fill="{GRV["gray"]}">· {rname}</text>''')
        extra = len(repos) - 2
        if extra > 0:
            bx = PAD + 14
            by = ry + 2 * 14 - 7
            lines.append(f'''
<rect x="{bx}" y="{by}" width="20" height="14" rx="4" fill="{GRV["bg1"]}"/>
<text x="{bx+10}" y="{by+10}" font-family={FONT!r} font-size="8" font-weight="600" fill="{GRV["dimgray"]}" text-anchor="middle">+{extra}</text>''')
        # ── Separator ──────────────────────────────────────────────
        nlines = min(len(repos), 2)
        sep_y = y + 18 + BAR_H + 22 + nlines * 14 + 10
        lines.append(f'''
<line x1="{PAD}" y1="{sep_y}" x2="{W-PAD}" y2="{sep_y}" stroke="{GRV["bg1"]}" stroke-dasharray="2 4" opacity=".5"/>''')
        y += 38 + nlines * 14 + BLOCK_GAP
    # ── Footer ─────────────────────────────────────────────────────
    fy = H - 40 + 14
    total_bytes = sum(b for _, b in ranked)
    lines.append(f'''
<line x1="{PAD}" y1="{fy-6}" x2="{W-PAD}" y2="{fy-6}" stroke="url(#fade)" stroke-width="1"/>
<text x="{PAD}" y="{fy+8}" font-family={FONT!r} font-size="9" fill="{GRV["dimgray"]}">{fmt_bytes(total_bytes)} total · {now}</text>
<text x="{W-PAD}" y="{fy+8}" font-family={FONT!r} font-size="9" fill="{GRV["dimgray"]}" text-anchor="end">@{USERNAME}</text>''')
    lines.append("\n</svg>")
    return "".join(lines)
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
