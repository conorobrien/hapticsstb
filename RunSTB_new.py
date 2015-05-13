
import numpy as np
import hapticsstb

plot_type = 1

sample_rate = 500
sample_length = sample_rate*5

sensor = hapticsstb.STB(sample_rate)

if plot_type:
    plot = hapticsstb.Plot(plot_type, sample_rate*5)

sensor_hist = np.zeros((sample_length,15))

sensor.bias()
print sensor.bias_vector

sensor.start_sampling()

try:
    for ii in range(0,sample_length):
        # sensor_hist[ii,0:15] = sensor.read_data()
        print sensor.read_M40()
        if plot_type:
            plot.Update(sensor_hist[ii,0:15])

except KeyboardInterrupt:
    pass

sensor.stop_sampling()
sensor.close()

np.savetxt('test.csv', sensor_hist[:(ii+1),0:15], delimiter=",")
