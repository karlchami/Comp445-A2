#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import collections
import curses, curses.ascii, curses.panel
import random
import time
import sys
import select
import threading

#gui = None

class LockedCurses(threading.Thread):
    """
    This class essentially wraps curses operations so that they
    can be used with threading.  Noecho and cbreak are always in
    force.

    Usage: call start() to start the thing running.  Then call
    newwin, new_panel, mvaddstr, and other standard curses functions
    as usual.

    Call teardown() to end.

    Note: it's very important that the user catch things like
    keyboard interrupts and redirect them to make us shut down
    cleanly.  (This could be improved...)
    """
    def __init__(self, debug=False):
        super(LockedCurses, self).__init__()
        self._lock = threading.Lock()

        # ick!
        self.panel = self

        # generic cond var
        self._cv = threading.Condition(self._lock)
        # results-updated cond var
        self._resultcv = threading.Condition(self._lock)

        self._workqueue = collections.deque()
        self._starting = False
        self._running = False
        self._do_quit = False
        self._screen = None
        self._ticket = 0
        self._served = -1
        self._result = {}
        self._debug = debug

    def start(self):
        assert(not self._running)
        assert(self._screen is None)
        self._screen = curses.initscr()
        with self._lock:
            self._starting = True
            super(LockedCurses, self).start()
            while self._starting:
                self._cv.wait()
        self.debug('started!')

    def run(self):
        # This happens automatically inside the new thread; do not
        # call it yourself!
        self.debug('run called!')
        assert(not self._running)
        assert(self._screen is not None)
        curses.savetty()
        curses.noecho()
        curses.cbreak()
        self._running = True
        self._starting = False
        with self._lock:
            self._cv.notifyAll()
            while not self._do_quit:
                while len(self._workqueue) == 0 and not self._do_quit:
                    self.debug('run: waiting for work')
                    self._cv.wait()
                # we have work to do, or were asked to quit
                self.debug('run: len(workq)={}'.format(len(self._workqueue)))
                while len(self._workqueue):
                    ticket, func, args, kwargs = self._workqueue.popleft()
                    self.debug('run: call {}'.format(func))
                    self._result[ticket] = func(*args, **kwargs)
                    self._served = ticket
                    self.debug('run: served {}'.format(ticket))
                    self._resultcv.notifyAll()

            # Quitting!  NB: resettty should do all of this for us
            # curses.nocbreak()
            # curses.echo()
            curses.resetty()
            curses.endwin()
            self._running = False
            self._cv.notifyAll()

    def teardown(self):
        with self._lock:
            if not self._running:
                return
            self._do_quit = True
            while self._running:
                self._cv.notifyAll()
                self._cv.wait()

    def debug(self, string):
        if self._debug:
            sys.stdout.write(string + '\r\n')

    def _waitch(self):
        """
        Wait for a character to be readable from sys.stdin.
        Return True on success.

        Unix-specific (ugh)
        """
        while True:
            with self._lock:
                if not self._running:
                    return False
            # Wait about 0.1 second for a result.  Really, should spin
            # off a thread to do this instead.
            l = select.select([sys.stdin], [], [], 0.1)[0]
            if len(l) > 0:
                return True
            # No result: go around again to recheck self._running.

    def refresh(self):
        s = self._screen
        if s is not None:
            self._passthrough('refresh', s.refresh)

    def _passthrough(self, fname, func, *args, **kwargs):
        self.debug('passthrough: fname={}'.format(fname))
        with self._lock:
            self.debug('got lock, fname={}'.format(fname))
            if not self._running:
                raise ValueError('called {}() while not running'.format(fname))
            # Should we check for self._do_quit here?  If so,
            # what should we return?
            ticket = self._ticket
            self._ticket += 1
            self._workqueue.append((ticket, func, args, kwargs))
            self.debug('waiting for ticket {}, fname={}'.format(ticket, fname))
            while self._served < ticket:
                self._cv.notifyAll()
                self._resultcv.wait()
            return self._result.pop(ticket)

    def newwin(self, *args, **kwargs):
        w = self._passthrough('newwin', curses.newwin, *args, **kwargs)
        return WinWrapper(self, w)

    def new_panel(self, win, *args, **kwargs):
        w = win._interior
        p = self._passthrough('new_panel', curses.panel.new_panel, w,
                              *args, **kwargs)
        return LockedWrapper(self, p)


class LockedWrapper(object):
    """
    Wraps windows and panels and such.  locker is the LockedCurses
    that we need to use to pass calls through.
    """
    def __init__(self, locker, interior_object):
        self._locker = locker
        self._interior = interior_object

    def __getattr__(self, name):
        i = self._interior
        l = self._locker
        a = getattr(i, name)
        if callable(a):
            l.debug('LockedWrapper: pass name={} as func={}'.format(name, a))
            # return a function that uses passthrough
            return lambda *args, **kwargs: l._passthrough(name, a,
                                                          *args, **kwargs)
        # not callable, just return the attribute directly
        return a


class WinWrapper(LockedWrapper):
    def getch(self):
        """
        Overrides basic getch() call so that it's specifically *not*
        locked.  This is a bit tricky.
        """
        # (This should really test for nodelay mode too though.)
        l = self._locker
        ok = l._waitch()
        if ok:
            return l._passthrough('getch', self._interior.getch)
        return curses.ERR

    def getstr(self, y, x, maxlen):
        self.move(y, x)
        l = 0
        s = ""
        while True:
            self.refresh()
            c = self.getch()
            if c in (curses.ERR, ord('\r'), ord('\n')):
                break
            if c == ord('\b'):
                if len(s) > 0:
                    s = s[:-1]
                    x -= 1
                    self.addch(y, x, ' ')
                    self.move(y, x)
            else:
                if curses.ascii.isprint(c) and len(s) < maxlen:
                    c = chr(c)
                    s += c
                    self.addch(c)
                    x += 1
        return s


class ui(object):
    def __init__(self):
        self.curses = LockedCurses()
        self.curses.start()
        #self.stdscr.keypad(1)

        self.win1 = self.curses.newwin(10, 50, 0, 0)
        self.win1.border(0)
        self.pan1 = self.curses.panel.new_panel(self.win1)
        self.win2 = self.curses.newwin(10, 50, 0, 0)
        self.win2.border(0)
        self.pan2 = self.curses.panel.new_panel(self.win2)
        self.win3 = self.curses.newwin(10, 50, 12, 0)
        self.win3.border(0)
        self.pan3 = self.curses.panel.new_panel(self.win3)

        self.win1.addstr(1, 1, "Window 1")
        self.win2.addstr(1, 1, "Window 2")
        self.win3.addstr(1, 1, "Input: ")

        self.output_str = ""
        self.stop_requested = False

    def refresh(self):
        #self.curses.panel.update_panels()
        self.win3.refresh()
        self.win2.refresh()
        self.win1.refresh()
        #self.curses.refresh()

    def quit_ui(self):
        self.curses.teardown()
        print ("UI quitted")


def worker_output(ui):
    count = 0
    running = 1

    while not ui.stop_requested:
        ui.win2.addstr(3, 1, str(count)+": "+str(int(round(random.random()*999))))
        ui.win2.addstr(4, 1, str(running))

        ui.win2.addstr(5, 1, ui.output_str)

        ui.refresh()
        time.sleep(0.1)
        count += 1


class feeder:
    # Fake U.I feeder
    def __init__(self):
        self.running = False
        self.ui = ui()
        self.count = 0

    def stop(self):
        self.running = False

    def run(self):
        self.running = True
        try:
            self.feed()
        finally:
            self.ui.quit_ui()

    def feed(self):
        t = threading.Thread(target=worker_output, args=(self.ui,))
        t.start()

        user_input = ""

        while not user_input.startswith("q"):
            self.ui.win3.addstr(1, 1, "Input: ")
            user_input = self.ui.win3.getstr(1, 8, 20)
            self.ui.win3.addstr(2, 1, "Output: %s" % user_input)
            self.ui.refresh()
            self.ui.win3.clear()

            time.sleep(.2)
        self.ui.stop_requested = True
        t.join()


if __name__ == "__main__":
    f = feeder()
    f.run()