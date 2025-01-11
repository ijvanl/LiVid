import cv2, numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageChops


def bound_depth(value, lower, upper, contrast):
	return np.clip((1.0 - abs((value - lower) / (upper - lower))) * contrast, 0.0, 1.0)

def resize_img(arr, size):
	return np.float32(np.array(Image.fromarray(np.uint8(arr)).resize((size[1], size[0])))) / 255.0

def gs_to_rgb(arr):
	return np.stack((arr, ) * 3, axis=-1)

def zoom_at(img, x, y, zoom):
	w, h = img.size
	zoom2 = zoom * 2
	img = img.crop(
		(x - w / zoom2, y - h / zoom2, 
		x + w / zoom2, y + h / zoom2)
	)
	return img.resize((w, h))

last_image = None


BLACK_IMG = Image.fromarray(np.zeros((640, 480))).convert("RGB").resize(
		(640, 480), resample=2
	)

class PostProcessFunctionsBuiltIn:
	def pp_video(rgb, depth, confidence, intrinsic_matrix, pp, zoom_x, zoom_y, zoom_amount):
		screen = np.swapaxes(rgb, 0, 1)

		screen_img = Image.fromarray(screen).convert("RGB").resize((640, 480), resample=2)
		screen_img = screen_img.transpose(Image.FLIP_LEFT_RIGHT)
		screen_img = zoom_at(screen_img, zoom_x, zoom_y, zoom_amount)

		screen = np.array(screen_img)

		return screen

	def pp_depth(rgb, depth, confidence, intrinsic_matrix, pp, zoom_x, zoom_y, zoom_amount):
		screen = np.swapaxes(depth, 0, 1)
		screen = np.clip(screen, 0.0, 1.0)

		screen_img = Image.fromarray(screen * 255).convert("RGB").resize((640, 480), resample=2)
		screen_img = screen_img.transpose(Image.FLIP_LEFT_RIGHT)
		screen_img = zoom_at(screen_img, zoom_x, zoom_y, zoom_amount)

		screen = np.array(screen_img)

		return screen

	def pp_outline(rgb, depth, confidence, intrinsic_matrix, pp, zoom_x, zoom_y, zoom_amount):
		global last_image

		screen = np.swapaxes(depth, 0, 1)

		screen = bound_depth(screen, pp.depth_lower_bound, pp.depth_upper_bound, pp.depth_contrast)
		screen = np.clip(screen, 0.0, 1.0)

		screen_img = Image.fromarray(screen * 255).convert("RGB").filter(
			ImageFilter.FIND_EDGES
		).resize((640, 480), resample=2)

		screen_img = screen_img.transpose(Image.FLIP_LEFT_RIGHT)
		screen_img = zoom_at(screen_img, zoom_x, zoom_y, zoom_amount)

		if last_image is None:
			last_image = screen_img

		last_image = Image.blend(last_image, BLACK_IMG, pp.fade_coeff)
		screen_img = ImageChops.add(screen_img, last_image.filter(ImageFilter.GaussianBlur(pp.blur_radius)))

		last_image = screen_img

		screen = np.array(screen_img)

		return screen

	def pp_lamp_smoke(rgb, depth, confidence, intrinsic_matrix, pp, zoom_x, zoom_y, zoom_amount):
		global last_image

		screen = np.swapaxes(depth, 0, 1)

		screen = bound_depth(screen, pp.depth_lower_bound, pp.depth_upper_bound, pp.depth_contrast)
		screen = np.clip(screen, 0.0, 1.0)

		screen_img = Image.fromarray(screen * 255).convert("RGB").resize(
			(640, 480), resample=2
		)

		screen_img = screen_img.transpose(Image.FLIP_LEFT_RIGHT)
		screen_img = zoom_at(screen_img, zoom_x, zoom_y, zoom_amount)

		if last_image is None:
			last_image = screen_img

		last_image = Image.blend(last_image, BLACK_IMG, pp.fade_coeff)
		screen_img = ImageChops.add(screen_img, last_image.filter(ImageFilter.GaussianBlur(pp.blur_radius)))

		last_image = screen_img

		screen = np.array(screen_img)

		return screen

	def pp_lamp_nosmoke(rgb, depth, confidence, intrinsic_matrix, pp, zoom_x, zoom_y, zoom_amount):
		global last_image

		screen = np.swapaxes(depth, 0, 1)

		screen = bound_depth(screen, pp.depth_lower_bound, pp.depth_upper_bound, pp.depth_contrast)
		screen = np.clip(screen, 0.0, 1.0)

		screen_img = Image.fromarray(screen * 255).convert("RGB").resize(
			(640, 480), resample=2
		)

		screen_img = screen_img.transpose(Image.FLIP_LEFT_RIGHT)
		screen_img = zoom_at(screen_img, zoom_x, zoom_y, zoom_amount)

		if last_image is None:
			last_image = screen_img

		screen = np.array(screen_img)

		return screen