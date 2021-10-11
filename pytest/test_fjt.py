#!/usr/bin/env python


def bug(state, slotstate):
    if state:
        if slotstate is not None:
            for key, value in slotstate.items():
                setattr(state, key, 2)


# From 2.7 disassemble
# Problem is not getting while, because
# COME_FROM not added
def bug_loop(disassemble, tb=None):
    if tb:
        try:
            tb = 5
        except AttributeError:
            raise RuntimeError
        while tb:
            tb = tb.tb_next
    disassemble(tb)
