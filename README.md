# BatchPack

**Split big folders into batches and zip them, with one click.**

BatchPack is a small desktop app (Python + Tkinter) that splits the files in a folder into numbered batch folders (e.g. 200 files each) and optionally zips each batch. No command line or script editing needed.

## Features

- Pick any source folder with a file browser
- Choose files per batch and the batch name prefix
- Move or copy files (keep originals)
- Zip each batch into its own `.zip`
- Choose where the zips are saved
- Optionally delete batch folders after zipping
- Progress bar and live log
- No dependencies: standard library only

## Requirements

- Python 3.8+ (Tkinter is included with the standard Windows/macOS installers)

On some Linux distros: `sudo apt install python3-tk`

## Usage

```bash
python batchpack.py
```

1. Click **Browse** and select the folder containing your files.
2. Set **Files per batch** and the **prefix** (default `Batch`).
3. Tick the steps you want: split, zip, or both.
4. Click **Start**.

Result example:

```
MyFolder/
  Batch_001/   Batch_001.zip
  Batch_002/   Batch_002.zip
```

## Notes

- Only files directly inside the selected folder are split; subfolders are ignored.
- Existing files in a batch folder are never overwritten.
- Existing zips with the same name are replaced.
- Zipping only targets folders named `<prefix>_###`.
- Moving files and deleting folders ask for confirmation first.

## Build an .exe (optional)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed batchpack.py
```

## License

MIT
