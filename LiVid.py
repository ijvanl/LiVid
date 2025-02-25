from __init__ import *

if __name__ == '__main__':
	app = LiVidApp()

	dev = lidar.LidarDevice(app.postprocess_fn)

	app.run(dev)