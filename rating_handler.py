# Currently implements the ELO system

# returns list of new rating of A and B
def get_new_ratings(A, B, outcome):
    # A = int, B = int, outcome = 1 if A won, 0.5 if A tied, 0 if A lost
    k = 32
    EA = 1 / (1 + 10**((B-A)/400))
    EB = 1 / (1 + 10**((A-B)/400))

    newA = A + k * (outcome - EA)
    newB = B + k * (outcome - EB)

    return [newA, newB]

# compares two rating objects
def compare(A, B):
    return A - B