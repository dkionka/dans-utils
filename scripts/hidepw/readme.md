# hidepw.py

This script hides passwords in a matrix of random characters. You use it when you want to have a file with your passwords, but you want to make them hard to see.

## Strategies

By default it only generates lowercase letters. A good password has mixed case, numbers, and punctuation, but your password will probably stick out. There are different strategies:

- Use lowercase version of your password. You have to remember which letters are capitalized and where the non-letters go.
- Use mixed case version of your password with `-u`. Then you only have to remember where the non-letters go.
- Use `-a` to use all character types and review the output for the password being obvious.

<!-- USAGE EXAMPLES -->
## Usage Examples

Your password is __P@sw0rd__, but you leave out the punctuation to hide it better.

`./hidepw.py -r 5 -c 10 -u Pswrd`

In this example, you can find the password, __Pswrd__, but it is not obvious unless you know what you are looking for.

	P X C v c s x Z i H
	S N a T g t G P h p
	P P s w r d m I F L
	E O Z d Y R R F E B
	t w Z z a a T z u s
