use std::fs;
use std::net::{SocketAddr, TcpStream};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::Duration;

use tauri::{Manager, RunEvent};

/// Holds the child process of the Python backend JARVIS spawned on launch
/// (if it wasn't already running), so it can be cleaned up on exit.
struct BackendProcess(Mutex<Option<Child>>);

fn backend_healthy() -> bool {
    let addr: SocketAddr = match "127.0.0.1:8000".parse() {
        Ok(a) => a,
        Err(_) => return false,
    };
    TcpStream::connect_timeout(&addr, Duration::from_millis(300)).is_ok()
}

/// Locates the JARVIS project root (the directory containing `main.py`).
/// Resolution order:
///   1. A `backend_path` file shipped inside a macOS .app bundle.
///   2. The current working directory (dev mode / folder install).
///   3. The current executable, walking up parent directories.
fn find_backend_dir() -> Option<PathBuf> {
    if let Ok(exe) = std::env::current_exe() {
        let resource_hint = exe
            .parent()?
            .parent()?
            .join("Resources")
            .join("backend_path");
        if let Ok(raw) = fs::read_to_string(&resource_hint) {
            let hint = PathBuf::from(raw.trim());
            if hint.join("main.py").exists() {
                return Some(hint);
            }
        }
    }

    let mut dirs: Vec<PathBuf> = Vec::new();
    if let Ok(cwd) = std::env::current_dir() {
        dirs.push(cwd);
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            dirs.push(dir.to_path_buf());
            for ancestor in dir.ancestors() {
                dirs.push(ancestor.to_path_buf());
            }
        }
    }

    for dir in dirs {
        if dir.join("main.py").exists() {
            return Some(dir);
        }
    }
    None
}

fn spawn_backend() -> Option<Child> {
    if backend_healthy() {
        return None;
    }
    let backend_dir = find_backend_dir()?;
    let main_py = backend_dir.join("main.py");
    if !main_py.exists() {
        return None;
    }
    let candidates = [
        backend_dir.join(".venv/bin/python3"),
        backend_dir.join(".venv/Scripts/python.exe"),
        PathBuf::from("python3"),
        PathBuf::from("python"),
    ];
    for python in candidates {
        if let Ok(child) = Command::new(&python)
            .arg(&main_py)
            .current_dir(&backend_dir)
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
        {
            return Some(child);
        }
    }
    None
}

fn kill_backend(app_handle: &tauri::AppHandle) {
    if let Ok(mut guard) = app_handle.state::<BackendProcess>().0.lock() {
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

/// Keeps the Python backend alive for as long as the app runs.
/// The frontend auto-reconnects its WebSocket, so as soon as a backend is
/// running again the UI recovers on its own. Without this, a backend that
/// crashes (or fails its first spawn) leaves the app stuck on "SYSTEM OFFLINE".
fn monitor_backend(app_handle: tauri::AppHandle) {
    std::thread::spawn(move || {
        // If setup() already spawned a backend, treat it as freshly spawned so
        // it gets the full boot grace period.
        let already_running = match app_handle.state::<BackendProcess>().0.try_lock() {
            Ok(guard) => guard.is_some(),
            Err(_) => false,
        };
        let mut last_spawn = if already_running {
            std::time::Instant::now()
        } else {
            std::time::Instant::now() - Duration::from_secs(30)
        };
        loop {
            std::thread::sleep(Duration::from_secs(3));
            if backend_healthy() {
                continue;
            }
            let state = app_handle.state::<BackendProcess>();
            let mut guard = match state.0.try_lock() {
                Ok(guard) => guard,
                Err(_) => continue,
            };
            // A freshly spawned backend takes a few seconds to import its
            // dependencies and bind the port. Don't kill it while it boots.
            let still_alive = match guard.as_mut() {
                Some(child) => matches!(child.try_wait(), Ok(None)),
                None => false,
            };
            if still_alive && last_spawn.elapsed() < Duration::from_secs(20) {
                continue;
            }
            if let Some(mut child) = guard.take() {
                let _ = child.kill();
                let _ = child.wait();
            }
            if let Some(child) = spawn_backend() {
                *guard = Some(child);
                last_spawn = std::time::Instant::now();
            }
        }
    });
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            let child = spawn_backend();
            *app.state::<BackendProcess>().0.lock().unwrap() = child;
            monitor_backend(app.handle().clone());
            let window = app.get_webview_window("main").unwrap();
            window.set_title("JARVIS 2.0")?;
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let RunEvent::Exit = event {
                kill_backend(app_handle);
            }
        });
}
