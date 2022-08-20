import numpy as np
from scipy import special

def right_of_x(x):
    return 1 - left_of_x(x)

def left_of_x(x):
    return 0.5 * (1+special.erf(x/np.sqrt(2)))

def left_of_x_uni(x):
    return np.clip(x,0.0,1.0)

# Test n_V = 1,2,...,n_max as the number of draws from the distribution
n_max = 10

# test each value of n_V this many times for significance in the distribution of max-values
n_samples = 10000

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

n_v_max = 50
accuracy=0.001
t=np.zeros((n_v_max,2),dtype=float)
print(f'n \t tau_norm \t p_norm \t tau_uni \t p_uni')
for n in np.arange(n_v_max)+1:    # [1,7,33,123,257,515,925,1419,2109,3071]:
    max_values_norm = np.zeros(n_samples)
    max_values_uni = np.zeros(n_samples)
    for j in np.arange(n_samples):
        max_values_norm[j] = np.max(np.random.randn(n))
        max_values_uni[j] = np.max(np.random.rand(n))
    tau_norm=1.0
    p_norm = 0
    while p_norm < tau_norm and tau_norm > 0.01:
        tau_norm -= accuracy #0.0001
        p_norm = left_of_x(np.percentile(max_values_norm, (1 - tau_norm) * 100))
    t[n-1,0]=tau_norm

    tau_uni = 1.0
    p_uni = 0
    while p_uni < tau_uni and tau_uni > 0.01:
        tau_uni -= accuracy #0.0001
        p_uni = left_of_x_uni(np.percentile(max_values_uni, (1 - tau_uni) * 100))
    t[n-1,1]=tau_uni

    print(f'{n} \t {tau_norm:.4f} \t {p_norm:.4f} \t {tau_uni:.4f} \t {p_uni:.4f}')
    #print('-------------------------------------------')