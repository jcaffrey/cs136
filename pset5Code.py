import random

def ROP():
    # bidders in b1 face the optimal price based on bids in b2
        # optimal price defined as max revenue
    # and vice versa
    # really just need to decide whether to charge 1 or 10
    (b1,b2) = generateBins()

    (optB2, tensB2) = ROPOptPrice(b2)
    (optB1, tensB1) = ROPOptPrice(b1)

    revenue = 0

    if optB2 == 1:
        # charge 1 to everyone in b1
        revenue += len(b1)
    else:
        # charge ten
        revenue += tensB1 * 10

    if optB1 == 1:
        # charge 1 to everyone
        revenue += len(b2)
    else:
        # charge 10
        revenue += tensB2 * 10

    return revenue

# RSPE will likely charge 10 more often
def RSPE():
    (b1,b2) = generateBins()

    r1 = max(b1)
    r2 = max(b2)

    revenue = 0

    if r1 == 1:
        revenue += len(b2)
    else:
        # calc tens in b2
        for i in range(len(b2)):
            if b2[i] == 10:
                revenue += 10
    if r2 == 1:
        revenue += len(b1)
    else:
        # calc tens in b2
        for i in range(len(b1)):
            if b1[i] == 10:
                revenue += 10
    return revenue

def ROPOptPrice(b):
    optPrice = 0
    ones = 0
    tens = 0
    for i in range(len(b)):
        if b[i] == 1:
            ones += 1
        else:
            tens += 1

    if ones + tens > tens * 10:
        optPrice = 1
    else:
        optPrice = 10

    return (optPrice, tens)


def generateBins():
    a = []
    for i in range(100):
        if i < 10:
            a.append(10)
        else:
            a.append(1)
    b1 = []
    b2 = []

    for i in range(100):
        r = random.choice(a)
        if r == 1:
            #delete that 1
            a = a[:-1]
        else:
            #delete that 10
            a = a[1:]
        # place r into a certain bin on coin flip
        coin = random.randint(1,2)
        if coin == 1:
            b1.append(r)
        else:
            b2.append(r)

    return (b1,b2)

rop = 0
rspe = 0
for i in range(100):
    rop += ROP()
    rspe += RSPE()

print rop / 100.0
print rspe / 100.0

# print generateBins()
