"""Sync Scout-related local files to Google Drive.

Idempotent: lists what's already in each target Drive folder and skips matches by
filename. Safe to re-run any time new artefacts land.

Reuses the OAuth client at 01-scout/oauth/google-drive-client.json (installed-app type)
but requests the broader `drive` scope because we write into folders this client did
not create (those were created earlier via the Claude.ai Drive MCP, owned by the
user's Google account). The token is cached at ~/.config/scout-sync/token.json,
chmod 600. First run opens a browser; subsequent runs are silent.

Usage:
    uv run --with google-api-python-client --with google-auth-oauthlib \\
        python co-platform/agents/scout/sync-to-drive.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


HOME = Path.home()
SCOUT = HOME / "Desktop/Charlie-Oscar-OS-Prep/06-Agents/01-Agent-Build-Packs/Ai-ops/01-scout"
DOC_STORE_PARENT = HOME / "Desktop/Charlie-Oscar-OS-Prep/co-platform/agents/scout"

CLIENT_SECRETS = SCOUT / "oauth" / "google-drive-client.json"
TOKEN_CACHE = HOME / ".config" / "scout-sync" / "token.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]


# Drive folder IDs captured when these folders were created via the Drive MCP.
FOLDERS = {
    "agents/scout":                       "1k7xBtmFNo_8Q79ne4w0883uJZC853V3H",
    "agents/scout/goldens":               "1-AmWCHl1eMcsSZxFAjTCIo_-1VwGjZ4i",
    "agents/scout/mcp":                   "1Cg8GEY1sgKXvEpCmyhhWQ0idqGl1duye",
    "agents/scout/specs-source":          "1UfEopU0veFh26fW8hqaqNNdBJB-WjqLf",
    "agents/scout/doc-store":             "16TtKLkqjyr6vep0ha1HjN-N9DWbdXzUR",
    "agents/scout/doc-store/specs":       "1VugT47zisGy3FKhir_7zPmVj5_0X0aSo",
    "agents/scout/doc-store/evals":       "1yNNyZ-De02eRv6ESvy-wVyvsudGXXxTP",
    "agents/scout/doc-store/calibration": "1pisQrM7LYY36S63GErtIlE4Lf1j7JCCD",
    "agents/scout/hand-scores":           "1aSezsYSd6gzyVyHjRqtM6JTYjWZSUzh_",
}


# Each entry: (local source dir, target Drive folder ID)
# Files in each local dir are uploaded to the corresponding Drive folder, skipping
# anything that already exists there by name. Non-files (subdirs) are not recursed.
UPLOAD_MAP = [
    (SCOUT / "goldens",                              FOLDERS["agents/scout/goldens"]),
    (SCOUT / "hand-scores",                          FOLDERS["agents/scout/hand-scores"]),
    (DOC_STORE_PARENT / "doc-store" / "calibration", FOLDERS["agents/scout/doc-store/calibration"]),
    (DOC_STORE_PARENT / "mcp",                       FOLDERS["agents/scout/mcp"]),
]


# Names to skip (already uploaded via MCP earlier, or operational noise).
SKIP_NAMES = {
    ".DS_Store",
}

# Suffix/substring patterns to skip.
SKIP_PATTERNS = (".bak.", ".tmp", "__pycache__")


def get_credentials():
    creds = None
    TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if TOKEN_CACHE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_CACHE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS.exists():
                sys.exit(f"OAuth client file not found: {CLIENT_SECRETS}")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
            print("Opening browser for Google Drive OAuth consent...")
            print("  Requested scope: drive (write). One-time grant.")
            creds = flow.run_local_server(port=0)
        TOKEN_CACHE.write_text(creds.to_json())
        os.chmod(TOKEN_CACHE, 0o600)
    return creds


def list_existing(service, parent_id):
    files, page_token = [], None
    while True:
        resp = service.files().list(
            q=f"'{parent_id}' in parents and trashed = false",
            fields="nextPageToken, files(name)",
            pageSize=1000,
            pageToken=page_token,
        ).execute()
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return {f["name"] for f in files}


def guess_mime(path: Path) -> str:
    return {
        ".md":     "text/markdown",
        ".json":   "application/json",
        ".jsonl":  "application/jsonl",
        ".py":     "text/x-python",
        ".txt":    "text/plain",
        ".yaml":   "text/yaml",
        ".yml":    "text/yaml",
        ".toml":   "application/toml",
        ".lock":   "text/plain",
        ".sh":     "text/x-shellscript",
        ".dockerfile": "text/plain",
    }.get(path.suffix.lower(), "application/octet-stream")


def upload_one(service, local_path: Path, parent_id: str):
    media = MediaFileUpload(str(local_path), mimetype=guess_mime(local_path), resumable=False)
    body = {"name": local_path.name, "parents": [parent_id]}
    f = service.files().create(body=body, media_body=media, fields="id, name").execute()
    return f["id"]


def main():
    print("Scout -> Drive sync starting...")
    print(f"  OAuth client: {CLIENT_SECRETS}")
    print(f"  Token cache:  {TOKEN_CACHE}")

    creds = get_credentials()
    service = build("drive", "v3", credentials=creds)

    uploaded, skipped_existing, skipped_filter = 0, 0, 0
    failed = []

    for src_dir, parent_id in UPLOAD_MAP:
        print(f"\n=== {src_dir.relative_to(HOME)} -> Drive folder {parent_id} ===")
        if not src_dir.exists():
            print(f"   (source missing; skipping)")
            continue
        existing = list_existing(service, parent_id)
        print(f"   {len(existing)} file(s) already in target")

        for child in sorted(src_dir.iterdir()):
            if not child.is_file():
                continue
            if child.name in SKIP_NAMES or any(p in child.name for p in SKIP_PATTERNS):
                skipped_filter += 1
                continue
            if child.name in existing:
                skipped_existing += 1
                continue
            try:
                fid = upload_one(service, child, parent_id)
                print(f"  [uploaded] {child.name}  ({fid})")
                uploaded += 1
            except Exception as e:
                print(f"  [FAIL] {child.name}: {e}")
                failed.append((str(child), str(e)))

    print(f"\nDone. uploaded={uploaded}  skipped-existing={skipped_existing}  "
          f"skipped-filter={skipped_filter}  failed={len(failed)}")
    if failed:
        for path, err in failed:
            print(f"  FAIL: {path}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
