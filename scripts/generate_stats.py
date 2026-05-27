import os
import requests

USERNAME = "ulite-Amr"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

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

def get_language_stats() -> tuple[dict[str, int], dict[str, list[tuple[str, int]]]]:
    langs_size: dict[str, int] = {}
    langs_repos: dict[str, list[tuple[str, int]]] = {}
    
    query = """
    query($username: String!) {
      user(login: $username) {
        repositories(first: 100, isFork: false, ownerAffiliations: OWNER) {
          nodes {
            nameWithOwner
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node {
                  name
                }
              }
            }
          }
        }
        repositoriesContributedTo(first: 100, contributionTypes: [COMMIT, PULL_REQUEST]) {
          nodes {
            nameWithOwner
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node {
                  name
                }
              }
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
            timeout=15
        )
        resp.raise_for_status()
        result = resp.json()
        
        if "data" in result and result["data"] and result["data"]["user"]:
            user_data = result["data"]["user"]
            
            # Helper function to process repositories lists cleanly
            def process_repos(repos_list):
                for repo in repos_list:
                    if repo and "languages" in repo:
                        repo_name = repo.get("nameWithOwner", "Unknown")
                        for edge in repo["languages"]["edges"]:
                            lang_name = edge["node"]["name"]
                            size = edge["size"]
                            
                            langs_size[lang_name] = langs_size.get(lang_name, 0) + size
                            
                            if lang_name not in langs_repos:
                                langs_repos[lang_name] = []
                            langs_repos[lang_name].append((repo_name, size))

            process_repos(user_data["repositories"]["nodes"])
            process_repos(user_data["repositoriesContributedTo"]["nodes"])
                            
    except Exception as e:
        print(f"Error fetching GraphQL data: {e}")
        
    return langs_size, langs_repos

def build_svg(langs_size: dict[str, int], langs_repos: dict[str, list[tuple[str, int]]], top_n: int = 6) -> str:
    ranked = sorted(langs_size.items(), key=lambda x: x[1], reverse=True)[:top_n]
    total = sum(b for _, b in ranked)
    if total == 0:
        return ""

    W, PAD = 400, 20
    TITLE_H = 44
    BAR_H = 5
    BAR_W = W - PAD * 2
    FONT = "'JetBrains Mono','Fira Code','Courier New',monospace"

    # Dynamically calculate the perfect height (H) based on repositories list length
    H = TITLE_H + PAD
    for lang, _ in ranked:
        repos = sorted(langs_repos.get(lang, []), key=lambda x: x[1], reverse=True)
        num_repo_lines = min(len(repos), 3)
        if len(repos) > 3:
            num_repo_lines += 1
        H += 34 + (num_repo_lines * 14) + 12

    out = [
        f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect width="{W}" height="{H}" rx="8" fill="{GRV["bg"]}"/>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="7.5" stroke="{GRV["bg2"]}"/>
<rect x="{PAD}" y="16" width="3" height="14" rx="1.5" fill="{GRV["yellow"]}"/>
<text x="{PAD + 10}" y="27" font-family={FONT!r} font-size="12" font-weight="700" fill="{GRV["yellow"]}" letter-spacing="2">LANGUAGES &amp; SOURCES</text>
<line x1="{PAD}" y1="36" x2="{W - PAD}" y2="36" stroke="{GRV["bg2"]}"/>"""
    ]

    y = TITLE_H
    for i, (lang, count) in enumerate(ranked):
        pct = count / total
        color = LANG_COLORS.get(lang, FALLBACK[i % len(FALLBACK)])
        bar_fill = round(BAR_W * pct, 1)

        # Draw main language title, percentage, and progress bar
        out.append(f"""
<circle cx="{PAD + 5}" cy="{y + 10}" r="4" fill="{color}"/>
<text x="{PAD + 16}" y="{y + 14}" font-family={FONT!r} font-size="11.5" font-weight="600" fill="{GRV["fg"]}">{lang}</text>
<text x="{W - PAD}" y="{y + 14}" font-family={FONT!r} font-size="10.5" fill="{GRV["gray"]}" text-anchor="end">{pct * 100:.1f}%</text>
<rect x="{PAD}" y="{y + 20}" width="{BAR_W}" height="{BAR_H}" rx="2.5" fill="{GRV["bg1"]}"/>
<rect x="{PAD}" y="{y + 20}" width="{bar_fill}" height="{BAR_H}" rx="2.5" fill="{color}" opacity="0.85"/>""")

        # Process and draw repository names for the current language
        repos = sorted(langs_repos.get(lang, []), key=lambda x: x[1], reverse=True)
        repo_start_y = y + 34
        
        # Display top 3 repositories
        for r_idx, (repo_name, _) in enumerate(repos[:3]):
            out.append(f"""
<text x="{PAD + 16}" y="{repo_start_y + (r_idx * 14)}" font-family={FONT!r} font-size="9.5" fill="{GRV["dimgray"]}">↳ {repo_name}</text>""")
            
        # Display indicator if there are more than 3 repositories
        if len(repos) > 3:
            more_count = len(repos) - 3
            out.append(f"""
<text x="{PAD + 16}" y="{repo_start_y + (3 * 14)}" font-family={FONT!r} font-size="9.5" font-style="italic" fill="{GRV["dimgray"]}">↳ and {more_count} more...</text>""")

        # Advance y position based on the height of the current block
        num_repo_lines = min(len(repos), 3) + (1 if len(repos) > 3 else 0)
        y += 34 + (num_repo_lines * 14) + 12

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
        print("✓ assets/languages.svg generated successfully with source repositories")
    else:
        print("✗ No language data found")
