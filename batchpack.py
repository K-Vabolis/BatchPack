"""BatchPack - split files into numbered batch folders and zip each batch."""
import queue
import shutil
import threading
import tkinter as tk
import zipfile
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


def split_files(source, per_folder, prefix, copy, log, progress):
    files = sorted((p for p in source.iterdir() if p.is_file()),
                   key=lambda p: p.name.lower())
    if not files:
        log(f"No files found in: {source}")
        return
    total = len(files)
    done = 0
    for idx, start in enumerate(range(0, total, per_folder), start=1):
        folder = source / f"{prefix}_{idx:03d}"
        folder.mkdir(exist_ok=True)
        chunk = files[start:start + per_folder]
        for f in chunk:
            dest = folder / f.name
            if dest.exists():
                log(f"Skipped (exists): {dest.name}")
            elif copy:
                shutil.copy2(f, dest)
            else:
                shutil.move(str(f), str(dest))
            done += 1
            progress(done / total * 100)
        log(f"{folder.name}: {len(chunk)} files")


def find_batches(source, prefix):
    key = prefix.lower() + "_"
    return sorted((p for p in source.iterdir()
                   if p.is_dir() and p.name.lower().startswith(key)),
                  key=lambda p: p.name.lower())


def zip_batches(source, zip_dir, prefix, delete_after, log, progress):
    batches = find_batches(source, prefix)
    if not batches:
        log(f"No '{prefix}_###' folders found in: {source}")
        return
    zip_dir.mkdir(parents=True, exist_ok=True)
    for i, batch in enumerate(batches, start=1):
        zip_path = zip_dir / f"{batch.name}.zip"
        count = 0
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(batch.rglob("*")):
                if f.is_file():
                    zf.write(f, Path(batch.name) / f.relative_to(batch))
                    count += 1
        log(f"Created {zip_path.name} ({count} files)")
        if delete_after:
            shutil.rmtree(batch)
            log(f"Removed folder: {batch.name}")
        progress(i / len(batches) * 100)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BatchPack")
        self.geometry("640x560")
        self.minsize(560, 500)
        self.q = queue.Queue()

        self.source = tk.StringVar()
        self.zip_out = tk.StringVar()
        self.per_folder = tk.IntVar(value=200)
        self.prefix = tk.StringVar(value="Batch")
        self.copy = tk.BooleanVar(value=False)
        self.do_split = tk.BooleanVar(value=True)
        self.do_zip = tk.BooleanVar(value=True)
        self.delete_after = tk.BooleanVar(value=False)

        self.build()
        self.after(100, self.poll)

    def build(self):
        pad = {"padx": 10, "pady": 4}
        f = ttk.Frame(self, padding=10)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)

        ttk.Label(f, text="Folder with files").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(f, textvariable=self.source).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(f, text="Browse", command=self.pick_source).grid(row=0, column=2, **pad)

        ttk.Label(f, text="Zip output folder").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(f, textvariable=self.zip_out).grid(row=1, column=1, sticky="ew", **pad)
        ttk.Button(f, text="Browse", command=self.pick_zip).grid(row=1, column=2, **pad)
        ttk.Label(f, text="(blank = same as source folder)", foreground="gray").grid(
            row=2, column=1, sticky="w", padx=10)

        ttk.Label(f, text="Files per batch").grid(row=3, column=0, sticky="w", **pad)
        ttk.Spinbox(f, from_=1, to=100000, textvariable=self.per_folder, width=10).grid(
            row=3, column=1, sticky="w", **pad)

        ttk.Label(f, text="Batch name prefix").grid(row=4, column=0, sticky="w", **pad)
        ttk.Entry(f, textvariable=self.prefix, width=20).grid(row=4, column=1, sticky="w", **pad)

        opts = ttk.LabelFrame(f, text="Options", padding=8)
        opts.grid(row=5, column=0, columnspan=3, sticky="ew", padx=10, pady=8)
        ttk.Checkbutton(opts, text="Step 1: Split files into batch folders",
                        variable=self.do_split).pack(anchor="w")
        ttk.Checkbutton(opts, text="Keep originals (copy instead of move)",
                        variable=self.copy).pack(anchor="w", padx=20)
        ttk.Checkbutton(opts, text="Step 2: Zip each batch folder",
                        variable=self.do_zip).pack(anchor="w", pady=(6, 0))
        ttk.Checkbutton(opts, text="Delete batch folders after zipping",
                        variable=self.delete_after).pack(anchor="w", padx=20)

        self.btn = ttk.Button(f, text="Start", command=self.start)
        self.btn.grid(row=6, column=0, columnspan=3, pady=6)

        self.bar = ttk.Progressbar(f, maximum=100)
        self.bar.grid(row=7, column=0, columnspan=3, sticky="ew", padx=10)

        self.logbox = tk.Text(f, height=12, state="disabled", wrap="word")
        self.logbox.grid(row=8, column=0, columnspan=3, sticky="nsew", padx=10, pady=8)
        f.rowconfigure(8, weight=1)

    def pick_source(self):
        d = filedialog.askdirectory(title="Select folder with files")
        if d:
            self.source.set(d)

    def pick_zip(self):
        d = filedialog.askdirectory(title="Select zip output folder")
        if d:
            self.zip_out.set(d)

    def log(self, msg):
        self.q.put(("log", msg))

    def progress(self, val):
        self.q.put(("bar", val))

    def poll(self):
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "log":
                    self.logbox.config(state="normal")
                    self.logbox.insert("end", val + "\n")
                    self.logbox.see("end")
                    self.logbox.config(state="disabled")
                elif kind == "bar":
                    self.bar["value"] = val
                elif kind == "done":
                    self.btn.config(state="normal")
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def start(self):
        source = Path(self.source.get())
        if not source.is_dir():
            messagebox.showerror("BatchPack", "Pick a valid source folder.")
            return
        if not (self.do_split.get() or self.do_zip.get()):
            messagebox.showerror("BatchPack", "Select at least one step.")
            return
        try:
            per = int(self.per_folder.get())
            if per < 1:
                raise ValueError
        except (ValueError, tk.TclError):
            messagebox.showerror("BatchPack", "Files per batch must be a positive number.")
            return
        prefix = self.prefix.get().strip() or "Batch"

        warn = []
        if self.do_split.get() and not self.copy.get():
            warn.append("Files will be MOVED into batch folders.")
        if self.do_zip.get() and self.delete_after.get():
            warn.append("Batch folders will be DELETED after zipping.")
        if warn and not messagebox.askyesno("Confirm", "\n".join(warn) + "\n\nContinue?"):
            return

        zip_dir = Path(self.zip_out.get()) if self.zip_out.get().strip() else source
        self.btn.config(state="disabled")
        self.bar["value"] = 0
        threading.Thread(
            target=self.run,
            args=(source, zip_dir, per, prefix),
            daemon=True,
        ).start()

    def run(self, source, zip_dir, per, prefix):
        try:
            if self.do_split.get():
                self.log("--- Splitting ---")
                split_files(source, per, prefix, self.copy.get(), self.log, self.progress)
            if self.do_zip.get():
                self.log("--- Zipping ---")
                self.progress(0)
                zip_batches(source, zip_dir, prefix, self.delete_after.get(),
                            self.log, self.progress)
            self.log("Finished.")
        except Exception as e:
            self.log(f"Error: {e}")
        finally:
            self.q.put(("done", None))


if __name__ == "__main__":
    App().mainloop()
