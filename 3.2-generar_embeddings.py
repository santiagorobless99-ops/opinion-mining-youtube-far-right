"""
Generación de embeddings para el corpus de comentarios de YouTube.

Entrada: comentarios_para_embeddings.csv (necesita al menos la columna 'texto_clean')
Salida:
    embeddings.npy                    — matriz NumPy (n_comentarios x dim_embedding)
    comentarios_index_embeddings.csv  — metadatos alineados a cada fila de la matriz
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
    Carga el CSV y verifica que la columna de texto existe.
    Devuelve un DataFrame con índice limpio desde 0.
    """
    print(f"Leyendo corpus desde: {path}")
    df = pd.read_csv(path, sep=";", encoding="utf-8", engine="python")

    if text_col not in df.columns:
        raise ValueError(f"La columna '{text_col}' no existe. Disponibles: {list(df.columns)}")

    # No debería haber NaN tras el preprocesamiento, pero por si acaso
    df = df.dropna(subset=[text_col])
    df[text_col] = df[text_col].astype(str).str.strip()
    df = df[df[text_col] != ""].copy()
    df = df.reset_index(drop=True)

    print(f"Comments loaded: {len(df)}")
    return df


def cargar_modelo(model_name: str) -> SentenceTransformer:
    """
    Carga el modelo de sentence-transformers.
    La primera ejecución lo descarga desde HuggingFace.
    """
    print(f"Cargando modelo: {model_name}")
    model = SentenceTransformer(model_name)
    print("Modelo cargado.")
    return model


def generar_embeddings(model: SentenceTransformer, textos: list) -> np.ndarray:
    """
    Codifica la lista de textos en una matriz de embeddings normalizada.
    Se normaliza a norma unitaria para que la similitud coseno sea equivalente al producto punto.
    """
    print(f"Generando embeddings para {len(textos)} textos...")
    embeddings = model.encode(
        textos,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    print(f"Shape de la matriz de embeddings: {embeddings.shape}")
    return embeddings


def guardar_resultados(df: pd.DataFrame, embeddings: np.ndarray,
                       path_embeddings: str, path_index: str):
    """
    Guarda:
    - la matriz de embeddings como .npy
    - un CSV de metadatos con una fila por embedding (alineado por índice)
    """
    print(f"Guardando embeddings en: {path_embeddings}")
    np.save(path_embeddings, embeddings)

    # Columnas de metadatos a conservar junto a los embeddings
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

    print(f"Guardando índice en: {path_index}")
    df_index.to_csv(path_index, sep=";", encoding="utf-8", index=False)

    print(f"Listo. embeddings.npy -> {embeddings.shape}, índice -> {len(df_index)} filas")


def main():
    df = cargar_corpus(INPUT_FILE, TEXT_COLUMN)
    model = cargar_modelo(MODEL_NAME)
    textos = df[TEXT_COLUMN].tolist()
    embeddings = generar_embeddings(model, textos)
    guardar_resultados(df, embeddings, OUTPUT_EMBEDDINGS, OUTPUT_INDEX)


if __name__ == "__main__":
    main()
