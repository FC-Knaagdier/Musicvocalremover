"""Verwijdert de zang uit een nummer met Demucs (AI-scheiding)."""

import subprocess
from pathlib import Path

import numpy as np

MODELS = {
    "Snel (htdemucs)": "htdemucs",
    "Beste kwaliteit (htdemucs_ft, 4x trager)": "htdemucs_ft",
}
FORMATS = ("mp3", "flac", "wav")
AUDIO_EXT = (".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".opus", ".wma", ".mp4", ".mkv", ".webm")


class Cancelled(Exception):
    pass


def _load_audio(path, samplerate):
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-f", "f32le",
           "-acodec", "pcm_f32le", "-ac", "2", "-ar", str(samplerate), "-"]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0 or not proc.stdout:
        raise RuntimeError("Kan bestand niet lezen: " + proc.stderr.decode(errors="replace").strip())
    return np.frombuffer(proc.stdout, dtype=np.float32).reshape(-1, 2).T.copy()


def _save_audio(wav, path, samplerate, fmt):
    codec = {"mp3": ["-codec:a", "libmp3lame", "-q:a", "0"],
             "flac": ["-codec:a", "flac"],
             "wav": ["-codec:a", "pcm_s16le"]}[fmt]
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(samplerate), "-ac", "2",
           "-i", "-", *codec, str(path)]
    data = np.ascontiguousarray(np.clip(wav, -1, 1).T, dtype=np.float32).tobytes()
    proc = subprocess.run(cmd, input=data, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError("Opslaan mislukt: " + proc.stderr.decode(errors="replace").strip())


class Separator:
    def __init__(self):
        self._models = {}
        self.cancel_flag = False

    def _get_model(self, name):
        if name not in self._models:
            from demucs.pretrained import get_model
            model = get_model(name)
            model.eval()
            self._models[name] = model
        return self._models[name]

    def process(self, src, out_dir, model_name="htdemucs", fmt="mp3", keep_vocals=False,
                progress=lambda fraction, text: None):
        import torch
        from demucs.apply import apply_model

        self.cancel_flag = False
        src, out_dir = Path(src), Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        progress(0.0, "Model laden (eerste keer wordt het gedownload)...")
        model = self._get_model(model_name)
        sr = model.samplerate
        if self.cancel_flag:
            raise Cancelled()

        progress(0.03, "Bestand inlezen...")
        audio = _load_audio(src, sr)
        length = audio.shape[1]
        ref = audio.mean(0)
        mean, std = ref.mean(), ref.std() + 1e-8
        mix = torch.from_numpy((audio - mean) / std)

        n_models = len(getattr(model, "models", [model]))

        def callback(info):
            if self.cancel_flag:
                raise Cancelled()
            if info["state"] == "end":
                frac = (info["model_idx_in_bag"] + min(info["segment_offset"] / length, 1.0)) / n_models
                progress(0.05 + 0.85 * frac, "Zang verwijderen...")

        with torch.no_grad():
            sources = apply_model(model, mix[None], device="cpu", split=True, overlap=0.25,
                                  progress=False, callback=callback, num_workers=0)[0]
        sources = sources * std + mean
        names = list(model.sources)
        vocals_idx = names.index("vocals")
        instrumental = sum(sources[i] for i in range(len(names)) if i != vocals_idx).numpy()

        progress(0.92, "Opslaan...")
        stem = src.stem
        inst_path = out_dir / f"{stem} (instrumentaal).{fmt}"
        _save_audio(instrumental, inst_path, sr, fmt)
        result = [inst_path]
        if keep_vocals:
            voc_path = out_dir / f"{stem} (zang).{fmt}"
            _save_audio(sources[vocals_idx].numpy(), voc_path, sr, fmt)
            result.append(voc_path)
        progress(1.0, "Klaar")
        return result
