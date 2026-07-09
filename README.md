# 🦜 Parrot Video Analyzer Agent

**Turn a raw lecture recording into a clean study video — automatically.**

Parrot listens to your lecture, remembers what matters, and cuts out everything that doesn't: student chatter, "can you repeat that?", dead air, breaks, and off-topic tangents. What's left is a tight, watchable video of the instructor actually teaching.

> Named Parrot because it repeats back only what's worth remembering — the "Parrot Memory" node evolves a running summary of the lecture as it goes, chunk by chunk.

---

## 🧠 How it works

```
Teams VTT + Video
        │
        ▼
┌───────────────────┐
│ Transcript Parser  │  → cleans captions, groups into sliding-window chunks
└─────────┬──────────┘
          ▼
┌───────────────────┐
│  Parrot Memory     │  → evolves the lecture topic, remembers key points
└─────────┬──────────┘
          ▼
┌───────────────────┐
│ Segment Extractor  │  → decides exactly which timestamps to KEEP
└─────────┬──────────┘
          ▼
┌───────────────────┐
│   Video Editor     │  → ffmpeg cuts + stitches the final study video
└───────────────────┘
```

Built on **LangGraph** for clean, typed state management across chunks — the lecture's evolving topic and memory flow forward automatically as the pipeline works through the recording.

## ✨ Features

- 🎯 **Smart cutting** — keeps instructor teaching, cuts student mic time, logistics, breaks, and chatter
- 🔁 **Repeat-aware** — if a student asks the instructor to repeat something, the *answer* is always kept
- 🧵 **Sliding-window context** — chunks overlap so nothing gets lost at the edges
- 📝 **Auto-generated summary** — a bullet-point recap of the whole lecture, for free
- 🗑️ **QA video** — a second "discarded" video so you can sanity-check what got cut
- 🎬 **Lossless cuts** — ffmpeg stream-copy, no re-encoding

## 🚀 Quick Start

### Prerequisites
- [**uv**](https://docs.astral.sh/uv/) – a fast Python package installer and resolver.
- **ffmpeg** – installed and available on your `PATH`.
- Python 3.10+ (uv will manage the virtual environment for you).

### One‑command setup

```bash
git clone https://github.com/Muhammed-M/Parrot_Video-Analyzer-Agent.git
cd Parrot_Video-Analyzer-Agent
./setup.sh
```

Create a `.env` file:

```env
MODEL_NAME=your-model-name
PROVIDER_API_KEY=your-api-key
BASE_URL=https://your-provider-endpoint
```



## 📂 Project Structure

```
src/
├── graph.py               # LangGraph pipeline definition
├── state.py                # Shared agent state
├── nodes/
│   ├── summary_writer.py    # Summaries the Video in txt file
│   ├── parrot_memory.py    # Evolves topic + memory per chunk
│   └── segment_extractor.py # Decides what to keep
└── utils/
    ├── transcript_parser.py # VTT parsing + chunking
    └── video_editor.py      # ffmpeg cutting/stitching
main.py                      # Entry point / orchestration
```
---

🦜 *Squawk less, learn more.*
