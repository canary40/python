import tkinter as tk
import urllib.parse
import webbrowser
import threading
import os
from pystray import Icon, MenuItem as item, Menu
from PIL import Image
import sys
import ctypes
import json

def disable_maximize_button(window):
    if sys.platform == "win32":
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
        style &= ~0x00010000  # WS_MAXIMIZEBOX
        ctypes.windll.user32.SetWindowLongW(hwnd, -16, style)
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
            0x0001 | 0x0002 | 0x0020)  # SWP_NOMOVE | SWP_NOSIZE | SWP_FRAMECHANGED

def register_custom_browsers():
    user_profile = os.environ.get("USERPROFILE", "")  # ottiene C:\Users\<username>

    def load_browser_paths(filename="browserpaths.txt"):
        with open(filename, 'r') as file:
            browser_paths = json.load(file)
    
        user_profile = os.getenv("USERPROFILE")  # Ottieni la cartella dell'utente
    
        for browser, paths in browser_paths.items():
            for i, path in enumerate(paths):
                browser_paths[browser][i] = path.replace("USERNAME", user_profile.split(os.sep)[-1])
    
        return browser_paths
    
    browsers_paths = load_browser_paths()
    
    for name, paths in browsers_paths.items():
        for path in paths:
            if os.path.exists(path):
                webbrowser.register(name, None, webbrowser.BackgroundBrowser(path))
                break

register_custom_browsers()

def risorsa_percorso(rel_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(os.path.abspath("."), rel_path)

def load_search_engines(filename="searchengines.txt"):
    with open(filename, 'r') as file:
        search_engines = json.load(file)
    return search_engines

search_engines = load_search_engines()

selected_engine_var = None
selected_browser_var = None
entry = None
root = None
tray_icon = None

browsers = ["Default", "Chrome", "Firefox", "OperaGX", "Vivaldi"]

def perform_search(event=None):
    global entry, selected_engine_var, selected_browser_var
    
    query = entry.get("1.0", "end-1c").strip()
    engine = selected_engine_var.get()
    
    if not query:
        return

    encoded_query = urllib.parse.quote(query)
    base_url = search_engines.get(engine, "")
    
    if engine == "":
        url = base_url.format(encoded_query)
    elif base_url:
        url = base_url + encoded_query
    else:
        url = "https://"

    browser_choice = selected_browser_var.get()
    
    if browser_choice == "Default":
        webbrowser.open(url)
    else:
        try:
            browser = webbrowser.get(browser_choice)
            browser.open(url)
        except webbrowser.Error:
            webbrowser.open(url)
    
    hide_window()

def create_gui():
    global root, entry, selected_engine_var, selected_browser_var
    
    root = tk.Tk()
    root.title("advanced search")
    root.configure(bg="black")
    
    width, height = 500, 300
    root.geometry(f"{width}x{height}")
    root.resizable(False, True)
    root.after(0, lambda: disable_maximize_button(root))
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    # Icona finestra
    icon_path = risorsa_percorso("favicon.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Errore nel caricare l'icona finestra: {e}")

    selected_engine_var = tk.StringVar(value="Google")
    selected_browser_var = tk.StringVar(value="Default")
    
    top_frame = tk.Frame(root, bg="black")
    top_frame.pack(anchor="nw", padx=10, pady=10)
    
    browser_label = tk.Label(top_frame, text="Scegli browser:", bg="black", fg="white", font=("Helvetica", 10))
    browser_label.pack(side="left")
    
    browser_menu = tk.OptionMenu(top_frame, selected_browser_var, *browsers)
    browser_menu.config(bg="black", fg="white", highlightthickness=0, activebackground="gray20", activeforeground="white")
    browser_menu["menu"].config(bg="black", fg="white")
    browser_menu.pack(side="left", padx=(5,0))
    
    # Titolo (come label)
    label = tk.Label(root, text="Inserisci la tua ricerca:", bg="black", fg="white", font=("Helvetica", 14))
    label.pack(pady=(5, 5))  # meno spazio sopra perché menu è già lì

    entry = tk.Text(root, height=2, font=("Helvetica", 12), bg="white", fg="black", insertbackground="black", wrap="word")
    entry.pack(fill="x", padx=10, pady=5)
    entry.pack(pady=5)
    entry.focus()

    def enter_pressed(event):
        perform_search()
        return "break"  # blocca inserimento newline

    entry.bind("<Return>", enter_pressed)

    radio_frame = tk.Frame(root, bg="black")
    radio_frame.pack(pady=10)

    engines = list(search_engines.keys())
    half = (len(engines) + 1) // 2

    row1_frame = tk.Frame(radio_frame, bg="black")
    row1_frame.pack()
    for engine in engines[:half]:
        rb = tk.Radiobutton(
            row1_frame, text=engine, variable=selected_engine_var, value=engine,
            bg="black", fg="white", selectcolor="gray20", font=("Helvetica", 10)
        )
        rb.pack(side="left", padx=5)

    row2_frame = tk.Frame(radio_frame, bg="black")
    row2_frame.pack(pady=(5,0))
    for engine in engines[half:]:
        rb = tk.Radiobutton(
            row2_frame, text=engine, variable=selected_engine_var, value=engine,
            bg="black", fg="white", selectcolor="gray20", font=("Helvetica", 10)
        )
        rb.pack(side="left", padx=5)

    search_button = tk.Button(root, text="Cerca", command=perform_search, bg="gray20", fg="white", font=("Helvetica", 12))
    search_button.pack(pady=10)

    root.protocol("WM_DELETE_WINDOW", hide_window)
    
def show_window(icon, item):
    root.after(0, root.deiconify)

def hide_window(icon=None, item=None):
    if root:
        root.withdraw()

def quit_app(icon, item):
    icon.stop()
    if root:
        root.destroy()

myappid = 'tkinter.python.test.1.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
def setup_tray_icon():
    global tray_icon

    icon_path = risorsa_percorso("favicon.ico")
    if not os.path.exists(icon_path):
        print("⚠️ Immagine favicon.ico non trovata.")
        return

    image = Image.open(icon_path)

    menu = Menu(
        item('Apri', show_window),
        Menu.SEPARATOR,
        item('Esci', quit_app)
    )

    tray_icon = Icon("advanced search", image, "advanced search", menu)
    tray_icon.run_detached()  # non blocca il thread principale

if __name__ == "__main__":
    threading.Thread(target=setup_tray_icon, daemon=True).start()
    create_gui()
    root.mainloop()
