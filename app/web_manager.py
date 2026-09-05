#!/usr/bin/env python3
import html
import json
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
HOST = "127.0.0.1"
PORT = 8787

DEFAULTS = {
    "source": "/Users/djsly/Desktop/2025/2025 all songs",
    "usb_target": "/Volumes/NO NAME/2025/2025 all songs",
    "crates": "/Users/djsly/Music/_Serato_Backup/Subcrates",
    "report": str(Path.home() / "Desktop" / "truth_report.json"),
}


def run_cmd(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out_lines = []
    assert proc.stdout is not None
    for line in proc.stdout:
        out_lines.append(line)
    rc = proc.wait()
    return rc, "".join(out_lines)


def choose_folder(prompt: str):
    script = f'POSIX path of (choose folder with prompt "{prompt}")'
    rc, out = run_cmd(["osascript", "-e", script])
    if rc != 0:
        return None, out.strip()
    return out.strip(), ""


def render_page(values, output="", error=""):
    source = html.escape(values.get("source", ""))
    usb_target = html.escape(values.get("usb_target", ""))
    crates = html.escape(values.get("crates", ""))
    report = html.escape(values.get("report", ""))
    output_html = html.escape(output)
    error_html = html.escape(error)

    return f"""<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>KasseKordrato Web Manager</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; margin: 20px; background: #f4f6f8; }}
    .card {{ background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); max-width: 1100px; margin: 0 auto; }}
    h1 {{ margin-top: 0; }}
    label {{ display:block; margin-top:10px; font-weight:600; }}
    input {{ width:100%; padding:10px; border:1px solid #ccd1d5; border-radius:8px; }}
    .row {{ display:flex; gap:10px; margin-top:14px; flex-wrap:wrap; }}
    button {{ border:none; border-radius:8px; padding:10px 14px; cursor:pointer; font-weight:600; }}
    .primary {{ background:#0b66ff; color:#fff; }}
    .warn {{ background:#d83b01; color:#fff; }}
    .muted {{ background:#e8edf2; }}
    pre {{ background:#0f1720; color:#d9e1ea; padding:12px; border-radius:8px; overflow:auto; min-height:220px; }}
    .error {{ color:#b00020; font-weight:700; margin-top:10px; }}
    .hint {{ color:#445; margin-top:8px; }}
  </style>
</head>
<body>
  <div class=\"card\"> 
    <h1>KasseKordrato Web Manager</h1>
    <p class=\"hint\">Run this from browser instead of CLI. After USB sync, still use Rekordbox Export Mode for CDJ database.</p>
    <form method=\"post\">
      <label>Source Folder</label>
      <input name=\"source\" value=\"{source}\" />
      <div class=\"row\"><button class=\"muted\" name=\"action\" value=\"browse_source\">Browse Source (Finder)</button></div>

      <label>USB Target Folder</label>
      <input name=\"usb_target\" value=\"{usb_target}\" />
      <div class=\"row\"><button class=\"muted\" name=\"action\" value=\"browse_usb\">Browse USB (Finder)</button></div>

      <label>Serato Subcrates (optional)</label>
      <input name=\"crates\" value=\"{crates}\" />
      <div class=\"row\"><button class=\"muted\" name=\"action\" value=\"browse_crates\">Browse Crates (Finder)</button></div>

      <label>Truth Report Output</label>
      <input name=\"report\" value=\"{report}\" />

      <div class=\"row\">
        <button class=\"primary\" name=\"action\" value=\"truth\">Run Truth Report</button>
        <button class=\"muted\" name=\"action\" value=\"dry\">Dry-Run USB Sync</button>
        <button class=\"warn\" name=\"action\" value=\"sync\" onclick=\"return confirm('Run real 1:1 USB sync now?');\">Run 1:1 USB Sync</button>
      </div>
    </form>
    {f'<div class="error">{error_html}</div>' if error else ''}
    <h3>Output</h3>
    <pre>{output_html}</pre>
  </div>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _write_html(self, body):
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        self._write_html(render_page(DEFAULTS))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(length).decode("utf-8", errors="replace")
        form = parse_qs(data)

        values = {
            "source": form.get("source", [DEFAULTS["source"]])[0].strip(),
            "usb_target": form.get("usb_target", [DEFAULTS["usb_target"]])[0].strip(),
            "crates": form.get("crates", [DEFAULTS["crates"]])[0].strip(),
            "report": form.get("report", [DEFAULTS["report"]])[0].strip(),
        }
        action = form.get("action", [""])[0]

        if action == "browse_source":
            chosen, err = choose_folder("Choose source folder")
            if chosen:
                values["source"] = chosen
                self._write_html(render_page(values))
            else:
                self._write_html(render_page(values, error=f"Finder browse failed: {err or 'unknown error'}"))
            return
        if action == "browse_usb":
            chosen, err = choose_folder("Choose USB target folder")
            if chosen:
                values["usb_target"] = chosen
                self._write_html(render_page(values))
            else:
                self._write_html(render_page(values, error=f"Finder browse failed: {err or 'unknown error'}"))
            return
        if action == "browse_crates":
            chosen, err = choose_folder("Choose Serato subcrates folder")
            if chosen:
                values["crates"] = chosen
                self._write_html(render_page(values))
            else:
                self._write_html(render_page(values, error=f"Finder browse failed: {err or 'unknown error'}"))
            return

        source = Path(values["source"])
        usb_target = Path(values["usb_target"])
        crates = Path(values["crates"])

        if not source.exists():
            self._write_html(render_page(values, error=f"Source folder not found: {source}"))
            return

        output = ""
        if action == "truth":
            cmd = [
                "python3",
                str(TOOLS / "music_truth_report.py"),
                "--source",
                str(source),
                "--out",
                values["report"],
            ]
            if values["crates"] and crates.exists():
                cmd.extend(["--serato-subcrates", str(crates)])
            rc, out = run_cmd(cmd)
            output = "$ " + " ".join(cmd) + "\n" + out + f"\nExit code: {rc}"

        elif action in {"dry", "sync"}:
            if not usb_target.exists():
                self._write_html(render_page(values, error=f"USB target not found: {usb_target}"))
                return
            cmd = [
                "python3",
                str(TOOLS / "usb_rekordbox_sync.py"),
                "--source",
                str(source),
                "--usb-target",
                str(usb_target),
            ]
            if action == "dry":
                cmd.append("--dry-run")
            rc, out = run_cmd(cmd)
            output = "$ " + " ".join(cmd) + "\n" + out + f"\nExit code: {rc}"

        self._write_html(render_page(values, output=output))


if __name__ == "__main__":
    print(f"KasseKordrato Web Manager running at http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
