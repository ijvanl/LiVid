from PIL import Image
import numpy as np

from postprocess import *
from postprocess.tools import *


class PPFunctionName(PPFunction): # TODO: change the name of this class (to something cool!)
	def __init__(self):
		super().__init__(use_streams=[PP_DEPTH])
	
	def values(self):
		return {
			"value_1": ("Value 1", 0.1, 1.0, 10.0),
		}
	
	def postprocess(self, pp):
		screen = self.depth(pp.value_1)
		return screen # Finally, return your final processed image.


__PP_FUNCTIONS_SUITE__ = [PPFunctionName()] # TODO: update with the new, cool name of my class