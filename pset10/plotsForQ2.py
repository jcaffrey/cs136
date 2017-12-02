import math
import matplotlib.pyplot as plt

p = 0.8
notP = 0.2

def logScoring(q):
    notQ = 1.0 - q
    try:
        return p * math.log(q) + notP * math.log(notQ)
    except:
        print 'woah q is ' + str(q)
        return

points = 1*(10**4) #Number of points
xmin, xmax = 0.0001, .99999
xlist = map(lambda x: float(xmax - xmin)*x/points, range(points+1))
ylist = map(lambda q: logScoring(q), xlist)
plt.plot(xlist, ylist)
plt.xlabel('q')
plt.ylabel('S(q,p) - expected payment')
plt.title('Logarithmic Scoring Rule')
plt.axvline(x=.8)
plt.show()
