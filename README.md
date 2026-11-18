# Vocal Remover (Linux Mint)

Verwijdert de zang uit een nummer en bewaart alleen de muziek (AI-model Demucs, werkt offline na de eerste keer).

## Installeren
```bash
cd "Vocal remover Linux"
chmod +x install.sh run.sh
./install.sh
```
Daarna staat **Vocal Remover** in het startmenu (categorie Geluid & Video), of start met `./run.sh`.

## Gebruik
- **App:** nummers toevoegen, uitvoermap/formaat kiezen, op *Zang verwijderen* klikken.
  Resultaat: `<naam> (instrumentaal).mp3` (optioneel ook `<naam> (zang).mp3`).
- **Terminal:** `./run.sh nummer.mp3 -o ~/Muziek/Instrumentaal -f flac [-q] [--zang]`

## Opmerkingen
- Het eerste gebruik downloadt het model (80 MB; 4x meer voor de beste kwaliteit).
- Draait op de CPU: een nummer van 4 minuten duurt ca. 1-3 minuten (de "beste kwaliteit" is 4x trager).
- Ondersteunt mp3, flac, wav, ogg, m4a, opus en meer (via ffmpeg).
