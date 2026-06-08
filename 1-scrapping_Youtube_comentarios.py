from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import csv
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Clave de API desde .env — obtener en https://console.cloud.google.com/
API_KEY = os.getenv("YOUTUBE_API_KEY")

# Videos seleccionados para el corpus. Criterio: solo influencers de derecha española,
# sin clips de TV ni contenido descontextualizado. Estrategia de búsqueda: cuenta anónima
# (para evitar sesgo algorítmico), palabras clave: "universidad progre", "universidad woke",
# "universidad privada".
VIDEO_IDS = [
    "2qyTVETSOKE", # Rodri Salas https://www.youtube.com/watch?v=2qyTVETSOKE
    "n04uHumiiDU", # Roberto Vaquero short https://www.youtube.com/shorts/n04uHumiiDU
    "OoGYc4KhRWI", # Roberto Vaquero short https://www.youtube.com/shorts/OoGYc4KhRWI
    "qCB2E_YBgP0", # Roberto Vaquero https://www.youtube.com/watch?v=qCB2E_YBgP0
    "eUkDaMirjYU", # Wall St. Wolverine https://www.youtube.com/watch?v=eUkDaMirjYU
    "E770DNGYeUA", # Wall St. Wolverine short https://www.youtube.com/shorts/E770DNGYeUA
    "ozhKAomDTjE", # Wall St. Wolverine short https://www.youtube.com/shorts/ozhKAomDTjE
    "bviJ0PnO8EI", # Wall St. Wolverine short https://www.youtube.com/shorts/bviJ0PnO8EI
    "Ed-EJHjxI88", # Wall St. Wolverine short https://www.youtube.com/shorts/Ed-EJHjxI88
    "QVSKDUA9p9s", # Wall St. Wolverine short https://www.youtube.com/shorts/QVSKDUA9p9s
    "2GcQVaqdgEU", # Wall St. Wolverine short https://www.youtube.com/shorts/2GcQVaqdgEU
    "hnUDs-zXKUs", # Wall St. Wolverine interviewing Juan Ramón Rallo https://www.youtube.com/watch?v=hnUDs-zXKUs
    "HkW8QsGeL8A", # Worldcast interviewing Juan Ramón Rallo https://www.youtube.com/shorts/HkW8QsGeL8A
    "2_srTgttqH4", # Juan Ramón Rallo on private university https://www.youtube.com/watch?v=2_srTgttqH4
    "oNiHsD6uF1Q", # Iker Jiménez "universidad pública vs privada" https://www.youtube.com/watch?v=oNiHsD6uF1Q
]

OUTPUT_FILE = "comentarios_multivideo_robusto2.csv"
FECHA_DESCARGA = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

youtube = build("youtube", "v3", developerKey=API_KEY)

def descargar_comentarios_y_replies(video_id: str):
    """
    Descarga comentarios principales y sus respuestas para un video.
    Devuelve una tupla: (lista de dicts, estado_descarga).
    """
    comentarios = []
    token_siguiente = None
    estado_descarga = "EXITO"

    try:
        respuesta_inicial = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText",
            pageToken=token_siguiente
        ).execute()

        respuesta = respuesta_inicial

        while True:
            for item in respuesta["items"]:
                # Comentario principal
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
                    "fecha_descarga": FECHA_DESCARGA,
                    "estado_video": estado_descarga,
                })

                # Respuestas
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
                        "fecha_descarga": FECHA_DESCARGA,
                        "estado_video": estado_descarga,
                    })

            token_siguiente = respuesta.get("nextPageToken")
            if not token_siguiente:
                break

            respuesta = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=100,
                textFormat="plainText",
                pageToken=token_siguiente
            ).execute()

    except HttpError as e:
        estado_descarga = f"ERROR_API_{e.resp.status}"
        print(f"  -> {estado_descarga}: {video_id}. Detalle: {e.content.decode()}")

    except Exception as e:
        estado_descarga = "ERROR_OTRO"
        print(f"  -> {estado_descarga}: error inesperado en {video_id}. Detalle: {e}")

    # Devolver lo recolectado antes del fallo (si hay) y el estado final
    return comentarios, estado_descarga


def guardar_csv(datos, archivo):
    """Guarda la lista de dicts en un CSV delimitado por punto y coma."""
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
            "fecha_descarga",
            "estado_video",
        ]
        escritor = csv.DictWriter(
            f,
            fieldnames=campos,
            delimiter=";",
            quoting=csv.QUOTE_MINIMAL
        )
        escritor.writeheader()
        for fila in datos:
            fila['texto'] = fila['texto'].replace('\n', ' ').replace('\r', ' ')
            escritor.writerow(fila)

if __name__ == "__main__":
    todos_los_comentarios = []
    resultados_globales = []

    for vid in VIDEO_IDS:
        print(f"Descargando comentarios y respuestas para {vid}...")
        comentarios, estado = descargar_comentarios_y_replies(vid)
        print(f"  -> {len(comentarios)} filas procesadas. Estado: {estado}")

        if estado != "EXITO" and not comentarios:
            todos_los_comentarios.append({
                "video_id": vid,
                "comment_id": "", "parent_id": "", "is_reply": "",
                "autor": "", "texto": f"DESCARGA FALLIDA - {estado}",
                "likes": 0, "fecha": "",
                "fecha_descarga": FECHA_DESCARGA,
                "estado_video": estado,
            })
        else:
            todos_los_comentarios.extend(comentarios)

    print(f"\n--- Resumen de la ejecución ---")
    print(f"Total de filas (todos los videos): {len(todos_los_comentarios)}")
    guardar_csv(todos_los_comentarios, OUTPUT_FILE)
    print(f"Guardado en {OUTPUT_FILE}")
