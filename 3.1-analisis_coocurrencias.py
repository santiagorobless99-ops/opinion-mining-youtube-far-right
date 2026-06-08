import pandas as pd
from collections import Counter

# === CONFIG ===

INPUT_FILE = "comentarios_limpios.csv"
SEP = ";"
TOKENS_COLUMN = "tokens_no_stop_str"  # lemas sin stopwords separados por espacios
OUTPUT_FILE = "coocurrencias.csv"

# Palabras clave teóricamente motivadas — interesa cómo co-ocurren con otros
# términos en el discurso sobre universidad pública vs. privada.
KEYWORDS = [
    "universidad",
    "carrera",
    "estudiar",
    "trabajo",
    "trabajar",
    "público",
    "privado",
    "plan",
    "b"
]

TOP_N = 20


def cargar_datos():
    """Lee el CSV preprocesado y devuelve un DataFrame."""
    print(f"Leyendo: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE, sep=SEP)

    if TOKENS_COLUMN not in df.columns:
        raise ValueError(
            f"La columna '{TOKENS_COLUMN}' no existe. Columnas disponibles: {list(df.columns)}"
        )

    # Rellenamos NaN para que .split() no falle
    df[TOKENS_COLUMN] = df[TOKENS_COLUMN].fillna("")

    print(f"Filas cargadas: {len(df)}")
    return df


def construir_coocurrencias(df, keywords):
    """
    Construye los conteos de co-ocurrencias para cada palabra clave.

    Lógica: por cada comentario, si aparece la keyword, se cuenta cada
    otro token del mismo comentario como co-ocurrencia. Se usa un set
    para búsquedas O(1) por keyword.

    Devuelve un DataFrame con columnas: keyword, token, cooc_freq, cooc_rel.
    """
    cooc_dict = {kw: Counter() for kw in keywords}

    print("Calculando co-ocurrencias...")

    for tokens_str in df[TOKENS_COLUMN]:
        tokens = str(tokens_str).split()

        if not tokens:
            continue

        token_set = set(tokens)

        for kw in keywords:
            if kw in token_set:
                for tok in tokens:
                    if tok == kw:
                        continue
                    cooc_dict[kw][tok] += 1

    print("Construyendo DataFrame...")

    rows = []
    for kw, counter in cooc_dict.items():
        total_cooc = sum(counter.values())

        for tok, freq in counter.most_common():
            rel = freq / total_cooc if total_cooc > 0 else 0.0
            rows.append({
                "keyword": kw,
                "token": tok,
                "cooc_freq": freq,
                "cooc_rel": rel
            })

    cooc_df = pd.DataFrame(rows)
    cooc_df = cooc_df.sort_values(
        by=["keyword", "cooc_freq"],
        ascending=[True, False]
    ).reset_index(drop=True)

    return cooc_df


def guardar_resultados(cooc_df):
    """Guarda el DataFrame de co-ocurrencias en un CSV."""
    print(f"Guardando en: {OUTPUT_FILE}")
    cooc_df.to_csv(OUTPUT_FILE, index=False, sep=";", encoding="utf-8")
    print("Guardado.")


def mostrar_top_por_keyword(cooc_df, keywords, n=TOP_N):
    """Muestra por pantalla los n tokens más frecuentes por keyword."""
    for kw in keywords:
        print(f"\n=== '{kw}' ===")
        sub = cooc_df[cooc_df["keyword"] == kw].head(n)
        if sub.empty:
            print("  (sin co-ocurrencias)")
            continue

        for i, row in sub.iterrows():
            print(f"  {row['token']:<20} cooc_freq={row['cooc_freq']:<4} cooc_rel={row['cooc_rel']:.4f}")


def main():
    df = cargar_datos()
    cooc_df = construir_coocurrencias(df, KEYWORDS)
    guardar_resultados(cooc_df)
    mostrar_top_por_keyword(cooc_df, KEYWORDS, n=TOP_N)


if __name__ == "__main__":
    main()
