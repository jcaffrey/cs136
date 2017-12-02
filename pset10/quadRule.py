import math
import matplotlib.pyplot as plt

p = 0.8
notP = 0.2
points = 1*(10**4) #Number of points
xmin, xmax = 0, 1
xlist = map(lambda x: float(xmax - xmin)*x/points, range(points+1))


print [xlist[x]*xlist[x] for x in range(len(xlist))][:10]
sumQSquared = sum([xlist[x]*xlist[x] for x in range(len(xlist))])
print sumQSquared

def quadScoringSimple(q):
    notQ = 1.0 - q
    try:
        return p*(2*q-((q**2)+(notQ**2))) + notP*(2*notQ-((q**2)+(notQ**2)))
    except:
        print 'woah q is ' + str(q)
        return
# def quadScoring(q):
#     notQ = 1.0 - q
#     try:
#         s = 2*q - sumQSquared
#     except:
#         print 'woah q is ' + str(q)
#         return

ylist = map(lambda q: quadScoringSimple(q), xlist)
plt.plot(xlist, ylist)
plt.xlabel('q')
plt.ylabel('S(q,p) - expected payment')
plt.title('Quadratic Scoring Rule')
plt.axvline(x=.8)
plt.show()
