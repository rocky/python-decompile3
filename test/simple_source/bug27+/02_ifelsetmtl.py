# Issue #148 on 2.7
# Bug is in handling CONTINUE like JUMP_LOOP
# Similar code is probably found in a 2.7 stdlib. mapurl?
def reduce_url(url):
    atoms = []
    for atom in url:
        if atom == ".":
            pass  # JUMP_LOOP is patched as CONTINUE here
        elif atom == "..":
            atoms.push()
    return atoms
