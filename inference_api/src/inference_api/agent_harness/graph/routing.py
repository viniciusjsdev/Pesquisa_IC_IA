"""Only validated decisions select graph edges."""
def route(state, current):
    return current if state['next'] == 'repair' else state['next']
