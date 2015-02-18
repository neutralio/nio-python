#!/usr/bin/python
'''
Progress Bar - A Simple Progress Bar to use in the command line
Written in 2015 by Garrett Berg <garrett@cloudformdesign.com>

© Creative Commons 0
To the extent possible under law, the author(s) have dedicated all copyright
and related and neighboring rights to this software to the public domain
worldwide. THIS SOFTWARE IS DISTRIBUTED WITHOUT ANY WARRANTY.
<http://creativecommons.org/publicdomain/zero/1.0/>
'''

from __future__ import print_function
from sys import stdout
import time
import itertools

class Bar:
    def __init__(self, format, print=print):
        self._format = format
        self._print = print
        self._lastlen = 0

    def _clear(self):
        self._print('\r' + ' ' * self._lastlen, end='\r')  # clear last text

    def show(self, *args, **kwargs):
        self._clear()
        length = 20
        bar = "[{:%s}]" % length
        count = kwargs['count']
        total = kwargs['total']
        bar = bar.format("=" * int((count * length) // total) + '>')
        toprint = self._format.format(*args, bar=bar, **kwargs)
        self._print(toprint, end='\r')
        self._lastlen = len(toprint)
        stdout.flush()

    def stop(self, format, *args, **kwargs):
        self._clear()
        self._print(format.format(*args, **kwargs))
        stdout.flush()

class ProgressBar:
    BAR = ("{name:<25} | {body:<28} | "
           "{count:8.3g} /{total:<8.3g} | {min:2d}:{sec:>4.1f} {bar} "
           "{minl:2d}:{secl:>4.1f}")
    DONE = ("{name:<25} | {check:<4} | {sec:>4.1f} sec | {frequency:<7g} Hz | "
            "{count:8.3g} /{total:<8.3g}")

    def __init__(self, name='', format=None, print=print):
        if format is None:
            format = self.BAR
        self._print = print
        self._bar = Bar(format, print)
        self._name = name
        self._values = None

    def _stats(self):
        elapsed = time.time() - self._start
        freq = self._count / elapsed if elapsed > 0 else float('nan')
        left = freq * (self._total - self._count)
        return elapsed, freq, left

    def show(self, body=''):
        elapsed, freq, left = self._stats()
        kwargs = {
            'name': self._name,
            'body': body,
            'count': self._count,
            'total': self._total,
            'min': int(elapsed // 60),
            'sec': elapsed % 60,
            'minl': int(left // 60),
            'secl': left % 60,
        }
        self._bar.show(**kwargs)

    def stop(self):
        elapsed, freq, left = self._stats()
        kwargs = dict(
            name=self._name,
            check='done' if self._count == self._total else 'FAIL',
            sec=elapsed,
            frequency=freq,
            count=self._count,
            total=self._total
        )
        self._bar.stop(self.DONE, **kwargs)

    def update(self, value):
        '''update the progress bar to a specified value'''
        self._count = value
        self.show()

    def next(self):
        return self.__next__()

    def __next__(self):
        try:
            out = next(self._values)
        except StopIteration:
            self.stop()
            raise
        self._count += 1
        self.show()
        return out

    def __iter__(self, values = None):
        if self._values is not None:
            return self
        else:
            return itertools.count()

    def __call__(self, values):
        if isinstance(values, int):
            values = range(values)
        self._values = iter(values)
        self._total = len(values)
        self._count = 0
        self._start = time.time()
        return self


if __name__ == '__main__':
    bar = ProgressBar('test')
    for n in bar(range(10)):
        time.sleep(0.1)
    for n in bar(10):
        time.sleep(0.1)
