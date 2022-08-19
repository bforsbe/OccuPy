import numpy as np
from scipy import special

def right_of_x(x):
    return 1 - left_of_x(x)

def left_of_x(x):
    return 0.5 * (1+special.erf(x/np.sqrt(2)))

# Test n_V = 1,2,...,n_max as the number of draws from the distribution
n_max = 10

# test each value of n_V this many times for significance in the distribution of max-values
n_samples = 1000000

# prob thresholds
p = [0.5,0.6,0.7,0.8,0.9, 0.95, 0.99]

out=np.zeros(n_max)

# print(f'n_V \t tau')
#
# p_str='     \t'
# for k in p:
#     p_str = f'{p_str} \t {k:.3f} '
# print(f'     \t {p_str}')
# print(f'----------------------------------------------------------------------------------------')
#
# for i in np.arange(n_max):
#     max_values = np.zeros(n_samples)
#     for j in np.arange(n_samples):
#         max_values[j] = np.max(np.random.randn(i + 1))
#     #The estimated mean of the max-value distribution
#     v = left_of_x(np.mean(max_values))
#     p_str=f'{v:.3f} \t '
#     for k in p:
#         v = left_of_x(np.percentile(max_values,(1-k)*100))
#         p_str = f'{p_str} \t {v:.3f} '
#
#     print(f'{i+1} \t {p_str}')

print(f'n \t tau \t p')
for n in [1,7,33,123,257,515,925,1419,2109,3071]:
    max_values = np.zeros(n_samples)
    for j in np.arange(n_samples):
        max_values[j] = np.max(np.random.randn(n))
    tau=1.0
    p = 0
    while p < tau and tau > 0.01:
        tau -= 0.0001
        p = left_of_x(np.percentile(max_values,(1-tau)*100))
    print(f'{n} \t {tau:.4f} \t {p:.4f}')
    #print('-------------------------------------------')