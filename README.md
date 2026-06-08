# Opinion Mining: Far-Right Discourse on YouTube (Spain)

NLP pipeline for collecting and analyzing comments on Spanish far-right YouTube channels. Part of a doctoral research project examining how far-right online communities construct discourse around cultural and educational topics.

## Research Context

This pipeline was developed for a PhD thesis (Universitat de València) on the platformization of far-right discourse in Spain and Argentina. The corpus consists of comments on videos by Spanish right-wing influencers discussing the public vs. private university debate — a flashpoint in broader "culture war" narratives.

**Sampled channels:** Rodri Salas, Roberto Vaquero, Wall Street Wolverine, Juan Ramón Rallo, Iker Jiménez.

## Pipeline

Four sequential scripts, each building on the previous output:

| Script | Input | Output | Description |
|---|---|---|---|
| `1-scrapping_Youtube_comentarios.py` | YouTube API | `comentarios_*.csv` | Downloads top-level comments and replies via YouTube Data API v3 |
| `2.1-preprocesamiento_coocurrencias_red.py` | raw CSV | `comentarios_limpios_coocurrencias.csv` | Text cleaning, language detection, spaCy lemmatization |
| `2.2-preprocesamiento_embeddings.py` | raw CSV | `comentarios_limpios_embeddings.csv` | Light cleaning for sentence embedding (preserves punctuation/emoji) |
| `3.1-analisis_coocurrencias.py` | preprocessed CSV | `coocurrencias.csv` | Co-occurrence frequency analysis per keyword |
| `3.2-generar_embeddings.py` | preprocessed CSV | `embeddings.npy` | Multilingual sentence embeddings via `sentence-transformers` |

## Methods

**Text preprocessing:** lowercasing, URL/mention removal, language detection (`langdetect`), lemmatization and stopword removal (spaCy `es_core_news_sm`).

**Co-occurrence analysis:** token-level co-occurrence frequencies and relative frequencies for a configurable set of theoretical keywords (e.g., *universidad*, *privado*, *trabajo*).

**Semantic embeddings:** `paraphrase-multilingual-MiniLM-L12-v2` (384-dimensional vectors, normalized). Enables downstream clustering, similarity search, and semantic mapping of the discourse.

## Installation

```bash
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```

**Configure credentials:**

```bash
cp .env.example .env
# Edit .env and add your YouTube Data API v3 key
# Get one at: https://console.cloud.google.com/
```

## Usage

Run scripts in order:

```bash
python 1-scrapping_Youtube_comentarios.py
python 2.1-preprocesamiento_coocurrencias_red.py
python 2.2-preprocesamiento_embeddings.py
python 3.1-analisis_coocurrencias.py
python 3.2-generar_embeddings.py
```

Before running the scraper, configure `VIDEO_IDS` in `1-scrapping_Youtube_comentarios.py` with the YouTube video IDs you want to analyze.

## Output Files

| File | Description |
|---|---|
| `comentarios_*.csv` | Raw scraped data (comment ID, author, text, likes, date, reply flag) |
| `comentarios_limpios_coocurrencias.csv` | Tokenized/lemmatized corpus |
| `comentarios_limpios_embeddings.csv` | Cleaned text ready for embedding |
| `coocurrencias.csv` | Co-occurrence matrix (keyword × token × freq) |
| `embeddings.npy` | NumPy array of sentence embeddings |

> Raw data files are excluded from this repository. Contact the author for access.

## Notes

- The YouTube API quota is 10,000 units/day on a standard key. The scraper handles `HttpError` and logs partial results on quota exhaustion.
- Language detection (`langdetect`) is probabilistic; short comments may be misclassified.
- The keyword list in `3.1-analisis_coocurrencias.py` is theoretically motivated and can be reconfigured.


## Authors

Santiago Robles — PhD Candidate, Social Sciences, Universitat de València  
Ignacio Lezica Cabrera — PhD, Social Sciences, Universitat de València 
Contact: santiagorobless99@gmail.com
