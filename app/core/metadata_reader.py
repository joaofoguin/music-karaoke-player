import base64
from pathlib import Path

from mutagen import File
from mutagen.id3 import ID3


def primeiro_valor(valor, padrao=""):
    if valor is None:
        return padrao

    if isinstance(valor, (list, tuple)):
        if not valor:
            return padrao
        return str(valor[0])

    return str(valor)


def extrair_capa(audio, caminho: Path) -> bytes | None:
    """Tenta extrair a capa de arte incorporada em múltiplos formatos de áudio."""
    ext = caminho.suffix.lower()

    # 1. MP3 via ID3 APIC
    if ext == ".mp3":
        try:
            id3 = ID3(caminho)
            for tag in id3.getall("APIC"):
                if tag.data:
                    return tag.data
        except Exception:
            pass

    if audio is None:
        return None

    # 2. FLAC via audio.pictures
    if hasattr(audio, "pictures") and audio.pictures:
        try:
            return audio.pictures[0].data
        except Exception:
            pass

    tags = getattr(audio, "tags", None)
    if not tags:
        return None

    # 3. MP4 / M4A / AAC via covr
    if "covr" in tags:
        try:
            covers = tags["covr"]
            if covers and len(covers) > 0:
                return bytes(covers[0])
        except Exception:
            pass

    # 4. OGG / FLAC / Vorbis com METADATA_BLOCK_PICTURE
    if "metadata_block_picture" in tags or "METADATA_BLOCK_PICTURE" in tags:
        try:
            raw_block = tags.get("metadata_block_picture") or tags.get("METADATA_BLOCK_PICTURE")
            if isinstance(raw_block, list) and raw_block:
                b64_data = raw_block[0]
            else:
                b64_data = raw_block

            if isinstance(b64_data, str):
                b64_bytes = b64_data.encode("ascii")
            else:
                b64_bytes = b64_data

            picture_data = base64.b64decode(b64_bytes)
            # Mutagen FLAC Picture structure: skip header (32 bytes min) to get raw image bytes
            from mutagen.flac import Picture
            pic = Picture(picture_data)
            return pic.data
        except Exception:
            pass

    # 5. Fallback para imagem na mesma pasta (cover.jpg, folder.jpg, etc.)
    pasta = caminho.parent
    for nome_img in ("cover.jpg", "cover.png", "folder.jpg", "folder.png", "front.jpg", "front.png"):
        img_path = pasta / nome_img
        if img_path.is_file():
            try:
                return img_path.read_bytes()
            except Exception:
                pass

    return None


def ler_metadados(caminho: Path) -> dict:
    """Extrai informações e metadados de um arquivo de áudio de forma segura."""
    titulo = caminho.stem
    artista = ""
    album = ""
    capa = None
    duracao = 0.0

    try:
        audio = File(caminho, easy=False)

        if audio is not None:
            if audio.info:
                duracao = getattr(audio.info, "length", 0.0)

            tags = audio.tags
            if tags:
                # Extração universal de título
                if "TIT2" in tags:
                    titulo = primeiro_valor(tags["TIT2"], titulo)
                elif "title" in tags:
                    titulo = primeiro_valor(tags["title"], titulo)
                elif "TITLE" in tags:
                    titulo = primeiro_valor(tags["TITLE"], titulo)
                elif "\xa9nam" in tags:  # MP4 name
                    titulo = primeiro_valor(tags["\xa9nam"], titulo)

                # Extração universal de artista
                if "TPE1" in tags:
                    artista = primeiro_valor(tags["TPE1"])
                elif "artist" in tags:
                    artista = primeiro_valor(tags["artist"])
                elif "ARTIST" in tags:
                    artista = primeiro_valor(tags["ARTIST"])
                elif "\xa9ART" in tags:  # MP4 artist
                    artista = primeiro_valor(tags["\xa9ART"])

                # Extração universal de álbum
                if "TALB" in tags:
                    album = primeiro_valor(tags["TALB"])
                elif "album" in tags:
                    album = primeiro_valor(tags["album"])
                elif "ALBUM" in tags:
                    album = primeiro_valor(tags["ALBUM"])
                elif "\xa9alb" in tags:  # MP4 album
                    album = primeiro_valor(tags["\xa9alb"])

            capa = extrair_capa(audio, caminho)

    except Exception:
        pass

    return {
        "title": titulo,
        "artist": artista,
        "album": album,
        "cover": capa,
        "format": caminho.suffix.lower().replace(".", ""),
        "duration": duracao,
    }