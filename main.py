import requests
import json
from datetime import datetime
import pytz
from geopy.geocoders import Nominatim
import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading


class PrayerTimesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Horaires de Prière Islamique")
        self.root.geometry("800x600")

        # Configuration par défaut
        self.method = 2  # ISNA par défaut
        self.school = 0  # Shafii par défaut
        self.timezone = "Africa/Algiers"  # Par défaut

        # Interface utilisateur
        self.create_widgets()

        # Détection automatique de la localisation
        self.detect_location()

    def create_widgets(self):
        # Frame principale
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame de configuration
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=5)

        # Localisation
        ttk.Label(config_frame, text="Ville/Pays:").grid(row=0, column=0, sticky=tk.W)
        self.location_entry = ttk.Entry(config_frame, width=30)
        self.location_entry.grid(row=0, column=1, padx=5)

        self.detect_btn = ttk.Button(config_frame, text="Détecter automatiquement", command=self.detect_location)
        self.detect_btn.grid(row=0, column=2, padx=5)

        # Méthode de calcul
        ttk.Label(config_frame, text="Méthode:").grid(row=1, column=0, sticky=tk.W)
        self.method_var = tk.StringVar()
        methods = {
            "1": "Université des Sciences Islamiques, Karachi",
            "2": "Islamic Society of North America (ISNA)",
            "3": "Muslim World League (MWL)",
            "4": "Umm Al-Qura, Makkah",
            "5": "Egyptian General Authority of Survey",
            "7": "Institut de Géophysique d'Alger"
        }
        self.method_combo = ttk.Combobox(config_frame, textvariable=self.method_var, values=list(methods.values()))
        self.method_combo.grid(row=1, column=1, padx=5, sticky=tk.W)
        self.method_combo.current(1)  # ISNA par défaut

        # École juridique
        ttk.Label(config_frame, text="École:").grid(row=2, column=0, sticky=tk.W)
        self.school_var = tk.StringVar()
        schools = {
            "0": "Shafii (angle 18°)",
            "1": "Hanafi (angle 19°)"
        }
        self.school_combo = ttk.Combobox(config_frame, textvariable=self.school_var, values=list(schools.values()))
        self.school_combo.grid(row=2, column=1, padx=5, sticky=tk.W)
        self.school_combo.current(0)  # Shafii par défaut

        # Bouton de mise à jour
        self.update_btn = ttk.Button(config_frame, text="Mettre à jour", command=self.update_prayer_times)
        self.update_btn.grid(row=3, column=1, pady=10)

        # Affichage des horaires
        times_frame = ttk.LabelFrame(main_frame, text="Horaires de Prière", padding="10")
        times_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Tableau des horaires
        columns = ("Prière", "Heure")
        self.times_tree = ttk.Treeview(times_frame, columns=columns, show="headings", height=6)

        for col in columns:
            self.times_tree.heading(col, text=col)
            self.times_tree.column(col, width=100, anchor=tk.CENTER)

        self.times_tree.pack(fill=tk.BOTH, expand=True)

        # Prochaine prière
        self.next_prayer_label = ttk.Label(main_frame, text="", font=('Helvetica', 12, 'bold'))
        self.next_prayer_label.pack(pady=10)

        # Calendrier mensuel
        self.calendar_btn = ttk.Button(main_frame, text="Voir le calendrier mensuel",
                                       command=self.show_monthly_calendar)
        self.calendar_btn.pack(pady=5)

        # Initialisation
        self.update_prayer_times()

    def detect_location(self):
        try:
            # Utilisation d'un service IP pour détecter la localisation approximative
            response = requests.get('https://ipinfo.io/json')
            data = response.json()
            city = data.get('city', '')
            country = data.get('country', '')

            if city and country:
                self.location_entry.delete(0, tk.END)
                self.location_entry.insert(0, f"{city}, {country}")

                # Détection du fuseau horaire
                timezone = data.get('timezone', '')
                if timezone:
                    self.timezone = timezone

                self.update_prayer_times()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de détecter la localisation: {str(e)}")

    def get_coordinates(self, location):
        geolocator = Nominatim(user_agent="prayer_times_app")
        location = geolocator.geocode(location)
        if location:
            return (location.latitude, location.longitude)
        return None

    def update_prayer_times(self):
        location = self.location_entry.get()
        if not location:
            messagebox.showwarning("Attention", "Veuillez entrer une localisation")
            return

        try:
            # Récupération des coordonnées
            coords = self.get_coordinates(location)
            if not coords:
                raise ValueError("Localisation introuvable")

            # Récupération de la méthode sélectionnée
            method_mapping = {
                "Université des Sciences Islamiques, Karachi": 1,
                "Islamic Society of North America (ISNA)": 2,
                "Muslim World League (MWL)": 3,
                "Umm Al-Qura, Makkah": 4,
                "Egyptian General Authority of Survey": 5,
                "Institut de Géophysique d'Alger": 7
            }
            method = method_mapping.get(self.method_var.get(), 2)

            # Récupération de l'école sélectionnée
            school_mapping = {
                "Shafii (angle 18°)": 0,
                "Hanafi (angle 19°)": 1
            }
            school = school_mapping.get(self.school_var.get(), 0)

            # Date actuelle
            today = datetime.now().strftime("%d-%m-%Y")

            # Appel à l'API Aladhan
            url = f"http://api.aladhan.com/v1/timings/{today}"
            params = {
                "latitude": coords[0],
                "longitude": coords[1],
                "method": method,
                "school": school
            }

            response = requests.get(url, params=params)
            data = response.json()

            if data['code'] != 200:
                raise ValueError("Erreur dans la récupération des horaires")

            # Mise à jour de l'interface
            self.display_prayer_times(data['data']['timings'])

            # Démarrer le suivi de la prochaine prière
            self.track_next_prayer(data['data']['timings'])

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de récupérer les horaires: {str(e)}")

    def display_prayer_times(self, timings):
        # Nettoyage du tableau
        for item in self.times_tree.get_children():
            self.times_tree.delete(item)

        # Prières à afficher
        prayers = {
            "Fajr": "Fajr",
            "Dhuhr": "Dhuhr",
            "Asr": "Asr",
            "Maghrib": "Maghrib",
            "Isha": "Isha"
        }

        # Ajout des horaires
        for prayer, label in prayers.items():
            time_str = timings.get(prayer, '')
            if time_str:
                # Conversion au fuseau horaire local
                try:
                    naive_time = datetime.strptime(time_str, "%H:%M")
                    local_tz = pytz.timezone(self.timezone)
                    local_time = local_tz.localize(naive_time).strftime("%H:%M")
                    self.times_tree.insert("", tk.END, values=(label, local_time))
                except:
                    self.times_tree.insert("", tk.END, values=(label, time_str))

    def track_next_prayer(self, timings):
        # Obtenir l'heure actuelle
        now = datetime.now(pytz.timezone(self.timezone))
        current_time = now.strftime("%H:%M")

        # Liste des prières dans l'ordre
        prayer_order = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

        # Trouver la prochaine prière
        next_prayer = None
        for prayer in prayer_order:
            prayer_time = datetime.strptime(timings[prayer], "%H:%M").time()
            prayer_datetime = now.replace(hour=prayer_time.hour, minute=prayer_time.minute, second=0, microsecond=0)

            if prayer_datetime > now:
                next_prayer = (prayer, prayer_datetime.strftime("%H:%M"))
                break

        # Si toutes les prières sont passées, prendre Fajr du lendemain
        if not next_prayer:
            next_prayer = ("Fajr", timings["Fajr"])

        # Mise à jour de l'interface
        self.next_prayer_label.config(text=f"Prochaine prière: {next_prayer[0]} à {next_prayer[1]}")

        # Planifier une notification
        self.schedule_notification(next_prayer[0], next_prayer[1])

    def schedule_notification(self, prayer_name, prayer_time):
        # Calculer le temps restant
        now = datetime.now(pytz.timezone(self.timezone))
        prayer_datetime = datetime.strptime(prayer_time, "%H:%M")
        prayer_datetime = now.replace(hour=prayer_datetime.hour, minute=prayer_datetime.minute, second=0, microsecond=0)

        # Si l'heure est déjà passée, ajouter un jour
        if prayer_datetime < now:
            prayer_datetime += timedelta(days=1)

        delta = (prayer_datetime - now).total_seconds()

        # Planifier la notification 5 minutes avant
        notification_time = max(0, delta - 300)  # 5 minutes = 300 secondes

        # Démarrer un thread pour la notification
        threading.Timer(notification_time, self.show_notification, [prayer_name]).start()

    def show_notification(self, prayer_name):
        messagebox.showinfo("Rappel de Prière", f"La prière de {prayer_name} va commencer dans 5 minutes!")

    def show_monthly_calendar(self):
        location = self.location_entry.get()
        if not location:
            messagebox.showwarning("Attention", "Veuillez entrer une localisation")
            return

        try:
            coords = self.get_coordinates(location)
            if not coords:
                raise ValueError("Localisation introuvable")

            # Récupération de la méthode et de l'école
            method_mapping = {v: k for k, v in self.method_combo['values'].items()}
            method = method_mapping.get(self.method_var.get(), 2)

            school_mapping = {v: k for k, v in self.school_combo['values'].items()}
            school = school_mapping.get(self.school_var.get(), 0)

            # Mois et année actuels
            month = datetime.now().month
            year = datetime.now().year

            # Appel à l'API pour le calendrier mensuel
            url = f"http://api.aladhan.com/v1/calendarByAddress"
            params = {
                "address": location,
                "method": method,
                "school": school,
                "month": month,
                "year": year
            }

            response = requests.get(url, params=params)
            data = response.json()

            if data['code'] != 200:
                raise ValueError("Erreur dans la récupération du calendrier")

            # Afficher le calendrier dans une nouvelle fenêtre
            self.display_monthly_calendar(data['data'])

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de récupérer le calendrier: {str(e)}")

    def display_monthly_calendar(self, calendar_data):
        # Création d'une nouvelle fenêtre
        calendar_window = tk.Toplevel(self.root)
        calendar_window.title("Calendrier Mensuel des Prières")
        calendar_window.geometry("1000x600")

        # Création d'un tableau
        columns = ("Date", "Fajr", "Dhuhr", "Asr", "Maghrib", "Isha")
        tree = ttk.Treeview(calendar_window, columns=columns, show="headings", height=30)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor=tk.CENTER)

        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Remplissage du tableau
        for day in calendar_data:
            date = day['date']['readable']
            timings = day['timings']

            tree.insert("", tk.END, values=(
                date,
                timings['Fajr'],
                timings['Dhuhr'],
                timings['Asr'],
                timings['Maghrib'],
                timings['Isha']
            ))


if __name__ == "__main__":
    root = tk.Tk()
    app = PrayerTimesApp(root)
    root.mainloop()
