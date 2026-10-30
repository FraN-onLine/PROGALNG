"""
PLFP - Programming Language Final Project (very good name)

PLFP is a minimal programming language that supports:
    * Variable declaration: variable [name] is [expression]
    * Printing: display [name]   OR   display "string"

An [expression] can be an integer or float value, a string, a variable name, or a combination
using the arithmetic operators plus, minus, times, over with parentheses and
standard operator precedence (times/over before plus/minus).

This file is the interpreter. It currently can read any .plfp source file, uses regular expressions and a small recursive-descent
parser to evaluate expressions, executes the statements, and prints the output.

How to run:
    python interpreter.py [source_file.plfp]
"""

# regex is used for the PLFP syntax recognition, and sys is used for command-line argument handling
import re
import sys


# Tokenizer
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
        ASK      - keyword "ask", which is the input function 
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
    
    #Create a combined regex pattern with named groups for each token type
    token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)

    tokens = []
    #this is our tokenizer loop, which uses the regex to find all matches in the input text
    for match in re.finditer(token_regex, text):
        kind = match.lastgroup
        value = match.group()

        if kind == 'SKIP':
            continue
        if kind == 'MISMATCH':
            raise SyntaxError(f"Unexpected character {value!r} in expression")

        # for strings, we strip the quotes then append the token with type STRING and the stripped value
        if kind == 'STRING':
            value = value[1:-1]
            tokens.append(('STRING', value))
        # for numbers, we convert to int or float based on the decimal point, then append the token with type NUMBER and the numeric value
        elif kind == 'NUMBER':
            value = float(value) if '.' in value else int(value)
            tokens.append(('NUMBER', value))
        # for identifiers, we check if they match any of the keywords and map them to their corresponding token type; otherwise, we keep them as IDENT
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
            #which includes the rest like LPAREN, RPAREN, SUB, we just append the token with its type and None as value
            tokens.append((kind, None))

    return tokens


# our class parser is used to parse the tokenized expression into an AST (syntax tree) that can be evaluated later. It implements a recursive descent parser for the expression grammar defined in the docstring.
class Parser:
    # note, in EBNF {} means zero or more repetitions, and () means grouping. The grammar is defined using EBNF notation, and the parser implements this grammar using recursive methods for each non-terminal in the grammar. The precedence is handled by the order of method calls, with parse_expression calling parse_term, which calls parse_factor, ensuring that multiplication/division is evaluated before addition/subtraction.
    """
    Grammar (with precedence, low to high):

        expression := term {('plus' | 'minus') term}
        term       := factor {('times' | 'over') factor}
        factor     := NUMBER | STRING | IDENT | '(' expression ')' | '-' factor | 'ask' STRING
    """

    #helper functions peek and consume are used to look at the next token without consuming it, and to consume the next token and advance the position, respectively. 
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    #the parse function serves as our entry point for parsing an expression. It calls parse_expression to parse the entire expression and checks if there are any remaining tokens after parsing, raising a SyntaxError if there are unexpected tokens left.
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

    # here are our other parser functions, which aids on parsing the terms according to the grammar rules.
    def parse_term(self):
        node = self.parse_factor()
        while self.peek() and self.peek()[0] in ('TIMES', 'OVER'):
            op = self.consume()[0].lower()
            right = self.parse_factor()
            node = ('binop', op, node, right)
        return node

    # parse function does one of few things
    # if a factor is expected and there is no factor, raises a syntax error
    # it also looks into the next token to determine what kind of factor it is, and handles unary minus, parentheses, numbers, strings, identifiers, and the 'ask' keyword for user input.
    # bracket matching is also enforced here giving more error handling for our PL
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


#these are helper values to check what type of token we are dealing with
def _is_number(value):
    return isinstance(value, (int, float))


def _is_string(value):
    return isinstance(value, str)


#evaluation of any arithmetic expressions are done here, for this it is described at lines 201 to 212
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

    #more error messages are defined here if variable name does not exist
    if kind == 'var':
        name = node[1]
        if name in variables:
            return variables[name]
        raise NameError(f"Variable '{name}' is not defined")

    if kind == 'ask':
        prompt = node[1]
        user_input = input(prompt)
        #Try to convert the input to a number, fall back to string.
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

    #for every binary operation, we evaluate the left and right operands, check their types, and perform the operation if valid; otherwise, we raise a TypeError with an error message to guide them
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

#this is a strip to any inline comment, which is defined as a # character that is not inside a double-quoted string. It returns the line with the comment stripped and trailing whitespace removed.
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


# we use regex to check what kind of statement each line is, then call the right function for it

# Match variable declarations: "variable [name] is [expression]"
# Group 1 which is (\w+) = variable name, Group 2 which is (.+?) = expression after 'is'
VAR_PATTERN = re.compile(r'^\s*variable\s+(\w+)\s+is\s+(.+?)\s*$', re.IGNORECASE)

# Match display statements: "display [expression]," (the trailing comma is optional)
# Group 1 here is the expression to tokenize, parse, and print
DISP_PATTERN = re.compile(r'^\s*display\s+(.+?)\s*,?\s*$', re.IGNORECASE)


# this state dispatch table is used to map regex patterns to their corresponding evaluation functions.
# each entry has the pattern, which group holds the name (if any), which group holds the expression, and the function to call
STATE_DISPATCH = [
    {
        'pattern': VAR_PATTERN,
        'name_group': 1,       # capture group 1 = variable name
        'expr_group': 2,       # capture group 2 = expression after 'is'
        'evaluator': 'eval_declare_var',
        'doc': 'Declare variable: variable NAME is EXPRESSION'
    },
    {
        'pattern': DISP_PATTERN,
        'name_group': None,    # display has no name, only an expression
        'expr_group': 1,       # capture group 1 = expression to display
        'evaluator': 'eval_print_statement',
        'doc': 'Print: display EXPRESSION,'
    },
]

def eval_declare_var(name, expr_str, variables, line_number):
    """Declare a variable from the regex-matched name and expression string.

   basically this function takes the variable name and expression string, tokenizes the expression, parses it into an AST, evaluates it, and stores the result in the variables dictionary under the given name.
    Any error (bad syntax, undefined variable, type mismatch) is caught and
    reported with the line number, so the user can fix it.
    """
    try:
        tokens = tokenize_expression(expr_str)
        parser = Parser(tokens)
        ast = parser.parse()
        value = evaluate(ast, variables)
        variables[name] = value
    except Exception as e:
        print(f"Error on line {line_number}: {e}")

# basicaly this function evaluates the display keyword which is used to print values of an expressio
def eval_print_statement(name, expr_str, variables, line_number):
    """Evaluate and print an expression for the display statement.
    """
    try:
        tokens = tokenize_expression(expr_str)
        parser = Parser(tokens)
        ast = parser.parse()
        value = evaluate(ast, variables)
        print(value)
    except Exception as e:
        print(f"Error on line {line_number}: {e}")

# what this does is to read the source file line by line, strip comments and whitespace, match each line against the regex patterns in STATE_DISPATCH, and call the corresponding evaluator function with the extracted variable name and expression string.
# also if no pattern matches, it shows an error message.
def run_plfp_file(filename):
    """Read a PLFP source file and execute its statements.
       Further documentation of how PLFP works is in the README.md file, 
       which is included with the source code.
    """
    variables = {}

    # read the whole source file up. if it is missing or unreadable we
    # report it and exit, because there is nothing else we can do
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: File not found: {filename}")
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    for line_number, raw_line in enumerate(lines, start=1):
        #strip any inline comment first, then surrounding whitespace, so the
        #regex patterns below never have to worry about stray '#' or spaces
        line = strip_inline_comment(raw_line).strip()
        if not line or line.startswith('#'):
            continue

        # Iterate through STATE_DISPATCH to look for matching patterns.
        # We pull the variable name (if any) and the expression out of the match
        # groups, then hand them to the entry's evaluator function. If nothing
        # matches at all, the line is not valid PLFP and we say so.
        matched = False
        for entry in STATE_DISPATCH:
            pat = entry['pattern']
            m = pat.match(line)
            if m:
                name = m.group(entry['name_group']) if entry['name_group'] else None
                expr_str = m.group(entry['expr_group'])
                ev = globals()[entry['evaluator']]
                try:
                    ev(name, expr_str, variables, line_number)
                    matched = True
                    break
                except Exception as e:
                    print(f"Error on line {line_number}: {e}")
                    matched = True
                    break

        if not matched:
            print(f"Error on line {line_number}: Unrecognized statement: {raw_line.rstrip()}")

# start of the interpreter script, 
if __name__ == '__main__':
    if len(sys.argv) < 2:
        #shows how to use the interpreter if no source file is provided as a command-line argument
        print("Usage: python interpreter.py <source_file.plfp>")
        sys.exit(1)

    source_file = sys.argv[1]

    # only .plfp files are PLFP source code, anything else is probably a mistake
    if not source_file.lower().endswith('.plfp'):
        print(f"Error: '{source_file}' is not a .plfp file")
        sys.exit(1)

    run_plfp_file(source_file)