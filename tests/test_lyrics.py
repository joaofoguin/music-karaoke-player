from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from core.lyrics import (
    LyricLine,
    convert_chord_sheet_to_lyric_lines,
    current_line_index,
    extract_chords_and_lyrics,
    format_timestamp_ms,
    is_chord_line,
    load_lrc,
    parse_chord_sheet,
    parse_timestamp_ms,
    render_chord_line_html,
    save_lrc,
)


def test_is_chord_line():
    assert is_chord_line("C  Am  G  F") is True
    assert is_chord_line("[Intro] C#m7  F#m7  B7  E") is True
    assert is_chord_line("A letra da música aparecerá aqui") is False
    assert is_chord_line("") is False


def test_parse_chord_sheet():
    chord_sheet = """[Intro] C  Am  F  G

C                  Am
A letra da música aparecerá aqui
G                  F
quando houver um arquivo de karaoke

Em                 C
Na próxima etapa
"""
    lines = parse_chord_sheet(chord_sheet)
    assert len(lines) == 4
    # Primeira linha: (chords, text)
    assert "C" in lines[0][0]
    # Segunda linha: acordes separados da frase limpa
    assert "C" in lines[1][0]
    assert "Am" in lines[1][0]
    assert lines[1][1] == "A letra da música aparecerá aqui"


def test_convert_chord_sheet_to_lyric_lines():
    chord_sheet = """C   Am
Primeiro verso
"""
    lyric_lines = convert_chord_sheet_to_lyric_lines(chord_sheet)
    assert len(lyric_lines) == 1
    assert isinstance(lyric_lines[0], LyricLine)
    assert lyric_lines[0].timestamp_ms == 0
    assert lyric_lines[0].text == "Primeiro verso"
    assert "C" in lyric_lines[0].chords
    assert "Am" in lyric_lines[0].chords


def test_load_lrc_parsing():
    lrc_sample = """[00:04.20]Primeira linha da música
[00:08.50][chords:C   Am]Segunda linha com acordes
[00:15.00][00:25.00]Refrão repetido
[01:02.123]Final da música
"""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".lrc", delete=False) as f:
        f.write(lrc_sample)
        temp_path = Path(f.name)

    try:
        lines = load_lrc(temp_path)
        assert len(lines) == 5
        assert lines[0].timestamp_ms == 4200
        assert lines[0].clean_lyrics == "Primeira linha da música"
        assert lines[1].timestamp_ms == 8500
        assert lines[1].extracted_chords == ["C", "Am"]
        assert lines[1].clean_lyrics == "Segunda linha com acordes"
    finally:
        temp_path.unlink(missing_ok=True)


def test_save_lrc():
    lines = [
        LyricLine(timestamp_ms=1500, text="Linha 1", chords="C"),
        LyricLine(timestamp_ms=62000, text="Linha 2", chords="G7"),
    ]

    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".lrc", delete=False) as f:
        temp_path = Path(f.name)

    try:
        ok = save_lrc(temp_path, lines, title="Teste", artist="Artista")
        assert ok is True
        loaded = load_lrc(temp_path)
        assert len(loaded) == 2
        assert loaded[0].timestamp_ms == 1500
        assert loaded[0].clean_lyrics == "Linha 1"
        assert loaded[0].chords == "C"
        assert loaded[1].timestamp_ms == 62000
    finally:
        temp_path.unlink(missing_ok=True)


def test_extract_chords_and_lyrics():
    raw = "[chords: C  Am  F#m7  G] Olá mundo aqui é um teste"
    chords, clean = extract_chords_and_lyrics(raw)
    assert "C" in chords
    assert "Am" in chords
    assert clean == "Olá mundo aqui é um teste"


def test_format_and_parse_timestamp():
    assert format_timestamp_ms(65230) == "01:05.23"
    assert parse_timestamp_ms("01:05.23") == 65230
    assert parse_timestamp_ms("00:00.00") == 0


def test_render_chord_line_html():
    line = LyricLine(timestamp_ms=5000, text="Verso com acordes", chords="C   G")
    html = render_chord_line_html(line, is_active=True, show_chords=True)
    assert "C" in html
    assert "G" in html
    assert "Verso com acordes" in html


def test_render_chord_line_html_with_link():
    line = LyricLine(timestamp_ms=5000, text="Verso clicável")
    html = render_chord_line_html(line, is_active=False, link_href="line:3")
    assert 'href="line:3"' in html
    assert "Verso clicável" in html


def test_current_line_index():
    lines = [
        LyricLine(1000, "Line 1"),
        LyricLine(5000, "Line 2"),
        LyricLine(10000, "Line 3"),
    ]

    assert current_line_index(lines, 500) == -1
    assert current_line_index(lines, 1000) == 0
    assert current_line_index(lines, 3000) == 0
    assert current_line_index(lines, 5000) == 1
    assert current_line_index(lines, 7000) == 1
    assert current_line_index(lines, 10000) == 2
    assert current_line_index(lines, 99999) == 2
