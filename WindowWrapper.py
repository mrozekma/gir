class WindowWrapper:
	def __init__(self, win):
		self.win = win

	def __getattr__(self, n):
		return getattr(self.win, n)

	def addline(self, *args):
		self.addstr(*args)
		if len(args) in (2, 4): # Looking for the 'attr' argument
			rest = self.getmaxyx()[1] - self.getyx()[1] - 1
			self.addstr(' ' * rest, args[-1])

	def fillline(self, row, attr):
		self.addline(row, 0, '', attr)
