import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Type
from GetData.GD_Schema import SchemaSparplan, SchemaFixkosten, SchemaKaufitem


def gui_main():
    root = tk.Tk()
    root.title("Finanz_Tracker")
    #root.geometry('400x400')

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    #Tab 1: Kaufitem
    frame_kauf = ttk.Frame(notebook)
    erstelle_formular(frame_kauf, SchemaKaufitem, lambda x: print("Kaufitem:", x))
    notebook.add(frame_kauf, text="Kaufitem")



def erstelle_formular(parent, schema_klasse: Type, speichern_callback):
