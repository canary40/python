  GNU nano 8.3                              ansa_notifiche2.py
import feedparser
import time
import subprocess
import os

FEEDS_FILE = "feeds.txt"
CHECK_INTERVAL = 10  # ogni 10 secondi
last_notified_ids = {}  # dizionario {url_feed: ultimo_id}


def load_feeds(file_path):
    """Carica i feed RSS da un file di testo."""
    if not os.path.exists(file_path):
        print(f"File {file_path} non trovato. Creane uno con una lista di feed (uno per riga).")
        return []
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def notify(feed_title, article_title):
    subprocess.run([
        "termux-notification",
        "--title", feed_title,
        "--content", article_title,
        "--priority", "high"
    ])


def get_feed(url):
    """Scarica e parse RSS."""
    return feedparser.parse(url)


if __name__ == "__main__":
    print("Avvio Notifier ANSA su Termux...")

    FEED_URLS = load_feeds(FEEDS_FILE)
    if not FEED_URLS:
        exit(1)

    # Avvio iniziale: mostra l'ultima notizia per ogni feed
    for url in FEED_URLS:
        feed = get_feed(url)
        feed_title = feed.feed.get("title", url)

        if feed.entries:
            last_entry = feed.entries[0]
            last_notified_ids[url] = last_entry.id
            notify(feed_title, last_entry.title)
            print(f"[{last_entry.title}] Ultimo articolo: {feed_title}")

    # Loop di monitoraggio
    while True:
        try:
            for url in FEED_URLS:
                feed = get_feed(url)
                feed_title = feed.feed.get("title", url)

                if feed.entries:
                    latest_entry = feed.entries[0]
                    if last_notified_ids.get(url) != latest_entry.id:
                        last_notified_ids[url] = latest_entry.id
                        notify(feed_title, latest_entry.title)

                        # Stampa la nuova notizia
                        print(f"\n[{feed_title}] Nuovo articolo: {latest_entry.title}")

                        # Mostra anche gli ultimi 5 articoli (live feed)
                        print("\n--- Ultime notizie ---")
                        for entry in feed.entries[:5]:
                            print(f"- {entry.title}")

        except Exception as e:
            print(f"Errore: {e}")

        time.sleep(CHECK_INTERVAL)