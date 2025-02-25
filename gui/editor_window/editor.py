import tkinter as tk
import tkinter.ttk as ttk

import idlelib.colorizer as ic
import idlelib.percolator as ip
import re

class PatchTextEditor(ttk.Frame):
	def __init__(self, master, modified_event=None):
		super().__init__(master)
		self.text_modified = False
		self.modified_event = modified_event

		self.text = tk.Text(
			self, bd=0,
			highlightthickness=0,
			height=1,
			font=("Courier Prime Sans", 13)
		)
		self.text.pack(expand=True, fill=tk.BOTH)
		self.cdg = ic.ColorDelegator()
		self.cdg.prog = re.compile(r'\b(?P<MYGROUP>tkinter)\b|' + ic.make_pat().pattern, re.S)
		self.cdg.idprog = re.compile(r'\s+(\w+)', re.S)

		self.cdg.tagdefs['MYGROUP'] = {'foreground': '#7F7F7F'}

		# These five lines are optional. If omitted, default colours are used.
		self.cdg.tagdefs['COMMENT'] = {'foreground': '#999999'}
		self.cdg.tagdefs['KEYWORD'] = {'foreground': '#007F00'}
		self.cdg.tagdefs['BUILTIN'] = {'foreground': '#7F7F00'}
		self.cdg.tagdefs['STRING'] = {'foreground': '#7F3F00'}
		self.cdg.tagdefs['DEFINITION'] = {'foreground': '#007F7F'}

		ip.Percolator(self.text).insertfilter(self.cdg)

		font = tk.font.Font(font=self.text['font'])
		tab = font.measure('    ')

		self.text.config(tabs=tab, undo=True)

		self.text.bind("<<Modified>>", self.on_modified)
		self.text.bind("<Return>", self.auto_indent)
	
	def on_modified(self, event):
		if (self.text_modified == False) and (self.modified_event is not None):
			self.modified_event(event)
		self.text_modified = True
		self.resize_to_length()
		self.text.edit_modified(False)

	def resize_to_length(self):
		self.text["height"] = int(self.text.index("end-1c").split(".")[0])

	def get_text(self):
		return self.text.get("1.0", "end-1c") # from line 1 column 0 (1.0), to end minus trailing \n (end-1c)

	def open_text(self, contents):
		old_text = self.get_text()
		self.text.delete("1.0", "end") # delete from line 1 column 0 (1.0), to end
		self.text.insert("end", contents)
		return old_text
	
	def auto_indent(self, event):
		# get leading whitespace from current line
		line = self.text.get("insert linestart", "insert")
		match = re.match(r'^(\s+)', line)
		whitespace = match.group(0) if match else ""

		# insert the newline and the whitespace
		self.text.insert("insert", f"\n{whitespace}")

		# return "break" to inhibit default insertion of newline
		return "break"