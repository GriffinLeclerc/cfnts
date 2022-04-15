import statistics as stats

def mapInt(num):
    return int(num)

def percent(num):
    return (num * 100)

def printThresh(l, threshold):
    count = len(l)
    outliers = list(filter(lambda n: n > threshold, l))
    threshCount = len(outliers)

    print("Values above " + str(threshold))
    print("     Number: " + str(threshCount))
    percent = '%.2f'%((threshCount/count) * 100)
    print("     Ratio: " + str(threshCount) + "/" + str(count) + " | or " + percent + "%")

def printInfo(lines):    
    print("Num Measurements: " + str(len(lines)))
    print("Avg: " + str(stats.mean(lines)))
    print("Min: " + str(min(lines)))
    print("Max: " + str(max(lines)))
    print("Mid: " + str(stats.median(lines)))


file1 = open('results/server_ntp_enc', 'r')
lines = list(map(mapInt, file1.readlines()))

printInfo(lines)

printThresh(lines, 3000) 
printThresh(lines, 4000)
printThresh(lines, 5000)
printThresh(lines, 6000)
printThresh(lines, 10000)
