import hashlib
import json
import os
from pathlib import Path

import folium
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import AntPath
from streamlit_folium import st_folium

import plant_id
import scoring
import serp

# ---- edit these two before submitting ----
AUTHOR = "Gauri Agarwal"
REPO_URL = ""  # e.g. "https://github.com/you/balcon-bridge"
# ------------------------------------------

BASE = Path(__file__).parent
PLANTS = json.loads((BASE / "plants.json").read_text(encoding="utf-8"))

# Keys can live in a .env file next to app.py (see .env.example)
try:
    from dotenv import load_dotenv

    load_dotenv(BASE / ".env")
except ImportError:
    pass

st.set_page_config(page_title="Balcon Bridge", page_icon="🐝", layout="wide")

st.markdown(
    """
<style>
.hero {background: linear-gradient(135deg,#14532d 0%,#16a34a 60%,#facc15 130%);
       padding: 38px 32px; border-radius: 20px; margin-bottom: 18px;}
.hero-title {font-size: 46px; font-weight: 800; color: #ffffff; line-height: 1.1; font-family: 'PT Serif', Georgia, serif;}
.hero-sub {font-size: 20px; color: #ecfccb; margin-top: 8px;}
.card {border: 1px solid #bbf7d0; border-radius: 14px; padding: 16px 18px;
       background: #f0fdf4; height: 100%; color: #14532d;}
.card h4 {margin: 0 0 8px 0; color: #166534;}
.step {border-radius: 14px; padding: 14px; background: #ffffff; border: 2px solid #86efac;
       text-align: center; height: 100%; color: #14532d;}
.step-n {font-size: 28px;}
</style>
""",
    unsafe_allow_html=True,
)

if "ids" not in st.session_state:
    st.session_state.ids = {}

if "page" not in st.session_state:
    st.session_state.page = None  # None = landing screen

PAGES = ["🏠 Home", "🐝 Try Balcon Bridge", "⚙️ How it works", "🌍 Vision", "ℹ️ About"]

threshold = 500
if st.session_state.page is not None:
    with st.sidebar:
        st.markdown(
            """<div style="font-size:34px; font-weight:700; line-height:1.2; color:#14532d; font-family:'PT Serif', Georgia, serif;">🐝 Balcon Bridge</div>""",
            unsafe_allow_html=True,
        )
        st.caption("Every balcony is a bridge.")
        threshold = st.slider(
            "Pollinator hop distance (m)", 100, 2000, 500, 50,
            help="How far a pollinator can hop between green spots. Varies by species, see the research panel.",
        )
        st.caption("All scores are rough estimates, not scientific measurements.")
        with st.expander("🔑 API keys", expanded=not plant_id.available()):
            st.caption("Paste a key here and it works instantly for this session. Or put it in a .env file.")
            pk = st.text_input("PlantNet key (automatic plant ID)", type="password", key="pk_input")
            if pk.strip():
                os.environ["PLANTNET_API_KEY"] = pk.strip()
            sk = st.text_input("SerpApi key", type="password", key="sk_input")
            if sk.strip():
                os.environ["SERPAPI_API_KEY"] = sk.strip()
        if plant_id.available():
            st.success("Automatic plant ID is on.")
        else:
            st.info("Automatic plant ID is off. Paste your PlantNet key above, or type plant names.")


# =====================================================================
# HOME
# =====================================================================
def render_home():
    st.markdown(
        '<div class="hero"><div class="hero-title">🐝 Balcon Bridge</div>'
        '<div class="hero-sub">Every balcony is a bridge for the city\'s pollinators.</div></div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.markdown(
        '<div class="card"><h4>🌆 The problem</h4>'
        "Bees and butterflies need a chain of flowers and green spaces they can hop between. "
        "In dense cities, parks and gardens are scattered islands, and the gaps between them "
        "are hard to cross.</div>",
        unsafe_allow_html=True,
    )
    c2.markdown(
        '<div class="card"><h4>💡 Our idea</h4>'
        "Small balcony gardens can act as stepping stones. Balcon Bridge checks whether yours "
        "connects to the nearest green spaces, and tells you what to plant, or where a new "
        "garden should go, to close the gap.</div>",
        unsafe_allow_html=True,
    )
    c3.markdown(
        '<div class="card"><h4>🎁 What you get</h4>'
        "A Balcon Bridge score, an animated corridor map, red warnings where the corridor breaks, "
        "a season-by-season plant plan, nearby nurseries, and the research behind it.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("### How you use it")
    s1, s2, s3, s4 = st.columns(4)
    for col, n, title, text in (
        (s1, "📸", "Snap", "Photograph your plants with your phone."),
        (s2, "🔎", "Scan", "We identify the plants and find green spaces near you."),
        (s3, "🗺️", "See", "Watch your balcony join (or miss) the city's corridor."),
        (s4, "🌱", "Act", "Plant what's missing. Invite neighbours to close the gaps."),
    ):
        col.markdown(
            f'<div class="step"><div class="step-n">{n}</div><b>{title}</b><br>{text}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("### What makes it different")
    st.markdown(
        "- **It finds where the corridor breaks**, not just a score. Red gaps show the smallest set of "
        "bridges that would connect your neighbourhood.\n"
        "- **\"What if neighbours join?\"** A slider adds stepping-stone gardens and shows the corridor forming.\n"
        "- **Every number is traceable.** Scores come from a visible formula, and the research panel "
        "shows the papers behind pollinator ranges.\n"
        "- **Live data, any city.** Built on live Google Maps and Google Scholar search through SerpApi, "
        "so there is no hand-made dataset to maintain.\n"
        "- **Honest by design.** Everything is labelled as an estimate."
    )

    st.markdown("### Who it helps")
    w1, w2, w3, w4 = st.columns(4)
    w1.markdown('<div class="card"><b>🏠 Residents</b><br>See what your balcony adds.</div>', unsafe_allow_html=True)
    w2.markdown('<div class="card"><b>🏘️ Societies (RWAs)</b><br>Plan shared green stepping stones.</div>', unsafe_allow_html=True)
    w3.markdown('<div class="card"><b>🏫 Schools</b><br>A hands-on biodiversity project.</div>', unsafe_allow_html=True)
    w4.markdown('<div class="card"><b>🌿 NGOs and planners</b><br>Spot weak links in the green network.</div>', unsafe_allow_html=True)

    st.success("👉 Tap **🐝 Try Balcon Bridge** at the top to build your own corridor.")


# =====================================================================
# TRY IT
# =====================================================================
def render_tool(threshold: int):
    st.subheader("Check your balcony's bridge")
    st.caption("Snap your plants, tell us where you live, see how connected you are.")

    area = st.text_input("📍 Your area", placeholder="e.g. Dwarka Sector 12, Delhi")
    files = st.file_uploader(
        "📸 Photos of your plants (on a phone, choose 'Take photo')",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
    )
    manual = st.text_input("✍️ Or type plant names, comma separated", placeholder="tulsi, marigold, hibiscus")

    owned: list[str] = []
    photo_gps = None
    for i, f in enumerate(files or []):
        jpeg, gps = plant_id.prepare(f.getvalue())
        photo_gps = photo_gps or gps
        h = hashlib.md5(jpeg).hexdigest()
        if h not in st.session_state.ids:
            with st.spinner(f"Identifying plant in photo {i + 1}..."):
                try:
                    st.session_state.ids[h] = plant_id.identify(jpeg)
                except Exception as e:
                    st.warning(f"Could not identify photo {i + 1}: {e}")
                    st.session_state.ids[h] = []
        suggestions = st.session_state.ids[h]

        c1, c2 = st.columns([1, 3])
        c1.image(jpeg)
        if suggestions:
            c2.markdown(f"**Photo {i + 1}: top matches**")
            labels, lines = {}, []
            for n_, sg in enumerate(suggestions, 1):
                genus = sg["scientific"].split()[0].lower()
                name = sg["common"] or sg["scientific"]
                pct = int(sg["score"] * 100)
                info = PLANTS.get(genus)
                if info:
                    value = "★" * info["value"] + "☆" * (3 - info["value"]) + " pollinator value"
                else:
                    value = "not in our plant list yet (counted as low value)"
                lines.append(f"- 🌿 **{name}** (_{sg['scientific']}_) · {pct}% match · {value}")
                labels[f"{n_}. {name} ({pct}%)"] = genus
            c2.markdown("\n".join(lines))
            choice = c2.radio("Use which one?", [*labels, "Skip this photo"], key=f"sel_{h}", horizontal=True)
            if choice in labels:
                owned.append(labels[choice])
        elif plant_id.available():
            c2.write("Could not recognise a plant in this photo. Try a closer shot of a leaf or flower, or type the name above.")
        else:
            c2.write("Automatic plant ID is off (no PLANTNET_API_KEY). Type the plant name above.")

    for name in [n for n in manual.split(",") if n.strip()]:
        owned.append(scoring.match_plant(name, PLANTS) or name.strip().lower())

    if owned:
        st.write("🌿 Your plants:", ", ".join(sorted(set(owned))))

    use_gps = False
    if photo_gps:
        use_gps = st.checkbox("Use the GPS location saved in my photo", value=True)

    if st.button("Build my bridge 🐝", type="primary"):
        if not owned:
            st.error("Add at least one plant (photo or typed name).")
        elif not area.strip() and not (use_gps and photo_gps):
            st.error("Enter your area.")
        else:
            with st.status("Building your bridge...", expanded=True) as status:
                try:
                    st.write("📍 Locating your area (Google Maps via SerpApi)")
                    home = photo_gps if (use_gps and photo_gps) else serp.geocode(area)
                    st.write("🌳 Finding parks, gardens and nurseries nearby")
                    patches, nurseries = serp.find_places(*home)
                    st.write("📚 Pulling pollinator research (Google Scholar via SerpApi)")
                    papers = serp.research()
                    st.write("🕸️ Building the pollinator network")
                    st.session_state.show_graph = False
                    st.session_state.result = {
                        "home": home, "patches": patches, "nurseries": nurseries,
                        "papers": papers, "owned": owned,
                    }
                    status.update(label="Done! Scroll down for your result", state="complete", expanded=False)
                except Exception as e:
                    status.update(label="Something went wrong", state="error")
                    st.error(f"{e}")

    res = st.session_state.get("result")
    if not res:
        return

    home, owned_r = res["home"], res["owned"]
    an = scoring.analyze(home, res["patches"], threshold)

    k = 0
    if an["gaps"]:
        k = st.slider(
            "🤝 What if neighbours add stepping-stone gardens? Bridge this many gaps",
            0, len(an["gaps"]), 0,
        )
    n_conn, stones = scoring.apply_bridges(an, k)
    total, plant_part, conn_part = scoring.score(owned_r, PLANTS, n_conn)

    open_gaps = max(len(an["gaps"]) - k, 0)
    card_recs = scoring.recommend(owned_r, PLANTS)
    top_plant = card_recs[0][1]["common"][0].title() if card_recs else "Great seasonal mix already"
    tag = "Pollinator-friendly" if plant_part >= 3.5 else "Needs more pollinator plants"
    card_html = (
        '<div style="border:2px solid #16a34a;border-radius:16px;padding:18px 22px;'
        'background:#f0fdf4;max-width:540px;margin-bottom:8px;">'
        '<div style="background:#16a34a;color:white;padding:6px 12px;border-radius:8px;'
        'font-weight:700;display:inline-block;">✅ Scan complete · Biodiversity hub identified</div>'
        '<div style="font-size:16px;color:#14532d;margin-top:12px;line-height:1.9;">'
        f'<b>Score:</b> {total} / 10 <span style="opacity:.6">(estimate)</span><br>'
        f'<b>Connected green patches:</b> {n_conn} &nbsp;·&nbsp; <b>Gaps:</b> {open_gaps}<br>'
        f'<b>Recommended plant:</b> {top_plant}<br>'
        f'<b>Tag:</b> {tag}'
        '</div></div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)
    st.caption(f"Plants: {plant_part}/5 · Connectivity: {conn_part}/5")

    nodes = an["nodes"]
    m = folium.Map(location=home, zoom_start=15, tiles="OpenStreetMap")
    home_members = an["comps"][an["home_idx"]]
    for u, v in an["edges"]:
        in_home = u in home_members and v in home_members
        pts = [(nodes[u]["lat"], nodes[u]["lng"]), (nodes[v]["lat"], nodes[v]["lng"])]
        if in_home:
            AntPath(pts, color="#16a34a", pulse_color="#bbf7d0", weight=5,
                    delay=900, dash_array=[10, 20]).add_to(m)
        else:
            folium.PolyLine(pts, color="#86efac", weight=2, opacity=0.8).add_to(m)
    for idx, g in enumerate(an["gaps"]):
        a, b = nodes[g["a"]], nodes[g["b"]]
        folium.PolyLine(
            [(a["lat"], a["lng"]), (b["lat"], b["lng"])],
            color="#16a34a" if idx < k else "#dc2626", weight=3, dash_array="8",
            tooltip=f"{int(g['dist'])} m gap: needs {len(g['stones'])} stepping-stone garden(s)",
        ).add_to(m)
    for nid, n in nodes.items():
        if nid == "home":
            folium.Marker((n["lat"], n["lng"]), tooltip="Your balcony",
                          icon=folium.Icon(color="blue", icon="home")).add_to(m)
        else:
            folium.CircleMarker((n["lat"], n["lng"]), radius=7, color="#166534",
                                fill=True, fill_color="#22c55e", fill_opacity=0.9,
                                tooltip=f"{n['name']} ({n['kind']})").add_to(m)
    deg: dict = {}
    for u, v in an["edges"]:
        deg[u] = deg.get(u, 0) + 1
        deg[v] = deg.get(v, 0) + 1
    hubs = sorted([(d, nid) for nid, d in deg.items() if nid != "home" and d >= 2], reverse=True)[:2]
    for d, nid in hubs:
        n = nodes[nid]
        folium.Marker(
            (n["lat"], n["lng"]),
            tooltip=f"Eco-Nexus: {n['name']} links {d} green spaces",
            icon=folium.DivIcon(html=(
                '<div style="background:#14532d;color:white;padding:2px 8px;border-radius:10px;'
                'font-size:12px;white-space:nowrap;transform:translate(-30px,-34px);">🌳 Eco-Nexus</div>'
            )),
        ).add_to(m)
    for s in stones:
        folium.CircleMarker((s["lat"], s["lng"]), radius=6, color="#16a34a",
                            fill=True, fill_color="#bbf7d0", fill_opacity=1,
                            tooltip="Possible new stepping-stone garden").add_to(m)
    try:
        st_folium(m, height=520, use_container_width=True, returned_objects=[])
    except TypeError:
        st_folium(m, height=520, returned_objects=[])
    st.caption(
        "Animated green = connected corridor · Red dashed = gap · Light-green dots = gardens neighbours could add "
        "· 🌳 Eco-Nexus = green space linking the most neighbours"
    )

    st.subheader("📊 Compare: today vs. what's possible")
    st.caption("See how your score could grow if you swap in better plants and your neighbours join in.")
    if st.button("📊 See graph", key="see_graph"):
        st.session_state.show_graph = True
    if st.session_state.get("show_graph"):
        with st.spinner("Generating your 3D graph..."):
            render_comparison(an, owned_r)
        if st.button("Hide graph", key="hide_graph"):
            st.session_state.show_graph = False
            st.rerun()

    st.subheader("🌱 What to plant next")
    recs = scoring.recommend(owned_r, PLANTS)
    missing = scoring.missing_seasons(owned_r, PLANTS)
    if missing:
        st.write(f"Nothing of yours is in bloom in: **{', '.join(missing)}**.")
    season_icon = {"summer": "☀️", "monsoon": "🌧️", "winter": "❄️"}
    for genus, info in recs:
        stars = "★" * info["value"] + "☆" * (3 - info["value"])
        st.markdown(
            f"- {season_icon.get(info['for_season'], '🌸')} **{info['common'][0].title()}** "
            f"(_{genus.title()}_) · fills your **{info['for_season']}** gap · pollinator value {stars}"
        )
    if not recs:
        st.write("Great coverage across seasons!")

    if res["nurseries"]:
        near = sorted(res["nurseries"], key=lambda n: scoring.haversine_m(home, (n["lat"], n["lng"])))[:3]
        st.write("🛒 Nearby nurseries:")
        for n in near:
            dist = int(scoring.haversine_m(home, (n["lat"], n["lng"])))
            st.markdown(f"- {n['name']} ({dist} m away)")

    with st.expander("📚 Research behind pollinator ranges (Google Scholar)"):
        for p in res["papers"]:
            st.markdown(f"**[{p['title']}]({p['link']})**  \n{p['snippet']}")
        if not res["papers"]:
            st.write("No papers returned.")

    st.subheader("📣 Share your result")
    st.code(
        f"My balcony scored {total}/10 on Balcon Bridge 🐝 "
        f"({n_conn} green spaces connected, {open_gaps} gaps to bridge). "
        "Every balcony is a bridge for the city's pollinators. Check yours!",
        language="text",
    )
    st.caption("Plant values in plants.json are rough starter estimates. Verify them against research before presenting.")


# =====================================================================
# HOW IT WORKS
# =====================================================================
def render_how():
    st.header("⚙️ How it works")

    st.graphviz_chart(
        """
digraph G {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor="#f0fdf4", color="#16a34a", fontname="Helvetica"];
  edge [color="#16a34a"];
  photo [label="Plant photo\\n(phone camera)"];
  plantnet [label="Plant ID\\n(Pl@ntNet)"];
  area [label="Your area"];
  maps [label="Google Maps\\n(SerpApi)"];
  patches [label="Parks, gardens,\\nnurseries"];
  graph [label="Pollinator network\\n(hop distance)"];
  gaps [label="Gaps + stepping\\nstones"];
  scholar [label="Google Scholar\\n(SerpApi)"];
  out [label="Score, map, plant plan,\\nresearch", fillcolor="#bbf7d0"];
  photo -> plantnet -> out;
  area -> maps -> patches -> graph -> gaps -> out;
  scholar -> out;
}
"""
    )

    st.subheader("What powers each step")
    st.markdown(
        "| Step | Tool | What it does |\n"
        "|---|---|---|\n"
        "| Locate area | **Google Maps** via SerpApi | Turns your area into coordinates |\n"
        "| Find green spaces | **Google Maps** via SerpApi | Parks, gardens and plant nurseries nearby |\n"
        "| Identify plants | **Pl@ntNet** | Suggests the species in your photo (you can correct it) |\n"
        "| Evidence | **Google Scholar** via SerpApi | Papers on pollinator movement and green connectivity |\n"
        "| Network and gaps | **NetworkX** | Builds the green-space network and finds the minimum bridges |\n"
        "| Map | **Folium** | Animated corridors, gaps and hubs |"
    )

    st.subheader("How the score works")
    st.markdown(
        "The Balcon Bridge score is out of 10, made of two halves:\n\n"
        "- **Plants (max 5):** each plant has a pollinator value (1 to 3) in `plants.json`. "
        "`plant score = min(5, 0.7 × sum of values of your different plants)`\n"
        "- **Connectivity (max 5):** how many green spaces are within hop distance through the network. "
        "`connectivity score = min(5, 1.25 × connected green spaces)`\n\n"
        "The plant values are rough starter estimates, and the hop distance is a slider because it "
        "varies by species. Treat the score as a **conversation starter**, not a measurement."
    )

    st.subheader("How gaps and stepping stones are found")
    st.markdown(
        "1. Two places are **connected** if they are within the hop distance.\n"
        "2. Connected places form **clusters**. Your balcony sits in one cluster.\n"
        "3. We find the closest pair of places between clusters, then keep only the gaps that "
        "actually merge clusters (a minimum spanning approach). That is the **fewest bridges** "
        "needed to connect the whole neighbourhood.\n"
        "4. A gap of distance `d` needs about `ceil(d / hop) - 1` **stepping-stone gardens**. "
        "The slider on the result page shows the corridor forming as neighbours join in."
    )

    with st.expander("⚠️ Limitations (we'd rather tell you)"):
        st.markdown(
            "- The score is an **estimate**, not a field measurement of biodiversity.\n"
            "- Pollinator hop distance differs a lot between species. Use the slider and the research panel.\n"
            "- Google Maps coverage varies by area, so some green spaces may be missing.\n"
            "- Plant identification from a photo can be wrong. You can always change it.\n"
            "- Plant values are starter estimates and should be verified against research."
        )
    with st.expander("🔒 Privacy"):
        st.markdown(
            "Photos are sent to the plant identification service to get a species name, and this app "
            "does not save them. Only search results are cached on the server."
        )


# =====================================================================
# VISION
# =====================================================================
def render_vision():
    st.header("🌍 Our vision: from one balcony to the whole city")
    st.caption("The images below are concept art of where this could go. The working product is the Try Balcon Bridge page.")
    a, b = st.columns(2)
    p1, p2 = BASE / "assets" / "concept_1.png", BASE / "assets" / "concept_2.png"
    if p1.exists():
        a.image(str(p1), caption="Concept: scan a balcony, see it join the city's pollinator network")
    if p2.exists():
        b.image(str(p2), caption="Concept: a scan report that grows into city-scale corridors")

    st.subheader("Roadmap (not built yet)")
    st.markdown(
        "- 📱 Live camera scan inside a mobile app\n"
        "- 🌡️ Sourced cooling and carbon ranges, shown with their research links\n"
        "- 🏘️ Neighbourhood challenges: a society closes its gaps together\n"
        "- 🏛️ A dashboard for planners and NGOs to spot weak links across a city\n"
        "- 🔌 An open-source package so other apps can use the connectivity engine"
    )


# =====================================================================
# ABOUT
# =====================================================================
def render_about():
    st.header("ℹ️ About")
    st.markdown(
        f"**Balcon Bridge** was built solo by **{AUTHOR}** for the SerpApi hackathon.\n\n"
        "**Why:** pollinators need connected green spaces, and every balcony can be a small part of that. "
        "Balcon Bridge makes the invisible network visible so people know exactly where to plant.\n\n"
        "**Built with:** Python, Streamlit, SerpApi (Google Maps and Google Scholar), Pl@ntNet, "
        "NetworkX and Folium."
    )
    if REPO_URL:
        st.markdown(f"**Open source:** [{REPO_URL}]({REPO_URL})")
    st.caption("Scores and plant values are estimates. Not scientific advice.")


# =====================================================================
# 3D COMPARISON: today vs what's possible
# =====================================================================
def _bar3d(x, y, h, color, name, text, showlegend, w=0.8, d=0.8):
    X = [x, x + w, x + w, x, x, x + w, x + w, x]
    Y = [y, y, y + d, y + d, y, y, y + d, y + d]
    Z = [0, 0, 0, 0, h, h, h, h]
    tris = [(0, 1, 2), (0, 2, 3), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
            (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    return go.Mesh3d(
        x=X, y=Y, z=Z,
        i=[t[0] for t in tris], j=[t[1] for t in tris], k=[t[2] for t in tris],
        color=color, opacity=0.92, flatshading=True, name=name, legendgroup=name,
        showlegend=showlegend, hovertemplate=f"{name}: {text}<extra></extra>",
    )


def _names(genera):
    out = []
    for g in genera:
        info = PLANTS.get(g)
        out.append(info["common"][0].title() if info else g.title())
    return ", ".join(out)


def render_comparison(an, owned_r):
    upgraded, dropped, added = scoring.upgrade_plants(owned_r, PLANTS)
    n_now, _ = scoring.apply_bridges(an, 0)
    n_all, _ = scoring.apply_bridges(an, len(an["gaps"]))
    now = scoring.score(owned_r, PLANTS, n_now)
    better = scoring.score(upgraded, PLANTS, n_now)
    together = scoring.score(upgraded, PLANTS, n_all)

    scenarios = [("Today", now), ("Better plants", better), ("Plants + neighbours join", together)]
    xs = [0, 2.4, 4.8]
    fig = go.Figure()
    for idx, (label, (total, pp, cp)) in enumerate(scenarios):
        fig.add_trace(_bar3d(xs[idx], 0, max(pp, 0.05), "#16a34a", "Plants", f"{pp}/5", idx == 0))
        fig.add_trace(_bar3d(xs[idx], 1.6, max(cp, 0.05), "#0284c7", "Connectivity", f"{cp}/5", idx == 0))
        fig.add_trace(go.Scatter3d(
            x=[xs[idx] + 0.4], y=[1.2], z=[max(pp, cp) + 0.7], mode="text",
            text=[f"{total}/10"], textfont=dict(size=18, color="#14532d"),
            showlegend=False, hoverinfo="skip",
        ))
    fig.update_layout(
        height=520, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.04),
        scene=dict(
            xaxis=dict(title="", tickmode="array", tickvals=[x + 0.4 for x in xs],
                       ticktext=[s[0] for s in scenarios]),
            yaxis=dict(title="", tickmode="array", tickvals=[0.4, 2.0],
                       ticktext=["Plants", "Connectivity"]),
            zaxis=dict(title="Score", range=[0, 6.5]),
            camera=dict(eye=dict(x=1.7, y=-1.8, z=0.9)),
            aspectmode="manual", aspectratio=dict(x=1.7, y=1, z=0.8),
        ),
    )
    st.plotly_chart(fig)

    if dropped and added:
        change = f"swap **{_names(dropped)}** for **{_names(added)}**"
    elif added:
        change = f"add **{_names(added)}**"
    else:
        change = "your mix already covers every season, so the plant half barely changes"
    st.markdown(
        f"- **Today ({now[0]}/10):** your plants score {now[1]}/5, and {n_now} green space(s) connect to you ({now[2]}/5).\n"
        f"- **Better plants ({better[0]}/10):** {change}. Only the plant half changes; connectivity stays the same.\n"
        f"- **Plants + neighbours join ({together[0]}/10):** if neighbours add stepping-stone gardens that close "
        f"all {len(an['gaps'])} gap(s), {n_all} green space(s) connect to you ({together[2]}/5)."
    )
    with st.expander("How to read this 3D graph"):
        st.markdown(
            "- Left to right is the journey: **today**, then **better plants**, then **the neighbourhood joins in**.\n"
            "- The **height** of a bar is the score. 🟩 Green = the plant half (max 5). 🟦 Blue = the connectivity half (max 5).\n"
            "- The number floating above each group is the total out of 10.\n"
            "- Drag to rotate, scroll to zoom, hover on a bar for its value.\n"
            "- These are **estimates** based on starter plant values and your hop-distance setting, not measurements."
        )


# =====================================================================
# LANDING (video + typing heading + clouds) and NAV
# =====================================================================
FONT_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Felipa&family=Griffy&family=PT+Serif:wght@700&display=swap');
"""

LANDING_CSS = "<style>" + FONT_CSS + """
html, body {background:#ecfdf5 !important;}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] {background: transparent !important;}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {display:none !important;}
.block-container {max-width: 1250px; padding-top: 0 !important;}
.bg-video {position:fixed; top:0; left:0; width:100vw; height:100vh; object-fit:cover; z-index:-2; filter: blur(2px) brightness(1.08) saturate(1.0); transform: scale(1.04);}
.bg-overlay {position:fixed; top:0; left:0; right:0; bottom:0; z-index:-1; background: linear-gradient(180deg, rgba(240,253,244,.32) 0%, rgba(236,253,245,.14) 55%, rgba(220,252,231,.34) 100%);}
.landing-top {text-align:center; margin: 12vh 0 8vh 0;}
.bee {font-size: 50px; animation: bob 3s ease-in-out infinite;}
.typing-box {position:relative; display:inline-block; font-family:'PT Serif', Georgia, serif; font-weight:700; font-size:min(7vw, 96px); line-height:1.15; letter-spacing:.08em; color:#14532d;}
.typing-box .ghost {visibility:hidden; white-space:nowrap; display:block;}
.typing-box .typed {position:absolute; left:0; top:0; white-space:nowrap; overflow:hidden; width:0; border-right:.05em solid #14532d; text-shadow:0 3px 16px rgba(255,255,255,.95), 0 0 2px rgba(255,255,255,.9); animation: typing 2.4s steps(13, end) .6s forwards, caret .75s step-end infinite;}
.tagline {margin: 18px auto 0 auto; max-width: 760px; font-family:'Felipa', Georgia, serif; font-style: italic; font-weight:400; font-size:clamp(18px, 2.1vw, 27px); line-height:1.5; color:#2d6a4f; text-shadow:0 1px 10px rgba(255,255,255,.98); opacity:0; animation: fadein 1s ease 3.2s forwards;}
.st-key-landing {margin-top: 34px;}
.st-key-landing [data-testid="stHorizontalBlock"] {gap: 1.4rem; flex-wrap: nowrap !important; align-items: flex-start;}
.st-key-landing [data-testid="stHorizontalBlock"] > div, .st-key-landing [data-testid="stColumn"] {min-width: 0 !important; flex: 1 1 0 !important; width: auto !important;}
.st-key-landing [data-testid="stButton"] {width:100%; opacity:0; animation: fadein 1s ease 3.5s forwards, floaty 6s ease-in-out 4.6s infinite;}
.st-key-landing [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stButton"] {animation-delay: 3.7s, 4.6s;}
.st-key-landing [data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stButton"] {animation-delay: 3.9s, 4.6s;}
.st-key-landing [data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stButton"] {animation-delay: 4.1s, 4.6s;}
.st-key-landing [data-testid="stHorizontalBlock"] > div:nth-child(5) [data-testid="stButton"] {animation-delay: 4.3s, 4.6s;}
.st-key-landing button {position:relative; overflow:visible; box-sizing:border-box; display:flex; align-items:center; justify-content:center; width:100%; height:112px !important; min-height:112px; padding:14px 12px 0 12px; background:#ffffff; border:none; border-radius:60px; box-shadow:0 14px 30px rgba(20,83,45,.26), inset 0 -8px 0 rgba(22,163,74,.12); transition: transform .25s, background .25s;}
.st-key-landing button::before {content:""; position:absolute; top:-24px; left:9%; width:40%; height:50px; background:#ffffff; border-radius:50%; transition: background .25s;}
.st-key-landing button::after {content:""; position:absolute; top:-32px; right:10%; width:46%; height:60px; background:#ffffff; border-radius:50%; transition: background .25s;}
.st-key-landing button p {position:relative; z-index:2; margin:0; text-align:center; line-height:1.15; font-family:'Griffy', cursive !important; font-size:clamp(14px, 1.45vw, 21px); font-weight:400; color:#14532d;}
.st-key-landing button:hover, .st-key-landing button:focus {transform: translateY(-8px) scale(1.05); background:#f0fdf4; outline:none; box-shadow:0 18px 34px rgba(20,83,45,.35);}
.st-key-landing button:hover::before, .st-key-landing button:hover::after, .st-key-landing button:focus::before, .st-key-landing button:focus::after {background:#f0fdf4;}
@keyframes typing {from {width:0;} to {width:100%;}}
@keyframes caret {50% {border-color: transparent;}}
@keyframes fadein {from {opacity:0;} to {opacity:1;}}
@keyframes floaty {0%, 100% {transform: translateY(0);} 50% {transform: translateY(-9px);}}
@keyframes bob {0%, 100% {transform: translateY(0);} 50% {transform: translateY(-8px);}}
@media (max-width: 760px) {
.st-key-landing [data-testid="stHorizontalBlock"] {flex-wrap: wrap !important;}
.st-key-landing [data-testid="stHorizontalBlock"] > div, .st-key-landing [data-testid="stColumn"] {flex: 1 1 42% !important;}
}
</style>
"""

INNER_CSS = "<style>" + FONT_CSS + """
.stApp {background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%);}
[data-testid="stHeader"] {background: transparent;}
.st-key-nav {margin-top: 22px; margin-bottom: 12px;}
.st-key-nav [data-testid="stHorizontalBlock"] {gap: .9rem; flex-wrap: nowrap !important; align-items: flex-start;}
.st-key-nav [data-testid="stHorizontalBlock"] > div, .st-key-nav [data-testid="stColumn"] {min-width: 0 !important; flex: 1 1 0 !important; width: auto !important;}
.st-key-nav [data-testid="stButton"] {width:100%;}
.st-key-nav button {position:relative; overflow:visible; box-sizing:border-box; display:flex; align-items:center; justify-content:center; width:100%; height:60px !important; min-height:60px; padding:8px 8px 0 8px; background:#ffffff; border:none; border-radius:40px; box-shadow:0 6px 14px rgba(20,83,45,.18); transition: transform .2s;}
.st-key-nav button::before {content:""; position:absolute; top:-10px; left:9%; width:38%; height:24px; background:#ffffff; border-radius:50%;}
.st-key-nav button::after {content:""; position:absolute; top:-14px; right:10%; width:42%; height:28px; background:#ffffff; border-radius:50%;}
.st-key-nav button p {position:relative; z-index:2; margin:0; text-align:center; line-height:1.1; font-family:'Griffy', cursive !important; font-size:clamp(12px, 1.1vw, 16px); font-weight:400; color:#14532d;}
.st-key-nav button:hover {transform: translateY(-3px);}
.st-key-nav [data-testid="stBaseButton-primary"], .st-key-nav [data-testid="stBaseButton-primary"]::before, .st-key-nav [data-testid="stBaseButton-primary"]::after {background:#16a34a;}
.st-key-nav [data-testid="stBaseButton-primary"] p {color:#ffffff;}
</style>
"""

THEME_CSS = """<style>
:root {
  --c-head: #14532d;
  --c-desc: #14532d;
  --c-cloud: #ffffff;
  --c-cloud-hover: #f0f9ff;
  --c-cloud-text: #14532d;
  --c-outline: #16a34a;
  --c-accent: #bae6fd;
  --c-accent-text: #0c4a6e;
  --c-base1: #eefaf2;
  --c-base2: #d9f1e2;
  --c-side: #9fd3b3;
}
.typing-box {color: var(--c-head);}
.typing-box .typed {border-right-color: var(--c-head);}
.tagline {color: var(--c-desc); background: rgba(255,255,255,.62); backdrop-filter: blur(6px); padding: 12px 26px; border-radius: 18px; display: inline-block; text-shadow: none;}
.st-key-landing button, .st-key-landing button::before, .st-key-landing button::after {background: var(--c-cloud);}
.st-key-landing button:hover, .st-key-landing button:focus, .st-key-landing button:hover::before, .st-key-landing button:hover::after, .st-key-landing button:focus::before, .st-key-landing button:focus::after {background: var(--c-cloud-hover);}
.st-key-landing button p {color: var(--c-cloud-text);}
.st-key-landing button {box-shadow: none !important; filter: drop-shadow(3px 0 0 var(--c-outline)) drop-shadow(-3px 0 0 var(--c-outline)) drop-shadow(0 3px 0 var(--c-outline)) drop-shadow(0 -3px 0 var(--c-outline)) drop-shadow(0 10px 12px rgba(20,83,45,.22));}
.st-key-nav button, .st-key-nav button::before, .st-key-nav button::after {background: var(--c-cloud);}
.st-key-nav button:hover, .st-key-nav button:hover::before, .st-key-nav button:hover::after {background: var(--c-cloud-hover);}
.st-key-nav button p {color: var(--c-cloud-text);}
.st-key-nav button {box-shadow: none !important; filter: drop-shadow(2px 0 0 var(--c-outline)) drop-shadow(-2px 0 0 var(--c-outline)) drop-shadow(0 2px 0 var(--c-outline)) drop-shadow(0 -2px 0 var(--c-outline)) drop-shadow(0 6px 8px rgba(20,83,45,.18));}
.st-key-nav [data-testid="stBaseButton-primary"], .st-key-nav [data-testid="stBaseButton-primary"]::before, .st-key-nav [data-testid="stBaseButton-primary"]::after {background: var(--c-accent);}
.st-key-nav [data-testid="stBaseButton-primary"] p {color: var(--c-accent-text);}
.stApp:has(.st-key-nav) {background: linear-gradient(180deg, var(--c-base1) 0%, var(--c-base2) 100%) !important;}
.card {background: #ffffff; border-color: #86efac;}
.step {border-color: #86efac;}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div, [data-testid="stSidebarContent"] {background: var(--c-side) !important;}
[data-testid="stSidebar"] {border-right: 1px solid rgba(20,83,45,.25);}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"], [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color: #14532d !important; opacity: .9;}
[data-testid="stMain"] [data-baseweb="input"], [data-testid="stMain"] [data-baseweb="base-input"], [data-testid="stMain"] [data-baseweb="textarea"], [data-testid="stMain"] [data-baseweb="select"] > div {background: #ffffff !important;}
[data-testid="stMain"] input, [data-testid="stMain"] textarea {background: #ffffff !important;}
[data-testid="stMain"] [data-testid="stFileUploaderDropzone"] {background: #ffffff !important; border: 1px dashed #4ade80;}
</style>"""

BYLINE_CSS = """
<style>
.byline {position:fixed; right:18px; bottom:12px; z-index:9999; font-size:14px; font-weight:700; color:#14532d; background:rgba(255,255,255,.8); padding:5px 14px; border-radius:999px; box-shadow:0 4px 12px rgba(20,83,45,.2);}
</style>
"""


def render_landing():
    st.markdown(LANDING_CSS, unsafe_allow_html=True)
    if (BASE / "static" / "bg.mp4").exists():
        st.markdown(
            '<video class="bg-video" autoplay muted loop playsinline>'
            '<source src="/app/static/bg.mp4" type="video/mp4"></video>',
            unsafe_allow_html=True,
        )
    st.markdown('<div class="bg-overlay"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="landing-top"><div class="bee">🐝</div>'
        '<div class="typing-box"><span class="ghost">BALCON BRIDGE</span>'
        '<span class="typed">BALCON BRIDGE</span></div>'
        '<div class="tagline">Every balcony is a bridge for the city\'s pollinators.<br>See how your plants connect to the green spaces around you.</div></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="landing"):
        cols = st.columns(len(PAGES))
        for i, (col, label) in enumerate(zip(cols, PAGES)):
            if col.button(label, key=f"cloud_{i}"):
                st.session_state.page = i
                st.rerun()


def render_nav():
    st.markdown(INNER_CSS, unsafe_allow_html=True)
    with st.container(key="nav"):
        cols = st.columns(len(PAGES) + 1)
        if cols[0].button("🏡 Start", key="nav_start"):
            st.session_state.page = None
            st.rerun()
        for i, (col, label) in enumerate(zip(cols[1:], PAGES)):
            kind = "primary" if st.session_state.page == i else "secondary"
            if col.button(label, key=f"nav_{i}", type=kind):
                st.session_state.page = i
                st.rerun()


page = st.session_state.page
if page is None:
    render_landing()
else:
    render_nav()
    if page == 0:
        render_home()
    elif page == 1:
        render_tool(threshold)
    elif page == 2:
        render_how()
    elif page == 3:
        render_vision()
    else:
        render_about()

st.markdown(THEME_CSS + BYLINE_CSS + f'<div class="byline">by {AUTHOR}</div>', unsafe_allow_html=True)