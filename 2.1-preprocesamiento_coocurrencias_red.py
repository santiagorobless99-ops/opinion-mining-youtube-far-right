# Requires Python 3.11 (last version fully compatible with spaCy).
# Run inside a virtualenv: .\venv\Scripts\python.exe 2.1-preprocesamiento_coocurrencias_red.py

import pandas as pd
import re
from langdetect import detect, LangDetectException
import spacy
from spacy.lang.es.stop_words import STOP_WORDS

# === CONFIG ===
INPUT_FILE = "comentarios_multivideo_robusto.csv"
OUTPUT_FILE = "comentarios_limpios.csv"
TEXT_COLUMN = "texto"


def cargar_datos():
    """Lee el CSV y devuelve un DataFrame."""
    print(f"Leyendo: {INPUT_FILE}")
    df = pd.read_csv(
        INPUT_FILE,
        sep=";",
        engine="python"
    )

    if TEXT_COLUMN not in df.columns:
        raise ValueError(f"La columna '{TEXT_COLUMN}' no existe. Columnas disponibles: {list(df.columns)}")

    df = df.dropna(subset=[TEXT_COLUMN])
    df = df.reset_index(drop=True)
    print(f"Filas cargadas: {len(df)}")
    return df


def limpiar_ruido(text):
    """
    Limpieza básica de ruido:
    - minúsculas
    - eliminar saltos de línea
    - eliminar URLs
    - eliminar marcas de tiempo (ej. 1:23, 12:03:45)
    - reemplazar caracteres no alfanuméricos por espacios
    """
    if not isinstance(text, str):
        text = str(text)

    text = text.lower()
    text = text.replace("\n", " ")
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\b\d{1,2}:\d{2}(:\d{2})?\b", "", text)
    text = re.sub(r"[^\w\sáéíóúñü]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def detectar_idioma(text):
    """
    Devuelve el código de idioma (ej. 'es', 'en').
    Textos muy cortos son poco fiables; devuelve 'unknown' para menos de 3 caracteres.
    """
    if not isinstance(text, str) or len(text.strip()) < 3:
        return "unknown"
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


def procesar_con_spacy(df):
    """
    Aplica spaCy a la columna 'clean' para obtener:
    - tokens (todas las palabras)
    - lemmas (formas base)
    - tokens_no_stop (lemas sin stopwords, solo alfabéticos)
    """
    print("Cargando modelo de spaCy (es_core_news_sm)...")
    nlp = spacy.load("es_core_news_sm")

    tokens_list = []
    lemmas_list = []
    tokens_no_stop_list = []

    print("Procesando con spaCy (puede tardar un momento)...")

    for doc in nlp.pipe(df["clean"].tolist(), batch_size=50):
        tokens = []
        lemmas = []
        tokens_no_stop = []

        for token in doc:
            if token.is_space:
                continue

            tokens.append(token.text)
            lemmas.append(token.lemma_)

            # Solo conservamos lemas sin stopwords y compuestos únicamente de letras
            if (not token.is_stop) and token.is_alpha:
                tokens_no_stop.append(token.lemma_.lower())

        tokens_list.append(tokens)
        lemmas_list.append(lemmas)
        tokens_no_stop_list.append(tokens_no_stop)

    df["tokens"] = tokens_list
    df["lemmas"] = lemmas_list
    df["tokens_no_stop"] = tokens_no_stop_list

    # Convertimos listas a cadenas separadas por espacios para guardar en CSV
    df["tokens_str"] = df["tokens"].apply(lambda toks: " ".join(toks))
    df["lemmas_str"] = df["lemmas"].apply(lambda toks: " ".join(toks))
    df["tokens_no_stop_str"] = df["tokens_no_stop"].apply(lambda toks: " ".join(toks))

    return df


def main():
    # 1. Cargar datos
    df = cargar_datos()

    # 2. Limpiar ruido y guardar en columna 'clean'
    print("Limpiando texto...")
    df["clean"] = df[TEXT_COLUMN].apply(limpiar_ruido)

    # 3. Detectar idioma
    print("Detectando idioma...")
    df["lang"] = df["clean"].apply(detectar_idioma)

    # 4. Conservar solo comentarios en español
    antes = len(df)
    df = df[df["lang"] == "es"].reset_index(drop=True)
    print(f"Comentarios en español: {len(df)} (descartados {antes - len(df)})")

    # 5. Tokenizar y lematizar con spaCy
    df = procesar_con_spacy(df)

    # 6. Guardar
    columnas_a_guardar = [
        TEXT_COLUMN,
        "clean",
        "lang",
        "tokens_str",
        "lemmas_str",
        "tokens_no_stop_str"
    ]

    print(f"Guardando en: {OUTPUT_FILE}")
    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
        columns=columnas_a_guardar,
        sep=";"
    )
    print("Listo.")


if __name__ == "__main__":
    main()
