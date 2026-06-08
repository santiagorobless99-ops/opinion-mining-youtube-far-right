from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import csv
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === CONFIGURA TU API KEY EN UN ARCHIVO .env ===
# Crea un archivo .env en esta carpeta con el contenido:
#   YOUTUBE_API_KEY=tu_clave_aqui
# Obtén una clave en: https://console.cloud.google.com/
API_KEY = os.getenv("YOUTUBE_API_KEY")

VIDEO_IDS = [
    "2qyTVETSOKE", # Rodri Salas video https://www.youtube.com/watch?v=2qyTVETSOKE
    "n04uHumiiDU", # Roberto Vaquero short https://www.youtube.com/shorts/n04uHumiiDU
    "OoGYc4KhRWI", # Roberto Vaquero short https://www.youtube.com/shorts/OoGYc4KhRWI
    "qCB2E_YBgP0",# Roberto Vaquero video https://www.youtube.com/watch?v=qCB2E_YBgP0
    "eUkDaMirjYU", # Wall St. Wolverine video https://www.youtube.com/watch?v=eUkDaMirjYU
    "E770DNGYeUA", # Wall St. Wolverine short https://www.youtube.com/shorts/E770DNGYeUA
    "ozhKAomDTjE", # Wall St. Wolverine short https://www.youtube.com/shorts/ozhKAomDTjE
    "bviJ0PnO8EI", # Wall St. Wolverine short https://www.youtube.com/shorts/bviJ0PnO8EI
    "Ed-EJHjxI88", # Wall St. Wolverine short https://www.youtube.com/shorts/Ed-EJHjxI88
    "QVSKDUA9p9s", # Wall St. Wolverine short https://www.youtube.com/shorts/QVSKDUA9p9s
    "2GcQVaqdgEU", # Wall St. Wolverine short https://www.youtube.com/shorts/2GcQVaqdgEU
    "hnUDs-zXKUs", # Wall St. Wolverine entrevistando a Juan Ramón Rallo video https://www.youtube.com/watch?v=hnUDs-zXKUs 
    "HkW8QsGeL8A", # Worldcast entrevistando a Juan Ramón Rallo https://www.youtube.com/shorts/HkW8QsGeL8A
    "2_srTgttqH4", # Juan Ramón Rallo atacando universidad privada video https://www.youtube.com/watch?v=2_srTgttqH4
    "oNiHsD6uF1Q", # Iker Jiménez video "universidad pública vs privada" https://www.youtube.com/watch?v=oNiHsD6uF1Q
    # Criterio de selección: sólo vídeos de influencers de derecha españoles, no clips sacados de la tele ni vídeos descontextualizados
    # Estrategia de búsqueda usada: cuenta de Youtube anónima para no sesgar el algoritmo. Keywords: "universidad progre"...
    # ... "universidad woke", "universidad privada"
]

OUTPUT_FILE = "comentarios_multivideo_robusto2.csv"
FECHA_DESCARGA = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# === CREAR EL CLIENTE DE YOUTUBE ===
youtube = build("youtube", "v3", developerKey=API_KEY)

def descargar_comentarios_y_replies(video_id: str):
    """
    Descarga comentarios de nivel superior y replies de un vídeo concreto.
    Devuelve una tupla: (lista de diccionarios, estado_descarga).
    """
    comentarios = []
    token_siguiente = None
    estado_descarga = "EXITO"

    try:
        # PRIMER INTENTO DE LLAMADA A LA API
        respuesta_inicial = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText",
            pageToken=token_siguiente
        ).execute()

        respuesta = respuesta_inicial # Usar la primera respuesta

        while True:
            for item in respuesta["items"]:
                # ---------- Comentario de nivel superior ----------
                top_comment = item["snippet"]["topLevelComment"]
                top_snippet = top_comment["snippet"]
                top_id = top_comment["id"]

                comentarios.append({
                    "video_id": video_id,
                    "comment_id": top_id,
                    "parent_id": "",
                    "is_reply": 0,
                    "autor": top_snippet.get("authorDisplayName"),
                    "texto": top_snippet.get("textDisplay"),
                    "likes": top_snippet.get("likeCount"),
                    "fecha": top_snippet.get("publishedAt"),
                    "fecha_descarga": FECHA_DESCARGA, # Nuevo metadato
                    "estado_video": estado_descarga, # Nuevo metadato
                })

                # ---------- Replies (respuestas al comentario) ----------
                replies = item.get("replies", {}).get("comments", [])
                for reply in replies:
                    r_snippet = reply["snippet"]
                    r_id = reply["id"]

                    comentarios.append({
                        "video_id": video_id,
                        "comment_id": r_id,
                        "parent_id": top_id,
                        "is_reply": 1,
                        "autor": r_snippet.get("authorDisplayName"),
                        "texto": r_snippet.get("textDisplay"),
                        "likes": r_snippet.get("likeCount"),
                        "fecha": r_snippet.get("publishedAt"),
                        "fecha_descarga": FECHA_DESCARGA, # Nuevo metadato
                        "estado_video": estado_descarga, # Nuevo metadato
                    })

            token_siguiente = respuesta.get("nextPageToken")
            if not token_siguiente:
                break

            # Llamada para la siguiente página
            respuesta = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=100,
                textFormat="plainText",
                pageToken=token_siguiente
            ).execute()

    except HttpError as e:
        # Manejo de errores específicos de la API (404, 403, etc.)
        estado_descarga = f"ERROR_API_{e.resp.status}"
        print(f"  -> {estado_descarga}: Error al procesar {video_id}. Detalle: {e.content.decode()}")

    except Exception as e:
        # Manejo de otros errores no relacionados directamente con la API
        estado_descarga = f"ERROR_OTRO"
        print(f"  -> {estado_descarga}: Error inesperado en {video_id}. Detalle: {e}")

    # Devolver comentarios recogidos hasta el fallo (si los hay) y el estado final
    return comentarios, estado_descarga


def guardar_csv(datos, archivo):
    """
    Guarda la lista de diccionarios en un CSV con separador ';'.
    """
    with open(archivo, "w", newline="", encoding="utf-8") as f:
        campos = [
            "video_id",
            "comment_id",
            "parent_id",
            "is_reply",
            "autor",
            "texto",
            "likes",
            "fecha",
            "fecha_descarga", # Nuevo campo
            "estado_video",   # Nuevo campo
        ]
        escritor = csv.DictWriter(
            f,
            fieldnames=campos,
            delimiter=";",
            quoting=csv.QUOTE_MINIMAL
        )
        escritor.writeheader()
        for fila in datos:
            # Asegurarse de que el campo "texto" se maneje correctamente
            # para evitar problemas con comillas y delimitadores.
            fila['texto'] = fila['texto'].replace('\n', ' ').replace('\r', ' ')
            escritor.writerow(fila)

if __name__ == "__main__":
    todos_los_comentarios = []
    resultados_globales = []

    for vid in VIDEO_IDS:
        print(f"Descargando comentarios + replies de {vid}...")
        comentarios, estado = descargar_comentarios_y_replies(vid)
        print(f"  -> {len(comentarios)} líneas procesadas. Estado: {estado}")

        # Si hay un error, se añade una línea de metadato de error (si no hay comentarios)
        if estado != "EXITO" and not comentarios:
            todos_los_comentarios.append({
                "video_id": vid,
                "comment_id": "", "parent_id": "", "is_reply": "",
                "autor": "", "texto": f"NO SE PUDO DESCARGAR - {estado}",
                "likes": 0, "fecha": "",
                "fecha_descarga": FECHA_DESCARGA,
                "estado_video": estado,
            })
        else:
            todos_los_comentarios.extend(comentarios)

    print(f"\n--- Resumen de la Ejecución ---")
    print(f"Total líneas finales (todos los vídeos): {len(todos_los_comentarios)}")
    guardar_csv(todos_los_comentarios, OUTPUT_FILE)
    print(f"Guardado en {OUTPUT_FILE}")