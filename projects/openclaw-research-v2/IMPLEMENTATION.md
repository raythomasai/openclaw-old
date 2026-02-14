# OpenClaw Research v2 - Implementation Plan
## Tonight (Feb 3, 2026)

---

## 🎯 Goal
Implement the core research pipeline: Scout → Harvester → Deduplication → Output

---

## 📋 Implementation Steps

### Phase 1: Foundation Setup (18:00-19:00)

#### 1.1 Create Project Structure
```bash
mkdir -p projects/openclaw-research-v2/{src/{agents,collectors,dedup,output,utils},data/{raw,processed},config}
```

#### 1.2 Create Config File
- `config.yaml` with API keys and source configs
- Environment variables for secrets

#### 1.3 Set Up Dependencies
```bash
cd projects/openclaw-research-v2
python3 -m venv venv
source venv/bin/activate
pip install requests tweepy praw python-dotenv redis
```

---

### Phase 2: Collector Implementation (19:00-21:00)

#### 2.1 Twitter/X Collector
- Use Twitter API v2 (or tweepy)
- Search: "OpenClaw", "@openclaw_ai", "#openclaw"
- Rate limiting: 450 req/15min
- Output: JSON lines to `data/raw/twitter.jsonl`

#### 2.2 YouTube Collector
- YouTube Data API
- Search: OpenClaw tutorials, demos, showcases
- Extract: title, description, view count, comments
- Output: `data/raw/youtube.jsonl`

#### 2.3 Reddit Collector
- Use Pushshift API (faster, unlimited)
- Search: r/OpenClaw, r/ArtificialIntelligence, r/automation
- Fallback: Reddit API if Pushshift fails
- Output: `data/raw/reddit.jsonl`

#### 2.4 GitHub Collector
- GitHub API search
- Search: OpenClaw repos, forks, stars
- Extract: README, issues, discussions
- Output: `data/raw/github.jsonl`

---

### Phase 3: Deduplication Engine (21:00-22:00)

#### 3.1 Content Fingerprinting
- SHA-256 hash of content (normalized: lowercase, stripped)
- Bloom filter for memory-efficient dedup
- Redis set for exact-match dedup

#### 3.2 Similarity Detection
- SimHash or MinHash for near-duplicate detection
- Threshold: 0.85 similarity
- Output: `data/processed/deduplicated.jsonl`

---

### Phase 4: Output Generator (22:00-23:00)

#### 4.1 Slack Formatter
- One-line summaries with links
- Batch by source
- Post to #research

#### 4.2 Document Generator
- Markdown → Google Doc (via Google Docs API)
- PDF export (markdown → PDF)

---

## 🚀 Tonight's Run Command

```bash
cd projects/openclaw-research-v2
source venv/bin/activate
python src/main.py --sources twitter youtube reddit github --output slack
```

---

## 📁 File Structure

```
projects/openclaw-research-v2/
├── config/
│   └── config.yaml          # API keys, settings
├── src/
│   ├── agents/
│   │   ├── scout.py         # Discover new sources
│   │   ├── harvester.py    # Pull from all sources
│   │   ├── analyzer.py     # Quality scoring
│   │   └── synthesizer.py  # Generate outputs
│   ├── collectors/
│   │   ├── twitter.py
│   │   ├── youtube.py
│   │   ├── reddit.py
│   │   ├── github.py
│   │   └── hackernews.py
│   ├── dedup/
│   │   ├── fingerprint.py
│   │   └── dedup.py
│   ├── output/
│   │   ├── slack.py
│   │   ├── docs.py
│   │   └── pdf.py
│   └── utils/
│       ├── rate_limiter.py
│       └── logger.py
├── data/
│   ├── raw/                 # Unprocessed data
│   └── processed/           # Deduplicated, scored
├── main.py                  # Entry point
└── requirements.txt
```

---

## ✅ Success Criteria (End of Night)

- [ ] Collect data from 4+ sources
- [ ] Zero duplicates in final output
- [ ] Post to Slack #research with findings
- [ ] Auto-generate Markdown document
- [ ] Ready for PDF export

---

## 🔑 API Keys Needed

| Source | Status | Location |
|--------|--------|----------|
| Twitter API | ⚠️ Check 1Password | op get item "Twitter API" |
| YouTube API | ⚠️ Check 1Password | op get item "Google Cloud" |
| GitHub Token | ⚠️ Check 1Password | op get item "GitHub" |
| Reddit API | ✅ Pushshift (free) | - |
| Discord Token | ⚠️ If needed | - |

---

## 📞 Post-Run Tasks

1. Review findings quality
2. Adjust scoring algorithm
3. Add missing sources
4. Schedule cron job for nightly runs

---

*Plan created: 2026-02-03 10:46 CST*
