# 🐝 Balcon Bridge

**Every balcony is a bridge for the city's pollinators.**

Balcon Bridge shows whether your balcony garden connects to nearby green spaces, where the pollinator corridor breaks, and what to plant to close the gap. It is built on live Google Maps and Google Scholar data through SerpApi.

- **Hackathon:** SerpApi India Hackathon 2026
- **Track:** Knowledge & Public Interest
- **Demo video:** `<add your unlisted video link here>`
- **Built by:** Gauri Agarwal

---

## The problem

Bees and butterflies need a chain of flowers and green spaces they can hop between. In dense cities, parks and gardens are scattered islands, and the gaps between them are hard to cross.

Many people want to help and put a few plants on their balcony, but they cannot tell:

- whether their plants actually help pollinators,
- which plants to add,
- whether there is any green space nearby to connect to,
- which single change would matter most.

Balcon Bridge turns that guesswork into a concrete answer.

## What it does

You enter your area and your plants (photo or typed names). Balcon Bridge then shows:

| Output | Meaning |
|---|---|
| **Balcon Bridge score (x/10)** | Plant quality (max 5) plus connectivity to nearby green spaces (max 5). An estimate. |
| **Animated corridor map** | Green flowing lines = connected corridor. Red dashed lines = gaps. |
| **Eco-Nexus hubs** | The green spaces that link the most neighbours. |
| **"What if neighbours join?" slider** | Adds stepping-stone gardens and shows the corridor forming. |
| **Plant plan** | Season-by-season gaps and plants that fill them. |
| **Nearby nurseries** | Where to buy those plants, with distance. |
| **Research panel** | Papers behind pollinator movement ranges (Google Scholar). |
| **3D comparison graph** | Today vs. better plants vs. neighbours joining, with a plain-language explanation of each bar. |
| **Share text** | A ready-to-copy summary of your result. |

## How SerpApi is used

SerpApi provides all of the live location and research data. Without it, the map, the network, the gaps, the score and the evidence panel cannot be produced.

| SerpApi engine | Where (`serp.py`) | What it does | Why it matters |
|---|---|---|---|
| **Google Maps** (`google_maps`) | `geocode()` | Turns "Dwarka Sector 12, Delhi" into coordinates | Works for any area, no hand-made city list |
| **Google Maps** (`google_maps`) | `find_places()` | Finds parks, gardens (green patches) and plant nurseries around the point | These places **are** the network: every node, edge, gap and score comes from them |
| **Google Scholar** (`google_scholar`) | `research()` | Fetches papers on pollinator foraging distance and green connectivity | Backs the hop-distance assumption with sources instead of guesses |

About 5 SerpApi searches are used per new area (1 geocode, 3 place queries, 1 Scholar query). Results are cached on disk in `.cache/`, so repeating an area costs nothing.

## How it works

1. **Locate:** the area is geocoded with Google Maps (or taken from the photo's GPS data if present).
2. **Find green spaces:** parks and gardens become nodes in a network. Nurseries are kept separately for recommendations.
3. **Connect:** two places are *connected* if they are within the **hop distance** (adjustable, default 500 m). Connected places form clusters (NetworkX). Your balcony sits in one cluster.
4. **Find gaps:** the closest pair of places between clusters is found, then only the gaps that actually merge clusters are kept (a minimum-spanning approach). This is the **fewest bridges** needed to connect the neighbourhood.
5. **Stepping stones:** a gap of distance `d` needs about `ceil(d / hop) - 1` new gardens. The slider simulates adding them.
6. **Score:**
   - `plant score = min(5, 0.7 × sum of pollinator values of your different plants)`
   - `connectivity score = min(5, 1.25 × green spaces connected to you)`
7. **Recommend:** seasons with nothing in bloom are matched to plants in `plants.json`.

Plant identification from a photo uses the free Pl@ntNet API (optional). You can always correct the suggestion or type plant names instead.

## Setup

**Requirements:** Python 3.10 or newer, a free SerpApi key. A Pl@ntNet key is optional.

```bash
git clone <your-repo-url>
cd balcon-bridge
python -m pip install -r requirements.txt
```

Set your keys (never commit them). Easiest: copy `.env.example` to `.env` and fill it in. Or paste them in the app sidebar under 🔑 API keys. Or set them in the terminal:

```powershell
# Windows PowerShell
$env:SERPAPI_API_KEY="your-serpapi-key"
$env:PLANTNET_API_KEY="your-plantnet-key"   # optional
```

```bash
# macOS / Linux
export SERPAPI_API_KEY="your-serpapi-key"
export PLANTNET_API_KEY="your-plantnet-key"   # optional
```

Run:

```bash
python -m streamlit run app.py
```

On Windows, use `py` instead of `python` if `python` is not found.

**Free keys:**
- SerpApi: https://serpapi.com/users/sign_up?plan=free (250 searches per month)
- Pl@ntNet (optional): https://my.plantnet.org

**Use it from a phone (same WiFi):**
```bash
python -m streamlit run app.py --server.address 0.0.0.0
```
Then open `http://<your-computer-ip>:8501` on the phone and use "Take photo" in the uploader.

**Optional fonts:** the landing page uses the Matcha Home and Mexina fonts if you place them in `static/fonts/` (see the note in that folder). Without them, similar Google fonts are used.

Without a Pl@ntNet key the app still works: type plant names such as `tulsi, marigold, hibiscus`.

## Project structure

| File | Purpose |
|---|---|
| `app.py` | Streamlit app: animated landing screen, then Home, Try Balcon Bridge, How it works, Vision, About |
| `serp.py` | SerpApi calls (Google Maps, Google Scholar) with disk caching |
| `plant_id.py` | Photo preparation, EXIF GPS, Pl@ntNet identification |
| `scoring.py` | Network building, gap finding, bridges, score, recommendations |
| `plants.json` | Starter plant data (pollinator value and bloom seasons) |
| `assets/` | Concept art used on the Vision page |
| `static/bg.mp4` | Slowed, silent background video for the landing screen |
| `.streamlit/config.toml` | Theme and static file serving (needed for the background video) |

## Limitations (honest)

- The score is an **estimate**, not a field measurement of biodiversity.
- Pollinator hop distance differs a lot between species. Use the slider and the research panel.
- Google Maps coverage varies by area, so some green spaces may be missing.
- Photo identification can be wrong; you can correct it.
- Pollinator values and bloom seasons in `plants.json` are starter estimates and should be verified against research.
- The images on the Vision page are concept art, not screenshots of the product.

## AI tools used

- **Claude (Anthropic):** used as a coding assistant to design the app, write the code and draft this README. The idea, direction, testing and decisions are the author's.
- `<add any other AI tool you used, for example for the concept images>`

## Roadmap (not built)

- Live camera scan in a mobile app
- Sourced cooling and carbon ranges shown with their research links
- Neighbourhood challenges for housing societies
- A dashboard for planners and NGOs
- An open-source package exposing the connectivity engine

## License

MIT, see `LICENSE`.
