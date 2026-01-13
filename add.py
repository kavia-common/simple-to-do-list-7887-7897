#!/usr/bin/env python3
import sys

# PUBLIC_INTERFACE
def add(a: int, b: int) -> int:
    """
    Returns the sum of two integers.

    Args:
        a (int): First integer.
        b (int): Second integer.

    Returns:
        int: The sum of a and b.
    """
    return a + b

def print_usage_and_exit():
    print("Usage: python add.py <num1> <num2>")
    print("Adds two integers and prints the result.")
    print("Example: python add.py 2 3")
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Error: Two integer arguments required.")
        print_usage_and_exit()

    try:
        num1 = int(sys.argv[1])
        num2 = int(sys.argv[2])
    except ValueError:
        print("Error: Both arguments must be integers.")
        print_usage_and_exit()

    result = add(num1, num2)
    print(result)
