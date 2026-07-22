// Watch Register — Tauri shell around the local-first web app in /src.
// v1 intentionally does no custom filesystem work in Rust: the app still
// uses the browser-standard WebCrypto + IndexedDB it already had, just
// inside a native window instead of a browser tab. Native vault
// read/write/wipe commands are a documented next step — see README.

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running Watch Register");
}
