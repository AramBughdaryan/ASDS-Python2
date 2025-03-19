import time
import inspect
import types
import marshal
import sys
import os
import ast
import random
import textwrap
import linecache
from functools import wraps
from contextlib import ContextDecorator

class Retry(ContextDecorator):
    """
    A context manager that uses bytecode caching to retry a block of code.
    
    This approach extracts only the code inside the with block and re-executes it on retry.
    """
    
    def __init__(self, max_retries=3, delay=1, exceptions=(Exception,)):
        self.max_retries = max_retries
        self.delay = delay
        self.exceptions = exceptions
        self.retries = 0
        self._retry_mode = False
        self._with_block_code = None
        self._frame_globals = None
        self._frame_locals = None
    
    def __enter__(self):
        caller_frame = inspect.currentframe().f_back
        filename = caller_frame.f_code.co_filename
        lineno = caller_frame.f_lineno
        
        if not self._retry_mode:
            # Store globals and locals from the caller's frame
            self._frame_globals = caller_frame.f_globals.copy()
            self._frame_locals = caller_frame.f_locals.copy()
            
            # Extract the code inside the with block
            self._with_block_code = self._extract_with_block_code(filename, lineno)
        
        return self
    
    def _extract_with_block_code(self, filename, lineno):
        """Extract the code inside the with block."""
        try:
            # Get the source code of the file
            if filename == '<stdin>' or filename.startswith('<ipython-'):
                # Handle interactive sessions
                return None
            
            with open(filename, 'r') as file:
                source_lines = file.readlines()
            
            # Find the with block starting from the line number
            indent = None
            start_line = lineno
            end_line = lineno
            
            # Find the indentation of the with statement
            line = source_lines[lineno - 1].rstrip()
            if 'with' in line and ':' in line:
                indent = len(line) - len(line.lstrip())
                
                # Find the end of the with block
                for i in range(lineno, len(source_lines)):
                    line = source_lines[i].rstrip()
                    if line and not line.isspace():
                        curr_indent = len(line) - len(line.lstrip())
                        if curr_indent <= indent and i > lineno:
                            end_line = i
                            break
                    end_line = i + 1
                
                # Extract the block (excluding the with statement)
                block_lines = source_lines[lineno:end_line]
                if block_lines:
                    # Remove common indentation from the block
                    block_indent = min(len(line) - len(line.lstrip()) for line in block_lines if line.strip())
                    block_code = ''.join(line[block_indent:] for line in block_lines)
                    return block_code
            
            return None
        except Exception as e:
            print(f"Error extracting with block code: {e}")
            return None
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return True
        if not issubclass(exc_type, self.exceptions):
            return False
        
        if self.retries < self.max_retries:
            self.retries += 1
            print(f"Retry {self.retries}/{self.max_retries} after {exc_type.__name__}: {exc_val}")
            
            time.sleep(self.delay)
            self._retry_mode = True
            
            # If we successfully extracted the with block code
            if self._with_block_code:
                try:
                    # Execute just the code inside the with block
                    exec(self._with_block_code, self._frame_globals, self._frame_locals)
                    return True
                except Exception as e:
                    exc_type, exc_val, exc_tb = sys.exc_info()
                    return self.__exit__(exc_type, exc_val, exc_tb)
            else:
                # Fallback to the simple retry approach if block extraction failed
                return True  # Suppress the exception to retry
        else:
            print(f"Retries exhausted ({self.max_retries}). Last error: {exc_type.__name__}: {exc_val}")
            return False  # Re-raise the exception


def flaky_operation():
    ran_number = random.random()
    print('flaky_operation: ', ran_number)
    if ran_number < 0.95:  # Simulate 95% chance of failure
        raise ValueError("Operation failed!")
    print("Operation successful.")

with RetryWithBytecodeCaching(max_retries=3, delay=1, exceptions=(ValueError,)):
    flaky_operation()

with RetryWithBytecodeCaching(max_retries=3, delay=1, exceptions=(ValueError,)):
    ran_number = random.random()
    print('flaky_operation: ', ran_number)
    if ran_number < 0.95:  # Simulate 95% chance of failure
        raise ValueError("Operation failed!")
    print("Operation successful.")

    
    