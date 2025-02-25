import os, sys

tf = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.py.txt"), "r")
TEMPLATE_STRING = tf.read()
tf.close()

class LiVidModel:
	def __init__(self):
		self.patch_triggers = {}
		self.patches = {}
		self.current_patch_name = None
	
	def add_patch(self, name):
		self.patches[name] = {
			"text": str(TEMPLATE_STRING),
			"values": {
				"fake1": ("Fake 1", 0.1, 1.0, 5.0),
				"fake2": ("Fake 2", 0.1, 0.5, 10.0),
				"fake3": ("Fake 3", 0.1, 2.0, 30.0),
			},
			"mappings": []
		}
	
	def get_current_patch(self):
		if self.current_patch_name is not None:
			return self.patches[self.current_patch_name]
		else: return None

	def remove_patch(self, name):
		self.patches.pop(name)