#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Algorithms for search."""
import abc
import six
import time
import heapq
import collections


class TimeoutError(Exception):
    """Exception raised when a function call times out."""
    pass


@six.add_metaclass(abc.ABCMeta)
class Search:
    """A type of search."""

    @abc.abstractmethod
    def create_queue(self):
        """Create a queue for storing the states in the search."""
        raise NotImplementedError()

    def is_new(self, state, seen, prbolem):
        """Check if a state is new."""
        return state not in seen

    def add_to_seen(self, state, seen, problem):
        """Add a state to seen set."""
        seen.add(state)

    def create_seen_set(self):
        """Create a structure to store information of states seen."""
        return set()

    def push_if_new(self, queue, state, seen, problem):
        """Add a state to the queue if it hasn't been evaluated yet."""
        if state not in seen:
            self.push(queue, state)
            self.add_to_seen(state, seen, problem)

    @abc.abstractmethod
    def push(self, queue, state):
        """Add a state to the queue."""
        raise NotImplementedError()

    @abc.abstractmethod
    def pop(self, queue):
        """Get the next state from the queue."""
        raise NotImplementedError()

    def branch(self, problem, state):
        """Branch a state into its possible continuations."""
        actions = problem.actions(state)
        new_states = []
        for action in actions:
            new_state = action(state)
            try:
                new_state._action_history = state._action_history + [action]
            except:
                new_state._action_history = [action]

            new_states.append(new_state)

        return new_states

    def solve(self, problem, initial_state=None, timeout=None):
        """Get a solution to the problem."""
        if not timeout:
            timeout = float('inf')

        start = time.time()
        initial_state = initial_state or problem.initial_state()

        queue = self.create_queue()
        seen = self.create_seen_set()
        self.push_if_new(queue, initial_state, seen, problem)

        while len(queue) > 0:
            current = time.time()
            if current - start > timeout:
                raise TimeoutError()

            state = self.pop(queue)
            if problem.is_solution(state):
                return state

            branched_states = self.branch(problem, state)
            for branched_state in branched_states:
                self.push_if_new(queue, branched_state, seen, problem)

        return None


class BreadthFirstSearch(Search):
    """
    A breadth first search.

    >>> bfs = BreadthFirstSearch()
    >>> q = bfs.create_queue()
    >>> bfs.push(q, 1)
    >>> bfs.push(q, 2)
    >>> len(q)
    2
    >>> bfs.pop(q)
    1
    >>> len(q)
    1
    """

    def create_queue(self):
        """Create a FIFO queue for storing the states in the search."""
        return collections.deque()

    def push(self, queue, state):
        """Add a state to the queue."""
        queue.append(state)

    def pop(self, queue):
        """Get the next state from the queue."""
        return queue.popleft()


class DepthFirstSearch(Search):
    """
    A depth first search.

    >>> dfs = DepthFirstSearch()
    >>> q = dfs.create_queue()
    >>> dfs.push(q, 1)
    >>> dfs.push(q, 2)
    >>> len(q)
    2
    >>> dfs.pop(q)
    2
    >>> len(q)
    1
    """

    def create_queue(self):
        """Create a LIFO stack for storing the states in the search."""
        return []

    def push(self, queue, state):
        """Add a state to the stack."""
        queue.append(state)

    def pop(self, queue):
        """Get the next state from the stack."""
        return queue.pop()


class BestFirstSearch(Search):
    """An optiminal search."""

    def __init__(self, heuristic=None):
        """
        Initialize an instance of A* search.

        The instance requires an heuristic function which
        receives a state and outputs an expected delta for the solution.

        The heuristic must be admissible to ensure an optimal solution.

        If no heuristic is provided, the Zero Heuristic is used.

        >>> a = BestFirstSearch()
        >>> a.heuristic(1)
        0
        >>> a.heuristic("Sample")
        0
        """
        self.heuristic = heuristic or ZeroHeuristic()
        self.value_states_dict = {}

    def create_queue(self):
        """Create a priority queue for storing the states in the search."""
        return []

    def push(self, queue, state, value=None):
        """
        Add a state to the priority queue.

        Manage the priority queue as a heap of (value, stack),
        where stack contains all the states with the same value.

        This minimizes the number of times the heap is used.

        States are retrieved using LIFO in order to try a depth first approach.

        [value] => stack
        relationships are stored in the variable self.value_states_dict
        """
        if value is None:
            g = state.value
            h = self.heuristic(state)
            f = g + h
        else:
            f = value

        if f in self.value_states_dict:
            stack = self.value_states_dict[f]
        else:
            stack = []
            self.value_states_dict[f] = stack
            heapq.heappush(queue, (f, stack))

        stack.append(state)

    def pop(self, queue):
        """Get the next state from the priority queue."""
        value, stack = queue[0]
        element = stack.pop()

        if not stack:
            heapq.heappop(queue)
            del self.value_states_dict[value]

        return element


class IterativeDepthFirstSearch(BestFirstSearch):
    """
    An optimal iterative search.

    This algorithm iteratively improves the found solution until it's optimal
    or time runs out.
    """

    def sort_states(self, problem, states):
        """Sort branched states before insertion."""
        pass

    def pop(self, queue):
        """Get the next state from the priority queue."""
        value, stack = queue[0]
        element = stack.pop()

        if not stack:
            heapq.heappop(queue)
            del self.value_states_dict[value]

        return value, element

    def solve(self, problem, initial_state=None,
              timeout=None, soft_timeout=None):
        """Get a solution to the problem."""
        if not timeout:
            timeout = float('inf')

        if not soft_timeout:
            soft_timeout = min(timeout, float('inf'))

        start = time.time()
        initial_state = initial_state or problem.initial_state()
        initial_heuristic_value = initial_state.value + self.heuristic(
            initial_state)

        queue = self.create_queue()
        seen = self.create_seen_set()
        self.push_if_new(queue, initial_state, seen, problem)

        best_solution = None
        best_value = float('inf')

        while len(queue) > 0:
            value, state = self.pop(queue)

            if value >= best_value:
                break

            current = time.time()
            ellapsed_time = current - start

            if best_solution and ellapsed_time > soft_timeout:
                break
            elif ellapsed_time > timeout:
                raise TimeoutError()

            remaining_time = timeout - ellapsed_time
            new_solution = self.run(
                problem, state, queue, seen, remaining_time)

            if new_solution:
                new_value = new_solution.value

                if new_value < best_value or not best_solution:
                    best_solution = new_solution
                    best_value = new_value

        return best_solution

    def run(self, problem, initial_state, queue, seen,
            timeout=None):
        """
        Get a temporary solution.

        Multiple calls to run function will improve on the initial solution.
        """
        if not timeout:
            timeout = float('inf')

        start = time.time()
        reached_solution = False
        current_state = initial_state
        while True:
            current = time.time()
            if current - start > timeout:
                break

            if problem.is_solution(current_state):
                reached_solution = True
                break

            branched_states = self.branch(problem, current_state)
            branched_states = filter(
                lambda x: self.is_new(x, seen, problem),
                branched_states
            )

            self.sort_states(problem, branched_states)

            new_seen = self.create_seen_set()
            new_states = []
            for state in branched_states:
                if not new_seen or self.is_new(state, new_seen, problem):
                    new_states.append(state)
                    self.add_to_seen(state, new_seen, problem)

            if new_states:
                new_states.reverse()

                # Continue the run through the first state
                current_state = new_states[0]

                # Store the rest for another run
                new_values = [state.value + self.heuristic(state)
                              for state in new_states]

                values_with_states = zip(new_values, new_states)
                for value, state in values_with_states[1:]:
                    self.push(queue, state, value=value)
                    self.add_to_seen(state, seen, problem)

            else: # No way to continue this run
                break

        return current_state if reached_solution else None


class GreedySearch(Search):
    """A greedy search."""

    def create_queue(self):
        """Create a queue for storing the states in the search."""
        return []

    def push(self, queue, state):
        """Add a state to the queue."""
        if not queue or queue[0].value > state.value:
            del queue[:]
            queue.append(state)

    def pop(self, queue):
        """Get the next state from the queue."""
        return queue.pop()

    def solve(self, problem, initial_state=None, timeout=None):
        """Get a solution to the problem."""
        if not timeout:
            timeout = float('inf')

        start = time.time()
        initial_state = initial_state or problem.initial_state()

        seen = self.create_seen_set()
        queue = self.create_queue()
        self.push_if_new(queue, initial_state, seen, problem)

        best_solution = initial_state
        best_value = initial_state.value

        while len(queue) > 0:
            current = time.time()
            if current - start > timeout:
                break

            current_state = self.pop(queue)
            if current_state.value > best_value:
                break
            else:
                best_solution = current_state
                best_value = current_state.value

            branched_states = self.branch(problem, current_state)
            for branched_state in branched_states:
                self.push_if_new(queue, branched_state, seen, problem)

        return best_solution


@six.add_metaclass(abc.ABCMeta)
class Heuristic:
    """An evaluation function used for heuristic purposes."""

    @abc.abstractmethod
    def __call__(self, state):
        """Evaluate a state."""
        raise NotImplementedError()


class ZeroHeuristic(Heuristic):
    """
    The Zero Heuristic.

    >>> h = ZeroHeuristic()
    >>> h(1)
    0
    >>> h("state")
    0
    """

    def __call__(self, state):
        """Evaluate a state, return zero."""
        return 0


def unit_test():
    """Test the module."""
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    unit_test()
