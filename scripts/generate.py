"""Generates the SVG cards used by README.md.
Live data is used when GH_TOKEN is set; otherwise sample data is drawn."""
import os, json, math, random, urllib.request
from datetime import date, timedelta

USER = "cartscode"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
TOKEN = os.environ.get("GH_TOKEN", "")
W = 900
BG, ACC, BAR = "#0d1117", "#38BDF8", "#2f81f7"
CARD, EDGE, TXT, MUT = "#0f1722", "#1e3a5f", "#e6edf3", "#9fb0c3"
FONT = "'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'Fira Code',Consolas,'Courier New',monospace"
LANG_COLORS = {"Python": "#3b82f6", "JavaScript": "#facc15", "Java": "#f97316",
               "C#": "#a855f7", "HTML": "#ef4444", "CSS": "#06b6d4", "TypeScript": "#2563eb"}

os.makedirs(OUT, exist_ok=True)

def svg(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs>{defs}</defs><rect width="{w}" height="{h}" fill="{BG}"/>{body}</svg>')

def save(name, s):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(s)

def fade(id_, rtl=False):
    a, b = ("1", "0") if rtl else ("0", "1")
    return (f'<linearGradient id="{id_}" x1="0" x2="1"><stop offset="0" stop-color="{ACC}" stop-opacity="{a}"/>'
            f'<stop offset="1" stop-color="{ACC}" stop-opacity="{b}"/></linearGradient>')

# ---------- header ----------
def header():
    body = f'''
<line x1="30" y1="42" x2="225" y2="42" stroke="url(#l)" stroke-width="2"/>
<line x1="675" y1="42" x2="870" y2="42" stroke="url(#r)" stroke-width="2"/>
<text x="450" y="60" text-anchor="middle" font-family="{FONT}" font-size="50" font-weight="800" letter-spacing="7" fill="#7dd3fc">CARTER CARIG</text>
<text x="450" y="104" text-anchor="middle" font-family="{MONO}" font-size="19" fill="#7dd3fc">BS Information Technology Student | Aspiring Web Developer</text>
<text x="450" y="132" text-anchor="middle" font-family="{MONO}" font-size="19" fill="#7dd3fc">Building Ideas Into Reality | Always Learning and Improving</text>
<line x1="30" y1="168" x2="320" y2="168" stroke="url(#l)" stroke-width="2"/>
<line x1="580" y1="168" x2="870" y2="168" stroke="url(#r)" stroke-width="2"/>
<rect x="332" y="148" width="236" height="40" rx="20" fill="none" stroke="{ACC}" stroke-width="2">
<animate attributeName="stroke-opacity" values="1;0.35;1" dur="3s" repeatCount="indefinite"/></rect>
<text x="450" y="174" text-anchor="middle" font-family="{FONT}" font-size="17" font-weight="700" fill="{ACC}">DEVELOPER IN PROGRESS</text>'''
    save("header.svg", svg(W, 205, body, fade("l") + fade("r", True)))

# ---------- section titles ----------
def title(slug, text):
    text = text.replace("&", "&amp;")
    body = (f'<rect x="2" y="8" width="4" height="28" rx="1" fill="{BAR}"/>'
            f'<text x="20" y="31" font-family="{FONT}" font-size="24" font-weight="700" letter-spacing="1" fill="{TXT}">{text}</text>')
    save(f"title-{slug}.svg", svg(W, 44, body))

# ---------- data ----------
def gql(q):
    req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": q}).encode(),
                                 headers={"Authorization": "bearer " + TOKEN})
    return json.load(urllib.request.urlopen(req, timeout=30))["data"]["user"]["contributionsCollection"]

def fetch_live():
    c = gql('{user(login:"%s"){contributionsCollection{totalCommitContributions contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}}}' % USER)
    cal = c["contributionCalendar"]
    weeks = [[(date.fromisoformat(d["date"]), d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]]
    hdr = {"Authorization": "bearer " + TOKEN}
    repos = json.load(urllib.request.urlopen(urllib.request.Request(
        f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner", headers=hdr), timeout=30))
    tot = {}
    for r in repos:
        if r["fork"]:
            continue
        for k, v in json.load(urllib.request.urlopen(urllib.request.Request(r["languages_url"], headers=hdr), timeout=30)).items():
            tot[k] = tot.get(k, 0) + v
    s = sum(tot.values()) or 1
    top = sorted(tot.items(), key=lambda x: -x[1])[:4]
    langs = [(k, round(v * 100 / s, 1)) for k, v in top]
    langs.append(("Others", round(100 - sum(p for _, p in langs), 1)))
    return weeks, cal["totalContributions"], c["totalCommitContributions"], langs

def fetch_sample():
    rnd = random.Random(7)
    end = date.today()
    start = end - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)
    weeks, d = [], start
    while d <= end:
        w = []
        for _ in range(7):
            w.append((d, (rnd.choice([1, 1, 2, 3, 5]) if rnd.random() < 0.25 else 0) if d <= end else None))
            d += timedelta(days=1)
        weeks.append(w)
    total = sum(c for w in weeks for _, c in w if c)
    langs = [("Python", 32.4), ("JavaScript", 27.9), ("Java", 18.7), ("C#", 11.2), ("Others", 9.8)]
    return weeks, total, total, langs

try:
    if not TOKEN:
        raise RuntimeError("no token")
    weeks, total, commits, langs = fetch_live()
except Exception as e:
    print("Using sample data:", e)
    weeks, total, commits, langs = fetch_sample()

# ---------- contribution card ----------
def contrib():
    mx = max([c or 0 for w in weeks for _, c in w] + [1])
    shades = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    def lvl(c):
        if not c: return 0
        r = c / mx
        return 1 if r <= .25 else 2 if r <= .5 else 3 if r <= .75 else 4
    x0, y0, s, g = 52, 48, 10, 3
    out = [f'<rect x="2" y="2" width="896" height="166" rx="12" fill="{CARD}" stroke="{EDGE}" stroke-width="1.5"/>']
    last_m, last_i = None, -9
    for i, w in enumerate(weeks):
        m = w[0][0].month
        if m != last_m and i - last_i >= 3:
            out.append(f'<text x="{x0 + i * (s + g)}" y="36" font-family="{FONT}" font-size="11" fill="{MUT}">{w[0][0].strftime("%b")}</text>')
            last_m, last_i = m, i
        for j, (_, c) in enumerate(w):
            if c is None: continue
            out.append(f'<rect x="{x0 + i * (s + g)}" y="{y0 + j * (s + g)}" width="{s}" height="{s}" rx="2" fill="{shades[lvl(c)]}"/>')
    for name, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        out.append(f'<text x="44" y="{y0 + row * (s + g) + 9}" text-anchor="end" font-family="{FONT}" font-size="11" fill="{MUT}">{name}</text>')
    out.append(f'<line x1="770" y1="45" x2="770" y2="125" stroke="{EDGE}" stroke-width="2"/>'
               f'<text x="830" y="68" text-anchor="middle" font-family="{FONT}" font-size="13" fill="{TXT}">Total Contributions</text>'
               f'<text x="830" y="108" text-anchor="middle" font-family="{FONT}" font-size="38" font-weight="700" fill="#22c55e">{total}</text>'
               f'<text x="830" y="132" text-anchor="middle" font-family="{FONT}" font-size="13" fill="{TXT}">in the last year</text>')
    save("contributions.svg", svg(W, 170, "".join(out)))

# ---------- statistics ----------
GH = "M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"

def stats():
    cum, run = [], 0
    for w in weeks:
        run += sum(c or 0 for _, c in w)
        cum.append(run)
    pts = cum[::max(1, len(cum) // 14)][:15] or [0, 1]
    hi = max(pts[-1], 1)
    poly = " ".join(f"{270 + i * 110 / (len(pts) - 1):.1f},{120 - p * 50 / hi:.1f}" for i, p in enumerate(pts))
    left = (f'<g transform="translate(2,2)"><rect width="400" height="146" rx="12" fill="{CARD}" stroke="{EDGE}" stroke-width="1.5"/>'
            f'<path transform="translate(34,35) scale(3.4)" fill="#93c5fd" d="{GH}"/>'
            f'<text x="150" y="58" font-family="{FONT}" font-size="15" fill="{MUT}">Total Commits</text>'
            f'<text x="150" y="102" font-family="{FONT}" font-size="38" font-weight="700" fill="{TXT}">{commits}</text>'
            f'<polyline points="{poly}" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-linejoin="round"/></g>')
    r, C, off, segs = 32, 2 * math.pi * 32, 0, []
    for k, p in langs:
        ln = C * p / 100
        col = LANG_COLORS.get(k, "#6b7280")
        segs.append(f'<circle cx="70" cy="73" r="{r}" fill="none" stroke="{col}" stroke-width="14" '
                    f'stroke-dasharray="{ln:.2f} {C - ln:.2f}" stroke-dashoffset="{-off:.2f}" transform="rotate(-90 70 73)"/>')
        off += ln
    leg = []
    for i, (k, p) in enumerate(langs):
        cx, row = (150, i) if i < 3 else (330, i - 3)
        y = 62 + row * 26
        leg.append(f'<circle cx="{cx}" cy="{y - 5}" r="5" fill="{LANG_COLORS.get(k, "#6b7280")}"/>'
                   f'<text x="{cx + 16}" y="{y}" font-family="{FONT}" font-size="14" fill="{TXT}">{k.replace("&", "&amp;")}</text>'
                   f'<text x="{cx + 120}" y="{y}" text-anchor="end" font-family="{FONT}" font-size="14" fill="{TXT}">{p}%</text>')
    right = (f'<g transform="translate(418,2)"><rect width="480" height="146" rx="12" fill="{CARD}" stroke="{EDGE}" stroke-width="1.5"/>'
             f'<text x="150" y="34" font-family="{FONT}" font-size="15" fill="{TXT}">Top Languages</text>'
             + "".join(segs) + "".join(leg) + "</g>")
    save("statistics.svg", svg(W, 152, left + right))

# ---------- footer ----------
def footer():
    body = f'''
<line x1="30" y1="30" x2="160" y2="30" stroke="url(#l)" stroke-width="2"/>
<line x1="740" y1="30" x2="870" y2="30" stroke="url(#r)" stroke-width="2"/>
<text x="450" y="36" text-anchor="middle" font-family="{FONT}" font-size="17" font-weight="600" letter-spacing="7" fill="{ACC}">THANK YOU FOR VISITING MY PROFILE</text>
<text x="450" y="70" text-anchor="middle" font-family="{FONT}" font-size="12" letter-spacing="4" fill="{MUT}">LEARNING · BUILDING · IMPROVING</text>'''
    save("footer.svg", svg(W, 85, body, fade("l") + fade("r", True)))

header(); footer(); contrib(); stats()
for slug, t in [("about", "ABOUT ME"), ("tech", "TECHNOLOGIES & TOOLS"), ("projects", "FEATURED PROJECTS"),
                ("activity", "GITHUB CONTRIBUTION & ACTIVITY"), ("stats", "GITHUB STATISTICS")]:
    title(slug, t)
print("done")
