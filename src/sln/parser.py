"""Core Lexer, Parser, and data structures."""

from numbers import Number

def memoize(f):
    memo = {}
    def helper(*args):
        if args not in memo:
            memo[args] = f(*args)
        return memo[args]
    return helper

class SLNError(Exception):
    def __init__(self, msg):
        self.history = []
        self.msg = msg

    def print(self):
        for msg in self.history:
            print(msg)
        print("error: " + self.msg)

    def append(self, msg):
        self.history.append(msg)

class Symbol:
    def __init__(self):
        pass

    def __repr__(self):
        return self.string

    @classmethod
    def new(cls, text):
        assert(type(text) == str)
        self = cls()
        self.string = text
        return self

@memoize
def symbol(str):
    return Symbol.new(str)

class Symbols:
    CurlyList = symbol('curly-list')
    SquareList = symbol('square-list')
    DictSeparator = symbol(':')
    DictBinder = symbol('=')
    Plain = symbol('plain')

################################################################################

class Token:
    Empty = -1
    EOF = 0
    Open = '('
    Close = ')'
    SquareOpen = '['
    SquareClose = ']'
    CurlyOpen = '{'
    CurlyClose = '}'
    String = '"'
    BlockString = 'B'
    Quote = '\''
    Symbol = 'S'
    Escape = '\\'
    Separator = ';'
    Integer = 'I'
    Real = 'F'

TOKEN_TERMINATORS = "()[]{}\"';#,"

integer_literal_suffixes = set("i8 i16 i32 i64 u8 u16 u32 u64 usize".strip().split())
real_literal_suffixes = set("f32 f64".strip().split())

def isspace(c):
    return c in ' \t\n\r'

def parse_hexchar(c):
    if (c >= '0') and (c <= '9'):
        return ord(c) - ord('0')
    elif (c >= 'a') and (c <= 'f'):
        return ord(c) - ord('a') + 10
    elif (c >= 'A') and (c <= 'F'):
        return ord(c) - ord('A') + 10
    else:
        return -1

def unescape_string (buf):
    dst = ""
    src = 0
    l = len(buf)
    while src < l:
        c = buf[src]
        if c == '\\' and ((src+1) < l):
            c = buf[src+1]
            if c == 'n':
                dst += '\n'
                src += 2
                continue
            elif c == 't':
                dst += '\t'
                src += 2
                continue
            elif c == 'r':
                dst += '\r'
                src += 2
                continue
            elif c == '"':
                dst += '"'
                src += 2
                continue
            elif c == '\n':
                src += 2
                # skip until next non whitespace character
                while src < l:
                    c = buf[src]
                    if c in ' \t':
                        src += 1
                    else:
                        break
                continue
            elif c == 'x' and ((src+3) < l):
                c0 = parse_hexchar(buf[src+2])
                c1 = parse_hexchar(buf[src+3])
                if (c0 >= 0) and (c1 >= 0):
                    dst += chr((c0 << 4) | c1)
                    src += 3
                    continue
        dst += c
        src += 1
    return dst

class Lexer:
    def __init__ (self):
        self.cursor = 0
        self.next_cursor = 0
        self.lineno = 1
        self.next_lineno = 1
        self.line = 0
        self.next_line = 0

    def column(self):
        return self.cursor - self.line + 1

    def next_column(self):
        return self.next_cursor - self.next_line + 1

    def get_string(self):
        return unescape_string(self.value[1:-1])

    def get_block_string(self):
        strip_col = self.column() + 4
        buf = self.value
        dest = ""
        start = 4
        end = len(buf)
        assert (end >= 0)
        # strip trailing whitespace up to the first LF after content
        last_lf = end
        while end != start:
            c = buf[end - 1]
            if not isspace(c):
                break
            if c == '\n':
                last_lf = end
            end -= 1
        end = last_lf
        while start != end:
            c = buf[start]
            start += 1
            dest += c
            if c == '\n':
                # strip leftside column
                for i in range(1, strip_col):
                    if start == end:
                        break
                    if (buf[start] != ' ') and (buf[start] != '\t'):
                        break
                    start += 1
        return (Symbols.Plain, dest)

    def get_symbol(self):
        return symbol(self.value)

    def get_integer(self):
        return int(self.value)

    def get_real(self):
        return float(self.value)

    def tokenize(state, text):
        state.buffer = text

        def location_error(msg):
            print(text)
            raise Exception("%i:%i: error: %s" % (state.lineno,state.column(),msg))

        def is_eof():
            return state.next_cursor == len(text)

        def chars_left():
            return len(text) - state.next_cursor

        def next():
            x = text[state.next_cursor]
            state.next_cursor = state.next_cursor + 1
            return x

        def next_token():
            state.lineno = state.next_lineno
            state.line = state.next_line
            state.cursor = state.next_cursor

        def newline():
            state.next_lineno = state.next_lineno + 1
            state.next_line = state.next_cursor

        def select_string():
            state.value = text[state.cursor:state.next_cursor]

        def reset_cursor():
            state.next_cursor = state.cursor

        def try_fmt_split(s):
            l = s.split(':')
            if len(l) == 2:
                return l
            else:
                return s,None

        def is_integer(s):
            tail = None
            if ':' in s:
                s,tail = try_fmt_split(s)
            if tail and not (tail in integer_literal_suffixes):
                return False
            if not s:
                return False
            if s[0] in '+-':
                s = s[1:]
            nums = '0123456789'
            if s.startswith('0x'):
                nums = nums + 'ABCDEFabcdef'
                s = s[2:]
            elif s.startswith('0b'):
                nums = '01'
                s = s[2:]
            elif len(s) > 1 and s[0] == '0':
                return False
            if len(s) == 0:
                return False
            for k,c in enumerate(s):
                if not c in nums:
                    return False
            return True

        def is_real(s):
            tail = None
            if ':' in s:
                s,tail = try_fmt_split(s)
            if tail and not (tail in real_literal_suffixes):
                return False
            if not s: return False
            if s[0] in '+-':
                s = s[1:]
            if s == 'inf' or s == 'nan':
                return True
            nums = '0123456789'
            if s.startswith('0x'):
                nums = nums + 'ABCDEFabcdef'
                s = s[2:]
            if len(s) == 0:
                return False
            for k,c in enumerate(s):
                if c == 'e':
                    return is_integer(s[k + 1:])
                if c == '.':
                    s = s[k + 1:]
                    for k,c in enumerate(s):
                        if c == 'e':
                            return is_integer(s[k + 1:])
                        if not c in nums:
                            return False
                    break
                if not c in nums:
                    return False
            return True

        def read_symbol():
            escape = False
            while True:
                if is_eof():
                    break
                c = next()
                if escape:
                    if c == '\n':
                        newline()
                    escape = False
                elif c == '\\':
                    escape = True
                elif isspace(c) or (c in TOKEN_TERMINATORS):
                    state.next_cursor = state.next_cursor - 1
                    break
            select_string()

        def read_string(terminator):
            escape = False
            while True:
                if is_eof():
                    location_error("unterminated sequence")
                    break
                c = next()
                if c == '\n' and not escape:
                    # 0.10
                    # newline()
                    # 0.11
                    location_error("unexpected line break in string")
                    break
                if escape:
                    escape = False
                elif c == '\\':
                    escape = True
                elif c == terminator:
                    break
            select_string()

        def read_block(indent):
            col = state.column() + indent
            while True:
                if is_eof():
                    break
                next_col = state.next_column()
                c = next()
                if c == '\n':
                    newline()
                elif not isspace(c) and (next_col <= col):
                    state.next_cursor = state.next_cursor - 1
                    break
            select_string()

        def read_block_string():
            next()
            next()
            next()
            read_block(3)

        def read_comment():
            read_block(0)

        def read_whitespace():
            while True:
                if is_eof():
                    break
                c = next()
                if c == '\n':
                    newline()
                elif not isspace(c):
                    state.next_cursor = state.next_cursor - 1
                    break
            select_string()

        while True:
            next_token()
            if is_eof():
                yield Token.EOF
                return
            c = next()
            cur = state.cursor
            if c == '\n':
                newline()
            if isspace(c):
                read_whitespace()
                continue
            elif c == '#':
                #token = Token.Comment
                read_comment()
                continue
            elif c == '(':
                token = Token.Open
                select_string()
            elif c == ')':
                token = Token.Close
                select_string()
            elif c == '[':
                token = Token.SquareOpen
                select_string()
            elif c == ']':
                token = TokenSquareClose
                select_string()
            elif c == '{':
                token = Token.CurlyOpen
                select_string()
            elif c == '}':
                token = Token.CurlyClose
                select_string()
            elif c == '\\':
                token = Token.Escape
                select_string()
            elif c == '"':
                token = Token.String
                if ((chars_left() >= 3)
                    and (text[state.next_cursor+0] == '"')
                    and (text[state.next_cursor+1] == '"')
                    and (text[state.next_cursor+2] == '"')):
                    token = Token.BlockString
                    read_block_string()
                else:
                    read_string(c)
            elif c == ';':
                token = Token.Separator
                select_string()
            elif c == '\'':
                token = Token.Symbol
                read_symbol()
            elif c == ',':
                token = Token.Symbol
                select_string()
            else:
                read_symbol()
                if is_integer(state.value):
                    token = Token.Integer
                elif is_real(state.value):
                    token = Token.Real
                else:
                    token = Token.Symbol
            yield token

class ListBuilder:
    def __init__ (self):
        self.prev = []
        self.eol = 0

    def append (self, value):
        self.prev.append(value)

    def is_empty(self):
        return len(self.prev) == 0

    def reset_start(self):
        self.eol = len(self.prev)

    def split(self, anchor):
        self.prev = [tuple(self.prev[:self.eol])]
        self.reset_start()

    def get_result(self):
        return tuple(self.prev)

_active_anchor = None
def trace(anchor):
    global _active_anchor
    _active_anchor = anchor


def error(msg, *args):
    raise SLNError(msg.format(*args))

def tag(anchor, obj):
    return obj

class Parser:
    def __init__(self, text):
        self.state = Lexer()
        self.tokenizer = self.state.tokenize(text)

    def anchor (self):
        pass

    def read_token (self):
        self.token = next(self.tokenizer)

    def trace (self, anchor):
        pass

    # parses a list to its terminator and returns a handle to the first cell
    def parse_list (self, end_token):
        start_anchor = self.anchor()
        builder = ListBuilder()
        self.read_token()
        while True:
            token = self.token
            if token == end_token:
                break
            elif token == Token.Escape:
                column = self.state.column()
                self.read_token()
                builder.append(self.parse_naked(column, end_token))
            elif token == Token.EOF:
                trace(self.anchor())
                error("format: parenthesis never closed\n{} opened here", start_anchor)
            elif token == Token.Separator:
                builder.split(self.anchor())
                self.read_token()
            else:
                builder.append(self.parse_any())
                self.read_token()
        return builder.get_result()

    # parses the next sequence and returns it wrapped in a cell that points to prev
    def parse_any(self):
        assert self.token != Token.EOF
        anchor = self.anchor()
        if self.token == Token.Open:
            return tag(anchor, self.parse_list(Token.Close))
        elif self.token == Token.SquareOpen:
            return tag(anchor, [tag(anchor, Symbols.SquareList)] +
                    self.parse_list(Token.SquareClose))
        elif self.token == Token.CurlyOpen:
            return tag(anchor, [tag(anchor, Symbols.CurlyList)] +
                    self.parse_list(Token.CurlyClose))
        elif self.token in (Token.Close, Token.SquareClose, Token.CurlyClose):
            trace(self.anchor())
            error("format: stray closing bracket")
        elif self.token == Token.String:
            return tag(anchor, self.state.get_string())
        elif self.token == Token.BlockString:
            return tag(anchor, self.state.get_block_string())
        elif self.token == Token.Symbol:
            return tag(anchor, self.state.get_symbol())
        elif self.token == Token.Integer:
            return tag(anchor, self.state.get_integer())
        elif self.token == Token.Real:
            return tag(anchor, self.state.get_real())
        else:
            trace(anchor)
            error("format: unexpected token '{}' ({})",
                self.state.buffer[self.state.cursor],
                ord(self.state.buffer[self.state.cursor]))

    def parse_naked(self, column, end_token):
        lineno = self.state.lineno
        escape = False
        subcolumn = 0

        anchor = self.anchor()
        builder = ListBuilder()

        unwrap_single = True
        while self.token != Token.EOF:
            if self.token == end_token:
                break
            elif self.token == Token.Escape:
                escape = True
                self.read_token()
                if self.state.lineno <= lineno:
                    trace(self.anchor())
                    error("format: list continuation character must be at beginning or end of sublist line")
                lineno = self.lineno
            elif self.state.lineno > lineno:
                if subcolumn == 0:
                    subcolumn = self.state.column()
                elif self.state.column() != subcolumn:
                    trace(self.anchor())
                    error("format: indentation mismatch")
                elif column != subcolumn:
                    if (column + 4) != subcolumn:
                        trace(self.anchor())
                        error("format: indentations must nest by 4 spaces")

                escape = False
                lineno = self.state.lineno
                # keep adding elements while we're in the same line
                while ((self.token != Token.EOF)
                        and (self.token != end_token)
                        and (self.state.lineno == lineno)):
                    builder.append(self.parse_naked(subcolumn, end_token))
            elif self.token == Token.Separator:
                self.read_token()
                unwrap_single = False
                if not builder.is_empty():
                    break
            else:
                builder.append(self.parse_any())
                lineno = self.state.next_lineno
                self.read_token()
            if (((not escape) or (self.state.lineno > lineno))
                and (self.state.column() <= column)):
                break

        result = builder.get_result()
        if unwrap_single and result and len(result) == 1:
            return result[0]
        else:
            return tag(anchor, result)

    def parse(self):
        self.read_token()
        lineno = 0

        anchor = self.anchor()
        builder = ListBuilder()

        while self.token != Token.EOF:
            if self.token == Token.Empty:
                break;
            elif self.token == Token.Escape:
                self.read_token()
                if self.lineno <= lineno:
                    trace(self.anchor())
                    error("format: list continuation character must be at beginning or end of sublist line")
                lineno = self.lineno
            elif self.state.lineno > lineno:
                if self.state.column() != 1:
                    trace(self.anchor())
                    error("format: indentation mismatch")
                lineno = self.state.lineno
                # keep adding elements while we're in the same line
                while ((self.token != Token.EOF)
                        and (self.token != Token.Empty)
                        and (self.state.lineno == lineno)):
                    builder.append(self.parse_naked(1, Token.Empty))
            elif self.token == Token.Separator:
                trace(self.anchor())
                error("format: unexpected list separation character")
            else:
                builder.append(self.parse_any())
                lineno = self.next_lineno
                self.read_token()
        return tag(anchor, builder.get_result())

    @staticmethod
    def parsed_to_string(parse_result):

        def _parsed_to_string_rec(target):

            # recurse if it is a tuple/list
            if issubclass(type(target), tuple):

                sub_accum = []
                for element in target:

                    transformed_target = _parsed_to_string_rec(element)
                    sub_accum.append(transformed_target)

                return sub_accum

            # handle if it is a symbol and just convert to string
            elif issubclass(type(target), Symbol):

                return str(target)

            # otherwise it is a basic type
            elif (
                    isinstance(target, str) or
                    isinstance(target, Number)
            ):

                return target

            else:
                raise SLNError("Unknown type in tree encountered")

        return _parsed_to_string_rec(parse_result)

    def parse_to_string(self):
        return self.parsed_to_string(self.parse())
