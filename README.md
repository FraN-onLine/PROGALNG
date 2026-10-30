# PLFP

PLFP is our Programming Languages FInal Project or PLFP for short hence the extension
it currently supports:
- Variable declaration with arithmetic  
- User input (`ask`)  
- Printing (`display`)  

## Files

| File | Purpose |
|------|---------|
| `interpreter.py` | The Python interpreter that reads and executes PLFP programs |
| `example.plfp`   | A sample PLFP program you can run immediately |
| `README.md`      | This documentation |

## Syntax

### Variable declaration

```
variable [name] is [expression]
```

- `[name]` is  a valid identifier (letters, digits, underscore; must start with a letter or underscore) followinf naming conventions in PL
- `[expression]` is a term that can be any of the folowing:
  - A number: `6`, `3.14`, `-5`
  - A string: `"hello"`
  - A variable name: `age`
  - An arithmetic expression using `plus`, `minus`, `times`, `over` representing the traditional +,-,x and /
  - Parenthesised sub-expressions: `(6 plus 7) over 8`
  - Unary negation: `-5` or `- age`
  - User input: `ask "prompt text"`, this is a variable listed from above(number or string) already embedded on assignment

Operator precedence follows standard arithmetic rules:
1. `parenthesized equations` following same precendence rules below.
2. `times` and `over` (multiplication/division)
3. `plus` and `minus` (addition/subtraction)

Examples:

```
variable age is 25
variable pi is 3.14159
variable name is "LIN PINEDA"

variable score is 10 plus 5 times 2        # 20
variable half is (10 plus 5) over 3        # 5
variable double_age is age times 2         # 50
variable y is (6 plus 7) over 8            # 1.625
variable greeting is "Hello" plus " " plus name   # "Hello LIN PINEDA"
variable user_age is ask "Enter your age: "       # prompts user for input
```

### Type rules (PLFP is intentionally strict)

| Operation | Allowed types | Result |
|-----------|--------------|--------|
| `plus` | number + number | number |
| `plus` | string + string | string (concatenation) |
| `minus` | number - number | number |
| `times` | number * number | number |
| `over` | number / number | number (division by zero = error) |
| unary `-` | -number | number |

Mixing types (e.g. `"hello" + 5` or `-"hello"`) produces a clear error message with the line number.

### Printing

Print a variable's value:

```
display [name],
```

Print a literal string:

```
display "some text"
```

Print the result of any expression:

```
display [expression],
```
expressions similarly are any expression listed above.
Examples:

```
display age,
display "hello",
display age plus 7 over 3,          # 25 + (7 / 3) = 27.333...
display (age plus 7) over 3,        # (25 + 7) / 3 = 10.667
display "Hello" plus " " plus name, # "Hello PLFP"
display ask "Enter a number: ",     # prompts user, then prints result
```

The trailing comma after `display ... ,` is optional.

### Comments

Lines starting with `#` are treated as comments and ignored.  
Inline comments after code are also supported.

## How to run

2. Open a terminal in the folder interpreter.py is placed on
2. Create a PLFP file in the folder and write your code.
3. Run the interpreter with the source file like below

```
python interpreter.py example.plfp
```

If the program uses `ask`, the interpreter will pause and wait for you to type a value and press Enter.

### Expected output for `example.plfp` (with input `30`)

```
Enter your age: 25
3.14159
Arom ALCAUSIn
20
5.0
60
50
30.0
1.625
Hello Arom ALCAUSIn
Hello from Arom ALCAUSIn!
```

## Error handling

All errors are reported with the line number where they occurred:

- **Undefined variable:** `Error on line 3: Variable '[varname]' is not defined`
- **Type mismatch:** `Error on line 1: Cannot add str and int. Use numbers with numbers or strings with strings.`
- **Division by zero:** `Error on line 1: Division by zero`
- **Syntax error:** `Error on line 1: Unexpected character '@' in expression`
- **Missing prompt:** `Error on line 1: Expected a string prompt after 'ask'`
