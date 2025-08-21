import tkinter as tk
from PIL import Image, ImageTk
import feedparser
import threading
import time
import webbrowser
import pygame
import pystray
from pystray import MenuItem as item
from pystray import Icon, Menu
import pyperclip
from babel.dates import format_datetime
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
import calendar
import html
import sys, os

first_check_error_shown = True

if getattr(sys, 'frozen', False):  
    # caso exe (PyInstaller)
    current_dir = os.path.dirname(sys.executable)
else:
    # caso script normale
    current_dir = os.path.dirname(os.path.abspath(__file__))

# cartella icone
icons_dir = os.path.join(current_dir, 'icons')

# controlli utili
if not os.path.exists(icons_dir):
    print(f"ERRORE: la cartella 'icons' non esiste in: {icons_dir}")
else:
    print("Cartella trovata:", icons_dir)
    print("Contenuto:", os.listdir(icons_dir))
    
feeds_file = os.path.join(current_dir, "feeds.txt")
rss_urls = []

last_titles = {}
ITALY_TZ = ZoneInfo("Europe/Rome")

def copy_link_to_clipboard(news_link):
    pyperclip.copy(news_link)
    print("Link copiato negli appunti!")

def format_entry_date(entry):
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            timestamp = calendar.timegm(entry.published_parsed)
            dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            dt_italy = dt_utc.astimezone(ITALY_TZ)
            return format_datetime(dt_italy, "EEEE dd MMMM yyyy, HH:mm", locale='it')
    except Exception as e:
        print("Errore formattando data della notizia:", e)
    return "Data sconosciuta"

def show_error_popup(message):
    global first_check_error_shown
    if first_check_error_shown:
        first_check_error_shown
        popup = tk.Tk()
        popup.title("Errore")
        popup.configure(bg='black')
        sw, sh = popup.winfo_screenwidth(), popup.winfo_screenheight()
        x = sw // 2 - 200 // 2
        y = sh // 2 - 200 // 2
        popup.geometry(f"400x200+{x}+{y}")
        tray_icon = Image.open(image_path) 
        icon_photo = ImageTk.PhotoImage(tray_icon)
        popup.iconphoto(False, icon_photo)
        tk.Label(popup, text=message, font=("Arial", 10, "bold"), fg="red", bg="black", wraplength=380, justify="center").pack(pady=30)
        tk.Button(popup, text="Chiudi", command=popup.destroy, padx=15, pady=2, bg="red", fg="white").pack(pady=5)
        popup.mainloop()

image_path = os.path.join(current_dir, 'favicon.png')
notification_sound = os.path.join(current_dir, 'notification.mp3')
print(f"Working directory: {os.getcwd()}")
print(f"Verifica percorso delle icone: {icons_dir}")

icone_feed = {}

with open(feeds_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            url, icon_name = line.split("|")
            url, icon_name = url.strip(), icon_name.strip()
            rss_urls.append(url)
            icone_feed[url] = Image.open(os.path.join(icons_dir, icon_name))
        except ValueError:
            print(f"Riga non valida in feeds.txt: {line}")

tray_icon = Image.open(image_path)

pygame.mixer.init()
pygame.mixer.music.load(notification_sound)

def play_notification():
    try:
        pygame.mixer.music.load(notification_sound)
        pygame.mixer.music.play()
    except Exception as e:
        print("Errore riproduzione suono:", e)

def show_popup(feed_url, feed_title, news_title, news_summary, news_link, entry):
    play_notification()
    popup = tk.Tk()
    popup.title(feed_title)
    popup.configure(bg='black')
    popup.geometry("1050x600")
    icon_photo = None
    if feed_url in icone_feed:
        icon_photo = ImageTk.PhotoImage(icone_feed[feed_url])
        popup.iconphoto(False, icon_photo)

    sw, sh = popup.winfo_screenwidth(), popup.winfo_screenheight()
    x = sw//2 - 1050//2
    y = sh//2 - 600//2
    popup.geometry(f'1050x600+{x}+{y}')
    
    header = tk.Frame(popup, bg="black")
    header.pack(fill="x")

    tk.Label(header, text=news_title, font=("Arial", 16, "bold"),
             fg="white", bg="black", wraplength=1000, justify="left").pack(anchor="w", padx=15, pady=(15, 5))

    tk.Label(header, text=f"{feed_title} - {format_entry_date(entry)}",
             font=("Arial", 10, "italic"), fg="gray", bg="black").pack(anchor="w", padx=15, pady=(0, 10))
    
    tk.Frame(header, bg="gray", height=1).pack(fill="x", padx=10, pady=5)
    
    sf = tk.Frame(popup)
    sf.pack(fill="both", expand=True)

    canvas = tk.Canvas(sf, bg="black", highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)

    vs = tk.Scrollbar(sf, orient="vertical", command=canvas.yview)
    vs.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=vs.set)

    cf = tk.Frame(canvas, bg="black")
    canvas.create_window((0, 0), window=cf, anchor="nw")

    cf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
    
    tk.Label(cf, text=html.unescape(news_summary),
             font=("Arial", 11), fg="white", bg="black", wraplength=980, justify="left").pack(anchor="w", padx=20, pady=10)

    if news_link:
        bf = tk.Frame(cf, bg="black")
        bf.pack(pady=10)
        tk.Button(bf, text="Apri Link", command=lambda: webbrowser.open(news_link),
                  padx=10, pady=2, bg="#444", fg="white").pack(side="left", padx=5)
        tk.Button(bf, text="Copia Link", command=lambda: copy_link_to_clipboard(news_link),
                  padx=10, pady=2, bg="#444", fg="white").pack(side="left", padx=5)
        
    tk.Frame(cf, bg="gray", height=1).pack(fill="x", padx=20, pady=15)    
    tk.Button(cf, text="Chiudi", command=popup.destroy,
              padx=15, pady=2, bg="red", fg="white").pack(pady=2)

    popup.mainloop()

def check_feed():
    global last_titles, first_check_error_shown
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            if feed.bozo:
                show_error_popup(f"Impossibile caricare il feed da {url}. Potrebbe essere bloccato dalla VPN o dalla regione.")
                first_check_error_shown = False
                continue
            if feed.entries:
                entry = feed.entries[0]
                if entry.title != last_titles.get(url):
                    last_titles[url] = entry.title
                    show_popup(url, feed.feed.title if 'title' in feed.feed else "Feed", entry.title, entry.summary, entry.get("link", None), entry)
        except Exception as e:
            if first_check_error_shown:
                show_error_popup(f"Errore durante l'accesso al feed da {url}: {str(e)}")
                first_check_error_shown = False
        continue
        print(f"Controllando feed: {url}")  # Debug
        feed = feedparser.parse(url)
        if feed.entries:
            entry = feed.entries[0]
            print(f"Ultimo titolo: {entry.title}")  # Debug
            if entry.title != last_titles.get(url):
                print(f"Nuovo articolo trovato: {entry.title}")  # Debug
                last_titles[url] = entry.title
                show_popup(
                    url,
                    feed.feed.title if 'title' in feed.feed else "Feed",
                    entry.title,
                    entry.summary,
                    entry.get("link", None),
                    entry
                )

def start_feed_checking():
    while True:
        check_feed()
        time.sleep(20)

def quit_program(icon, item):
    icon.stop()
    exit()

def start_tray():
    menu = (item('Esci', quit_program),)
    icon = pystray.Icon("live feed", tray_icon, "live feed", menu)
    icon.run()

threading.Thread(target=start_feed_checking, daemon=True).start()
start_tray()
