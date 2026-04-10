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
}