import os
import re
from pathlib import Path


INVALID_CHARS_PATTERN = re.compile(r'[\\/*?:"<>|]')


def sanitize_filename(name: str, replacement: str = "_") -> str:
    """Remove ou substitui caracteres inválidos para nomes de arquivos no Windows/Linux."""
    if not name:
        return ""
    sanitized = INVALID_CHARS_PATTERN.sub(replacement, name).strip(". ")
    return sanitized or "track"


def get_central_lyrics_dir(config_manager=None) -> Path:
    """Retorna o caminho da pasta central de letras/karaokê, criando o diretório se necessário."""
    default_dir = Path.home() / "Music" / "Karaoke_Lyrics"
    caminho_dir = default_dir

    if config_manager is not None:
        cfg_val = config_manager.get("karaoke/lyrics_directory", str(default_dir))
        if cfg_val:
            caminho_dir = Path(cfg_val)

    try:
        caminho_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    return caminho_dir


def get_lyrics_filename(artist: str = "", title: str = "", fallback_stem: str = "track") -> str:
    """Gera um nome de arquivo padronizado para a letra sincronizada."""
    artist_clean = sanitize_filename(artist.strip())
    title_clean = sanitize_filename(title.strip())

    if artist_clean and title_clean:
        return f"{artist_clean} - {title_clean}.lrc"
    elif title_clean:
        return f"{title_clean}.lrc"
    elif artist_clean:
        return f"{artist_clean} - {sanitize_filename(fallback_stem)}.lrc"
    else:
        return f"{sanitize_filename(fallback_stem)}.lrc"


def resolve_lyrics_path(track, config_manager=None) -> Path | None:
    """Busca o arquivo de letra/karaoke correspondente à faixa, priorizando a pasta central."""
    if track is None:
        return None

    central_dir = get_central_lyrics_dir(config_manager)
    artist = getattr(track, "artist", "") or ""
    title = getattr(track, "title", "") or ""
    track_path = getattr(track, "path", None)
    stem = Path(track_path).stem if track_path else ""

    # Candidatos na pasta central
    candidatos = [
        get_lyrics_filename(artist, title, stem),
        f"{sanitize_filename(title)}.lrc" if title else "",
        f"{sanitize_filename(stem)}.lrc" if stem else "",
    ]

    for cand in candidatos:
        if cand:
            caminho_central = central_dir / cand
            if caminho_central.is_file():
                return caminho_central

    # Fallback para a pasta do próprio arquivo de áudio
    if track_path:
        caminho_local = Path(track_path).with_suffix(".lrc")
        if caminho_local.is_file():
            return caminho_local

    return None


def get_save_lyrics_path(track, config_manager=None) -> Path:
    """Retorna o caminho ideal na pasta central de letras onde o arquivo deve ser gravado."""
    central_dir = get_central_lyrics_dir(config_manager)
    artist = getattr(track, "artist", "") or ""
    title = getattr(track, "title", "") or ""
    track_path = getattr(track, "path", None)
    stem = Path(track_path).stem if track_path else "musica"

    save_to_central = True
    if config_manager is not None:
        save_to_central = config_manager.get("karaoke/save_to_central_dir", True)

    if not save_to_central and track_path:
        return Path(track_path).with_suffix(".lrc")

    nome_arquivo = get_lyrics_filename(artist, title, stem)
    return central_dir / nome_arquivo
