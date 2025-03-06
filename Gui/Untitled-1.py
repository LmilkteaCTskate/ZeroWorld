def a(x,y):
    tmp = x[0]
    x[0] = y[0]
    y[0] = tmp
c=[1,2]
d=[4,5]
a(c,d)
print(c[0],d[0])