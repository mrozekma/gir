import curses

from Color import color


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

	def boundedBorder(self, topRow, leftCol, bottomRow, rightCol, title = None, clr = 0):
		self.addch(topRow, leftCol, curses.ACS_ULCORNER, clr)
		self.addch(topRow, rightCol, curses.ACS_URCORNER, clr)
		self.addch(bottomRow, leftCol, curses.ACS_LLCORNER, clr)
		self.addch(bottomRow, rightCol, curses.ACS_LRCORNER, clr)
		for i in range(leftCol + 1, rightCol):
			self.addch(topRow, i, curses.ACS_HLINE, clr)
			self.addch(bottomRow, i, curses.ACS_HLINE, clr)
		for i in range(topRow + 1, bottomRow):
			self.addch(i, leftCol, curses.ACS_VLINE, clr)
			self.addch(i, rightCol, curses.ACS_VLINE, clr)
		if title:
			self.addstr(topRow, leftCol + 2, " %s " % title, color.bold(clr))
