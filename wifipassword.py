import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import os

def centra_finestra(finestra, larghezza, altezza):
    finestra.update_idletasks()
    x = (finestra.winfo_screenwidth() // 2) - (larghezza // 2)
    y = (finestra.winfo_screenheight() // 2) - (altezza // 2)
    finestra.geometry(f"{larghezza}x{altezza}+{x}+{y}")

def get_wifi_passwords():
    try:
        profiles_output = subprocess.check_output("netsh wlan show profiles", shell=True, text=True)
        profiles = []
        for line in profiles_output.splitlines():
            if "Tutti i profili utente" in line or "All User Profile" in line:
                profile = line.split(":")[1].strip()
                profiles.append(profile)

        wifi_list = []

        for profile in profiles:
            try:
                profile_info = subprocess.check_output(
                    f'netsh wlan show profile name="{profile}" key=clear',
                    shell=True,
                    text=True
                )
                for line in profile_info.splitlines():
                    if "Contenuto chiave" in line or "Key Content" in line:
                        password = line.split(":")[1].strip()
                        break
                else:
                    password = "Nessuna password trovata"
            except subprocess.CalledProcessError:
                password = "Errore durante il recupero"
            wifi_list.append((profile, password))

        return wifi_list

    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante il recupero delle password:\n{e}")
        return []

def show_wifi_passwords():
    wifi_list = get_wifi_passwords()

    if not wifi_list:
        messagebox.showinfo("Info", "Nessuna rete Wi-Fi trovata.")
        return

    window = tk.Tk()
    window.title("Password Wi-Fi Salvate")

    # Imposta icona se esiste
    if os.path.exists("favicon.ico"):
        try:
            window.iconbitmap("favicon.ico")
        except Exception as e:
            print("Errore caricamento icona:", e)

    larghezza, altezza = 500, 400
    centra_finestra(window, larghezza, altezza)

    tree = ttk.Treeview(window, columns=("SSID", "Password"), show="headings")
    tree.heading("SSID", text="SSID")
    tree.heading("Password", text="Password")
    tree.pack(fill=tk.BOTH, expand=True)

    for ssid, password in wifi_list:
        tree.insert("", tk.END, values=(ssid, password))

    def on_double_click(event):
        item = tree.selection()
        if item:
            ssid, password = tree.item(item[0], "values")
            window.clipboard_clear()
            window.clipboard_append(password)
            messagebox.showinfo("Copiato", f"La password per '{ssid}' è stata copiata negli appunti.")

    tree.bind("<Double-1>", on_double_click)

    label = tk.Label(window, text="Doppio clic su una riga per copiare la password", fg="gray")
    label.pack(pady=5)

    window.mainloop()

if __name__ == "__main__":
    show_wifi_passwords()
