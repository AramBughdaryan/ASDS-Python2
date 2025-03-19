import time
import inspect
import types
import marshal
import sys
import os
import random
from functools import wraps
from contextlib import ContextDecorator
import dis

class Retry(ContextDecorator):
    """
    A context manager that uses bytecode caching to retry a block of code.

    This approach saves the bytecode of the function and re-executes it on retry,
    allowing for automatic retries without manual retry loops.
    """

    def __init__(self, max_retries=3, delay=1, exceptions=(Exception,)):
        self.max_retries = max_retries
        self.delay = delay
        self.exceptions = exceptions
        self.retries = 0
        self._cached_bytecode = None
        self._func_globals = None
        self._retry_mode = False
        print('1')

    def __enter__(self):
        frame = inspect.currentframe().f_back
        self._original_frame = frame

        code = frame.f_code
        
        # Analyze the bytecode to find the with-body portion
        instructions = list(dis.get_instructions(code))
        
        # Find BEFORE_WITH instruction
        before_with_index = None
        for i, instr in enumerate(instructions):
            if instr.opname == 'BEFORE_WITH':
                before_with_index = i
                break
        
        if before_with_index is not None:
            # The body starts after BEFORE_WITH + POP_TOP
            body_start_index = before_with_index + 2
            
            # Find the end of the with body (it will be before the WITH_EXCEPT_START)
            body_end_index = None
            for i in range(body_start_index, len(instructions)):
                if instructions[i].opname in ('WITH_EXCEPT_START', 'POP_BLOCK'):
                    body_end_index = i
                    break
            
            if body_end_index is not None:
                # TODO: Probably slicing something wrong here since we get segmentation fault 
                body_code_bytes = code.co_code[instructions[body_start_index].offset:instructions[body_end_index].offset]
                
                code = code.replace(co_code=body_code_bytes)
                self._cached_bytecode = marshal.dumps(code)
                self._func_globals = frame.f_globals.copy()
                self._func_locals = frame.f_locals.copy()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return True

        if not issubclass(exc_type, self.exceptions):
            return False

        if self.retries < self.max_retries:
            self.retries += 1
            print(
                f"Retry {self.retries}/{self.max_retries} after {exc_type.__name__}: {exc_val}"
            )

            time.sleep(self.delay)

            self._retry_mode = True

            code = marshal.loads(self._cached_bytecode)

            # Create a new function from the bytecode
            func = types.FunctionType(code, self._func_globals)

            try:
                func()
                return True
            except Exception as e:
                exc_type, exc_val, exc_tb = sys.exc_info()
                return self.__exit__(exc_type, exc_val, exc_tb)
        else:
            print(
                f"Retries exhausted ({self.max_retries}). Last error: {exc_type.__name__}: {exc_val}"
            )
            return False

def flaky_operation():
    ran_number = random.random()
    print('flaky_operation: ', ran_number)
    if ran_number < 0.9:
        raise ValueError("Operation failed!")
    print("Operation successful.")

def main():
    with Retry(max_retries=3, delay=1, exceptions=(ValueError,)):
        flaky_operation()

if __name__ == '__main__':
    # import dis
    # dis.dis(main)
    main()

