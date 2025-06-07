import csv
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, StringVar
from decimal import Decimal
from typing import Type
from datetime import datetime
from dataclasses import fields
from dateutil.relativedelta import relativedelta
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
    names = load_unique_names(schema_class)
    selected = StringVar()
    combo = ttk.Combobox(
        parent, textvariable=selected, values=names, state="readonly"
        )
    combo.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
    combo.bind('<<ComboxSelected>>', lambda _: load_latest_entry(
        schema_class, selected.get(), entrance)
        )

    entrance = {}
    for i, field in enumerate(fields(schema_class), start=1):
        ttk.Label(parent, text=field.name).grid(row=i, column=0, sticky="w")
        entry = ttk.Entry(parent)
        entry.grid(row=i, column=1, sticky="ew")
        entrance[field.name] = entry

    last_row = i
    cb_row = last_row + 1
    monatlich_var = tk.BooleanVar()
    ttk.Checkbutton(
        parent,
        text="Monatlich wiederholen",
        variable=monatlich_var
    ).grid(row=cb_row, column=0, columnspan=2, sticky="w", pady=(10, 0))

    tag_row = cb_row + 1
    ttk.Label(parent, text="Tag im Monat").grid(
        row=tag_row, column=0, sticky="w"
    )
    day_entry = ttk.Entry(parent)
    day_entry.grid(row=tag_row, column=1, sticky="ew")

    def safe():
        try:
            # build the instance
            value = {}
            for field in fields(schema_class):
                val = entrance[field.name].get()
                if field.type == Decimal:
                    value[field.name] = Decimal(val)
                else:
                    value[field.name] = val
            instance = schema_class(**value)

            # save the one-off
            speichern_callback(instance)

            # if recurring, append to template CSV
            if monatlich_var.get():
                tpl_file = TEMPLATE_FILES[schema_class]
                headers = ['name', 'amount', 'next_due', 'active']
                file_exists = os.path.isfile(tpl_file)

                today = datetime.today().date()
                day = int(day_entry.get())
                next_month = today + relativedelta(months=1)
                try:
                    next_due = next_month.replace(day=day)
                except ValueError:
                    last_day = (next_month + relativedelta(day=31)).day
                    next_due = next_month.replace(day=last_day)

                # Make sure this block is indented UNDER the 'with'
                with open(tpl_file, 'a', newline='', encoding='utf-8') as tf:
                    writer = csv.DictWriter(tf, fieldnames=headers)
                    if not file_exists:
                        writer.writeheader()
                    writer.writerow({
                        'name': instance.name,
                        'amount': str(instance.preis),
                        'next_due': next_due.isoformat(),
                        'active': 'True'
                    })

            # clear all fields after saving
            for entry in entrance.values():
                entry.delete(0, tk.END)
            day_entry.delete(0, tk.END)
            monatlich_var.set(False)

        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    save_row = tag_row + 1
    ttk.Button(
        parent,
        text="Speichern",
        command=safe
    ).grid(
        row=save_row,
        column=0,
        columnspan=2,
        pady=10,
        sticky="ew"
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

TEMPLATE_FILES = {
    SchemaFixkosten: "templates_fixkosten.csv",
    SchemaSparplan:  "templates_sparplan.csv",
    SchemaEinkommen: "templates_einkommen.csv",
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


def load_unique_names(schema_class):
    filepath = FILES[schema_class]
    if not os.path.exists(filepath):
        return []
    names = set()
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            names.add(row['name'])
    return sorted(names)


def load_latest_entry(schema_class, name, entrance):
    filepath = FILES[schema_class]
    latest = None
    latest_date = datetime.min
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['name'] != name:
                continue
            d = datetime.fromisoformat(row['datum'])
            if d > latest_date:
                latest_date = d
                latest = row

    if latest:
        for key, entry in entrance.items():
            entry.delete(0, tk.END)
            entry.insert(0, latest.get(key, ''))


def generate_recurring_entries():
    today = datetime.today().date()
    for schema_class, tpl_file in TEMPLATE_FILES.items():
        if not os.path.isfile(tpl_file):
            headers = ['name', 'amount', 'next_due', 'active']
            with open(tpl_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
            continue

        updated = []
        with open(tpl_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('active', 'False') != 'True':
                    updated.append(row)
                    continue

                next_due = datetime.fromisoformat(row['next_due']).date()
                while next_due <= today:
                    kwargs = {
                        'name': row['name'],
                        'preis': Decimal(row['amount']),
                        'datum': next_due
                    }
                    inst = schema_class(**kwargs)
                    safe_csv(inst)
                    next_due += relativedelta(months=1)

                row['next_due'] = next_due.isoformat()
                updated.append(row)
        if not updated:
            continue

        with open(tpl_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=updated[0].keys())
            writer.writeheader()
            writer.writerows(updated)
