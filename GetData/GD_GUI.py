import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from decimal import Decimal
from datetime import datetime
from Datenbank.DB_handling import DBHandler

class FinazntTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Finant Tracker")

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)

        # Einkauf Tab
        frame_einkauf = ttk.Frame(notebook)
        self.build_einkauf_form(frame_einkauf)
        notebook.add(frame_einkauf, text="Einkauf")

        # Scheduler Tab
        frame_scheduler = ttk.Frame(notebook)
        self.build_scheduler_form(frame_scheduler)
        notebook.add(frame_scheduler, text="Scheduler")

        # Wertpapier Tab
        frame_wertpapier = ttk.Frame(notebook)
        self.build_wertpapier_form(frame_wertpapier)
        notebook.add(frame_wertpapier, text="Wertpapier")

        # Einkaufszettel Bild Tab
        frame_bild = ttk.Frame(notebook)
        self.build_bild_form(frame_bild)
        notebook.add(frame_bild, text="Einkaufszettel Bild")

    def build_einkauf_form(self, parent):
        ttk.Label(parent, text="Name").grid(row=0, column=0, sticky="w")
        name_entry = ttk.Entry(parent)
        name_entry.grid(row=0, column=1)

        ttk.Label(parent, text="Betrag").grid(row=1, column=0, sticky="w")
        betrag_entry = ttk.Entry(parent)
        betrag_entry.grid(row=1, column=1)

        ttk.Label(parent, text="Kategorie").grid(row=2, column=0, sticky="w")
        kategorie_entry = ttk.Entry(parent)
        kategorie_entry.grid(row=2, column=1)

        ttk.Label(parent, text="Konto").grid(row=3, column=0, sticky="w")
        konto_entry = ttk.Entry(parent)
        konto_entry.grid(row=3, column=1)

        ttk.Label(parent, text="Ausgabentyp").grid(row=4, column=0, sticky="w")
        typ_entry = ttk.Entry(parent)
        typ_entry.grid(row=4, column=1)

        ttk.Label(parent, text="Datum (YYYY-MM-DD)").grid(
            row=5,
            column=0,
            sticky="w"
            )
        datum_entry = ttk.Entry(parent)
        datum_entry.grid(row=5, column=1)

        ttk.Button(parent, text="Speichern", command=lambda: self.save_einkauf(
            name_entry.get(),
            betrag_entry.get(),
            kategorie_entry.get(),
            konto_entry.get(),
            typ_entry.get(),
            datum_entry.get()
        )).grid(row=6, column=0, columnspan=2, pady=10)

    def build_scheduler_form(self, parent):
        ttk.Label(parent, text="Name").grid(row=0, column=0, sticky="w")
        name_entry = ttk.Entry(parent)
        name_entry.grid(row=0, column=1)

        ttk.Label(parent, text="Betrag").grid(row=1, column=0, sticky="w")
        betrag_entry = ttk.Entry(parent)
        betrag_entry.grid(row=1, column=1)

        ttk.Label(parent, text="Kategorie").grid(row=2, column=0, sticky="w")
        kategorie_entry = ttk.Entry(parent)
        kategorie_entry.grid(row=2, column=1)

        ttk.Label(parent, text="Wertpapier").grid(row=3, column=0, sticky="w")
        wertpapier_entry = ttk.Entry(parent)
        wertpapier_entry.grid(row=3, column=1)

        ttk.Label(parent, text="Anteile").grid(row=4, column=0, sticky="w")
        anteile_entry = ttk.Entry(parent)
        anteile_entry.grid(row=4, column=1)

        ttk.Label(parent, text="Ausgangs Konto").grid(
            row=5,
            column=0,
            sticky="w"
            )
        konto_aus_entry = ttk.Entry(parent)
        konto_aus_entry.grid(row=5, column=1)

        ttk.Label(parent, text="Eingangs Konto").grid(
            row=6,
            column=0,
            sticky="w"
            )
        konto_ein_entry = ttk.Entry(parent)
        konto_ein_entry.grid(row=6, column=1)

        ttk.Label(parent, text="Start-Datum (YYYY-MM-DD)").grid(
            row=7,
            column=0,
            sticky="w"
            )
        start_entry = ttk.Entry(parent)
        start_entry.grid(row=7, column=1)

        ttk.Label(parent, text="Next Due (YYYY-MM-DD)").grid(
            row=8,
            column=0,
            sticky="w"
            )
        next_due_entry = ttk.Entry(parent)
        next_due_entry.grid(row=8, column=1)

        active_var = tk.BooleanVar()
        active_check = ttk.Checkbutton(
            parent,
            text="Aktiv",
            variable=active_var
            )
        active_check.grid(row=9, column=0, columnspan=2, sticky="w")

        ttk.Button(
            parent,
            text="Speichern",
            command=lambda: self.save_scheduler(
                name_entry.get(),
                betrag_entry.get(),
                kategorie_entry.get(),
                wertpapier_entry.get(),
                anteile_entry.get(),
                konto_aus_entry.get(),
                konto_ein_entry.get(),
                start_entry.get(),
                next_due_entry.get(),
                active_var.get()
            )).grid(row=10, column=0, columnspan=2, pady=10)

    def build_wertpapier_form(self, parent):
        ttk.Label(parent, text="Name").grid(row=0, column=0, sticky="w")
        name_entry = ttk.Entry(parent)
        name_entry.grid(row=0, column=1)

        ttk.Label(parent, text="ISIN").grid(row=1, column=0, sticky="w")
        isin_entry = ttk.Entry(parent)
        isin_entry.grid(row=1, column=1)

        ttk.Label(parent, text="Ticker").grid(row=2, column=0, sticky="w")
        ticker_entry = ttk.Entry(parent)
        ticker_entry.grid(row=2, column=1)

        ttk.Label(parent, text="Instrument").grid(row=3, column=0, sticky="w")
        instrument_entry = ttk.Entry(parent)
        instrument_entry.grid(row=3, column=1)

        ttk.Button(
            parent,
            text="Speichern",
            command=lambda: self.save_wertpapier(
                name_entry.get(),
                isin_entry.get(),
                ticker_entry.get(),
                instrument_entry.get()
            )).grid(row=4, column=0, columnspan=2, pady=10)

    def build_bild_form(self, parent):
        ttk.Label(parent, text="Bild auswählen und hochladen").pack(pady=10)
        ttk.Button(
            parent,
            text="Bild auswählen",
            command=self.upload_bild
            ).pack()

    def upload_bild(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Bilddateien", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            messagebox.showinfo("Bild hochgeladen", f"Pfad: {file_path}")
            print(f"Bildpfad: {file_path}")

    def save_einkauf(self, name, betrag, kategorie, konto, typ, datum):
        try:
            # Hier würdest du dein DB-Insert aufrufen
            betrag_decimal = Decimal(betrag)
            datum_parsed = datetime.strptime(datum, "%Y-%m-%d")
            print(f"Speichern: {name}, {betrag_decimal}, {kategorie}, {konto},\
                  {typ}, {datum_parsed}")
            # z.B. db.insert_kontobewegung(...)
            messagebox.showinfo("Erfolg", "Einkauf gespeichert")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def save_scheduler(self, name, betrag, kategorie,  wertpapier,
                    anteile, konto_aus, konto_ein, start, next_due, active):
        db = DBHandler()

        def find_or_create_id(name, load_func, insert_func):
            for row in load_func():
                if row[1] == name:
                    return row[0]
            insert_func(name)
            return db.load_kategorien()[-1][0]

        id_kategorie = find_or_create_id(
            kategorie,
            db.load_kategorien,
            db.insert_kategorie
            )
        id_konto_aus = find_or_create_id(
            konto_aus,
            db.load_konten,
            db.insert_konto
            )
        id_konto_ein = find_or_create_id(
            konto_ein,
            db.load_konten,
            db.insert_konto
            )

        # Wertpapier-ID ermitteln
        id_wertpapier = None
        for row in db.load_aktieninfo():
            if row[1] == wertpapier:
                id_wertpapier = row[0]
                break

        if id_wertpapier is None and wertpapier:
            messagebox.showinfo(f"Wertpapier '{wertpapier}' nicht gefunden.\
                                Bitte zuerst im Tab 'Wertpapier' anlegen.")
            db.close()
            return

        betrag_val = Decimal(betrag) if betrag else None
        anteile_val = Decimal(anteile) if anteile else None
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        next_due_dt = datetime.strptime(next_due, "%Y-%m-%d")

        eintrag = {
            "name": name,
            "betrag": betrag_val,
            "anteil": anteile_val,
            "wertpapier": id_wertpapier,
            "kategorie": id_kategorie,
            "ausgangs_konto_id": id_konto_aus,
            "eingangs_konto_id": id_konto_ein,
            "start_datum": start_dt,
            "next_due": next_due_dt,
            "active": int(active)
        }

        found = False
        for row in db.load_scheduler():
            if name == row[1] or (
                id_wertpapier is not None and id_wertpapier == row[4]
            ):
                db.update_scheduler(eintrag)
                found = True
                break

        if not found:
            db.insert_scheduler(eintrag)

        db.close()

    def save_wertpapier(self, name, isin, ticker, instrument):
        try:
            db = DBHandler()

            alle_wertpapiere = db.load_aktieninfo()
            vorhandenes_id = None

            for wp in alle_wertpapiere:
                if wp[1] == name or wp[2] == isin or wp[3] == ticker:
                    vorhandenes_id = wp[0]
                    break

            wertpapier = {
                "name": name,
                "isin": isin,
                "ticker": ticker,
                "instrument": instrument
            }

            if vorhandenes_id:
                db.update_aktieninfo(wertpapier, vorhandenes_id)
                messagebox.showinfo("Aktualisiert", "Wertpapier aktualisiert.")
            else:
                db.insert_wertpapierinfo(wertpapier)
                messagebox.showinfo("Erfolg", "Neues Wertpapier gespeichert.")

            db.close()

        except Exception as e:
            messagebox.showerror("Fehler", str(e))
