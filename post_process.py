import statistics as stats

file1 = open('res', 'r')
lines = file1.readlines()

def mapInt(num):
    return int(num)

def printThresh(l, threshold):
    outliers = list(filter(lambda n: n > threshold, l))
    threshCount = len(outliers)
    print("Values above " + str(threshold))
    print("     Number: " + str(threshCount))
    print("     Ratio: " + str(threshCount) + "/" + str(count) + " | or " + str(threshCount/count))


lines = list(map(mapInt, lines))
count = len(lines)
    
print("Num Measurements: " + str(count))
print("Avg: " + str(stats.mean(lines)))
print("Min: " + str(min(lines)))
print("Max: " + str(max(lines)))

printThresh(lines, 200)
printThresh(lines, 300)
printThresh(lines, 500)