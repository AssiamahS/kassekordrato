#!/usr/bin/env python3
import json
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KasseKordrato Desktop Manager")
        self.geometry("860x620")

        self.source_var = tk.StringVar()
        self.usb_var = tk.StringVar()
        self.crates_var = tk.StringVar(value="/Users/djsly/Music/_Serato_Backup/Subcrates")
        self.report_var = tk.StringVar(value=str(Path.home() / "Desktop" / "truth_report.json"))

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Source Folder (music truth set)").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(frame, textvariable=self.source_var, width=90).grid(row=1, column=0, sticky="we", **pad)
        ttk.Button(frame, text="Choose Source", command=self.pick_source).grid(row=1, column=1, **pad)

        ttk.Label(frame, text="USB Target Folder").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(frame, textvariable=self.usb_var, width=90).grid(row=3, column=0, sticky="we", **pad)
        ttk.Button(frame, text="Choose USB", command=self.pick_usb).grid(row=3, column=1, **pad)

        ttk.Label(frame, text="Serato Backup Subcrates (optional)").grid(row=4, column=0, sticky="w", **pad)
        ttk.Entry(frame, textvariable=self.crates_var, width=90).grid(row=5, column=0, sticky="we", **pad)
        ttk.Button(frame, text="Choose Crates", command=self.pick_crates).grid(row=5, column=1, **pad)

        ttk.Label(frame, text="Truth Report Output").grid(row=6, column=0, sticky="w", **pad)
        ttk.Entry(frame, textvariable=self.report_var, width=90).grid(row=7, column=0, sticky="we", **pad)
        ttk.Button(frame, text="Choose Report", command=self.pick_report).grid(row=7, column=1, **pad)

        actions = ttk.Frame(frame)
        actions.grid(row=8, column=0, columnspan=2, sticky="w", **pad)
        ttk.Button(actions, text="1) Run Truth Report", command=self.run_truth_report).pack(side="left", padx=4)
        ttk.Button(actions, text="2) Sync 1:1 to USB", command=self.run_sync).pack(side="left", padx=4)
        ttk.Button(actions, text="3) Format USB (macOS)", command=self.run_format_usb).pack(side="left", padx=4)
        ttk.Button(actions, text="Open Report", command=self.open_report).pack(side="left", padx=4)

        self.output = tk.Text(frame, wrap="word", height=24)
        self.output.grid(row=9, column=0, columnspan=2, sticky="nsew", **pad)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(9, weight=1)

    def log(self, text: str):
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.update_idletasks()

    def pick_source(self):
        path = filedialog.askdirectory()
        if path:
            self.source_var.set(path)

    def pick_usb(self):
        path = filedialog.askdirectory()
        if path:
            self.usb_var.set(path)

    def pick_crates(self):
        path = filedialog.askdirectory()
        if path:
            self.crates_var.set(path)

    def pick_report(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            self.report_var.set(path)

    def validate_common(self):
        if not Path(self.source_var.get()).exists():
            messagebox.showerror("Missing Source", "Choose a valid source folder.")
            return False
        return True

    def run_cmd(self, cmd):
        self.log("$ " + " ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        assert proc.stdout is not None
        for line in proc.stdout:
            self.log(line.rstrip("\n"))
        rc = proc.wait()
        self.log(f"Exit code: {rc}")
        return rc

    def run_async(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def run_truth_report(self):
        if not self.validate_common():
            return

        def _task():
            cmd = [
                "python3",
                str(TOOLS / "music_truth_report.py"),
                "--source",
                self.source_var.get(),
                "--out",
                self.report_var.get(),
            ]
            crates = self.crates_var.get().strip()
            if crates and Path(crates).exists():
                cmd.extend(["--serato-subcrates", crates])
            rc = self.run_cmd(cmd)
            if rc == 0:
                self.log("Truth report complete.")

        self.run_async(_task)

    def run_sync(self):
        if not self.validate_common():
            return
        if not Path(self.usb_var.get()).exists():
            messagebox.showerror("Missing USB Target", "Choose a valid USB target folder.")
            return

        if not messagebox.askyesno(
            "Confirm 1:1 Sync",
            "This uses --delete on USB target to enforce exact 1:1 mirror. Continue?",
        ):
            return

        def _task():
            cmd = [
                "python3",
                str(TOOLS / "usb_rekordbox_sync.py"),
                "--source",
                self.source_var.get(),
                "--usb-target",
                self.usb_var.get(),
            ]
            rc = self.run_cmd(cmd)
            if rc == 0:
                self.log("USB sync complete. Next: Rekordbox Export Mode sync for Pioneer DB.")

        self.run_async(_task)

    def open_report(self):
        path = Path(self.report_var.get())
        if not path.exists():
            messagebox.showerror("Missing File", "Report file does not exist yet.")
            return
        try:
            data = json.loads(path.read_text())
            self.log(f"Report summary: tracks={data.get('track_count')} duplicate_groups={len(data.get('duplicates_by_hash', {}))}")
        except Exception:
            self.log(f"Report path: {path}")

    def run_format_usb(self):
        disk = simpledialog.askstring("Disk", "Enter disk id (example: disk4)")
        if not disk:
            return
        vol_name = simpledialog.askstring("Volume Name", "Enter new volume name", initialvalue="REKORDBOX")
        if not vol_name:
            return
        fs = simpledialog.askstring("Filesystem", "Enter MS-DOS or ExFAT", initialvalue="MS-DOS")
        if fs not in {"MS-DOS", "ExFAT"}:
            messagebox.showerror("Invalid FS", "Filesystem must be MS-DOS or ExFAT.")
            return

        if not messagebox.askyesno("Confirm Erase", f"This will ERASE /dev/{disk}. Continue?"):
            return

        def _task():
            cmd = [
                "python3",
                str(TOOLS / "format_usb_macos.py"),
                "--disk",
                disk,
                "--name",
                vol_name,
                "--fs",
                fs,
                "--yes-i-understand-erase",
            ]
            self.run_cmd(cmd)

        self.run_async(_task)


if __name__ == "__main__":
    App().mainloop()
