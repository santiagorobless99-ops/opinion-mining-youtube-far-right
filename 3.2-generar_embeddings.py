"""
Generates sentence embeddings for the YouTube comment corpus.

Input:  comentarios_para_embeddings.csv  (needs at least a 'texto_clean' column)
Output:
    embeddings.npy              — NumPy matrix (n_comments x embedding_dim)
    comentarios_index_embeddings.csv  — metadata aligned to each row of the matrix
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

# === CONFIG ===

INPUT_FILE = "comentarios_para_embeddings.csv"
TEXT_COLUMN = "texto_clean"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

OUTPUT_EMBEDDINGS = "embeddings.npy"
OUTPUT_INDEX = "comentarios_index_embeddings.csv"


def cargar_corpus(path: str, text_col: str) -> pd.DataFrame:
    """
    Loads the CSV and checks the text column exists.
    Returns a clean DataFrame with a 0-based index.
    """
    print(f"Reading corpus from: {path}")
    df = pd.read_csv(path, sep=";", encoding="utf-8", engine="python")

    if text_col not in df.columns:
        raise ValueError(f"Column '{text_col}' not found. Available: {list(df.columns)}")

    # There should be no NaN here after preprocessing, but just in case
    df = df.dropna(subset=[text_col])
    df[text_col] = df[text_col].astype(str).str.strip()
    df = df[df[text_col] != ""].copy()
    df = df.reset_index(drop=True)

    print(f"Comments loaded: {len(df)}")
    return df


def cargar_modelo(model_name: str) -> SentenceTransformer:
    """
    Loads the sentence-transformers model.
    First run will download it from HuggingFace.
    """
    print(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)
    print("Model loaded.")
    return model


def generar_embeddings(model: SentenceTransformer, textos: list) -> np.ndarray:
    """
    Encodes the text list into a normalized embedding matrix.
    I normalize to unit norm so cosine similarity reduces to dot product.
    """
    print(f"Generating embeddings for {len(textos)} texts...")
    embeddings = model.encode(
        textos,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    print(f"Embedding matrix shape: {embeddings.shape}")
    return embeddings


def guardar_resultados(df: pd.DataFrame, embeddings: np.ndarray,
                       path_embeddings: str, path_index: str):
    """
    Saves:
    - the embedding matrix as .npy
    - a metadata CSV with one row per embedding (aligned by index)
    """
    print(f"Saving embeddings to: {path_embeddings}")
    np.save(path_embeddings, embeddings)

    # Metadata columns I want to keep alongside the embeddings
    columnas_index = [
        "video_id",
        "comment_id",
        "parent_id",
        "is_reply",
        "autor",
        "likes",
        "fecha",
        "texto",
        "texto_clean",
        "lang",
    ]

    columnas_presentes = [c for c in columnas_index if c in df.columns]
    df_index = df[columnas_presentes].copy()
    df_index.insert(0, "embedding_idx", range(len(df_index)))

    print(f"Saving index to: {path_index}")
    df_index.to_csv(path_index, sep=";", encoding="utf-8", index=False)

    print(f"Done. embeddings.npy -> {embeddings.shape}, index -> {len(df_index)} rows")


def main():
    df = cargar_corpus(INPUT_FILE, TEXT_COLUMN)
    model = cargar_modelo(MODEL_NAME)
    textos = df[TEXT_COLUMN].tolist()
    embeddings = generar_embeddings(model, textos)
    guardar_resultados(df, embeddings, OUTPUT_EMBEDDINGS, OUTPUT_INDEX)


if __name__ == "__main__":
    main()
