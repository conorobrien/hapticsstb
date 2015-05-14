
import numpy as np
import hapticsstb

plot_type = hapticsstb.PLOT_FT

sample_rate = 500
sample_length = sample_rate*30

sensor = hapticsstb.STB(sample_rate)

if plot_type:
    sensor.plot_init(plot_type, 5)

sensor_hist = np.zeros((sample_length,15))

sensor.bias()
print sensor.bias_vector

sensor.start_sampling()

try:
    for ii in range(0,sample_length):
        sensor_hist[ii, 0:15] = sensor.read_data()
        if plot_type:
            sensor.plot_update()

except KeyboardInterrupt:
    pass

except:
	sensor.close()
	raise


sensor.stop_sampling()
sensor.close()

np.savetxt('test.csv', sensor_hist[:(ii+1),0:15], delimiter=",")
