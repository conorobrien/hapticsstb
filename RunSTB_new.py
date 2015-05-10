import numpy as np
import hapticsstb

sample_rate = 3000
sample_length = sample_rate*5

sensor = hapticsstb.STB(3000)

sensor_hist = np.zeros((sample_length,15))

sensor.bias()
print sensor.bias_vector

sensor.start_sampling()

for ii = range(0,sample_length):
    sensor_hist[ii,0:15] = sensor.readData()




