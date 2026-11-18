"""Grafische app (Tkinter) om de zang uit nummers te verwijderen."""

import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .separator import AUDIO_EXT, FORMATS, MODELS, Cancelled, Separator


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Vocal Remover")
        self.geometry("640x520")
        self.minsize(560, 460)
        self.separator = Separator()
        self.files = []
        self.events = queue.Queue()
        self.worker = None
        self._build()
        self.after(100, self._poll)

    def _build(self):
        pad = {"padx": 10, "pady": 4}
        top = ttk.Frame(self)
        top.pack(fill="both", expand=True, **pad)

        ttk.Label(top, text="Nummers:").pack(anchor="w")
        box = ttk.Frame(top)
        box.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(box, selectmode="extended", height=8)
        sb = ttk.Scrollbar(box, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        btns = ttk.Frame(top)
        btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="Toevoegen...", command=self.add_files).pack(side="left")
        ttk.Button(btns, text="Verwijder selectie", command=self.remove_selected).pack(side="left", padx=6)

        opts = ttk.LabelFrame(top, text="Instellingen")
        opts.pack(fill="x", pady=6)
        opts.columnconfigure(1, weight=1)

        ttk.Label(opts, text="Uitvoermap:").grid(row=0, column=0, sticky="w", padx=6, pady=3)
        self.out_var = tk.StringVar(value=str(Path.home() / "Muziek" / "Instrumentaal"))
        ttk.Entry(opts, textvariable=self.out_var).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(opts, text="Kiezen...", command=self.pick_out).grid(row=0, column=2, padx=6)

        ttk.Label(opts, text="Kwaliteit:").grid(row=1, column=0, sticky="w", padx=6, pady=3)
        self.model_var = tk.StringVar(value=next(iter(MODELS)))
        ttk.Combobox(opts, textvariable=self.model_var, values=list(MODELS), state="readonly") \
            .grid(row=1, column=1, columnspan=2, sticky="ew", padx=6)

        ttk.Label(opts, text="Formaat:").grid(row=2, column=0, sticky="w", padx=6, pady=3)
        self.fmt_var = tk.StringVar(value="mp3")
        ttk.Combobox(opts, textvariable=self.fmt_var, values=FORMATS, state="readonly", width=8) \
            .grid(row=2, column=1, sticky="w", padx=6)

        self.vocals_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="Zang ook apart opslaan", variable=self.vocals_var) \
            .grid(row=3, column=0, columnspan=3, sticky="w", padx=6, pady=3)

        self.progress = ttk.Progressbar(top, maximum=1.0)
        self.progress.pack(fill="x", pady=(8, 2))
        self.status = tk.StringVar(value="Voeg nummers toe om te beginnen.")
        ttk.Label(top, textvariable=self.status).pack(anchor="w")

        actions = ttk.Frame(top)
        actions.pack(fill="x", pady=6)
        self.start_btn = ttk.Button(actions, text="Zang verwijderen", command=self.start)
        self.start_btn.pack(side="left")
        self.cancel_btn = ttk.Button(actions, text="Stoppen", command=self.cancel, state="disabled")
        self.cancel_btn.pack(side="left", padx=6)
        ttk.Button(actions, text="Open uitvoermap", command=self.open_out).pack(side="right")

    def add_files(self):
        patterns = " ".join("*" + e for e in AUDIO_EXT)
        for f in filedialog.askopenfilenames(
                title="Kies nummers",
                filetypes=[("Audio/video", patterns), ("Alle bestanden", "*")]):
            if f not in self.files:
                self.files.append(f)
                self.listbox.insert("end", Path(f).name)

    def remove_selected(self):
        for i in reversed(self.listbox.curselection()):
            self.listbox.delete(i)
            del self.files[i]

    def pick_out(self):
        d = filedialog.askdirectory(title="Kies uitvoermap")
        if d:
            self.out_var.set(d)

    def open_out(self):
        d = Path(self.out_var.get())
        d.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(["xdg-open", str(d)])

    def start(self):
        if not self.files:
            messagebox.showinfo("Vocal Remover", "Voeg eerst een of meer nummers toe.")
            return
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        args = (list(self.files), self.out_var.get(), MODELS[self.model_var.get()],
                self.fmt_var.get(), self.vocals_var.get())
        self.worker = threading.Thread(target=self._run, args=args, daemon=True)
        self.worker.start()

    def cancel(self):
        self.separator.cancel_flag = True
        self.status.set("Stoppen...")

    def _run(self, files, out_dir, model, fmt, vocals):
        total = len(files)
        done, errors = [], []
        try:
            for i, f in enumerate(files):
                name = Path(f).name

                def progress(frac, text, i=i, name=name):
                    self.events.put(("progress", (i + frac) / total, f"[{i + 1}/{total}] {name}: {text}"))

                try:
                    done += self.separator.process(f, out_dir, model, fmt, vocals, progress)
                except Cancelled:
                    raise
                except Exception as e:
                    errors.append(f"{name}: {e}")
            self.events.put(("done", done, errors))
        except Cancelled:
            self.events.put(("cancelled",))

    def _poll(self):
        try:
            while True:
                ev = self.events.get_nowait()
                if ev[0] == "progress":
                    self.progress["value"] = ev[1]
                    self.status.set(ev[2])
                else:
                    self._finish(ev)
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _finish(self, ev):
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        if ev[0] == "cancelled":
            self.status.set("Gestopt.")
            self.progress["value"] = 0
            return
        done, errors = ev[1], ev[2]
        self.progress["value"] = 1.0
        self.status.set(f"Klaar: {len(done)} bestand(en) opgeslagen.")
        if errors:
            messagebox.showerror("Vocal Remover", "Fouten:\n\n" + "\n".join(errors))
        else:
            messagebox.showinfo("Vocal Remover", f"Klaar! Opgeslagen in:\n{self.out_var.get()}")


def main():
    App().mainloop()
