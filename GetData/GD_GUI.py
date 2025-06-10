import csv
import os
import tkinter as tk
from typing import get_origin, get_args, Union, Type, Optional, List, Dict
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
        Dynamically build a form for a given dataclass schema,
        using an editable Combobox for 'name' on three schemas.
    """
    entrance: Dict[str, ttk.Entry] = {}

    # layout grid: we'll increment row numbers
    row_idx = 0

    # determine if this schema supports monthly-repeat
    has_monthly = schema_class in (
        SchemaFixkosten, SchemaSparplan, SchemaEinkommen
        )

    # ----- NAME field: Combobox for three schemas, else Entry -----
    ttk.Label(parent, text="name").grid(row=row_idx, column=0, sticky="w")
    if schema_class in (SchemaFixkosten, SchemaSparplan, SchemaEinkommen):
        name_var = StringVar()
        names = load_template_names(schema_class)
        name_widget = ttk.Combobox(
            parent,
            textvariable=name_var,
            values=names,
            state="normal"  # editable
        )
        # on select or finish edit, populate rest
        name_widget.bind(
            "<<ComboboxSelected>>",
            lambda e: populate_from_template(
                schema_class, name_var.get(),
                entrance, monatlich_var, day_entry
            ))
        name_widget.bind(
            "<FocusOut>",
            lambda e: populate_from_template(
                schema_class, name_var.get(),
                entrance, monatlich_var, day_entry
            ))
    else:
        name_widget = ttk.Entry(parent)
    name_widget.grid(row=row_idx, column=1, sticky="ew")
    entrance["name"] = name_widget
    row_idx += 1

    # ----- all other dataclass fields (except name) -----
    for fld in [f for f in fields(schema_class) if f.name != "name"]:
        ttk.Label(parent, text=fld.name).grid(
            row=row_idx, column=0, sticky="w"
            )
        ent = ttk.Entry(parent)
        ent.grid(row=row_idx, column=1, sticky="ew")
        entrance[fld.name] = ent
        row_idx += 1

    # ----- monthly-repeat controls -----
    monatlich_var = tk.BooleanVar(value=False)
    if has_monthly:
        chk = ttk.Checkbutton(
            parent, text="Monatlich wiederholen", variable=monatlich_var
        )
        chk.grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=(10, 0))
        row_idx += 1

        ttk.Label(parent, text="Tag im Monat").grid(
            row=row_idx, column=0, sticky="w"
        )
        day_entry = ttk.Entry(parent)
        day_entry.grid(row=row_idx, column=1, sticky="ew")
        row_idx += 1
    else:
        # dummy so lambdas above don't break
        day_entry = ttk.Entry(parent)

    # ----- SAVE callback -----
    def safe():
        """
        Description:
            Gather form inputs, instantiate schema, save CSV + template.
        """
        try:
            # 1) build instance from form
            data = {}
            for fld in fields(schema_class):
                val = entrance[fld.name].get()
                if fld.name == "datum":
                    data[fld.name] = datetime.strptime(val, "%d.%m.%Y")
                else:
                    origin = get_origin(fld.type)
                    args = get_args(fld.type)
                    if origin is Union and Decimal in args:
                        data[fld.name] = Decimal(val) if val else None
                    elif fld.type is Decimal:
                        data[fld.name] = Decimal(val)
                    else:
                        data[fld.name] = val
            inst = schema_class(**data)

            # 2) compute missing preis/anteile for Sparplan
            if isinstance(inst, SchemaSparplan):
                kurs = fetch_low_yfinance_on_date(inst.ticker, inst.datum)
                if not inst.preis and inst.anteile:
                    inst.preis = inst.anteile * kurs
                elif inst.preis and not inst.anteile:
                    inst.anteile = inst.preis / kurs

            # 3) save main CSV
            speichern_callback(inst)

            # 4) handle template upsert (single or recurring)
            if monatlich_var.get() and has_monthly:
                # compute next_due from day_entry
                day = int(day_entry.get())
                today = datetime.today().date()
                # find first due > today
                next_due = today.replace(day=day)
                if next_due <= today:
                    next_due += relativedelta(months=1)
                upsert_template_entry(schema_class, inst, next_due, True)
            else:
                # single entry → next_due = inst.datum, active=False
                upsert_template_entry(
                    schema_class,
                    inst,
                    inst.datum.date(),
                    False
                )

            # 5) clear form
            for w in entrance.values():
                w.delete(0, tk.END)
            day_entry.delete(0, tk.END)
            monatlich_var.set(False)

        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    # ----- PLACE save button -----
    btn = ttk.Button(parent, text="Speichern", command=safe)
    btn.grid(row=row_idx, column=0, columnspan=2, pady=10, sticky="ew")


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
        On startup (or whenever called), read the Sparplan template CSV and
        for each active entry:
          1. Catch up all missed months by querying the live low price for
             each due date and writing a row to the main CSV.
          2. Advance next_due by one month each time until it falls > today.
          3. Rewrite the template CSV with the updated next_due for each entry.
    Input:
        None (uses global TEMPLATE_FILES, safe_csv, fetch_low_yfinance_on_date)
    Output:
        Appends rows into safe_sparplan.csv and updates templates_sparplan.csv.
    """
    today = datetime.today().date()
    tpl = TEMPLATE_FILES[SchemaSparplan]
    # build header: all dataclass fields + next_due + active
    headers = [f.name for f in fields(SchemaSparplan)] + ["next_due", "active"]

    # ensure the template file exists
    if not os.path.isfile(tpl):
        with open(tpl, 'w', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=headers).writeheader()

    updated_rows = []
    # read existing template entries
    with open(tpl, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # keep inactive entries untouched
            if row.get("active") != "True":
                updated_rows.append(row)
                continue

            # 1) build a base SchemaSparplan instance by converting types
            data = {}
            for fld in fields(SchemaSparplan):
                raw = row.get(fld.name)
                if raw is None:
                    continue
                if fld.name == "datum":
                    data[fld.name] = datetime.fromisoformat(raw)
                elif fld.type in (Decimal, Optional[Decimal]):
                    data[fld.name] = Decimal(raw) if raw else None
                else:
                    data[fld.name] = raw
            base_inst = SchemaSparplan(**data)

            # 2) catch-up loop for all months ≤ today
            due = datetime.fromisoformat(row["next_due"]).date()
            while due <= today:
                # always re-fetch live price and recalc shares
                kurs = fetch_low_yfinance_on_date(base_inst.ticker, due)
                shares = base_inst.preis / kurs

                # use dataclasses.replace to only change datum & anteile
                inst = replace(base_inst, datum=due, anteile=shares)
                safe_csv(inst)

                due += relativedelta(months=1)

            # 3) bump next_due forward to the first date > today
            row["next_due"] = due.isoformat()
            updated_rows.append(row)

    # rewrite the template CSV with updated next_due values
    with open(tpl, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(updated_rows)


# --- load_template_names ------------------
def load_template_names(schema_class: Type) -> List[str]:
    """
    Description:
        Read the template CSV for this schema and return all unique 'name'
        values.
    Input:
        schema_class -- one of SchemaFixkosten, SchemaSparplan, SchemaEinkommen
    Output:
        sorted list of strings
    """
    tpl = TEMPLATE_FILES[schema_class]
    if not os.path.exists(tpl):
        return []
    with open(tpl, newline="", encoding="utf-8") as f:
        return sorted({row["name"] for row in csv.DictReader(f)})


# --- populate_from_template ----------------
def populate_from_template(
    schema_class: Type,
    name: str,
    entrance: Dict[str, ttk.Entry],
    monatlich_var: tk.BooleanVar,
    day_entry: ttk.Entry
) -> None:
    """
    Description:
        If `name` exists in the template CSV, load that row into the form.
    Input:
        schema_class  -- the dataclass type
        name          -- selected name
        entrance      -- dict mapping field names to Entry widgets
        monatlich_var -- BooleanVar for monthly-repeat checkbox
        day_entry     -- Entry for day-of-month
    Output:
        fills the form in-place; returns None
    """
    tpl = TEMPLATE_FILES[schema_class]
    if not os.path.exists(tpl):
        return

    with open(tpl, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["name"] != name:
                continue
            # fill each field except "name"
            for fld, widget in entrance.items():
                if fld == "name":
                    continue
                widget.delete(0, tk.END)
                widget.insert(0, row.get(fld, ""))
            # set monthly checkbox and day
            active = row.get("active", "False") == "True"
            monatlich_var.set(active)
            # extract day from next_due
            if active and "next_due" in row:
                day = datetime.fromisoformat(row["next_due"]).day
                day_entry.delete(0, tk.END)
                day_entry.insert(0, f"{day:02}")
            return


# --- upsert_template_entry -----------------
def upsert_template_entry(
    schema_class: Type,
    inst,
    next_due: datetime.date,
    active: bool
) -> None:
    """
    Description:
        Insert or update a template-row for this instance:
        - If name exists, update 'next_due' and 'active'.
        - Else: append a new row.
    Input:
        schema_class -- the dataclass type
        inst         -- the instance just saved
        next_due     -- date for next_due field
        active       -- bool flag
    Output:
        mutates the template CSV on disk
    """
    tpl = TEMPLATE_FILES[schema_class]
    headers = [f.name for f in fields(schema_class)] + ["next_due", "active"]

    # read existing
    rows = []
    if os.path.exists(tpl):
        with open(tpl, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

    # build new row dict
    new = {}
    for fld in fields(schema_class):
        val = getattr(inst, fld.name)
        if isinstance(val, datetime):
            new[fld.name] = val.isoformat()
        else:
            new[fld.name] = "" if val is None else str(val)
    new["next_due"] = next_due.isoformat()
    new["active"] = "True" if active else "False"

    # upsert logic
    found = False
    for r in rows:
        if r["name"] == inst.name:
            r.update(new)
            found = True
            break
    if not found:
        rows.append(new)

    # write back
    with open(tpl, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


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
