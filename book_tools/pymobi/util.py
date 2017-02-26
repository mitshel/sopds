
def toStr(src, coding='utf-8'):
    """ for python3 """
    return src.decode(coding)


def toByte(src, coding='utf-8'):
    """ for python3 """
    return src.encode(coding)


def hexdump(src, length=16, sep='.'):
    """
    hexdump implementation in Python
    paste from https://gist.github.com/7h3rAm/5603718
    """
    FILTER = ''.join([
        (len(repr(chr(x))) == 3) and chr(x) or sep
        for x in range(256)
    ])
    lines = []
    for c in range(0, len(src), length):
        chars = src[c:c + length]
        if isinstance(chars, bytes):
            hhex = ' '.join(["%02x" % x for x in chars])
        else:
            hhex = ' '.join(["%02x" % ord(x) for x in chars])
        if len(hhex) > 24:
            hhex = "%s %s" % (hhex[:24], hhex[24:])
        if isinstance(chars, bytes):
            printable = ''.join([
                "%s" % ((x <= 127 and FILTER[x]) or sep)
                for x in chars
            ])
        else:
            printable = ''.join([
                "%s" % ((ord(x) <= 127 and FILTER[ord(x)]) or sep)
                for x in chars
            ])
        lines.append("%08x:  %-*s  |%s|\n" % (c, length * 3, hhex, printable))
    print(''.join(lines))


def decodeVarint(vint):
    """ backward-encoded Mobipocket variable-width integer. """
    fint = 0
    bitpos = 0
    while bitpos < 28:
        fint |= ((vint & 0x7f) << bitpos)
        if vint & 0x80:
            break
        vint >>= 8
        bitpos += 7
    return fint


def encodeVarint(fint):
    """ backward-encoded Mobipocket variable-width integer. """
    vint = 0
    bitpos = 0
    while bitpos < 32:
        vint |= ((fint & 0x7f) << bitpos)
        if fint < 127:
            vint |= (0x80 << bitpos)
            break
        fint >>= 7
        bitpos += 8
    return vint
