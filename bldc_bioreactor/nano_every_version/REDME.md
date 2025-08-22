# Arduino code for nano every

## Calculation of Timers


rangeFac/(16MHZ/prescaler) = timeout
rangeFac = timeout * frq / prescaler 

### Prescaler versus timeout range

16MHZ - 16bit ~ overflow: 65.536/16MHZ = 4.096 ms
16MHZ - 16bit ~ overflow: 1/16MHZ = 0 ms        
prescaler = 1: range 0ms - 4.096 ms

16MHZ - 16bit ~ overflow: 65.536/(16000000/2)HZ = 8.192 ms
16MHZ - 16bit ~ overflow: 65.536/(16000000/2)HZ = 0 ms            
prescaler = 2: range 0ms - 8.192 ms

prescaler = 4: range 0ms - 16.384 ms
prescaler = 8: range 0ms - 32.768 ms
prescaler = 16: range 0ms - 65.536 ms
prescaler = 32: range 0ms - 131.072 ms
prescaler = 64: range 0ms - 262.144ms ###
prescaler = 128: range 0ms - 524.288ms; step range: 0.008ms
prescaler = 256: range 0ms - 1.048576ms; step range: 0.016ms

1rpm = 1/60 rps = 0.0166 rps 

### timeout to rpm

1 phase ~ 10 deg : 1 rotation 36 phases 
60 seconds per rotation / 36 phases = 1.66 secoonds per phase 
15 rpm : 110ms 
30 rpm : 55.4ms timeout
60 rpm: 27.7ms timeout
120 rpm: 13.8ms timeout 


Flag
periodic Interrupt mode: CAPT

Counter
Set Counter aka range Fac: CCMP (low 0-7, high 8-15)




