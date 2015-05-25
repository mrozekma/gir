import curses
from curses.textpad import rectangle, Textbox
import git, gitdb
import os
import sys

from Color import color
from OutputBuffer import OutputBuffer
from WindowWrapper import WindowWrapper

# .git/rebase-merge/git-rebase-todo
# Rebase 8440467..f559b2f onto 9ed5d48
# Going to attach the commit *after* 8440467, through f559b2f, after 9ed5d48

def main(win, filename):
	win = WindowWrapper(win)
	curses.curs_set(0) # Hide cursor
	height, width = win.getmaxyx()

	commands = {
		'pick': color.white_blue,
		'reword': color.blue,
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

	max_length = max(19 + len(commit.summary) for command, commit in commits)
	command_win = WindowWrapper(curses.newpad(len(commits), max_length))
	for i, (command, commit) in enumerate(commits):
		clr = commands[command]
		command_win.fillline(i, clr)
		command_win.addstr(i, 2, commit.hexsha[:7], clr)
		command_win.addstr(i, 11, command, color.bold(clr))
		command_win.addstr(i, 18, commit.summary, clr)

	command_sel = 0
	command_scroll_row, command_scroll_col = 0, 0
	win.noutrefresh()
	while True:
		command_win.refresh(command_scroll_row, command_scroll_col, 0, 0, 20 - 1, width - 1)
		if command_scroll_col == 0:
			if command_scroll_row > 0:
				win.addch(0, 0, curses.ACS_UARROW, clr)
			if command_scroll_row + 20 < len(commits):
				win.addch(19, 0, curses.ACS_DARROW, clr)
			win.addch(command_sel - command_scroll_row, 0, curses.ACS_RARROW, clr)

		c = win.getch()
		if c == curses.KEY_UP and command_sel > 0:
			command_sel -= 1
			if command_sel < command_scroll_row:
				command_scroll_row = command_sel
		elif c == curses.KEY_DOWN and command_sel + 1 < len(commits):
			command_sel += 1
			if command_sel > command_scroll_row + 19:
				command_scroll_row = command_sel - 19
		elif c == curses.KEY_LEFT and command_scroll_col > 0:
			command_scroll_col -= 1
		elif c == curses.KEY_RIGHT and command_scroll_col + width + 1 < max_length:
			command_scroll_col += 1

if len(sys.argv) != 2:
	print "Expected a single filename"
	exit(1)

ob = OutputBuffer()
try:
	curses.wrapper(main, sys.argv[1])
finally:
	print ob.done()
