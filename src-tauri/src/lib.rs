// Watch Register — Tauri shell around the local-first web app in /src.
//
// STAGE 1 of moving storage off IndexedDB.
//
// Why: the collection lives in IndexedDB, and WebKit decides where that is by
// hashing an origin salt it owns. On 2026-07-22 that salt regenerated and the
// entire register was orphaned — no error, no warning, an app that looked
// freshly installed. Storage identity has to be ours, not the webview's.
//
// These commands write the sealed blob to a path we choose. In stage 1 the
// frontend treats this as a MIRROR only: IndexedDB stays the source of truth,
// so a bug here costs an unused file rather than a collection. Reads flip over
// once the mirror is confirmed working on a real machine.
//
// The blob is already encrypted before it reaches Rust — the passphrase and
// the master key never leave the webview, and this side only ever handles
// ciphertext.

use serde::Serialize;
use std::fs;
use std::path::PathBuf;
use tauri::Manager;

const STORE_FILE: &str = "register.vault";
const TEMP_FILE: &str = "register.vault.tmp";

#[derive(Serialize)]
struct StoreInfo {
    path: String,
    exists: bool,
    bytes: u64,
    modified_ms: u64,
}

fn store_dir(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    app.path()
        .app_data_dir()
        .map_err(|e| format!("no app data directory: {e}"))
}

/// Write the sealed register to disk.
///
/// Writes to a temporary file and renames it into place. Rename is atomic
/// within a filesystem, so a crash mid-write leaves the previous good copy
/// intact rather than a truncated one — which matters when the file is the
/// only copy of someone's collection.
#[tauri::command]
fn store_write(app: tauri::AppHandle, data: String) -> Result<u64, String> {
    let dir = store_dir(&app)?;
    fs::create_dir_all(&dir).map_err(|e| format!("cannot create {}: {e}", dir.display()))?;

    let tmp = dir.join(TEMP_FILE);
    let dest = dir.join(STORE_FILE);

    fs::write(&tmp, data.as_bytes()).map_err(|e| format!("write failed: {e}"))?;
    fs::rename(&tmp, &dest).map_err(|e| format!("rename failed: {e}"))?;

    Ok(data.len() as u64)
}

/// Read the sealed register back, or None when there is no file yet.
#[tauri::command]
fn store_read(app: tauri::AppHandle) -> Result<Option<String>, String> {
    let path = store_dir(&app)?.join(STORE_FILE);
    if !path.exists() {
        return Ok(None);
    }
    fs::read_to_string(&path)
        .map(Some)
        .map_err(|e| format!("read failed: {e}"))
}

/// Where the file is and what state it is in. Drives the diagnostic line in
/// the Data menu so the mirror can be confirmed working before anything
/// depends on it.
#[tauri::command]
fn store_info(app: tauri::AppHandle) -> Result<StoreInfo, String> {
    let path = store_dir(&app)?.join(STORE_FILE);
    let meta = fs::metadata(&path).ok();
    let modified_ms = meta
        .as_ref()
        .and_then(|m| m.modified().ok())
        .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
        .map(|d| d.as_millis() as u64)
        .unwrap_or(0);

    Ok(StoreInfo {
        path: path.to_string_lossy().into_owned(),
        exists: meta.is_some(),
        bytes: meta.as_ref().map(|m| m.len()).unwrap_or(0),
        modified_ms,
    })
}

/// Close the application. Used only by the "No, do not accept" button on the
/// terms screen, which appears before any vault exists -- so declining creates
/// nothing and removes nothing. An app that deleted itself because someone
/// declined terms would be alarming, and could not do so with the permissions
/// this app grants anyway.
#[tauri::command]
fn exit_app(app: tauri::AppHandle) {
    app.exit(0);
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            store_write,
            store_read,
            store_info,
            exit_app
        ])
        .run(tauri::generate_context!())
        .expect("error while running Watch Register");
}
