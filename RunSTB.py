
import numpy as np
import hapticsstb

plot_type = hapticsstb.PLOT_M40V

sample_rate = 500

sensor = hapticsstb.STB(sample_rate, pedal=True)

# Preallocate hist vector, use sensor.sample_rate since sample rate changes if you turn graphing on
sample_length = sensor.sample_rate*600
sensor_hist = np.zeros((sample_length,15))

if plot_type:
    sensor.plot_init(plot_type, 5)


sensor.bias()
print sensor.bias_vector

sensor.start_sampling()

print '*'*80
print "Waiting for Pedal Input"
print '*'*80

while sensor.pedal() != 1:
    pass

print '*'*80
print "Starting Sampling ..."
try:
    for ii in range(0,sample_length):
        sensor_hist[ii, 0:15] = sensor.read_data()
        if plot_type:
            sensor.plot_update()

        if sensor.pedal() == 2:
            print '*'*80
            print "Pedal Break, Finishing Testing"
            print '*'*80
            break
            
except KeyboardInterrupt:
    pass

except:
    sensor.close()
    raise


sensor.stop_sampling()
sensor.close()

np.savetxt('test.csv', sensor_hist[:(ii+1),0:15], delimiter=",")
