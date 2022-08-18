import numpy as np
from scipy import special

def right_of_x(x):
    return 1 - left_of_x(x)

def left_of_x(x):
    return 0.5 * (1+special.erf(x/np.sqrt(2)))

# Test n_V = 1,2,...,n_max as the number of draws from the distribution
n_max = 50

# test each value of n_V this many times for significance in the distribution of max-values
n_samples = 10000

out=np.zeros(n_max)

print(f'n_V \t tau')
for i in np.arange(n_max):
    max_values = np.zeros(n_samples)
    for j in np.arange(n_samples):
        max_values[j] = np.max(np.random.randn(i + 1))
    #The estimated mean of the max-value distribution
    out[i] = left_of_x(np.mean(max_values))
    print(f'{i+1} \t {out[i]:.4f}')
