from PIL import Image, ImageFilter, ImageOps, ImageChops
import numpy as np

from postprocess import *
from postprocess.tools import *

# Post-processor function classes must start with "PP".
class PPFunctionName(PPFunction): # TODO: change the name of this class (to something cool!)
	def __init__(self):
		# We want to use depth information, so we're calling `super().__init__` with `use_streams=[pp.PP_DEPTH]`.
		# Otherwise, we could add `PP_RGB` to get regular camera input as well.
		super().__init__(use_streams=[PP_DEPTH])
	
	def values(self):
		return {
			# These are the modifiable values displayed to the user.
			# name		 display name	minimum		default		maximum
			"value_1":	("Value 1",		0.1,		1.0,		10.0),
			"value_2":	("Value 2",		0.1,		1.0,		10.0),
		}
	
	def postprocess(self, pp):
		# Write your image processing code here.

		# We defined "value_1" as user-accessible in `values()`,
		# so we can access it here as a member of `pp`.
		color = color_field(pp.value_1, 0.0, 0.0)
		#                   hue         sat  value
		
		# `self.depth(contrast)` returns a frame of depth data from the LiDAR sensor.
		# We could also call `self.rgb()` for a frame of video from the camera, if we'd used `PP_RGB` (see above).
		mask = self.depth(pp.value_2)

		screen = ImageChops.multiply(color, mask)
		return screen # Finally, return your final processed image.