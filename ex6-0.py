import pyxel

pyxel.init(200,200)

a = 0

while True:
    pyxel.cls(7)
    pyxel.circ(a, a, 10, 0)
    pyxel.flip()
    a += 1
