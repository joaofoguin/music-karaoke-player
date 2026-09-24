from bisect import bisect_right
from dataclasses import dataclass
from html import escape
from pathlib import Path
import re


TIMESTAMP_PATTERN = re.compile(
    r"\[(?P<minutes>\d{1,3}):(?P<seconds>\d{2})(?:[.:](?P<fraction>\d{1,3}))?\]"
)

# Padrão para acordes e cifras embutidas entre colchetes (ex: [C], [Am], [F#m7], [Bb/D])
INLINE_CHORD_PATTERN = re.compile(
    r"\[(?P<chord>[A-G][b#]?(?:m|maj|min|dim|aug|sus[24]?|[0-9]{1,2}|add[0-9]|M|º|\+|-|\([b#]?[0-9]+\))*(?:/[A-G][b#]?)?)\]"
)

# Padrão para tag de cifras dedicada em LRC (ex: [chords: C  Am  G] ou <C  Am  G>)
CHORD_TAG_EXTRACTOR = re.compile(
    r"\[(?:chords?|cifras?):\s*(?P<chords>[^\]]+)\]|<(?P<chords_alt>[^>]+)>",
    re.IGNORECASE,
)

# Padrão para reconhecimento de acordes avulsos em linhas de cifras (ex: C, G/B, F#m7)
CHORD_TOKEN_PATTERN = re.compile(
    r"\b[A-G][b#]?(?:m|min|maj|M|dim|aug|sus[24]?|[0-9]{1,2}|add[0-9]|º|\+|-|\([b#]?[0-9]+\))*(?:/[A-G][b#]?)?\b"
)

RESERVED_CHORD_HEADERS = {
    "intro", "solo", "refrão", "refrao", "ponte", "outro", "verse", "chorus", "bridge",
    "2x", "3x", "4x", "|", "||", "rinf", "interlúdio", "interludio"
}


@dataclass(frozen=True)
class LyricLine:
    timestamp_ms: int
    text: str
    chords: str = ""

    @property
    def clean_lyrics(self) -> str:
        """Retorna o texto da letra 100% limpo, sem interferência de acordes."""
        return INLINE_CHORD_PATTERN.sub("", self.text).strip()

    @property
    def extracted_chords(self) -> list[str]:
        """Retorna os nomes das cifras, ocultando a posição opcional ACORDE@COLUNA."""
        if self.chords:
            return [token.split("@", 1)[0] for token in self.chords.split()]
        return [m.group("chord") for m in INLINE_CHORD_PATTERN.finditer(self.text)]

    @property
    def positioned_chords(self) -> list[tuple[str, int]]:
        """Retorna (acorde, coluna), preservando cifras posicionadas e aceitando LRCs antigos."""
        if not self.chords:
            return [(m.group("chord"), m.start()) for m in INLINE_CHORD_PATTERN.finditer(self.text)]

        result = []
        fallback = 0
        for token in self.chords.split():
            chord = token
            position = None
            if "@" in token:
                chord, raw_position = token.rsplit("@", 1)
                try:
                    position = max(0, int(raw_position))
                except ValueError:
                    position = None
            if position is None:
                position = fallback
            result.append((chord, position))
            fallback = max(fallback, position + len(chord) + 3)
        return result


def is_chord_line(line: str) -> bool:
    """Verifica se uma linha de texto contém predominantemente acordes e cifras."""
    tokens = [t.strip("()[]:, \t") for t in line.split() if t.strip("()[]:, \t")]
    if not tokens:
        return False

    chord_count = sum(
        1 for t in tokens
        if CHORD_TOKEN_PATTERN.fullmatch(t) or t.lower() in RESERVED_CHORD_HEADERS
    )
    return (chord_count / len(tokens)) >= 0.55


def parse_chord_sheet(text: str) -> list[tuple[str, str]]:
    """
    Processa um texto completo de cifra e separa claramente (cifras, letra_limpa).
    Nunca mistura acordes dentro do texto das frases.
    """
    raw_lines = [l.rstrip() for l in text.splitlines()]
    result: list[tuple[str, str]] = []
    i = 0

    while i < len(raw_lines):
        line = raw_lines[i]
        if not line.strip():
            i += 1
            continue

        # Linha LRC existente
        if TIMESTAMP_PATTERN.search(line):
            ts_clean = TIMESTAMP_PATTERN.sub("", line).strip()
            chords, clean_txt = extract_chords_and_lyrics(ts_clean)
            result.append((chords, clean_txt))
            i += 1
            continue

        if is_chord_line(line):
            # Verifica se a linha seguinte é uma linha de verso
            if (
                i + 1 < len(raw_lines)
                and raw_lines[i + 1].strip()
                and not is_chord_line(raw_lines[i + 1])
                and not TIMESTAMP_PATTERN.search(raw_lines[i + 1])
            ):
                next_line = raw_lines[i + 1].strip()
                # Extrai os acordes da linha de cifra
                matches = list(CHORD_TOKEN_PATTERN.finditer(line))
                chords_str = " ".join(f"{m.group(0)}@{m.start()}" for m in matches)
                result.append((chords_str, next_line))
                i += 2
            else:
                # Linha de cifra isolada (ex: [Intro] C Am F G ou Solo)
                matches = list(CHORD_TOKEN_PATTERN.finditer(line))
                chords_str = " ".join(f"{m.group(0)}@{m.start()}" for m in matches)
                header = re.sub(CHORD_TOKEN_PATTERN, "", line).strip(" \t:,-")
                result.append((chords_str, header))
                i += 1
        else:
            chords, clean_txt = extract_chords_and_lyrics(line.strip())
            result.append((chords, clean_txt))
            i += 1

    return result


def convert_chord_sheet_to_lyric_lines(text: str) -> list[LyricLine]:
    """Converte um texto de cifra colado em uma lista de LyricLine com texto limpo e cifras separadas."""
    raw_lines = [l.rstrip() for l in text.splitlines()]
    result = []
    i = 0

    while i < len(raw_lines):
        line = raw_lines[i]
        if not line.strip():
            i += 1
            continue

        # Verifica se já tem timestamp LRC
        match_ts = list(TIMESTAMP_PATTERN.finditer(line))
        if match_ts:
            ms = parse_timestamp_ms(match_ts[0].group(0))
            ts_clean = TIMESTAMP_PATTERN.sub("", line).strip()
            chords, clean_txt = extract_chords_and_lyrics(ts_clean)
            result.append(LyricLine(timestamp_ms=ms, text=clean_txt, chords=chords))
            i += 1
            continue

        if is_chord_line(line):
            if (
                i + 1 < len(raw_lines)
                and raw_lines[i + 1].strip()
                and not is_chord_line(raw_lines[i + 1])
                and not TIMESTAMP_PATTERN.search(raw_lines[i + 1])
            ):
                next_line = raw_lines[i + 1].strip()
                matches = list(CHORD_TOKEN_PATTERN.finditer(line))
                chords_str = " ".join(f"{m.group(0)}@{m.start()}" for m in matches)
                result.append(LyricLine(timestamp_ms=0, text=next_line, chords=chords_str))
                i += 2
            else:
                matches = list(CHORD_TOKEN_PATTERN.finditer(line))
                chords_str = " ".join(f"{m.group(0)}@{m.start()}" for m in matches)
                header = re.sub(CHORD_TOKEN_PATTERN, "", line).strip(" \t:,-")
                result.append(LyricLine(timestamp_ms=0, text=header, chords=chords_str))
                i += 1
        else:
            chords, clean_txt = extract_chords_and_lyrics(line.strip())
            result.append(LyricLine(timestamp_ms=0, text=clean_txt, chords=chords))
            i += 1

    return result


def extract_chords_and_lyrics(raw_text: str) -> tuple[str, str]:
    """Separa as cifras do texto da letra, garantindo que o texto retornado seja limpo."""
    chords = ""
    clean_text = raw_text

    # Verifica se há tag [chords: ...]
    m = CHORD_TAG_EXTRACTOR.search(clean_text)
    if m:
        chords = (m.group("chords") or m.group("chords_alt") or "").strip()
        clean_text = CHORD_TAG_EXTRACTOR.sub("", clean_text).strip()

    # Verifica se há tags inline [C], [Am] antigas
    inline_chords = [c.group("chord") for c in INLINE_CHORD_PATTERN.finditer(clean_text)]
    if inline_chords:
        if not chords:
            chords = "   ".join(inline_chords)
        clean_text = INLINE_CHORD_PATTERN.sub("", clean_text).strip()

    return chords, clean_text


def format_timestamp_ms(timestamp_ms: int) -> str:
    """Converte milissegundos para o formato de timestamp LRC [mm:ss.xx]."""
    if timestamp_ms < 0:
        timestamp_ms = 0

    total_seconds = timestamp_ms / 1000.0
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    centiseconds = int((total_seconds - int(total_seconds)) * 100)

    return f"{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def parse_timestamp_ms(timestamp_str: str) -> int:
    """Converte strings no formato mm:ss, mm:ss.xx ou mm:ss:xxx para milissegundos."""
    match = TIMESTAMP_PATTERN.search(f"[{timestamp_str.strip('[]')}]")
    if not match:
        return 0

    minutes = int(match["minutes"])
    seconds = int(match["seconds"])
    fraction = (match["fraction"] or "0").ljust(3, "0")[:3]
    return (minutes * 60 + seconds) * 1000 + int(fraction)


def render_chord_line_html(
    line: LyricLine,
    is_active: bool,
    active_color: str = "#ffffff",
    context_color: str = "#8f8f8f",
    chords_color: str = "#f59e0b",
    show_chords: bool = True,
    font_size: int = 32,
    link_href: str | None = None,
    editor_model: str = "stagebox",
) -> str:
    """Gera a representação visual da linha, centralizada de forma compatível com o Qt."""
    chords_list = line.extracted_chords
    letra_cor = active_color if is_active else context_color
    tamanho_verso = int(font_size * 1.25) if is_active else font_size
    peso_fonte = 800 if is_active else 500
    margem = 18 if is_active else 10
    opacidade = "1.0" if is_active else "0.75"
    clean = line.clean_lyrics or "♪"

    if editor_model == "winamp":
        lyric_lines = clean.splitlines() or ["♪"]
        positioned = line.positioned_chords if show_chords and chords_list else []

        # A posição @N é relativa ao início da letra. A cifra não pode
        # alterar a posição visual da letra: a grade de cifras é maior
        # apenas para acomodar cifras que estejam além do fim do verso.
        lyric_width = max((len(part) for part in lyric_lines), default=1)
        chord_end = max(
            (position + len(chord) for chord, position in positioned),
            default=0,
        )
        grid_width = max(lyric_width, chord_end, 1)

        # A linha atual é sempre centralizada pela sua própria largura.
        # O contexto não participa do cálculo da posição horizontal.
        linhas_grade = []
        if positioned:
            chord_cells = [" "] * grid_width
            for chord, position in positioned:
                for offset, char in enumerate(chord):
                    index = position + offset
                    if 0 <= index < grid_width:
                        chord_cells[index] = char
            linhas_grade.append(
                f'<div style="color:{chords_color}; font-size:{tamanho_verso}px; '
                f'font-weight:700; white-space:pre; margin:0 0 4px 0;">'
                f'{escape("".join(chord_cells).rstrip())}</div>'
            )

        for part in lyric_lines:
            linhas_grade.append(
                f'<div align="center" style="color:{letra_cor}; '
                f'font-size:{tamanho_verso}px; font-weight:{peso_fonte}; '
                f'white-space:pre; margin:0;">{escape(part)}</div>'
            )

        # A célula externa centraliza a grade como um bloco, mas cada verso
        # é centralizado pela própria largura. Assim, mudar @N desloca somente
        # a cifra e nunca empurra a frase para a esquerda.
        conteudo = (
            f'<table align="center" cellspacing="0" cellpadding="0" border="0" '
            f'style="margin:{margem}px auto; opacity:{opacidade};">'
            f'<tr><td>'
            f'{"".join(linhas_grade)}'
            f'</td></tr></table>'
        )
    else:
        partes = [
            f'<div align="center" style="margin:{margem}px 0; opacity:{opacidade};">'
        ]

        if show_chords and chords_list:
            positioned = line.positioned_chords
            max_position = max(
                (position + len(chord) for chord, position in positioned), default=1
            )
            cells = [" "] * max_position
            for chord, position in positioned:
                for offset, char in enumerate(chord):
                    index = position + offset
                    if 0 <= index < len(cells):
                        cells[index] = char
            chords_size = max(15, int(tamanho_verso * 0.6))
            partes.append(
                f'<div align="center" style="color:{chords_color}; '
                f'font-size:{chords_size}px; font-weight:700; '
                f'font-family:monospace; white-space:pre; margin-bottom:6px;">'
                f'{escape("".join(cells).rstrip())}</div>'
            )

        partes.append(
            f'<div align="center" style="color:{letra_cor}; font-size:{tamanho_verso}px; '
            f'font-weight:{peso_fonte}; letter-spacing:0.5px; line-height:1.6; '
            f'white-space:pre-wrap;">{escape(clean)}</div></div>'
        )
        conteudo = "".join(partes)

    if link_href:
        href = escape(link_href, quote=True)
        return f'<a href="{href}" style="text-decoration:none;">{conteudo}</a>'
    return conteudo


def load_lrc(path: Path) -> list[LyricLine]:
    """Lê e processa arquivos .lrc mantendo a letra limpa e extraindo as cifras."""
    if not path or not path.is_file():
        return []

    try:
        content = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            content = path.read_text(encoding="latin-1")
        except OSError:
            return []
    except OSError:
        return []

    lines: list[LyricLine] = []
    for raw_line in content.splitlines():
        matches = list(TIMESTAMP_PATTERN.finditer(raw_line))
        if not matches:
            continue

        raw_without_ts = TIMESTAMP_PATTERN.sub("", raw_line).strip()
        chords, clean_text = extract_chords_and_lyrics(raw_without_ts)

        for match in matches:
            minutes = int(match["minutes"])
            seconds = int(match["seconds"])
            fraction = (match["fraction"] or "0").ljust(3, "0")[:3]
            timestamp_ms = (minutes * 60 + seconds) * 1000 + int(fraction)
            lines.append(LyricLine(timestamp_ms=timestamp_ms, text=clean_text, chords=chords))

    return sorted(lines, key=lambda line: line.timestamp_ms)


def save_lrc(path: Path, lines: list[LyricLine], title: str = "", artist: str = "") -> bool:
    """Grava as linhas sincronizadas no formato padronizado LRC com tags de cifras organizadas."""
    if not path:
        return False

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        conteudo = []
        if title:
            conteudo.append(f"[ti:{title}]")
        if artist:
            conteudo.append(f"[ar:{artist}]")

        linhas_sincronizadas = [
            line for line in lines
            if line.timestamp_ms is not None
        ]

        for line in sorted(linhas_sincronizadas, key=lambda l: int(l.timestamp_ms)):
            timestamp_ms = max(0, int(line.timestamp_ms))
            ts = format_timestamp_ms(timestamp_ms)
            if line.chords:
                conteudo.append(f"[{ts}][chords:{line.chords}]{line.clean_lyrics}")
            else:
                conteudo.append(f"[{ts}]{line.clean_lyrics}")

        path.write_text("\n".join(conteudo) + "\n", encoding="utf-8")
        return True
    except OSError:
        return False


def current_line_index(lines: list[LyricLine], position_ms: int) -> int:
    """Localiza o índice do verso atual correspondente à posição atual do áudio."""
    if not lines:
        return -1

    timestamps = [line.timestamp_ms for line in lines]
    return bisect_right(timestamps, position_ms) - 1
