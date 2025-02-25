import tkinter as tk
import tkinter.ttk as ttk
from . import aux
import os, sys

from model import *

tf = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.py.txt"), "r")
TEMPLATE_STRING = tf.read()
tf.close()

def run_gui(model):
	from . import main_window

	root = tk.Tk()
	root.withdraw()

	t = main_window.LiVidMainWindow(root, model)

	root.mainloop()