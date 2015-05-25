class ScrollWindow:
	def __init__(self, win, drawcb, scrollVertical = True, scrollHorizontal = True):
		self.win = win
		self.drawcb = drawcb
		self.scrollVertical = scrollVertical
		self.scrollHorizontal = scrollHorizontal
		self.row = 1
		self.height, self.width = win.getmaxyx()
