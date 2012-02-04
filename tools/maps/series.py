def values(first, second, number):

    # Add the two values as in the Fibonacci sequence, but take the modulus of
    # 256 of the result to avoid overflowing into values that require two bytes
    # or more.
    
    while number > 0:
    
        new_value = (first + second) & 0xff
        
        yield new_value
        
        first = second
        second = new_value
        
        number -= 1

def unlimited_values(first, second):

    # Add the two values as in the Fibonacci sequence, but take the modulus of
    # 256 of the result to avoid overflowing into values that require two bytes
    # or more.
    
    while True:
    
        new_value = (first + second) & 0xff
        
        yield new_value
        
        first = second
        second = new_value
