"""
Preprocessing for embeddings.

Takes the raw scraping CSV as input (at minimum: video_id, comment_id,
parent_id, is_reply, autor, texto, likes, fecha, fecha_descarga, estado_video).

Output: same metadata + a 'texto_clean' column ready for sentence embedding models.
"""

import pandas as pd
import re
from langdetect import detect, LangDetectException

# === CONFIG ===

INPUT_FILE = "comentarios_multivideo_robusto2.csv"
OUTPUT_FILE = "comentarios_para_embeddings.csv"

TEXT_COL = "texto"
STATUS_COL = "estado_video"

# Quality filters for the text I'll embed
MIN_CHAR_LEN = 10
MIN_WORDS = 2

# I filter to Spanish only; set to False if running on a multilingual corpus
USAR_FILTRO_IDIOMA = True
IDIOMA_OBJETIVO = "es"


# === FUNCTIONS ===

def cargar_datos():
    """Reads the raw CSV and returns a DataFrame."""
    print(f"Reading: {INPUT_FILE}")
    df = pd.read_csv(
        INPUT_FILE,
        sep=";",
        encoding="utf-8",
        engine="python"
    )

    if TEXT_COL not in df.columns:
        raise ValueError(f"Text column '{TEXT_COL}' not found. Available: {list(df.columns)}")

    if STATUS_COL not in df.columns:
        raise ValueError(f"Status column '{STATUS_COL}' not found. Available: {list(df.columns)}")

    print(f"Rows loaded: {len(df)}")
    return df


def limpiar_texto_para_embeddings(texto):
    """
    Minimal cleaning for embeddings.
    I remove URLs, timestamps, and normalize whitespace, but I keep
    punctuation and emojis — they carry semantic information for the model.
    """
    if not isinstance(texto, str):
        texto = str(texto)

    texto = texto.strip()
    texto = texto.replace("\n", " ").replace("\r", " ")
    texto = re.sub(r"http\S+|www\.\S+", "", texto)
    texto = re.sub(r"\b\d{1,2}:\d{2}(:\d{2})?\b", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    texto = texto.lower().strip()

    return texto


def detectar_idioma_seguro(texto):
    """
    Detects language with langdetect.
    Returns 'unknown' on short or unparseable input.
    """
    if not isinstance(texto, str):
        return "unknown"
    texto = texto.strip()
    if len(texto) < 3:
        return "unknown"
    try:
        return detect(texto)
    except (LangDetectException, Exception):
        return "unknown"


def aplicar_filtros_de_calidad(df):
    """
    Applies quality filters in sequence:
    1. Keep only successfully downloaded rows
    2. Drop NaN text
    3. Clean text -> 'texto_clean'
    4. Drop empty texts after cleaning
    5. Filter by minimum length (chars and words)
    6. Optionally filter by language
    """
    # 1. Keep only successful downloads
    antes = len(df)
    df = df[df[STATUS_COL] == "EXITO"].copy()
    print(f"After status filter: {len(df)} rows (dropped {antes - len(df)})")

    # 2. Drop NaN
    df = df.dropna(subset=[TEXT_COL]).reset_index(drop=True)
    print(f"After dropping NaN: {len(df)} rows")

    # 3. Clean
    print("Cleaning text for embeddings...")
    df["texto_clean"] = df[TEXT_COL].apply(limpiar_texto_para_embeddings)

    # 4. Drop empties
    antes = len(df)
    df = df[df["texto_clean"].str.strip() != ""].copy()
    print(f"After dropping empty texts: {len(df)} rows (dropped {antes - len(df)})")

    # 5. Length filters
    df["n_chars"] = df["texto_clean"].str.len()
    df["n_words"] = df["texto_clean"].str.split().apply(len)

    antes = len(df)
    df = df[
        (df["n_chars"] >= MIN_CHAR_LEN) &
        (df["n_words"] >= MIN_WORDS)
    ].copy()
    print(f"After length filter: {len(df)} rows (dropped {antes - len(df)})")

    # 6. Language filter
    if USAR_FILTRO_IDIOMA:
        print("Detecting language...")
        df["lang"] = df["texto_clean"].apply(detectar_idioma_seguro)
        antes = len(df)
        df = df[df["lang"] == IDIOMA_OBJETIVO].copy().reset_index(drop=True)
        print(f"Spanish only: {len(df)} (dropped {antes - len(df)})")
    else:
        df["lang"] = "unknown"

    return df


def seleccionar_columnas_salida(df):
    """
    Selects the columns to keep: metadata for traceability + cleaned text.
    I only include columns that actually exist in the DataFrame.
    """
    columnas_basicas = [
        "video_id",
        "comment_id",
        "parent_id",
        "is_reply",
        "autor",
        "likes",
        "fecha",
        "fecha_descarga",
        STATUS_COL,
        TEXT_COL,
        "texto_clean",
        "n_chars",
        "n_words",
        "lang",
    ]

    columnas_presentes = [c for c in columnas_basicas if c in df.columns]
    return df[columnas_presentes].copy()


def main():
    # 1. Load raw data
    df = cargar_datos()

    # 2. Filter and clean
    df = aplicar_filtros_de_calidad(df)

    # 3. Select output columns
    df_salida = seleccionar_columnas_salida(df)

    # 4. Save
    print(f"Saving to: {OUTPUT_FILE}")
    df_salida.to_csv(OUTPUT_FILE, sep=";", encoding="utf-8", index=False)
    print("Done.")


if __name__ == "__main__":
    main()
