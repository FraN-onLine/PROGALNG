# PLFP

PLFP is our Programming Languages FInal Project or PLFP for short hence the extension
it currently supports:
- Variable declaration with arithmetic  
- Variable initialization
- User input (`ask`)  
- Printing (`display`)  

## Files

| File | Purpose |
|------|---------|
| `interpreter.py` | The Python interpreter that reads and executes PLFP programs |
| `example.plfp`   | A sample PLFP program you can run immediately |
| `edge_case1.plfp` ... `edge_case8.plfp` | Small programs for each edge case, see the section below |
| `README.md`      | This documentation |

## Syntax

### Variable declaration

```
variable [name] is [expression]
```

You can also declare a variable without a value at all, it just starts at 0 until you assign something:

```
variable [name]  
```

- `[name]` is  a valid identifier (letters, digits, underscore; must start with a letter or underscore) followinf naming conventions in PL
- `[name]` also cant be a keyword, so `variable plus is 3` gets rejected, keywords are reserved
- `[expression]` is a term that can be any of the folowing:
  - A number: `6`, `3.14`, `-5`
  - A string: `"hello"`
  - A variable name: `age`
  - An arithmetic expression using `plus`, `minus`, `times`, `over`, `mod` representing the traditional +,-,x,/ and %
  - Parenthesised sub-expressions: `(6 plus 7) over 8`
  - Unary negation: `-5` or `- age`
  - User input: `ask "prompt text"`, this is a variable listed from above(number or string) already embedded on assignment

Operator precedence follows standard arithmetic rules:
1. `parenthesized equations` following same precendence rules below.
2. `times`, `over` and `mod` (multiplication, division, remainder)
3. `plus` and `minus` (addition/subtraction)

Examples:

```
variable age is 25
variable pi is 3.14159
variable name is "LIN PINEDA"
variable counter                            # no value given, starts at 0

variable score is 10 plus 5 times 2        # 20
variable half is (10 plus 5) over 3        # 5.0 (over always gives a decimal)
variable leftover is 17 mod 5              # 2
variable double_age is age times 2         # 50
variable y is (6 plus 7) over 8            # 1.625
variable greeting is "Hello" plus " " plus name   # "Hello LIN PINEDA"
variable user_age is ask "Enter your age: "       # prompts user for input
```

### Type rules (no mixing types)

| Operation | Allowed types | Result |
|-----------|--------------|--------|
| `plus` | number + number | number |
| `plus` | string + string | string (concatenation) |
| `minus` | number - number | number |
| `times` | number * number | number |
| `over` | number / number | number (division by zero = error) |
| `mod` | number mod number | number (remainder, mod by zero = error) |
| unary `-` | -number | number |

if you mix types you get an error with the line number.

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

1. Open a terminal in the folder interpreter.py is placed on
2. Create a PLFP file in the folder and write your code.
3. Run the interpreter with the source file like below

```
python interpreter.py example.plfp
```

Only `.plfp` files are accepted, anything else (like `README.md`) gets rejected with an error.

If the program uses `ask`, the interpreter will pause and wait for you to type a value and press Enter.

### Expected output for `example.plfp` (with inputs `30`, `7` and `3`)

```
Enter your age: 30
3.14159
Arom ALCAUSIn
20
5.0
60
50
30.0
1.625
Hello Arom ALCAUSIn
30
27.333333333333332
10.666666666666666
Hello Arom ALCAUSIn
enter number 1: 7
enter number 2: 3
10
```

## Edge case files

we added small programs for the weird cases, run them the same way as the example
(`python interpreter.py edge_case1.plfp` and so on).

| File | What it shows |
|------|---------------|
| `edge_case1.plfp` | a variable with no value starts at 0 |
| `edge_case2.plfp` | negative numbers and double negatives like `-debt` |
| `edge_case3.plfp` | precedence, parentheses and `mod` |
| `edge_case4.plfp` | errors print with the line number but the program keeps going |
| `edge_case5.plfp` | keywords cant be used as variable names |
| `edge_case6.plfp` | `#` inside a string, extra spacing, the comma is optional |
| `edge_case7.plfp` | `ask` gives a number or a string depends what you type |
| `edge_case8.plfp` | missing expression and unrecognized statements |

## Error handling

All errors are reported with the line number where they occurred, a bad line doesnt stop the whole program:

- **Undefined variable:** `Error on line 3: Variable '[varname]' is not defined`
- **Type mismatch:** `Error on line 1: cant add str and int`
- **Division by zero:** `Error on line 1: Division by zero`
- **Modulo by zero:** `Error on line 1: Modulo by zero`
- **Syntax error:** `Error on line 1: Unexpected character '@' in expression`
- **Missing prompt:** `Error on line 1: Expected a string prompt after 'ask'`
- **Reserved word as name:** `Error on line 1: 'plus' is a reserved word, pick another name`
- **Missing expression:** `Error on line 1: Expected an expression after 'is'`
- **No input given:** `Error on line 1: Expected input but there was none`
- **Unknown statement:** `Error on line 1: Unrecognized statement: whatever was typed`

a bad line doesnt stop the program, but the interpreter exits with code 1 at the end if any line failed.