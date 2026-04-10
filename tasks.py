"""
Task definitions for the Python REPL Debugging Environment.

Each task has:
  - description:   what the code is SUPPOSED to do
  - broken_code:   the buggy starting code the agent receives
  - tests:         list of assert_code snippets that must pass for full credit
"""

TASKS = {

    # ──────────────────────────────────────────────────────────────────
    # EASY: Two simple bugs — off-by-one + wrong operator
    # ──────────────────────────────────────────────────────────────────
    "easy": {
        "description": (
            "Fix the function `sum_evens(n)` so that it returns the sum of all "
            "even numbers from 0 up to AND INCLUDING n. "
            "Also fix `is_palindrome(s)` so it correctly checks if a string is a palindrome."
        ),
        "broken_code": """\
def sum_evens(n):
    # BUG: should include n, and should skip odd numbers
    total = 0
    for i in range(1, n):   # bug 1: range should be range(0, n+1)
        if i % 2 == 1:       # bug 2: should be == 0 for even
            total += i
    return total

def is_palindrome(s):
    # BUG: comparison is wrong
    return s == s[::-0]     # bug 3: should be s[::-1]
""",
        "tests": [
            {
                "name": "sum_evens(10) == 30",
                "assert_code": "assert sum_evens(10) == 30, f'Expected 30, got {sum_evens(10)}'"
            },
            {
                "name": "sum_evens(0) == 0",
                "assert_code": "assert sum_evens(0) == 0, f'Expected 0, got {sum_evens(0)}'"
            },
            {
                "name": "sum_evens(6) == 12",
                "assert_code": "assert sum_evens(6) == 12, f'Expected 12, got {sum_evens(6)}'"
            },
            {
                "name": "is_palindrome('racecar') == True",
                "assert_code": "assert is_palindrome('racecar') == True, 'racecar should be palindrome'"
            },
            {
                "name": "is_palindrome('hello') == False",
                "assert_code": "assert is_palindrome('hello') == False, 'hello should not be palindrome'"
            },
        ],
    },

    # ──────────────────────────────────────────────────────────────────
    # MEDIUM: Logic bugs in a small data-processing pipeline
    # ──────────────────────────────────────────────────────────────────
    "medium": {
        "description": (
            "Fix the student grade processor. "
            "`average(scores)` should return the mean of a list of numbers. "
            "`letter_grade(avg)` should return 'A' (>=90), 'B' (>=80), 'C' (>=70), 'D' (>=60), or 'F'. "
            "`top_students(students)` takes a list of dicts with 'name' and 'scores', "
            "and returns names of students with letter grade 'A', sorted alphabetically."
        ),
        "broken_code": """\
def average(scores):
    # BUG: divides by wrong value
    return sum(scores) / len(scores) + 1   # bug: extra +1

def letter_grade(avg):
    # BUG: conditions are backwards / wrong thresholds
    if avg >= 90:
        return 'F'    # bug: should be 'A'
    elif avg >= 80:
        return 'D'    # bug: should be 'B'
    elif avg >= 70:
        return 'C'    # this one happens to be correct
    elif avg >= 60:
        return 'B'    # bug: should be 'D'
    else:
        return 'A'    # bug: should be 'F'

def top_students(students):
    result = []
    for s in students:
        avg = average(s['scores'])
        grade = letter_grade(avg)
        if grade == 'A':
            result.append(s['name'])
    # BUG: not sorted
    return result   # bug: should be sorted(result)
""",
        "tests": [
            {
                "name": "average([80, 90, 100]) == 90.0",
                "assert_code": "assert average([80, 90, 100]) == 90.0, f'Got {average([80, 90, 100])}'"
            },
            {
                "name": "average([70]) == 70.0",
                "assert_code": "assert average([70]) == 70.0, f'Got {average([70])}'"
            },
            {
                "name": "letter_grade(95) == 'A'",
                "assert_code": "assert letter_grade(95) == 'A', f'Got {letter_grade(95)}'"
            },
            {
                "name": "letter_grade(85) == 'B'",
                "assert_code": "assert letter_grade(85) == 'B', f'Got {letter_grade(85)}'"
            },
            {
                "name": "letter_grade(55) == 'F'",
                "assert_code": "assert letter_grade(55) == 'F', f'Got {letter_grade(55)}'"
            },
            {
                "name": "top_students sorted alphabetically",
                "assert_code": """\
students = [
    {'name': 'Zara', 'scores': [95, 92, 98]},
    {'name': 'Amit', 'scores': [91, 93, 90]},
    {'name': 'Priya', 'scores': [60, 65, 55]},
]
result = top_students(students)
assert result == ['Amit', 'Zara'], f'Got {result}'
"""
            },
        ],
    },

    # ──────────────────────────────────────────────────────────────────
    # HARD: Multiple interacting bugs in a mini task scheduler
    # ──────────────────────────────────────────────────────────────────
    "hard": {
        "description": (
            "Fix the task scheduler. "
            "`TaskQueue` is a priority queue where lower priority number = higher priority. "
            "`add_task(name, priority)` adds a task. "
            "`next_task()` pops and returns the name of the highest-priority (lowest number) task. "
            "`pending_count()` returns number of tasks still in queue. "
            "`run_all()` returns list of task names in execution order (highest priority first)."
        ),
        "broken_code": """\
class TaskQueue:
    def __init__(self):
        self.tasks = []

    def add_task(self, name, priority):
        # BUG: appends in wrong order (should be (priority, name))
        self.tasks.append((name, priority))

    def next_task(self):
        if not self.tasks:
            return None
        # BUG: should sort by priority (index 0 after fix), currently sorts by name
        self.tasks.sort(key=lambda x: x[0])
        # BUG: should pop index 0 (highest priority), pops last
        task = self.tasks.pop()
        # BUG: should return task[1] (name) after fix, currently returns task[0]
        return task[0]

    def pending_count(self):
        # BUG: off by one
        return len(self.tasks) - 1   # bug: should be len(self.tasks)

    def run_all(self):
        results = []
        # BUG: infinite loop risk — doesn't check empty correctly
        while self.pending_count() > 0:   # bug: pending_count is wrong so this may stop early
            results.append(self.next_task())
        return results
""",
        "tests": [
            {
                "name": "next_task returns highest priority (lowest number)",
                "assert_code": """\
q = TaskQueue()
q.add_task('low', 10)
q.add_task('high', 1)
q.add_task('mid', 5)
result = q.next_task()
assert result == 'high', f'Expected high, got {result}'
"""
            },
            {
                "name": "pending_count is correct",
                "assert_code": """\
q = TaskQueue()
q.add_task('a', 3)
q.add_task('b', 1)
assert q.pending_count() == 2, f'Expected 2, got {q.pending_count()}'
"""
            },
            {
                "name": "run_all returns correct order",
                "assert_code": """\
q = TaskQueue()
q.add_task('deploy', 2)
q.add_task('test', 1)
q.add_task('build', 3)
order = q.run_all()
assert order == ['test', 'deploy', 'build'], f'Got {order}'
"""
            },
            {
                "name": "run_all exhausts the queue",
                "assert_code": """\
q = TaskQueue()
q.add_task('x', 5)
q.add_task('y', 2)
q.run_all()
assert q.pending_count() == 0, f'Queue not empty after run_all: {q.pending_count()}'
"""
            },
            {
                "name": "next_task on empty returns None",
                "assert_code": """\
q = TaskQueue()
assert q.next_task() is None, 'Expected None on empty queue'
"""
            },
        ],
    },

    # ──────────────────────────────────────────────────────────────────
    # EXPERT: LRU Cache with 4 interacting bugs
    # ──────────────────────────────────────────────────────────────────
    "expert": {
        "description": (
            "Fix the LRUCache (Least Recently Used cache) implementation. "
            "`LRUCache(capacity)` creates a cache with a max number of entries. "
            "`get(key)` returns the value for key, or -1 if not present. Accessing a key marks it as most recently used. "
            "`put(key, value)` inserts or updates a key. If at capacity, evicts the least recently used key first. "
            "`size()` returns the current number of entries in the cache. "
            "There are 4 bugs to find and fix."
        ),
        "broken_code": """\
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.order = []  # tracks usage: index 0 = least recent, last = most recent

    def get(self, key):
        if key not in self.cache:
            return -1
        # BUG 1: removes key but forgets to re-append it (so order is wrong after get)
        self.order.remove(key)
        # missing: self.order.append(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.capacity:
            lru = self.order[0]
            del self.cache[lru]
            self.order.pop(0)
        self.cache[key] = value
        # BUG 2: missing self.order.append(key) — order never updated on put

    def size(self):
        # BUG 3: off by one
        return len(self.cache) + 1
""",
        "tests": [
            {
                "name": "basic get returns correct value",
                "assert_code": """\
c = LRUCache(2)
c.put(1, 10)
c.put(2, 20)
assert c.get(1) == 10, f'Expected 10, got {c.get(1)}'
assert c.get(2) == 20, f'Expected 20, got {c.get(2)}'
"""
            },
            {
                "name": "get on missing key returns -1",
                "assert_code": """\
c = LRUCache(2)
c.put(1, 1)
assert c.get(99) == -1, f'Expected -1, got {c.get(99)}'
"""
            },
            {
                "name": "size() is correct",
                "assert_code": """\
c = LRUCache(3)
assert c.size() == 0, f'Expected 0, got {c.size()}'
c.put(1, 1)
assert c.size() == 1, f'Expected 1, got {c.size()}'
c.put(2, 2)
assert c.size() == 2, f'Expected 2, got {c.size()}'
"""
            },
            {
                "name": "LRU eviction evicts least recently used",
                "assert_code": """\
c = LRUCache(2)
c.put(1, 1)
c.put(2, 2)
c.get(1)       # access 1, so 2 is now LRU
c.put(3, 3)    # should evict 2
assert c.get(2) == -1, f'Key 2 should have been evicted, got {c.get(2)}'
assert c.get(1) == 1,  f'Key 1 should still exist, got {c.get(1)}'
assert c.get(3) == 3,  f'Key 3 should exist, got {c.get(3)}'
"""
            },
            {
                "name": "update existing key does not grow cache",
                "assert_code": """\
c = LRUCache(2)
c.put(1, 1)
c.put(1, 100)
assert c.size() == 1,   f'Expected size 1, got {c.size()}'
assert c.get(1) == 100, f'Expected 100, got {c.get(1)}'
"""
            },
            {
                "name": "full eviction sequence",
                "assert_code": """\
c = LRUCache(2)
c.put(1, 1)
c.put(2, 2)
c.put(3, 3)    # evicts 1 (LRU)
assert c.get(1) == -1, f'1 should be evicted'
assert c.get(2) == 2
assert c.get(3) == 3
c.put(4, 4)    # evicts 2 (LRU)
assert c.get(2) == -1, f'2 should be evicted'
assert c.get(3) == 3
assert c.get(4) == 4
"""
            },
        ],
    },
}