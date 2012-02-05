"""
Copyright (C) 2011 David Boddie <david@boddie.org.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

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
