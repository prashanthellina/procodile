from procodile.buildspace import Location
import math

a = Location()
b = Location()
a.rotate((math.pi/2, (0, 0, 1)))
b.rotate((math.pi*1.5, (0, 0, 1)))

print a
print b

b1 = Location(b)
ainv = Location(a)
ainv.invert()
print b1.transform(ainv)
