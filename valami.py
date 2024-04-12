import numpy as np

# Assuming x1, y1, x2, y2 are NumPy arrays
def calculate_distances(x1, y1, x2, y2):
    # Reshape x1 and y1 to column vectors
    x1_col = x1.reshape((-1, 1))
    y1_col = y1.reshape((-1, 1))

    # Reshape x2 and y2 to row vectors
    x2_row = x2.reshape((1, -1))
    y2_row = y2.reshape((1, -1))

    # Calculate the squared differences
    dx_squared = (x1_col - x2_row) ** 2
    dy_squared = (y1_col - y2_row) ** 2

    # Calculate the Euclidean distances
    distances = np.sqrt(dx_squared + dy_squared)

    return distances

# Example usage:
x1 = np.array([1, 2, 3])
y1 = np.array([4, 5, 6])
x2 = np.array([7, 8, 9])
y2 = np.array([10, 11, 12])

d = calculate_distances(x1, y1, x2, y2)
row_indices, col_indices = np.where(d > 8)
print(row_indices, col_indices)