import cv2, numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageChops
from postprocess import *

class PPVideo(PatchClass):
	def __init__(self):
		super().__init__(use_streams=[PP_RGB])
	
	def postprocess(self, values):
		return self.rgb()

class PPDepth(PatchClass):
	def __init__(self):
		super().__init__(use_streams=[PP_DEPTH])
	
	def values(self):
		return { "contrast": ("Contrast", 0.1, 1.0, 10) }

	def postprocess(self, pp):
		return self.depth(pp.contrast)

class PPSilhouette(PatchClass):
	def __init__(self):
		super().__init__(use_streams=[PP_DEPTH])
	
	def values(self):
		return {
			"contrast": ("Contrast", 0.1, 1.0, 10.0),
			"lower_bound": ("Lower bound distance", 0.1, 0.5, 10.0),
			"upper_bound": ("Upper bound distance", 0.1, 1.25, 10.0),
			"fade_coeff": ("Outline fade speed", 0.1, 0.25, 1.0),
			"smoke_radius": ("Smoke radius", 1.0, 5.0, 20.0),
		}

	def postprocess(self, pp):
		return self.depth_bound(pp.lower_bound, pp.upper_bound, pp.contrast)

class PPOutline(PatchClass):
	def __init__(self):
		super().__init__(use_streams=[PP_DEPTH])
	
	def values(self):
		return {
			"contrast": ("Contrast", 0.1, 1.0, 10.0),
			"lower_bound": ("Lower bound distance", 0.1, 0.75, 10.0),
			"upper_bound": ("Upper bound distance", 0.1, 1.25, 10.0),
			"fade_coeff": ("Outline fade speed", 0.1, 0.25, 1.0),
			"smoke_radius": ("Smoke radius", 1.0, 5.0, 20.0),
		}

	def postprocess(self, pp):
		screen = self.depth_bound(pp.lower_bound, pp.upper_bound, pp.contrast)

		screen = screen.filter(ImageFilter.FIND_EDGES)

		last_image = Image.blend(self.last_image(), BLACK_IMG, pp.fade_coeff)
		screen = ImageChops.add(screen, last_image.filter(ImageFilter.GaussianBlur(pp.smoke_radius)))

		return screen


__PP_FUNCTIONS_SUITE__ = [PPVideo(), PPDepth(), PPSilhouette(), PPOutline()]


def bound_depth(value, lower, upper, contrast):
	return np.clip((1.0 - abs((value - lower) / (upper - lower))) * contrast, 0.0, 1.0)

def resize_img(arr, size):
	return np.float32(np.array(Image.fromarray(np.uint8(arr)).resize((size[1], size[0])))) / 255.0

def gs_to_rgb(arr):
	return np.stack((arr, ) * 3, axis=-1)

def zoom_at(img, x, y, zoom):
	w, h = img.size
	zoom2 = zoom * 2
	img = img.crop((x - w / zoom2, y - h / zoom2, x + w / zoom2, y + h / zoom2))
	return img.resize((w, h))


BLACK_IMG = Image.fromarray(np.zeros((640, 480))).convert("RGB").resize((640, 480), resample=2)
