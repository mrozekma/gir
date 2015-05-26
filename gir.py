import curses
from curses.textpad import rectangle, Textbox
import git, gitdb
import os
import sys

from Color import color
from OutputBuffer import OutputBuffer
from ScrollWindow import ScrollWindow
from WindowWrapper import WindowWrapper

# .git/rebase-merge/git-rebase-todo
# Rebase 8440467..f559b2f onto 9ed5d48
# Going to attach the commit *after* 8440467, through f559b2f, after 9ed5d48

MAX_COMMITS = 20

def title(str):
	sys.__stdout__.write("\033]0;%s\007" % str)

def main(win, filename):
	title('gir')
	win = WindowWrapper(win)
	curses.curs_set(0) # Hide cursor
	height, width = win.getmaxyx()

	commands = {
		'pick': color.white_blue,
		'reword': color.black_yellow,
		'edit': color.blue,
		'squash': color.blue,
		'fixup': color.blue,
		'exec' : color.blue,
	}

	repo = git.Repo(filename)

	with open(os.path.join(repo.git_dir, 'rebase-merge', 'onto')) as f:
		onto = f.read().strip()
	onto = repo.commit(onto)

	# Parse the file; don't load commit objects yet
	commits = []
	with open(filename) as f:
		for line in f:
			if line.strip() == '' or line[0] == '#':
				continue
			parts = line.split(' ', 2)
			if len(parts) != 3:
				raise RuntimeError("Malformed line: %s" % line)
			command, shahash, _ = parts
			if command not in commands:
				raise RuntimeError("Malformed line (bad command): %s" % line)
			commits.append((command, shahash))

	# Load all the commit objects at once and update 'commits'
	# I'm not positive this will get them all, so if necessary load missing objects individually
	objects = {commit.hexsha[:7]: commit for commit in repo.iter_commits(commits[-1][1], max_count = len(commits) + 1)}
	commits = [(command, objects[shahash] if shahash in objects else repo.commit(shahash)) for command, shahash in commits]

	def commandDraw(win, row, data):
		command, commit = data
		clr = commands[command]
		win.fillline(row, clr)
		win.addstr(row, 2, commit.hexsha[:7], clr)
		win.addstr(row, 11, command, color.bold(clr))
		win.addstr(row, 18, commit.summary, clr)
	def commandLen(data):
		command, commit = data
		return 18 + len(commit.summary)
	commandWin = ScrollWindow(commits, commandDraw, commandLen, 1, 1, width - 2, min(len(commits), MAX_COMMITS), True)

	def detailDraw(win, row, data):
		win.addstr(row, 0, "Line %d" % row)
	def detailLen(data):
		return len("Line %d" % data)
	detailWin = ScrollWindow(list(range(200)), detailDraw, detailLen, commandWin.targetHeight + 3, 1, width - 2, height - commandWin.targetHeight - 5)

	focusedWin = commandWin
	win.noutrefresh()
	while True:
		win.boundedBorder(0, 0, commandWin.targetHeight + 1, width - 1, 'Commits', color.white if focusedWin == commandWin else color.grey)
		command, commit = commandWin.getSelectedData()
		win.boundedBorder(commandWin.targetHeight + 2, 0, height - 2, width - 1, commit.hexsha, color.white if focusedWin == detailWin else color.grey)
		win.refresh() # Draw now so stuff before the right edge doesn't get overwritten later
		commandWin.draw()
		detailWin.draw()
		if commandWin.canScrollUp(literally = True):
			command, commit = commandWin.getFirstData()
			win.addch(1, 1, curses.ACS_UARROW, commands[command])
		if commandWin.canScrollDown(literally = True):
			command, commit = commandWin.getLastData()
			win.addch(commandWin.targetHeight, 1, curses.ACS_DARROW, commands[command])
		command, commit = commandWin.getSelectedData()
		win.addch(commandWin.selection - commandWin.curRow + 1, 1, curses.ACS_RARROW, commands[command])

		# Keypress
		c = win.getch()
		if c in (curses.KEY_UP, ord('k')) and focusedWin.canScrollUp():
			focusedWin.scrollUp()
		elif c in (curses.KEY_DOWN, ord('j')) and focusedWin.canScrollDown():
			focusedWin.scrollDown()
		elif c in (curses.KEY_LEFT, ord('h')) and focusedWin.canScrollLeft():
			focusedWin.scrollLeft()
		elif c in (curses.KEY_RIGHT, ord('l')) and focusedWin.canScrollRight():
			focusedWin.scrollRight()
		elif c == 336: # Shift+Up
			focusedWin = commandWin
		elif c == 337: # Shift+Down
			focusedWin = detailWin
		elif c in (curses.KEY_PPAGE, ord('K')):
			if focusedWin.canScrollUp(True):
				focusedWin.scrollUp(focusedWin.targetHeight, True)
			elif focusedWin.canScrollUp():
				focusedWin.scrollUp(focusedWin.targetHeight)
		elif c in (curses.KEY_NPAGE, ord('J')):
			if focusedWin.canScrollDown(True):
				focusedWin.scrollDown(focusedWin.targetHeight, True)
			elif focusedWin.canScrollDown():
				focusedWin.scrollDown(focusedWin.targetHeight)
		elif c == ord('H') and focusedWin.canScrollLeft():
			focusedWin.scrollLeft(focusedWin.targetWidth)
		elif c == ord('L') and focusedWin.canScrollRight():
			focusedWin.scrollRight(focusedWin.targetWidth)
		elif c == curses.KEY_HOME:
			if focusedWin.canScrollLeft():
				focusedWin.scrollLeft(focusedWin.width)
			elif focusedWin.canScrollUp():
				focusedWin.scrollUp(focusedWin.height)
		elif c == curses.KEY_END and focusedWin.canScrollDown():
			focusedWin.scrollDown(focusedWin.height)

if len(sys.argv) != 2:
	print "Expected a single filename"
	exit(1)

ob = OutputBuffer()
try:
	curses.wrapper(main, sys.argv[1])
finally:
	print ob.done()
	title('')
