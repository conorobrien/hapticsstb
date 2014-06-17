# cython: profile=True

import numpy as np
cimport numpy as np
import time



def Raw2FT(str x, np.ndarray[np.float64_t, ndim = 2] FT_transform, np.ndarray[np.float64_t, ndim = 2] bias):
	C = np.zeros((6,1), dtype = np.float64)
	#cdef np.ndarray[np.float64_t, ndim = 2] FT = np.zeros((6,1))
	cdef int i, j, y

	for i in range(0,6):
		j = i*2
		y = (ord(x[j])<<8) + (ord(x[j+1]))
		if y > 2048:
			C[5-i] = <float>(y - 4096)*0.0025
		else:
			C[5-i] = <float>y*0.0025
		# C[5-i] = Raw2Volts(x[j:(j+2)])


	return np.dot(FT_transform, (C - bias))

	

