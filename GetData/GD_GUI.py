import csv
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from decimal import Decimal
from typing import Type
from datetime import datetime
from dataclasses import fields
from GetData.GD_Schema import SchemaSparplan, SchemaFixkosten, \
    SchemaKaufitem, SchemaEinkommen


# --- Main GUI Function ---
def gui_main():
    root = tk.Tk()
    root.title("Finanz_Tracker")
    # root.geometry('400x400')

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    # Tab 1: Kaufitem
    frame_kauf = ttk.Frame(notebook)
    generat_formular(frame_kauf, SchemaKaufitem, safe_csv)
    notebook.add(frame_kauf, text="Kaufitem")

    # Tab 2: Fixkosten
    frame_fix = ttk.Frame(notebook)
    generat_formular(frame_fix, SchemaFixkosten, safe_csv)
    notebook.add(frame_fix, text="Fixkosten")

    # Tab 3: Sparplan
    frame_spar = ttk.Frame(notebook)
    generat_formular(frame_spar, SchemaSparplan, safe_csv)
    notebook.add(frame_spar, text="Sparplan")

    # Tab 4: Einkommen
    frame_einkommen = ttk.Frame(notebook)
    generat_formular(frame_einkommen, SchemaEinkommen, safe_csv)
    notebook.add(frame_einkommen, text="Einkommen")

    # Tab 5: Bild hochladen
    frame_bild = ttk.Frame(notebook)
    ttk.Label(frame_bild, text="Bild auswählen für OCR").pack(pady=10)
    ttk.Button(frame_bild, text="Bild hochladen", command=bild_upload).pack()
    notebook.add(frame_bild, text="Beleg hochladen")

    root.mainloop()


# --- Formualr generator ---
def generat_formular(parent, schema_class: Type, speichern_callback):
    entrance = {}
    for i, field in enumerate(fields(schema_class)):
        ttk.Label(parent, text=field.name).grid(row=i, column=0, sticky="w")
        entry = ttk.Entry(parent)
        entry.grid(row=i, column=1, sticky="ew")
        entrance[field.name] = entry

    def safe():
        try:
            value = {}
            for field in fields(schema_class):
                val = entrance[field.name].get()
                if field.type == Decimal:
                    value[field.name] = Decimal(val)
                else:
                    value[field.name] = val
            instance = schema_class(**value)
            speichern_callback(instance)

            for entry in entrance.values():
                entry.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    ttk.Button(
        parent,
        text="Speichern",
        command=safe).grid(
            row=len(fields(schema_class)),
            column=0,
            columnspan=2,
            pady=10
            )


# --- Bildupload ---
def bild_upload():
    filepath = filedialog.askopenfilename(
        filetypes=[("Bilder", "*.png *.jpg *.jpeg")]
        )
    if filepath:
        messagebox.showinfo("Bild hochgeladen", f"Pfad: {filepath}")
        print(f"Bildpfad: {filepath}")


# --- CSV Safe ---
FILES = {
    SchemaKaufitem: "safe_kaufitem.csv",
    SchemaFixkosten: "safe_fixkosten.csv",
    SchemaSparplan: "safe_sparplan.csv",
    SchemaEinkommen: "safe_einkommen.csv",
}


def safe_csv(instance):
    filepath = FILES[type(instance)]
    fieldname = [f.name for f in fields(instance)]
    file_exists = os.path.isfile(filepath)

    with open(filepath, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldname)
        if not file_exists:
            writer.writeheader()
        # Datum in ISO-Form umwandeln
        daten_dict = {
            k: (v.isoformat() if isinstance(v, datetime) else str(v))
            for k, v in instance.__dict__.items()
        }
        writer.writerow(daten_dict)
