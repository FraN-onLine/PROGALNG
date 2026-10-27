"""
PLFP - Simple Programming Language Interpreter
===============================================

PLFP is a minimal programming language that supports:
    * Variable declaration:  variable [name] is [expression]
    * Printing:              display [name]   OR   display "string"

An [expression] can be a number, a string, a variable name, or a combination
using the arithmetic operators plus, minus, times, over with parentheses and
standard operator precedence (times/over before plus/minus).

This file is the interpreter. It reads a PLFP source file (any extension,
conventionally .plfp), uses regular expressions and a small recursive-descent
parser to evaluate expressions, executes the statements, and prints the output.

How to run:
    python interpreter.py example.plfp

Syntax reference is documented in README.md.
"""

import re
import sys


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

def tokenize_expression(text):
    """
    Convert an expression string into a list of (type, value) tokens.

    Recognised token types:
        NUMBER   - integer or float literal
        STRING   - double-quoted string literal (quotes stripped)
        IDENT    - variable name (or keyword written as identifier)
        PLUS     - keyword "plus"
        MINUS    - keyword "minus"
        TIMES    - keyword "times"
        OVER     - keyword "over"
        ASK      - keyword "ask"
        SUB      - "-" (unary negation)
        LPAREN   - "("
        RPAREN   - ")"
    """
    token_specification = [
        ('LPAREN',   r'\('),
        ('RPAREN',   r'\)'),
        ('SUB',      r'-'),
        ('NUMBER',   r'\d+(?:\.\d+)?'),
        ('STRING',   r'"[^"]*"'),
        ('IDENT',    r'[a-zA-Z_]\w*'),
        ('SKIP',     r'\s+'),
        ('MISMATCH', r'.'),
    ]
    token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)

    tokens = []
    for match in re.finditer(token_regex, text):
        kind = match.lastgroup
        value = match.group()

        if kind == 'SKIP':
            continue
        if kind == 'MISMATCH':
            raise SyntaxError(f"Unexpected character {value!r} in expression")

        if kind == 'STRING':
            value = value[1:-1]
            tokens.append(('STRING', value))
        elif kind == 'NUMBER':
            value = float(value) if '.' in value else int(value)
            tokens.append(('NUMBER', value))
        elif kind == 'IDENT':
            keyword_map = {
                'plus':   'PLUS',
                'minus':  'MINUS',
                'times':  'TIMES',
                'over':   'OVER',
                'ask':    'ASK',
            }
            kind = keyword_map.get(value.lower(), 'IDENT')
            tokens.append((kind, value if kind == 'IDENT' else None))
        else:
            # LPAREN, RPAREN, SUB
            tokens.append((kind, None))

    return tokens


# ---------------------------------------------------------------------------
# Recursive-descent parser
# ---------------------------------------------------------------------------

class Parser:
    """
    Grammar (with precedence, low to high):

        expression := term (('plus' | 'minus') term)*
        term       := factor (('times' | 'over') factor)*
        factor     := NUMBER | STRING | IDENT | '(' expression ')' | '-' factor | 'ask' STRING
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def parse(self):
        node = self.parse_expression()
        if self.peek() is not None:
            raise SyntaxError("Unexpected token after complete expression")
        return node

    def parse_expression(self):
        node = self.parse_term()
        while self.peek() and self.peek()[0] in ('PLUS', 'MINUS'):
            op = self.consume()[0].lower()
            right = self.parse_term()
            node = ('binop', op, node, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek() and self.peek()[0] in ('TIMES', 'OVER'):
            op = self.consume()[0].lower()
            right = self.parse_factor()
            node = ('binop', op, node, right)
        return node

    def parse_factor(self):
        token = self.peek()
        if token is None:
            raise SyntaxError("Unexpected end of expression")

        if token[0] in ('MINUS', 'SUB'):
            self.consume()
            node = self.parse_factor()
            return ('unary_minus', node)

        if token[0] == 'LPAREN':
            self.consume()
            node = self.parse_expression()
            if self.peek() is None or self.peek()[0] != 'RPAREN':
                raise SyntaxError("Expected ')'")
            self.consume()
            return node

        if token[0] == 'NUMBER':
            self.consume()
            return ('num', token[1])

        if token[0] == 'STRING':
            self.consume()
            return ('str', token[1])

        if token[0] == 'IDENT':
            self.consume()
            return ('var', token[1])

        if token[0] == 'ASK':
            self.consume()                                 # consume 'ask'
            prompt_token = self.peek()
            if prompt_token is None or prompt_token[0] != 'STRING':
                raise SyntaxError("Expected a string prompt after 'ask'")
            self.consume()                                 # consume the string prompt
            return ('ask', prompt_token[1])

        raise SyntaxError(f"Unexpected token {token[0]} in expression")


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

def _is_number(value):
    return isinstance(value, (int, float))


def _is_string(value):
    return isinstance(value, str)


def evaluate(node, variables):
    """
    Recursively evaluate an AST node and return the resulting Python value.

    Type rules (PLFP is intentionally strict):
        plus   : number + number  -> number
                 string + string  -> string (concatenation)
                 anything else    -> TypeError
        minus  : number - number  -> number
                 anything else    -> TypeError
        times  : number * number  -> number
                 anything else    -> TypeError
        over   : number / number  -> number  (division by zero -> error)
                 anything else    -> TypeError
        unary_minus : -number -> number
                      -string -> TypeError
    """
    kind = node[0]

    if kind == 'num':
        return node[1]
    if kind == 'str':
        return node[1]

    if kind == 'var':
        name = node[1]
        if name in variables:
            return variables[name]
        raise NameError(f"Variable '{name}' is not defined")

    if kind == 'ask':
        prompt = node[1]
        user_input = input(prompt)
        # Try to convert the input to a number, fall back to string.
        try:
            if '.' in user_input:
                return float(user_input)
            return int(user_input)
        except ValueError:
            return user_input

    if kind == 'unary_minus':
        operand = evaluate(node[1], variables)
        if not _is_number(operand):
            raise TypeError(f"Cannot negate a non-numeric value: {operand!r}")
        return -operand

    if kind == 'binop':
        op = node[1]
        left = evaluate(node[2], variables)
        right = evaluate(node[3], variables)

        if op == 'plus':
            if _is_number(left) and _is_number(right):
                return left + right
            if _is_string(left) and _is_string(right):
                return left + right
            raise TypeError(
                f"Cannot add {type(left).__name__} and {type(right).__name__}. "
                f"Use numbers with numbers or strings with strings."
            )

        if op == 'minus':
            if _is_number(left) and _is_number(right):
                return left - right
            raise TypeError(
                f"Cannot subtract {type(right).__name__} from {type(left).__name__}. "
                f"Subtraction only works on numbers."
            )

        if op == 'times':
            if _is_number(left) and _is_number(right):
                return left * right
            raise TypeError(
                f"Cannot multiply {type(left).__name__} by {type(right).__name__}. "
                f"Multiplication only works on numbers."
            )

        if op == 'over':
            if _is_number(left) and _is_number(right):
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                return left / right
            raise TypeError(
                f"Cannot divide {type(left).__name__} by {type(right).__name__}. "
                f"Division only works on numbers."
            )

    raise ValueError(f"Unknown AST node kind: {kind}")


# ---------------------------------------------------------------------------
# Interpreter entry point
# ---------------------------------------------------------------------------


def strip_inline_comment(line):
    """
    Remove an inline comment (# ...) from a line, respecting double-quoted strings.
    Returns the line with the comment stripped and trailing whitespace removed.
    """
    in_string = False
    for i, ch in enumerate(line):
        if ch == '"':
            in_string = not in_string
        elif ch == '#' and not in_string:
            return line[:i].rstrip()
    return line


def run_plfp_file(filename):
    """
    Read a PLFP source file and execute its statements line by line.

    Parameters
    ----------
    filename : str
        Path to the PLFP source file.

    Returns
    -------
    None
    """
    variables = {}

    var_pattern = re.compile(r'^\s*variable\s+(\w+)\s+is\s+(.+)\s*$', re.IGNORECASE)
    disp_expr_pattern = re.compile(r'^\s*display\s+(.+?)\s*,?\s*$', re.IGNORECASE)

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file '{filename}': {e}")
        sys.exit(1)

    for line_number, raw_line in enumerate(lines, start=1):
        line = strip_inline_comment(raw_line).strip()

        if not line or line.startswith('#'):
            continue

        var_match = var_pattern.match(line)
        if var_match:
            name = var_match.group(1)
            expr_str = var_match.group(2).strip()

            try:
                tokens = tokenize_expression(expr_str)
                parser = Parser(tokens)
                ast = parser.parse()
                value = evaluate(ast, variables)
                variables[name] = value
            except Exception as e:
                print(f"Error on line {line_number}: {e}")
            continue

        disp_match = disp_expr_pattern.match(line)
        if disp_match:
            expr_str = disp_match.group(1).strip()

            try:
                tokens = tokenize_expression(expr_str)
                parser = Parser(tokens)
                ast = parser.parse()
                value = evaluate(ast, variables)
                print(value)
            except Exception as e:
                print(f"Error on line {line_number}: {e}")
            continue

        print(f"Error on line {line_number}: Unrecognized statement: {raw_line.rstrip()}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python interpreter.py <source_file.plfp>")
        sys.exit(1)

    source_file = sys.argv[1]
    run_plfp_file(source_file)