#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Algorithms for search."""
import collections
import heapq
import time


class Search:
    """A type of search."""

    def create_queue(self):
        """Create a queue for storing the states in the search."""
        raise NotImplementedError()

    def create_seen_set(self):
        """Create a structure to store information of states seen."""
        return set()

    def push_if_new(self, queue, state, seen, problem):
        """Add a state to the queue if it hasn't been evaluated yet."""
        if state not in seen:
            self.push(queue, state)
            seen.add(state)

    def push(self, queue, state):
        """Add a state to the queue."""
        raise NotImplementedError()

    def pop(self, queue):
        """Get the next state from the queue."""
        raise NotImplementedError()

    def solve(self, problem, initial_state=None, timeout=None):
        """Get a solution to the problem."""
        if timeout:
            start = time.time()

        initial_state = initial_state or problem.initial_state()

        queue = self.create_queue()
        seen = self.create_seen_set()
        self.push_if_new(queue, initial_state, seen, problem)

        while len(queue) > 0:
            if timeout:
                current = time.time()
                if current - start > timeout:
                    raise Exception("Function timed out.")

            state = self.pop(queue)
            if problem.is_solution(state):
                return state

            new_states = problem.branch(state)
            for state in new_states:
                self.push_if_new(queue, state, seen, problem)

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


class AStarSearch(Search):
    """An optiminal search."""

    def __init__(self, heuristic=None):
        """
        Initialize an instance of A* search.

        The instance requires an heuristic function which
        receives a state and outputs an expected delta for the solution.

        The heuristic must be admissible to ensure an optimal solution.

        If no heuristic is provided, the Zero Heuristic is used.

        >>> a = AStarSearch()
        >>> a.heuristic(1)
        0
        >>> a.heuristic("Sample")
        0
        """
        self.heuristic = heuristic
        self.value_states_dict = {}
        if not heuristic:
            self.heuristic = ZeroHeuristic()

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


class IterativeDepthFirstSearch(AStarSearch):
    """
    An optiminal iterative search.
    This algorithm iteratively improves the found solution until it's optimal
    or time runs out.
    """

    def pop(self, queue):
        """Get the next state from the priority queue."""
        value, stack = queue[0]
        element = stack.pop()

        if not stack:
            heapq.heappop(queue)
            del self.value_states_dict[value]

        return value, element

    def solve(self, problem, initial_state=None, timeout=None):
        """Get a solution to the problem."""
        if timeout:
            start = time.time()

        initial_state = initial_state or problem.initial_state()
        initial_heuristic_value = initial_state.value + self.heuristic(
            initial_state)
        print "Optimum might be %s" % initial_heuristic_value

        queue = self.create_queue()
        seen = self.create_seen_set()
        self.push_if_new(queue, initial_state, seen, problem)

        best_solution = None
        best_value = float('inf')

        while len(queue) > 0:
            if timeout:
                current = time.time()
                if current - start > timeout:
                    return best_solution

            value, state = self.pop(queue)

            if value >= best_value:
                return best_solution

            new_solution = self.run(problem, state, queue, seen)
            if new_solution:
                new_value = new_solution.value

                if new_value <= initial_heuristic_value:
                    return new_solution

                if best_solution:
                    if new_value < best_value:
                        best_solution = new_solution
                        best_value = new_value
                else:
                    best_solution = new_solution
                    best_value = new_value

        return None

    def run(self, problem, initial_state, queue, seen):
        """
        Get a temporary solution.

        Multiple calls to run function will improve on the initial solution.
        """
        current_state = initial_state
        while True:
            if problem.is_solution(current_state):
                return current_state

            branched_states = [state for state in problem.branch(current_state)
                               if self.is_new(state, seen, problem)]

            new_seen = self.create_seen_set()
            new_states = []
            for state in branched_states:
                if not new_seen or self.is_new(state, new_seen, problem):
                    new_states.append(state)
                    self.add_to_seen(state, new_seen, problem)

            new_values = [state.value + self.heuristic(state)
                          for state in new_states]

            values_with_states = sorted(zip(new_values, new_states))

            if values_with_states:
                current_state = values_with_states[0][1]
                for value, state in values_with_states[1:]:
                    self.push(queue, state, value=value)
                    self.add_to_seen(state, seen, problem)
            else:
                break

        return None


class Heuristic:
    """An evaluation function used for heuristic purposes."""

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
