import tkinter as tk
from GetData.GD_GUI import FinazntTrackerGUI


def main():
    root = tk.Tk()
    FinazntTrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
