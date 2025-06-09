import csv
import os
import tkinter as tk
from typing import get_origin, get_args, Union, Type
from tkinter import ttk, filedialog, messagebox, StringVar
from decimal import Decimal
from datetime import datetime
from dataclasses import fields, replace
from dateutil.relativedelta import relativedelta
from GetData.GD_Schema import SchemaSparplan, SchemaFixkosten, \
    SchemaKaufitem, SchemaEinkommen
from Depot.D_api import fetch_low_yfinance_on_date


def gui_main():
    """
    Description:
        Launch the main Tkinter window with tabs for each schema.
    Input:
        None
    Output:
        Starts the Tk mainloop; returns None.
    """
    root = tk.Tk()
    root.title("Finanz_Tracker")

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    # Tab 1: Kaufitem (no monthly repeat UI)
    frame_kauf = ttk.Frame(notebook)
    generat_formular(frame_kauf, SchemaKaufitem, safe_csv)
    notebook.add(frame_kauf, text="Kaufitem")

    # Tab 2: Fixkosten (with monthly repeat UI)
    frame_fix = ttk.Frame(notebook)
    generat_formular(frame_fix, SchemaFixkosten, safe_csv)
    notebook.add(frame_fix, text="Fixkosten")

    # Tab 3: Sparplan (with monthly repeat UI)
    frame_spar = ttk.Frame(notebook)
    generat_formular(frame_spar, SchemaSparplan, safe_csv)
    notebook.add(frame_spar, text="Sparplan")

    # Tab 4: Einkommen (with monthly repeat UI)
    frame_einkommen = ttk.Frame(notebook)
    generat_formular(frame_einkommen, SchemaEinkommen, safe_csv)
    notebook.add(frame_einkommen, text="Einkommen")

    # Tab 5: Upload receipt image
    frame_bild = ttk.Frame(notebook)
    ttk.Label(frame_bild, text="Select image for OCR").pack(pady=10)
    ttk.Button(frame_bild, text="Upload image", command=bild_upload).pack()
    notebook.add(frame_bild, text="Beleg hochladen")

    root.mainloop()


def generat_formular(parent, schema_class: Type, speichern_callback):
    """
    Description:
        Dynamically build a form for a given dataclass schema.
    Input:
        parent            -- Tkinter frame to attach the widgets
        schema_class      -- the dataclass type to generate fields for
        speichern_callback-- function to call for saving one-off entries
    Output:
        Attaches UI elements to `parent`; returns None.
    """
    # load existing names into dropdown
    names = load_unique_names(schema_class)
    selected = StringVar()
    combo = ttk.Combobox(parent, textvariable=selected,
                         values=names, state="readonly")
    combo.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
    combo.bind('<<ComboxSelected>>',
               lambda _: load_latest_entry(schema_class,
                                           selected.get(), entrance))

    # create one Entry widget per dataclass field
    entrance = {}
    for i, field in enumerate(fields(schema_class), start=1):
        ttk.Label(parent, text=field.name).grid(row=i, column=0, sticky="w")
        entry = ttk.Entry(parent)
        entry.grid(row=i, column=1, sticky="ew")
        entrance[field.name] = entry

    last_row = i

    # Only show monthly-repeat controls for these three schemas:
    has_monthly = schema_class in (
        SchemaFixkosten, SchemaSparplan, SchemaEinkommen)
    if has_monthly:
        cb_row = last_row + 1
        monatlich_var = tk.BooleanVar()
        ttk.Checkbutton(parent,
                        text="Monatlich wiederholen",
                        variable=monatlich_var).grid(
                            row=cb_row, column=0, columnspan=2,
                            sticky="w", pady=(10, 0))

        tag_row = cb_row + 1
        ttk.Label(parent, text="Tag im Monat").grid(
            row=tag_row, column=0, sticky="w")
        day_entry = ttk.Entry(parent)
        day_entry.grid(row=tag_row, column=1, sticky="ew")
    else:
        # dummy placeholders so safe() can refer to them safely
        monatlich_var = tk.BooleanVar(value=False)
        day_entry = ttk.Entry(parent)  # never actually used

    # --- save callback inside the form ---
    def safe():
        """
        Description:
            Gather form inputs, instantiate the schema, and save entries.
            If monthly repeat is checked, backfill all past months up to today,
            recalc shares for Sparplan on each iteration, and write a single
            template entry for the next_due date.
        Input:
            uses closure vars: entrance, schema_class, monatlich_var, day_entry
        Output:
            Writes rows into the main CSVs and the template CSV; clears fields.
        """
        try:
            # 1) build the instance from Entry fields
            data = {}
            for fld in fields(schema_class):
                val = entrance[fld.name].get()
                if fld.name == "datum":
                    data[fld.name] = datetime.strptime(val, "%d.%m.%Y")
                    continue
                origin = get_origin(fld.type)
                args = get_args(fld.type)
                if origin is Union and Decimal in args:
                    data[fld.name] = Decimal(val) if val else None
                elif fld.type is Decimal:
                    data[fld.name] = Decimal(val)
                else:
                    data[fld.name] = val

            inst = schema_class(**data)

            # 2) for Sparplan: always ensure anteile are calculated if missing
            if isinstance(inst, SchemaSparplan):
                if inst.anteile in ("", None) and inst.preis:
                    print("Datum: ", inst.datum)
                    print("Preis: ", inst.preis)
                    price = fetch_low_yfinance_on_date(
                        inst.ticker, inst.datum)
                    inst.anteile = inst.preis / price

            # 3) if monthly-repeat is active for allowed schemas:
            if monatlich_var.get() and has_monthly:
                # determine day of month to repeat on
                day = int(day_entry.get())
                start = inst.datum.date()
                today = datetime.today().date()

                # backfill or catch-up loop
                current = start
                while current <= today:
                    if isinstance(inst, SchemaSparplan):
                        # recalc shares on each monthly date
                        print("Datum: ", inst.datum)
                        print("Preis: ", inst.preis)
                        price = fetch_low_yfinance_on_date(
                            inst.ticker, current)
                        shares = inst.preis / price
                        new_inst = replace(inst, datum=current, anteile=shares)
                    else:
                        new_inst = replace(inst, datum=current)

                    safe_csv(new_inst)
                    # move to next month, same day
                    # (relativedelta handles overflow)
                    current += relativedelta(months=1)
                    current = current.replace(day=day)

                # write exactly one template entry for the *next* due date
                next_due = current  # first date > today
                tpl = TEMPLATE_FILES[schema_class]
                headers = (
                    [f.name for f in fields(schema_class)] +
                    ["next_due", "active"]
                )
                file_exists = os.path.isfile(tpl)

                with open(tpl, 'a', newline='', encoding='utf-8') as tf:
                    writer = csv.DictWriter(tf, fieldnames=headers)
                    if not file_exists:
                        writer.writeheader()

                    # build the row from the instance + next_due/active
                    row_data = {}
                    for fld in fields(schema_class):
                        val = getattr(inst, fld.name)
                        # convert datetime to ISO, others to str
                        if isinstance(val, datetime):
                            row_data[fld.name] = val.isoformat()
                        else:
                            row_data[fld.name] = str(val)

                    row_data["next_due"] = next_due.isoformat()
                    row_data["active"] = "True"

                    writer.writerow(row_data)
            else:
                # single entry for non-repeating or Kaufitem
                safe_csv(inst)

            # 4) clear all UI fields
            for e in entrance.values():
                e.delete(0, tk.END)
            day_entry.delete(0, tk.END)
            monatlich_var.set(False)

        except Exception as er:
            messagebox.showerror("Error", str(er))

    # place the Save button
    save_row = (tag_row if has_monthly else last_row) + 1
    ttk.Button(parent, text="Speichern", command=safe).grid(
        row=save_row, column=0, columnspan=2, pady=10, sticky="ew")


def bild_upload():
    """
    Description:
        Open a file dialog to select an image for OCR.
    Input:
        None
    Output:
        Displays a messagebox with the selected path; prints to console.
    """
    filepath = filedialog.askopenfilename(
        filetypes=[("Images", "*.png *.jpg *.jpeg")])
    if filepath:
        messagebox.showinfo("Image uploaded", f"Path: {filepath}")
        print(f"Image path: {filepath}")


def safe_csv(instance):
    """
    Description:
        Append a single dataclass-instance row to its corresponding CSV.
        For Sparplan, if anteile is missing, recalc based on price and date.
    Input:
        instance -- one instance of SchemaKaufitem/Fixkosten/Sparplan/Einkommen
    Output:
        Writes one row to the CSV file; returns None.
    """
    if isinstance(instance, SchemaSparplan):
        # recalc shares if still missing
        if instance.preis and not instance.anteile:
            print("Datum: ", instance.datum)
            print("Preis: ", instance.preis)
            price = fetch_low_yfinance_on_date(
                instance.ticker, instance.datum)
            instance.anteile = instance.preis / price

    path = FILES[type(instance)]
    cols = [f.name for f in fields(instance)]
    file_exists = os.path.isfile(path)

    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        if not file_exists:
            writer.writeheader()
        row = {
            k: (v.isoformat() if isinstance(v, datetime) else str(v))
            for k, v in instance.__dict__.items()
        }
        writer.writerow(row)


def load_unique_names(schema_class):
    """
    Description:
        Read the CSV for a schema and collect unique 'name' values.
    Input:
        schema_class -- the dataclass type
    Output:
        list of str, sorted
    """
    path = FILES[schema_class]
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as f:
        names = {row['name'] for row in csv.DictReader(f)}
    return sorted(names)


def load_latest_entry(schema_class, name, entrance):
    """
    Description:
        Load the most recent CSV row matching `name` into the form fields.
    Input:
        schema_class -- the dataclass type
        name         -- the selected name to look up
        entrance     -- dict mapping field names to ttk.Entry widgets
    Output:
        Fills the Entry widgets in-place; returns None.
    """
    path = FILES[schema_class]
    latest = None
    latest_dt = datetime.min
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['name'] != name:
                continue
            d = datetime.fromisoformat(row['datum'])
            if d > latest_dt:
                latest_dt, latest = d, row

    if latest:
        for k, widget in entrance.items():
            widget.delete(0, tk.END)
            widget.insert(0, latest.get(k, ""))


def generate_recurring_entries():
    """
    Description:
        On program start, read each TEMPLATE_FILE and generate
        any due rows into the main CSV, then bump next_due forward.
    Input:
        None
    Output:
        Mutates both main CSVs and template CSVs; returns None.
    """
    today = datetime.today().date()
    for schema_cls, tpl in TEMPLATE_FILES.items():
        # ensure template exists with dynamic headers
        headers = [f.name for f in fields(schema_cls)] + ["next_due", "active"]
        if not os.path.isfile(tpl):
            with open(tpl, 'w', newline='', encoding='utf-8') as f:
                csv.DictWriter(f, fieldnames=headers).writeheader()

        updated_rows = []
        with open(tpl, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                if row.get("active") != "True":
                    updated_rows.append(row)
                    continue
                due = datetime.fromisoformat(row["next_due"]).date()
                # emit one row per missed month
                while due <= today:
                    data = {
                        **{fld: row[fld] for fld in row
                           if fld not in ("next_due", "active")},
                        "datum": due.isoformat()
                    }
                    inst = schema_cls(**data)
                    safe_csv(inst)
                    due += relativedelta(months=1)
                # schedule next
                row["next_due"] = due.isoformat()
                updated_rows.append(row)

        # rewrite template file
        with open(tpl, 'w', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=headers).writeheader()
            csv.DictWriter(f, fieldnames=headers).writerows(updated_rows)


# --- file mappings ---
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
