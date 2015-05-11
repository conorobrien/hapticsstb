import numpy as np
import hapticsstb

sample_rate = 3000
sample_length = sample_rate*5

sensor = hapticsstb.STB(sample_rate)

sensor_hist = np.zeros((sample_length,15))

sensor.bias()
print sensor.bias_vector

sensor.start_sampling()

try:
    for ii in range(0,sample_length):
        sensor_hist[ii,0:15] = sensor.readData()
except KeyboardInterrupt:
    pass

sensor.stop_sampling()
sensor.close()