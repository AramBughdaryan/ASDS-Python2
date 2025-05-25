import threading
import time


def worker(n):
    print(f"[{threading.current_thread().name}] starting work")
    time.sleep(n)
    print(f"[{threading.current_thread().name}] done")

start_time = time.perf_counter()
t = threading.Thread(target=worker, args=(5,), name="Sleeper")

t.daemon = False # default; it’s non-daemon
# If the thread is daemon then it runs in background so python may be finished before worker function
# finished executing. if it is not daemon python will continue after line 22 and in line 26 it will wait until
# worker will finish it's execution

t.start() # calls run() in new thread

print("Is alive?", t.is_alive()) # likely True
print("Thread ID", t.native_id) # thread ID

t.join(timeout=3) # wait up to 3s

print("Joined?", not t.is_alive())

print(time.perf_counter() - start_time)