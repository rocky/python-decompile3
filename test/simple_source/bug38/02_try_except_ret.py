# The bug in 3.8 was handling the returns in the before and in the except blocks.
# This kind of code generation starts in 3.8
# The return value may appear on either side of a POP_BLOCK and
# the try_except will be missing not have specific COME_FROMs since
# there are returns
def set_reg(name, winreg):
    try:
        value = winreg(name)
        return value
    except WindowsError:
        return None


def get_reg(name, winreg):
    try:
        winreg(name)
        return True
    except WindowsError:
        return winreg
