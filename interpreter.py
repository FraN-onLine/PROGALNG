"""
PLFP - Programming Language Final Project (very good name)

PLFP is a minimal programming language that supports:
    * Variable declaration: variable [name] is [expression]
    * Variable with no value: variable [name]  (starts at 0)
    * Printing: display [name]   OR   display "string"

An [expression] can be an integer or float value, a string, a variable name, or a combination
using the arithmetic operators plus, minus, times, over, mod with parentheses and
standard operator precedence (times/over/mod before plus/minus).

This file is the interpreter. It can read any .plfp source file, uses regular expressions and a small recursive-descent
parser to evaluate expressions, executes the statements, and prints the output.

How to run:
    python interpreter.py [source_file.plfp]
"""

#regex is used for the PLFP syntax recognition, and sys is used for command-line argument handling
import re
import sys


#Tokenizer
def tokenize_expression(text):
    """turns an expression string into a list of (type, value) tokens,
    strings lose their quotes and numbers become int or float"""
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

        #for strings, we strip the quotes then append the token with type STRING and the stripped value
        if kind == 'STRING':
            value = value[1:-1]
            tokens.append(('STRING', value))
        #for numbers, we convert to int or float based on the decimal point, then append the token with type NUMBER and the numeric value
        elif kind == 'NUMBER':
            value = float(value) if '.' in value else int(value)
            tokens.append(('NUMBER', value))
        #for identifiers, we check if they match any of the keywords and map them to their corresponding token type; otherwise, we keep them as IDENT
        elif kind == 'IDENT':
            keyword_map = {
                'plus':   'PLUS',
                'minus':  'MINUS',
                'times':  'TIMES',
                'over':   'OVER',
                'mod':    'MOD',
                'ask':    'ASK',
            }
            kind = keyword_map.get(value.lower(), 'IDENT')
            tokens.append((kind, value if kind == 'IDENT' else None))
        else:
            #which includes the rest like LPAREN, RPAREN, SUB, we just append the token with its type and None as value
            tokens.append((kind, None))

    return tokens


#our class parser is used to parse the tokenized expression into an AST (syntax tree) that can be evaluated later. It implements a recursive descent parser for the expression grammar defined in the docstring.
class Parser:
    #note, in EBNF {} means zero or more repetitions, and () means grouping. The grammar is defined using EBNF notation, and the parser implements this grammar using recursive methods for each non-terminal in the grammar. The precedence is handled by the order of method calls, with parse_expression calling parse_term, which calls parse_factor, ensuring that multiplication/division is evaluated before addition/subtraction.
    """
    Grammar (with precedence, low to high):

        expression := term {('plus' | 'minus') term}
        term       := factor {('times' | 'over' | 'mod') factor}
        factor     := NUMBER | STRING | IDENT | '(' expression ')' | '-' factor | 'ask' STRING
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    #look at the next token without eating it
    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    #take the next token and move forward
    def consume(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    #start parsing here, also complains if there are tokens left over
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

    #here are our other parser functions, which aids on parsing the terms according to the grammar rules.
    def parse_term(self):
        node = self.parse_factor()
        while self.peek() and self.peek()[0] in ('TIMES', 'OVER', 'MOD'):
            op = self.consume()[0].lower()
            right = self.parse_factor()
            node = ('binop', op, node, right)
        return node

    #parse function does one of few things
    #if a factor is expected and there is no factor, raises a syntax error
    #it also looks into the next token to determine what kind of factor it is, and handles unary minus, parentheses, numbers, strings, identifiers, and the 'ask' keyword for user input.
    #bracket matching is also enforced here giving more error handling for our PL
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
            self.consume()                                 #consume 'ask'
            prompt_token = self.peek()
            if prompt_token is None or prompt_token[0] != 'STRING':
                raise SyntaxError("Expected a string prompt after 'ask'")
            self.consume()                                 #consume the string prompt
            return ('ask', prompt_token[1])

        raise SyntaxError(f"Unexpected token {token[0]} in expression")


#little helpers to check if a value is a number or a string
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
        mod    : number mod number -> number (remainder, mod by zero -> error)
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
        #if theres no more input to read (end of file) say it plainly
        try:
            user_input = input(prompt)
        except EOFError:
            raise EOFError("Expected input but there was none")
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
            raise TypeError(f"cant negate {operand!r}")
        return -operand

    #do the math but check the types first, error out if they dont match
    if kind == 'binop':
        op = node[1]
        left = evaluate(node[2], variables)
        right = evaluate(node[3], variables)

        if op == 'plus':
            if _is_number(left) and _is_number(right):
                return left + right
            if _is_string(left) and _is_string(right):
                return left + right
            raise TypeError(f"cant add {type(left).__name__} and {type(right).__name__}")

        if op == 'minus':
            if _is_number(left) and _is_number(right):
                return left - right
            raise TypeError("you can only subtract numbers")

        if op == 'times':
            if _is_number(left) and _is_number(right):
                return left * right
            raise TypeError("you can only multiply numbers")

        if op == 'mod':
            if _is_number(left) and _is_number(right):
                if right == 0:
                    raise ZeroDivisionError("Modulo by zero")
                return left % right
            raise TypeError("you can only do mod on numbers")

        if op == 'over':
            if _is_number(left) and _is_number(right):
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                return left / right
            raise TypeError("you can only divide numbers")

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


#we use regex to check what kind of statement each line is, then call the right function for it

#Match variable declarations: "variable [name] is [expression]"
#Group 1 which is (\w+) = variable name, Group 2 which is (.+?) = expression after 'is'
VAR_PATTERN = re.compile(r'^\s*variable\s+(\w+)\s+is\s+(.+?)\s*$', re.IGNORECASE)

#Match display statements: "display [expression]," (the trailing comma is optional)
#Group 1 here is the expression to tokenize, parse, and print
DISP_PATTERN = re.compile(r'^\s*display\s+(.+?)\s*,?\s*$', re.IGNORECASE)

#Match a variable with no value at all, like "variable counter"
#it just starts at 0 until something is assigned to it
VAR_EMPTY_PATTERN = re.compile(r'^\s*variable\s+(\w+)\s*$', re.IGNORECASE)

#Match "variable x is" with nothing after the is, so we can give a proper error
VAR_NO_EXPR_PATTERN = re.compile(r'^\s*variable\s+(\w+)\s+is\s*$', re.IGNORECASE)


#keywords are reserved, they cant be used as variable names
RESERVED_WORDS = ('variable', 'is', 'display', 'plus', 'minus', 'times', 'over', 'mod', 'ask')


def check_not_reserved(name):
    if name.lower() in RESERVED_WORDS:
        raise SyntaxError(f"'{name}' is a reserved word, pick another name")


def eval_declare_var(name, expr_str, variables, line_number):
    """Declare a variable from the regex-matched name and expression string.

   basically this function takes the variable name and expression string, tokenizes the expression, parses it into an AST, evaluates it, and stores the result in the variables dictionary under the given name.
    if something breaks we print the error with its line number so you can fix it
    """
    try:
        check_not_reserved(name)
        tokens = tokenize_expression(expr_str)
        parser = Parser(tokens)
        ast = parser.parse()
        value = evaluate(ast, variables)
        variables[name] = value
        return True
    except Exception as e:
        print(f"Error on line {line_number}: {e}")
        return False

#basicaly this function evaluates the display keyword which is used to print values of an expressio
def eval_print_statement(name, expr_str, variables, line_number):
    """evaluates the expression then prints it"""
    try:
        tokens = tokenize_expression(expr_str)
        parser = Parser(tokens)
        ast = parser.parse()
        value = evaluate(ast, variables)
        print(value)
        return True
    except Exception as e:
        print(f"Error on line {line_number}: {e}")
        return False


#for "variable counter" with no value, the variable just starts at 0
def eval_declare_empty(name, expr_str, variables, line_number):
    try:
        check_not_reserved(name)
        variables[name] = 0
        return True
    except Exception as e:
        print(f"Error on line {line_number}: {e}")
        return False


#the line was "variable x is" and then nothing, so tell them the expression is missing
def eval_missing_expression(name, expr_str, variables, line_number):
    print(f"Error on line {line_number}: Expected an expression after 'is'")
    return False

#statement table: pattern, which groups hold the name and expression, then the function to call
STATE_DISPATCH = [
    {
        'pattern': VAR_PATTERN,
        'name_group': 1,       #capture group 1 = variable name
        'expr_group': 2,       #capture group 2 = expression after 'is'
        'evaluator': eval_declare_var
    },
    {
        'pattern': VAR_EMPTY_PATTERN,
        'name_group': 1,       #just the name, theres no expression here
        'expr_group': None,
        'evaluator': eval_declare_empty
    },
    {
        'pattern': VAR_NO_EXPR_PATTERN,
        'name_group': 1,
        'expr_group': None,
        'evaluator': eval_missing_expression
    },
    {
        'pattern': DISP_PATTERN,
        'name_group': None,    #display has no name, only an expression
        'expr_group': 1,       #capture group 1 = expression to display
        'evaluator': eval_print_statement
    },
]

#what this does is to read the source file line by line, strip comments and whitespace, match each line against the regex patterns in STATE_DISPATCH, and call the corresponding evaluator function with the extracted variable name and expression string.
#also if no pattern matches, it shows an error message.
def run_plfp_file(filename):
    """Read a PLFP source file and execute its statements.
       Further documentation of how PLFP works is in the README.md file, 
       which is included with the source code.
    """
    variables = {}
    had_error = False

    #open the file, if it wont open just stop
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

        #try each pattern, the first one that matches runs its function,
        #if nothing matches the line is not valid PLFP
        matched = False
        for entry in STATE_DISPATCH:
            pat = entry['pattern']
            m = pat.match(line)
            if m:
                name = m.group(entry['name_group']) if entry['name_group'] else None
                expr_str = m.group(entry['expr_group']) if entry['expr_group'] else None
                ev = entry['evaluator']
                try:
                    ok = ev(name, expr_str, variables, line_number)
                except Exception as e:
                    print(f"Error on line {line_number}: {e}")
                    ok = False
                matched = True
                if not ok:
                    had_error = True
                break

        if not matched:
            print(f"Error on line {line_number}: Unrecognized statement: {line}")
            had_error = True

    #main uses this to exit with code 1 if anything failed along the way
    return had_error

#start of the interpreter script, 
if __name__ == '__main__':
    if len(sys.argv) < 2:
        #shows how to use the interpreter if no source file is provided as a command-line argument
        print("Usage: python interpreter.py <source_file.plfp>")
        sys.exit(1)

    source_file = sys.argv[1]

    #only .plfp files are PLFP source code, others are not read by the interpreter
    if not source_file.lower().endswith('.plfp'):
        print(f"Error: '{source_file}' is not a .plfp file")
        sys.exit(1)

    had_error = run_plfp_file(source_file)
    if had_error:
        sys.exit(1)
    sys.exit(0)