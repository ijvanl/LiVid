import cv2, numpy as np, colorsys
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

BLACK_IMG = Image.new("RGB", (640, 480), color="black")
WHITE_IMG = Image.new("RGB", (640, 480), color="white")


def lamp_fg_color(depth, bg_img, pp, zoom_x, zoom_y, zoom_amount):
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

	color_img = Image.new(
		"RGB", (640, 480),
		color=tuple([int(c * 255) for c in colorsys.hsv_to_rgb(pp.accent_hue / 360, 1.0, 1.0)])
	)

	mask_img = ImageChops.subtract(bg_img, screen_img)
	color_screen = ImageChops.multiply(screen_img, color_img)
	screen_img = ImageChops.add(mask_img, color_screen)
	#screen_img = ImageChops.difference(screen_img, last_image)

	last_image = screen_img

	screen = np.array(screen_img)

	return screen


class PPBasic:
	def pp_color_white_bg(rgb, depth, confidence, intrinsic_matrix, pp, zoom_x, zoom_y, zoom_amount):
		return lamp_fg_color(depth, WHITE_IMG, pp, zoom_x, zoom_y, zoom_amount)

	def pp_color_black_bg(rgb, depth, confidence, intrinsic_matrix, pp, zoom_x, zoom_y, zoom_amount):
		return lamp_fg_color(depth, BLACK_IMG, pp, zoom_x, zoom_y, zoom_amount)

	def pp_bleach(rgb, depth, confidence, intrinsic_matrix, pp, zoom_x, zoom_y, zoom_amount):
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

		color_img = Image.new(
			"RGB", (640, 480),
			color=tuple([int(c * 255) for c in colorsys.hsv_to_rgb(pp.accent_hue / 360, 1.0, 1.0)])
		)

		fade_color = Image.blend(WHITE_IMG, color_img, pp.fade_coeff)
		last_image = Image.blend(last_image, BLACK_IMG, pp.fade_coeff)
		last_image = ImageChops.multiply(last_image, fade_color)
		screen_img = ImageChops.add(screen_img, last_image)
		#screen_img = ImageChops.difference(screen_img, last_image)

		last_image = screen_img

		screen = np.array(screen_img)

		return screen

	def pp_solarize_bw(rgb, depth, confidence, intrinsic_matrix, pp, zoom_x, zoom_y, zoom_amount):
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

		color_img = Image.new(
			"RGB", (640, 480),
			color=tuple([int(c * 255) for c in colorsys.hsv_to_rgb(pp.accent_hue / 360, 1.0, 1.0)])
		)

		last_image = Image.blend(last_image, BLACK_IMG, pp.fade_coeff)
		screen_img = ImageChops.add_modulo(screen_img, last_image)
		#screen_img = ImageChops.difference(screen_img, last_image)

		last_image = screen_img

		screen = np.array(screen_img)

		return screen

	def pp_solarize_colour(rgb, depth, confidence, intrinsic_matrix, pp, zoom_x, zoom_y, zoom_amount):
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

		color_img = Image.new(
			"RGB", (640, 480),
			color=tuple([int(c * 255) for c in colorsys.hsv_to_rgb(pp.accent_hue / 360, 1.0, 1.0)])
		)

		fade_color = Image.blend(WHITE_IMG, color_img, pp.fade_coeff / 3)
		last_image = Image.blend(last_image, BLACK_IMG, pp.fade_coeff)
		last_image = ImageChops.multiply(last_image, fade_color)
		screen_img = ImageChops.add_modulo(screen_img, last_image.filter(ImageFilter.GaussianBlur(pp.blur_radius)))
		#screen_img = ImageChops.difference(screen_img, last_image)

		last_image = screen_img

		screen = np.array(screen_img)

		return screen


__PP_FUNCTIONS_SUITE__ = PPBasic