"""Gebruik:
  python vocal_remover.py                      -> grafische app
  python vocal_remover.py nummer.mp3 [...]     -> opdrachtregel (-o map, -f mp3|flac|wav, -q, --zang)
"""

import argparse
import sys


def cli(argv):
    from vocalremover.separator import FORMATS, Separator

    p = argparse.ArgumentParser(description="Verwijder de zang uit nummers.")
    p.add_argument("files", nargs="+")
    p.add_argument("-o", "--uit", default=".", help="uitvoermap")
    p.add_argument("-f", "--formaat", default="mp3", choices=FORMATS)
    p.add_argument("-q", "--beste", action="store_true", help="beste kwaliteit (trager)")
    p.add_argument("--zang", action="store_true", help="zang ook apart opslaan")
    a = p.parse_args(argv)
    model = "htdemucs_ft" if a.beste else "htdemucs"
    sep = Separator()
    for f in a.files:
        def progress(frac, text, f=f):
            print(f"\r{f}: {text} {frac * 100:3.0f}%\033[K", end="", flush=True)
        for out in sep.process(f, a.uit, model, a.formaat, a.zang, progress):
            print(f"\n-> {out}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli(sys.argv[1:])
    else:
        from vocalremover.gui import main
        main()
