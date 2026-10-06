import louisTestVisualizer


def testFunction(testValue):
    louisTestVisualizer.draw(locals())
    m = testValue * 2
    localString = "welcome to the test function"
    louisTestVisualizer.draw(locals())

def main():
    x = 4
    y = 10
    louisTestVisualizer.draw(locals())
    for i in range(10):
        y += 1
        louisTestVisualizer.draw(locals())
    coolString = "awesome freaking string"
    louisTestVisualizer.draw(locals())
    testFunction(5)
    louisTestVisualizer.draw(locals())


if __name__ == "__main__":
    main()