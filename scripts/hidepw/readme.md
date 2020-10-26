# hidepw.py

This script hides passwords in a matrix of random characters. You use it when you want a file with your passwords, but you want to make them hard to see. It looks like a mess, but they tend to jump out at you when you know what you are looking for.

## Strategies

By default it only generates lowercase letters. A good password has mixed case, numbers, and punctuation, but your password will probably stick out. There are different strategies:

- Use lowercase version of your password. You have to remember which letters are capitalized and where the non-letters go.
- Use mixed case version of your password with `-u`. Then you only have to remember where the non-letters go.
- Use `-a` to use all character types and review the output for the password being obvious.

<!-- USAGE EXAMPLES -->
## Usage Examples

Your password is __P@sw0rd__, but you leave out the punctuation (__Pswrd__) to hide it among letters only.

`./hidepw.py -r 5 -c 10 -u Pswrd`


	P X C v c s x Z i H
	S N a T g t G P h p
	P P s w r d m I F L
	E O Z d Y R R F E B
	t w Z z a a T z u s

You have trouble remembering your social security number, so you use the number-only options to hide it.

`./hidepw.py -r 5 -c 15 -n --no-lower 123456789`

	8 7 0 5 1 5 9 7 8 5 9 3 5 6 5
	8 4 5 9 5 5 3 5 8 1 5 3 0 1 8
	5 2 7 0 1 2 3 4 5 6 7 8 9 1 0
	5 2 6 0 7 2 8 6 9 5 1 0 1 7 9
	2 6 9 8 6 7 3 7 2 7 2 0 3 8 6
