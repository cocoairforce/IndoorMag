import numpy as np
import re
import glob
from scipy import interpolate
from math import *
import random
import matplotlib.pyplot as plt

walk = glob.glob('C:\Users\RP\Desktop\library_samples\lib_samples\*_w1_*.csv')

world_x = 2
world_y = 50
x0 = np.arange(0,3,1)
y0 = np.arange(0,51,1)
loc_prob = []
        
mag_map = []
for i in range(world_x+1):
      mag_map.append([])
      for j in range(world_y+1):
         mag_map[i].append(0)

for i in range(len(walk)):
     x,y,z = np.loadtxt(walk[i],delimiter =',', usecols=(2,3,4),unpack=True)
     a = int(re.split('\D+',walk[i])[1])
     mag = np.sqrt(x**2 + y**2 + z**2)
     mag_map[(a-52)/(world_y+1)][(a-52)%(world_y+1)] = np.mean(mag)

f = interpolate.interp2d(x0,y0,mag_map,kind = 'linear')     

class robot:
    def __init__(self):
        self.x = random.random() * world_x
        self.y = random.random() * world_y
        self.orientation = random.random() * 2.0 * pi
        self.forward_noise = 0.0;
        self.turn_noise    = 0.0;
        self.sense_noise   = 0.0;
        self.outside = 0

    def set_ori(self, new_orientation):
        if new_orientation < 0 or new_orientation >= 2 * pi:
            raise ValueError, 'Orientation must be in [0..2pi]'
        self.orientation = float(new_orientation)

    def set_pos(self, new_x, new_y):
        if new_x < 0 or new_x >= world_x:
            raise ValueError, 'X coordinate out of bound'
        if new_y < 0 or new_y >= world_y:
            raise ValueError, 'Y coordinate out of bound'
        self.x = float(new_x)
        self.y = float(new_y)
        
    def set(self, new_x, new_y, new_orientation):
        if new_x < 0 or new_x >= world_x:
            raise ValueError, 'X coordinate out of bound'
        if new_y < 0 or new_y >= world_y:
            raise ValueError, 'Y coordinate out of bound'
        if new_orientation < 0 or new_orientation >= 2 * pi:
            raise ValueError, 'Orientation must be in [0..2pi]'
        self.x = float(new_x)
        self.y = float(new_y)
        self.orientation = float(new_orientation)

    
    def set_noise(self, new_f_noise, new_t_noise, new_s_noise):
        # makes it possible to change the noise parameters
        # this is often useful in particle filters
        self.forward_noise = float(new_f_noise);
        self.turn_noise    = float(new_t_noise);
        self.sense_noise   = float(new_s_noise);
    
    
    def sense(self):
        return  f(self.x,self.y)+random.gauss(0.0,self.sense_noise)
    
    def move(self, turn, forward):
        if forward < 0:
            raise ValueError, 'Robot cant move backwards'         
        
        # turn, and add randomness to the turning command
        orientation = self.orientation + float(turn) + random.gauss(0.0, self.turn_noise)
        orientation %= 2 * pi
        
        # move, and add randomness to the motion command
        dist = float(forward) + random.gauss(0.0, self.forward_noise)
        x = self.x + (cos(orientation) * dist)
        y = self.y + (sin(orientation) * dist)
        out = 0
        if (x > world_x or x < 0):
              out = 1# cyclic truncate
        y %= world_y
        x %= world_x
        
        # set particle
        res = robot()

        if (out):
            res.outside = 1
            
        res.set(x, y, orientation)
        res.set_noise(self.forward_noise, self.turn_noise, self.sense_noise)
        return res
    
    def Gaussian(self, mu, sigma, x):
        # calculates the probability of x for 1-dim Gaussian with mean mu and var. sigma
        return exp(- ((mu - x) ** 2) / (sigma** 2) / 2.0) / sqrt(2.0 * pi * (sigma ** 2))

    def sudogauss(self, mu, sigma, x):
        # calculates the probability of x for 1-dim Gaussian with mean mu and var. sigma
        return exp(- ((mu - x) ** 2) / (sigma** 2) / 2.0) / 2.0
     
    def measurement_prob(self, measurement):   
        # calculates how likely a measurement should be     
        prob = 1.0;
        if(not self.outside):
              postion_mag = f(self.x,self.y)
              prob *= self.Gaussian(postion_mag,self.sense_noise,measurement)
        else:
              prob = 0.0
        #print measurement, postion_mag, prob
        return prob
    
    def __repr__(self):
        return '[x=%.6s y=%.6s orient=%.6s]' % (str(self.x), str(self.y), str(self.orientation))

def plot_part(p,s):
      x = []
      y = []
      for i in p:
          x.append(i.x)
          y.append(i.y)
      plt.plot(x,y,s)
      plt.xlabel("x")
      plt.ylabel("y")
      plt.xlim(0.,2.)
      plt.ylim(0.,50.)
      plt.show()
      plt.xlabel

def resample_weights(weights,particles):
     n = len(weights)
     indices = []
     l = sum(w)
     #print "l", l
     px = []
     py = []
     for i in range(len(p)):
        px.append(p[i].x)
        py.append(p[i].y)   

     for i in  range(len(weights)):
           w[i] /= l
     C = [0.] + [sum(weights[:i+1]) for i in range(n)]
     u0, j = random.random(), 0
     itu = [(u0+i)/n for i in range(n)]
     for u in itu:
       while u > C[j]:
         j+=1
       indices.append(particles[j-1])
     return indices

def resample_weights_cs373(weights,particles):
    p3 = []
    index = int(random.random() * N)
    beta = 0.0
    mw = max(weights)
    for i in range(N):
        beta += random.random() * 2.0 * mw
        while beta > weights[index]:
            beta -= weights[index]
            index = (index + 1) % N
        p3.append(particles[index])
    return p3

def eval(r, p):
    sum = 0.0;
    for i in range(len(p)): # calculate mean error
        dx = (p[i].x - r.x + (world_x/2.0)) % world_x - (world_x/2.0)
        dy = (p[i].y - r.y + (world_y/2.0)) % world_y - (world_y/2.0)
        err = sqrt(dx * dx + dy * dy)
        sum += err
    return sum / float(len(p))

mmse = []
error = []
j = 0
for i in [100,250,500,1000,1500,2000,3000,5000]:
      N = i
      
      myrobot = robot()
      myrobot.set(1.0,0.0,np.pi/2)
      myrobot.set_noise(0.2,0.0,2.0)

      Z = myrobot.sense()
      mmse.append([])
      error.append([])

      p = []
      for i in range(N):
          r = robot()
          a = np.pi/2
          r.set_pos(1.0,0.0)
          #r.set_ori(a) 
          r.set_noise(0.3,0.05,2.0)
          p.append(r)
      for t in range(25):
          myrobot = myrobot.move(0.0, 2.0)
          Z = myrobot.sense()
      
          p2 = []
          for i in range(N):
              p2.append(p[i].move(0.0,2.0))
          p = p2

          w = []
          for i in range(N):
              w.append(p[i].measurement_prob(Z))
          
          p = resample_weights(w,p) 
          mmse[j].append(eval(myrobot,p))
          est = robot()
          est.set(0.0,0.0,0.0)
          nor = 0.0
          for i in w:
                 nor += i 
          for i in range(len(w)):
                est.x += w[i]*(p[i].x)
                est.y += w[i]*(p[i].y)
          est.x /= nor
          est.y /= nor
          error[j].append(eval(myrobot,[est]))
          print "Estimate - {",est.x,",", est.y, "}"
          print "real- ", myrobot.x ,myrobot.y
      j+=1    
         
          
fig = plt.figure()
plt.plot(mmse[0],'b-',label = 'MMSE-100')
plt.plot(mmse[1],'g-',label = 'MMSE-250')
plt.plot(mmse[2],'r-',label = 'MMSE-500')
plt.plot(mmse[3],'c-',label = 'MMSE-1000')
plt.plot(mmse[4],'m-',label = 'MMSE-1500')
plt.plot(mmse[5],'k-',label = 'MMSE-2000')
plt.plot(mmse[6],'b--',label = 'MMSE-3000')
plt.plot(mmse[7],'g--',label = 'MMSE-5000')

plt.ylim(0,20)
plt.xlabel('no. of steps ( x 0.6 m)')
plt.ylabel('Error(x 0.3 m)')
plt.suptitle(' par{f = 0.3,t = 0.05,s = 2.0}{Rob - f = 0.20,s n= 2.0}-Initial-pos')
legend = plt.legend(loc='best', shadow=True)
frame = legend.get_frame()
frame.set_facecolor('0.90')
fig.savefig('MMSE-2.jpg')

fig1 = plt.figure()
plt.plot(error[0],'b-',label = 'Error-100')
plt.plot(error[1],'g-',label = 'Error-250')
plt.plot(error[2],'r-',label = 'Error-500')
plt.plot(error[3],'c-',label = 'Error-1000')
plt.plot(error[4],'m-',label = 'Error-1500')
plt.plot(error[5],'k-',label = 'Error-2000')
plt.plot(error[6],'b--',label = 'Error-3000')
plt.plot(error[7],'g--',label = 'Error-5000')

plt.ylim(0,20)
plt.xlabel('no. of steps ( x 0.6 m)')
plt.ylabel('Error(x 0.3 m)')
plt.suptitle(' par{f = 0.3,t = 0.05,s = 2.0}{Rob - f = 0.20,s n= 2.0}-Initial-pos')
legend = plt.legend(loc='best', shadow=True)
frame = legend.get_frame()
frame.set_facecolor('0.90')
fig1.savefig('Error-2.jpg')
 
    

    

