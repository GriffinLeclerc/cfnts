import statistics as stats
import matplotlib.pyplot as plt
import os
import numpy as np
import yaml

plotRequestNums = []
clientKELineNums = []
clientNTPLineNums = []

percentagesGreaterThan5s = []

def mapInt(num):
    return int(num)

def cullOutliers(data):
    avg = stats.mean(data)
    newData = []

    for point in data:
        if point < avg * 1000:
            newData.append(point)

    return newData

def relevantRequestNums(filename):
    if "ke" in filename:
        return clientKELineNums
    else:
        return clientNTPLineNums

# determines if the file in question has request number delimiters
def hasRequestNums(filename):
    with open(filename, 'r') as file:
        if "request" in file.read():
            return True
    return False

# The server side measurements do not know how many requests there are
# add that info to their results at known offsets based on the request measurements
def addRequestNums(filename):
    # don't add them if they're already there
    if hasRequestNums(filename):
        return

    lines = []
    with open(filename, 'r') as file:
        lines = file.readlines()

    with open(filename, 'w') as file:
        # ignore some warmup server measurements to measure steady state
        config = open('tests/experiment.yaml', 'r')
        yaml = yaml.safe_load(config)

        warmupRuns = int(yaml['warmup_runs'])
        index = 0

        # for curLineNum, line in enumerate(lines):
        curLineNum = 0
        for line in list(lines):
            # print("evaluate line " + str(curLineNum) + line, end='')

            if warmupRuns > 0:
                warmupRuns -= 1
                continue;
            
            if curLineNum in relevantRequestNums(filename):
                delimeter = str(plotRequestNums[index]) + " total request(s) per second\n"
                file.write(delimeter)
                curLineNum += 1
                index += 1

            file.write(line)
            curLineNum += 1

# Scale measurements 
def adjustMeasurement(l, scale):
    scalar = 1.0
    if scale == "ms":
        scalar = 1000000.0
    elif scale == "us":
        scalar = 1000.0
    
    for i, val in enumerate(l):
        l[i] = val / scalar

def adjustMeasurements(lists, scale):
    for l in lists:
        adjustMeasurement(l, scale)

# determine if the desired number of requests is relevant to the plot being made
def inPlotWindow(numRequests):
    return numRequests > minObsRequests and numRequests <= maxObsRequests

def addRequestNum(numRequests, lineNum, plotRequestNums, relevantRequestNums, filename, shouldMeasure):
    relevantRequestNums(filename).append(lineNum)

    if inPlotWindow(numRequests):
        if not shouldMeasure:
            return
        plotRequestNums.append(numRequests)

def addDataPoint(numRequests, measurements, meanMeasurements, minMeasurements, twentyfifthMeasurements, medianMeasurements, seventyfifthMeasurements, ninetiethMeasurements, maxMeasurements):
    if inPlotWindow(numRequests):
        if len(measurements) == 0:
            return
        
        measurements.sort()

        meanMeasurements.append(stats.mean(measurements))
        minMeasurements.append(min(measurements))
        twentyfifthMeasurements.append(stats.mean(measurements[:round(len(measurements) * 0.25)]))
        medianMeasurements.append(stats.mean(measurements[:round(len(measurements) * 0.50)]))
        seventyfifthMeasurements.append(stats.mean(measurements[:round(len(measurements) * 0.75)]))
        ninetiethMeasurements.append(stats.mean(measurements[:round(len(measurements) * 0.95)]))
        maxMeasurements.append(max(measurements))

# Plot the data
def plot(filename, plotname, scale):
    print(filename)

    file1 = open(filename, 'r')
    data = file1.readlines()

    numRequests = 0
    measurements = []

    meanMeasurements = []
    minMeasurements = []
    twentyfifthMeasurements = []
    medianMeasurements = []
    seventyfifthMeasurements = []
    ninetiethMeasurements = []
    maxMeasurements = []
    plotRequestNums.clear()

    actual = []
    desired = []

    for lineNum, line in enumerate(data):
        # print("line = " + line, end='')
        # print("line number = " + str(lineNum))

        # print(numRequests)
        
        if line.strip() == "":
            continue

        if "TRUE" in line:
            trueReqs = float(line.replace("TRUE REQS PER SECOND ", "").replace("\n", ""))
            # print("Desired: " + str(plotRequestNums[-1]) + " | Obtained: " + trueReqs)
            desired.append(plotRequestNums[-1])
            actual.append(trueReqs)
            continue

        if "request(s)" in line:
            if numRequests == 0:
                # no number of requests seen, set it and move on
                numRequests = int(line.replace(" total request(s) per second\n", ""))
                addRequestNum(numRequests, lineNum, plotRequestNums, relevantRequestNums, filename, True)
                continue

            # this line contatins the number of requests for the following measurements 
            # if numRequests != len(measurements):
            #     print("! " + filename + ": Requests: " + str(numRequests) + " | numMeasS: " + str(len(measurements)) + " !")

            # print("Add data for previous number of requests: " + str(len(measurements)))
            addDataPoint(numRequests, measurements, meanMeasurements, minMeasurements, twentyfifthMeasurements, medianMeasurements, seventyfifthMeasurements, ninetiethMeasurements, maxMeasurements)

            numRequests = int(line.replace(" total request(s) per second\n", ""))
            addRequestNum(numRequests, lineNum, plotRequestNums, relevantRequestNums, filename, len(measurements) != 0)

            count = 0
            for m in measurements:
                if m > 5000000000:
                    count += 1
            
            percentagesGreaterThan5s.append(count / len(measurements))

            # clear the measurements
            measurements = []

        else:
            measurements.append(int(line))

    file1.close()

    # if the server failed, add 0 RTTs to cause alarm

    plt.figure()
    plt.gcf().set_size_inches(20, 10)
    
    # add the last set of measurements
    addDataPoint(numRequests, measurements, meanMeasurements, minMeasurements, twentyfifthMeasurements, medianMeasurements, seventyfifthMeasurements, ninetiethMeasurements, maxMeasurements)

    adjustMeasurements([meanMeasurements, minMeasurements, twentyfifthMeasurements, medianMeasurements, seventyfifthMeasurements, ninetiethMeasurements, maxMeasurements], scale)

    plt.plot(plotRequestNums, meanMeasurements, 'm', label="Mean")
    # plt.plot(plotRequestNums, maxMeasurements, 'r', label="Max")

    plt.plot(plotRequestNums, minMeasurements, 'b', label="Min")
    plt.plot(plotRequestNums, twentyfifthMeasurements, label="25th Percentile")
    plt.plot(plotRequestNums, medianMeasurements, 'g', label="Median")
    plt.plot(plotRequestNums, seventyfifthMeasurements, label="75th Percentile")
    plt.plot(plotRequestNums, ninetiethMeasurements, 'r',  label="95th Percentile")

    plt.xlabel("Number of Requests Per Second")
    plt.ylabel("Total Operational Time (" + scale + ")")
    plt.legend(loc="upper left")

    plt.savefig(figurePath + plotname + ".pdf")

    plt.figure()
    plt.plot(list(range(0, len(actual))), actual, label="Actual")
    plt.plot(list(range(0, len(desired))), desired, label="Desired")
    plt.legend(loc="upper left")
    print(actual)
    plt.savefig(filename.replace("results/", "figures/") + "Num Measurements" + ".pdf")


# Make Pseudo Distribution
def plotPseudoCDF(obsNum, filename, plotname, scale):
    file1 = open(filename, 'r')
    lines = file1.readlines()
    
    data = []

    for lineNum, line in enumerate(lines):
        # if lineNum > 4000:
        #     continue

        if line.strip() == "":
                continue

        if "request(s)" in line:
            numRequests = int(line.replace(" total request(s) per second\n", ""))
            if numRequests == obsNum:
                hit = True
            else:
                hit = False
        else:
            if hit:
                data.append(int(line))

    adjustMeasurement(data, scale)

    data.sort()

    plt.figure()
    # plt.yscale("log")

    plt.title(plotname)
    plt.xlabel("Individual Observation")
    plt.ylabel("Total Operational Time (" + scale + ")")

    # data = data[:900]

    plt.scatter(list(range(0, len(data))), data, s=0.5)
    plt.savefig(figurePath + plotname + ".pdf")


def plotCDF(filename, plotname, scale):
    file1 = open(filename, 'r')
    lines = file1.readlines()

    data = []

    for lineNum, line in enumerate(lines):
        if line.strip() == "":
                continue

        if "request(s)" in line:
            continue
        else:
            data.append(int(line))

    adjustMeasurement(data, scale)

    n_bins = 50
    
    count, bins_count = np.histogram(data, n_bins)

    # print(hist)
    # print(bin_edges)

    plt.figure()
    plt.xlim([0, max(data) + 1])
    plt.gcf().set_size_inches(8, 4)

    # fig, ax = plt.subplots(figsize=(8, 4))

    # # plot the cumulative histogram
    # n, bins, patches = plt.hist(data, n_bins, density=True, histtype='step',
    #                         cumulative=True, align='left')

    # print(n)
    # print(bins)
    # print(patches)



    
    

    # getting data of the histogram
    count, bins_count = np.histogram(data, bins=60)
    print(count)
    print(bins_count)
    
    # finding the PDF of the histogram using count values
    pdf = count / sum(count)
    
    # using numpy np.cumsum to calculate the CDF
    # We can also find using the PDF values by looping and adding
    cdf = np.cumsum(pdf)
    print(cdf)
    
    # plotting PDF and CDF
    # plt.plot(bins_count[1:], pdf, color="red", label="PDF")
    plt.plot(bins_count[1:], cdf, label="CDF")
    plt.legend()

    np.insert(cdf, 1, 0.0)
    print(cdf)

    plt.hlines(y=0, xmin = -10, xmax = bins_count[1], color = 'C0')
    plt.vlines(x=bins_count[1], ymin = 0, ymax = min(cdf), color = 'C0')

    


    plt.grid(True)
    plt.title(plotname)
    plt.xlabel("Total Operational Time (" + scale + ")")
    plt.ylabel('Likelihood of occurrence')

    # plt.show()
    
    plt.savefig(figurePath + plotname + ".pdf")



# ----------------- Figure generation ----------------------

# administrative observation window
minObsRequests = 1
maxObsRequests = 1000000000

resultPath = "results/single-client/"
figurePath = resultPath.replace("results/", "figures/")
# figurePath = figurePath + str(minObsRequests) + "-" + str(maxObsRequests) + "/"

if not os.path.exists(figurePath):
    os.makedirs(figurePath)

clientKE = resultPath + 'client_nts_ke'
clientNTP = resultPath + 'client_nts_ntp'
serverKE = resultPath + 'server_ke_create'
serverNTP = resultPath + 'server_ntp_alone'
serverNTS = resultPath + 'server_nts_auth'

singleClient = True
if singleClient:
    plotCDF(clientKE, "Client KE CDF", "ms")
    # plotPseudoCDF(1, clientKE, "Client KE Pseudo CDF", "ms")
    

    # plotPseudoCDF(1, clientNTP, "Client NTS Pseudo CDF", "ms")
    # plotCDF(clientNTP, "Client NTS CDF", "ms")


    # plotCDF(serverNTP, "Server NTP CDF", "us")
    # plotCDF(serverNTS, "Server NTS CDF", "us")
    # plotCDF(serverKE, "Server KE CDF", "us")
    exit(0)


plot(clientKE, "Client NTS KE Total Time", "ms")
plot(clientNTP, "Client NTS NTP Total Time", "ms")

# print(percentagesGreaterThan5s)

print("Client plots complete")

addRequestNums(serverKE)
addRequestNums(serverNTP)
addRequestNums(serverNTS)

# print("Client numbers added to server files complete")

plot(serverKE, "Server NTS Key Creation", "us")
plot(serverNTP, "Server NTP Header Creation", "ns")
plot(serverNTS, "Server NTS Packet Creation", "us")

print("Server plots complete")

numReq = 200
# plotPseudoCDF(numReq, serverNTP, "Request " + str(numReq) + " Server NTP CDF", "us")

# plotPseudoCDF(200, clientNTP, "Request 200 NTP CDF", "ms")
# plotPseudoCDF(400, clientNTP, "Request 400 NTP CDF", "ms")

print("\"CDF\" plots complete")
