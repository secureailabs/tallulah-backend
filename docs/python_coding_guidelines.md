# Python Coding Guidelines

## 1. Code Layout
- **Indentation:** Use 4 spaces per indentation level.
- **Maximum Line Length:** Limit all lines to a maximum of 120 characters.
- **Blank Lines:** Use blank lines to separate functions and classes, and larger blocks of code inside functions.
- **Imports:** Imports should usually be on separate lines.

## 2. Naming Conventions
- **Functions:** Function names should be lowercase, with words separated by underscores.
- **Variables:** Use lowercase single letter, word, or words. Separate words with underscores.
- **Classes:** Class names should follow the UpperCaseCamelCase convention.
- **Constants:** Constants should be written in all capital letters with underscores separating words.

## 3. Comments
- **Block Comments:** Each line of a block comment starts with a # and a single space.
- **Inline Comments:** Use inline comments sparingly.

## 4. Whitespace in Expressions and Statements
- Avoid extraneous whitespace in the following situations:
  - Immediately inside parentheses, brackets or braces.
  - Immediately before a comma, semicolon, or colon.
  - Immediately before the open parenthesis that starts the argument list of a function call.

## 5. Programming Recommendations
- **Comparisons to singletons like None should always be done with `is` or `is not`.**
- **Use string methods instead of the string module.**
- **Use `.startswith()` and `.endswith()` instead of string slicing to check for prefixes or suffixes.**

## 6. Error and Exceptions
- **Handling Exceptions:** Use try-except blocks to handle expected exceptions.
- **Raising Exceptions:** Raise exceptions based on concrete error conditions.
- **User-defined Exceptions:** User-defined exception classes should typically be derived from the Exception class.
