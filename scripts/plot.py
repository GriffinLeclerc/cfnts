import binascii
from cProfile import label
from readline import parse_and_bind
import statistics as stats
import matplotlib.pyplot as plt
import os
import numpy as np
import yaml
import matplotlib.gridspec as gridspec

kePlotRequestNums = []
ntpPlotRequestNums = []
clientKELineNums = []
clientNTPLineNums = []

plt.rcParams['axes.axisbelow'] = True
plt.rcParams['pdf.fonttype'] = 42

def mapInt(num):
    return int(num)

def cullOutliers(data):
    avg = stats.mean(data)
    newData = []

    for point in data:
        if point < avg * 1000:
            newData.append(point)

    return newData

def relevantPlotNums(filename):
    if "ke" in filename:
        return kePlotRequestNums
    else:
        return ntpPlotRequestNums

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
        doc = yaml.safe_load(config)

        warmupRuns = int(doc['warmup_runs'])
        index = 0

        # for curLineNum, line in enumerate(lines):
        curLineNum = 0
        for line in list(lines):
            # print("evaluate line " + str(curLineNum) + line, end='')

            if warmupRuns > 0:
                warmupRuns -= 1
                continue;
            
            if curLineNum in relevantRequestNums(filename):
                delimeter = str(relevantPlotNums(filename)[index]) + " total request(s) per second\n"
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
    elif scale == r"$\mu$s":
        scalar = 1000.0
    
    for i, val in enumerate(l):
        l[i] = val / scalar

def adjustMeasurements(lists, scale):
    for l in lists:
        adjustMeasurement(l, scale)

# determine if the desired number of requests is relevant to the plot being made
def inPlotWindow(numRequests):
    return numRequests > minObsRequests and numRequests <= maxObsRequests

def addRequestNum(numRequests, lineNum, relevantRequestNums, filename, shouldMeasure):
    if inPlotWindow(numRequests):
        if not shouldMeasure:
            return
        relevantPlotNums(filename).append(numRequests)
        relevantRequestNums(filename).append(lineNum)

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
    print("Plotting: " + filename)

    file1 = open(filename, 'r')
    data = file1.readlines()

    numRequests = 0
    measurements = []

    # clear the x axis values from previous plots
    # the code reconstructs them from this specific file later
    relevantPlotNums(filename).clear()

    meanMeasurements = []
    minMeasurements = []
    twentyfifthMeasurements = []
    medianMeasurements = []
    seventyfifthMeasurements = []
    ninetiethMeasurements = []
    maxMeasurements = []

    actual = []
    desired = []

    timeoutCounts = []
    osCounts = []
    otherCounts = []

    tmpPrevNum = 0

    for lineNum, line in enumerate(data):
        # print("line = " + line, end='')
        # print("line number = " + str(lineNum))

        # print(numRequests)
        
        if line.strip() == "":
            continue

        if "TRUE" in line:
            trueReqs = float(line.replace("TRUE REQS PER SECOND ", "").replace("\n", ""))
            # print("Desired: " + str(relevantPlotNums(filename)[-1]) + " | Obtained: " + trueReqs)
            # desired.append(relevantPlotNums(filename)[-1])
            actual.append(trueReqs)
            continue

        # Timeout Errors: 0
        # OS Errors: 0
        # Other Errors: 0

        if "Timeout" in line:
            count = int(line.replace("Timeout Errors: ", ""))
            timeoutCounts.append((count / len(measurements)) * 100)
            continue

        if "OS" in line:
            count = int(line.replace("OS Errors: ", ""))
            osCounts.append((count / len(measurements)) * 100)
            continue

        if "Other" in line:
            count = int(line.replace("Other Errors: ", ""))
            otherCounts.append((count / len(measurements)) * 100)
            continue

        if "request(s)" in line:
            if numRequests == 0:
                # no number of requests seen, set it and move on
                numRequests = int(line.replace(" total request(s) per second\n", ""))
                addRequestNum(numRequests, lineNum, relevantRequestNums, filename, True)
                continue

            # this line contatins the number of requests for the following measurements 
            # if numRequests != len(measurements):
            #     print("! " + filename + ": Requests: " + str(numRequests) + " | numMeasS: " + str(len(measurements)) + " !")

            # print("Add data for previous number of requests: " + str(len(measurements)))
            addDataPoint(numRequests, measurements, meanMeasurements, minMeasurements, twentyfifthMeasurements, medianMeasurements, seventyfifthMeasurements, ninetiethMeasurements, maxMeasurements)

            numRequests = int(line.replace(" total request(s) per second\n", ""))
            addRequestNum(numRequests, lineNum, relevantRequestNums, filename, len(measurements) != 0)

            # clear the measurements
            measurements = []

        else:
            measurements.append(int(line))

    file1.close()

    # add the last set of measurements
    addDataPoint(numRequests, measurements, meanMeasurements, minMeasurements, twentyfifthMeasurements, medianMeasurements, seventyfifthMeasurements, ninetiethMeasurements, maxMeasurements)

    adjustMeasurements([meanMeasurements, minMeasurements, twentyfifthMeasurements, medianMeasurements, seventyfifthMeasurements, ninetiethMeasurements, maxMeasurements], scale)

    # plt.plot(relevantPlotNums(filename), ninetiethMeasurements, 'r',  label="95th Percentile")
    # plt.plot(relevantPlotNums(filename), seventyfifthMeasurements, label="75th Percentile")
    # plt.plot(relevantPlotNums(filename), medianMeasurements, 'g', label="Median")
    # plt.plot(relevantPlotNums(filename), twentyfifthMeasurements, label="25th Percentile")
    # plt.plot(relevantPlotNums(filename), minMeasurements, 'b', label="Min")  

    scalar = 0.6

    width = 12.8 * scalar
    height = 4.8 * scalar
    plt.rcParams.update({'font.size': 12 * scalar})
    custom_width = 1.0 * scalar

    if "server" in filename or "ntp" in filename:
        height = height * 0.5

    plt.figure()
    plt.gcf().set_size_inches(width, height)

    plt.plot(relevantPlotNums(filename), minMeasurements, 'b', label="Min", linewidth=custom_width)
    plt.plot(relevantPlotNums(filename), medianMeasurements, 'g', label="Median", linewidth=custom_width)

    if "client" in filename:
        plt.ylim(0, max(medianMeasurements))
    else:
        plt.ylim((min(minMeasurements) - (0.03 * min(minMeasurements)), max(medianMeasurements) + (0.03 * min(minMeasurements))))

    # locs, labels = plt.yticks()
    # locs = np.append(locs, min(minMeasurements))
    # plt.yticks(locs)

    plt.xlabel("Number of Requests Per Second")
    plt.ylabel("Time (" + scale + ")")
    plt.legend(loc="upper left")
    plt.grid(True)

    plt.margins(0, 0.01)
    # plt.yscale('log')
    if "client" in filename:
        plt.savefig(figurePath + plotname + "-min+median" + ".pdf", bbox_inches='tight', pad_inches = 0)


    # All measurements

    plt.figure()
    plt.gcf().set_size_inches(width, height)

    plt.plot(relevantPlotNums(filename), minMeasurements, 'b', label="Min", linewidth=custom_width)
    plt.plot(relevantPlotNums(filename), twentyfifthMeasurements, label="25th Percentile", linewidth=custom_width)
    plt.plot(relevantPlotNums(filename), medianMeasurements, 'g', label="Median", linewidth=custom_width)
    plt.plot(relevantPlotNums(filename), seventyfifthMeasurements, label="75th Percentile", linewidth=custom_width)
    plt.plot(relevantPlotNums(filename), ninetiethMeasurements, 'r',  label="95th Percentile", linewidth=custom_width)

    # print(stats.mean(minMeasurements))
    # print(stats.mean(twentyfifthMeasurements))
    # print(stats.mean(medianMeasurements))
    # print(stats.mean(seventyfifthMeasurements))

    # Measurements after the rtt increase
    # print(stats.mean(ninetiethMeasurements[20:]))
    # print(stats.mean(medianMeasurements[20:]))

    # plt.plot(relevantPlotNums(filename), meanMeasurements, 'm', label="Mean")
    # plt.plot(relevantPlotNums(filename), maxMeasurements, 'r', label="Max")

    plt.xlabel("Number of Requests Per Second")
    plt.ylabel("Time (" + scale + ")")
    plt.legend(loc="upper left")
    plt.grid(True)

    plt.margins(0, 0.01)
    # plt.yscale('log')
    plt.savefig(figurePath + plotname + "-all" + ".pdf", bbox_inches='tight', pad_inches = 0)


    # Reqs per second sanity check
    plt.figure()
    plt.plot(list(range(0, len(actual))), actual, label="Actual")
    plt.plot(list(range(0, len(desired))), desired, label="Desired")
    plt.legend(loc="upper left")
    # plt.savefig(filename.replace("results/", "figures/") + " Num Measurements Comparison" + ".pdf")

    if "client" in filename:
        # Error counts
        plt.figure()
        plt.gcf().set_size_inches(width, height)
        plt.rcParams.update({'font.size': 12 * scalar})
        plt.margins(0, 0.01)
        plt.grid(True)

        xAxisVals = list(range(0, len(timeoutCounts)))
        xAxisVals = list(map(lambda val: (val * 100) + 100, xAxisVals))
        plt.xlabel("Number of Requests Per Second")
        plt.ylabel("Percentage of requests that resulted in error")
        plt.stackplot(xAxisVals, timeoutCounts, osCounts, labels=["Connection timeout", "OS Error 11"], linewidth=custom_width)

        locs, labels = plt.yticks()
        locs = locs[1:]
        locs = locs[:-1]
        labels = list(map(lambda x: str(x) + "%", locs))
        plt.yticks(locs, labels)

        # plt.plot(xAxis, otherCounts, label="% Other errors")
        plt.legend(loc="upper left")
        plt.savefig(figurePath + "Error Rates " + plotname + ".pdf", bbox_inches='tight', pad_inches = 0)


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

        if "Error" in line:
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

    # data.sort()

    plt.figure()
    # plt.yscale("log")

    plt.title(plotname)
    plt.xlabel("Individual Observation")
    plt.ylabel("Time (" + scale + ")")

    # data = data[:900]

    plt.scatter(list(range(0, len(data))), data, s=0.5)
    plt.margins(0, 0)
    plt.savefig(figurePath + plotname + ".pdf", bbox_inches='tight', pad_inches = 0)


def plotCDFs(filenames, plotnames, figurename, scale):
    numFigs = len(filenames)

    plt.figure()

    maxX = 0
    colors = ['steelblue', 'orange', 'turquoise']
    
    for i, filename in enumerate(filenames):
        file1 = open(filename, 'r')
        lines = file1.readlines()

        data = []

        for lineNum, line in enumerate(lines):
            if line.strip() == "":
                    continue

            if "request(s)" in line or "Error" in line:
                continue
            else:
                data.append(int(line))

        adjustMeasurement(data, scale)

        print(plotnames[i] + " " + str(stats.median(data)) + " " + scale)

        n_bins = 50
        
        count, bins_count = np.histogram(data, n_bins)

        curSubplot = plt
        curPlotName = plotnames[i]

        xLim = max(data) + 1
        if (xLim > maxX):
            curSubplot.xlim([0, xLim])
            maxX = xLim


        # print(hist)
        # print(bin_edges)

        # fig, ax = plt.subplots(figsize=(8, 4))

        # # plot the cumulative histogram
        # n, bins, patches = plt.hist(data, n_bins, density=True, histtype='step',
        #                         cumulative=True, align='left')

        # print(n)
        # print(bins)
        # print(patches)


        # getting data of the histogram
        count, bins_count = np.histogram(data, bins=60)
        
        # finding the PDF of the histogram using count values
        pdf = count / sum(count)
        
        # using numpy np.cumsum to calculate the CDF
        # We can also find using the PDF values by looping and adding
        cdf = np.cumsum(pdf)

        # Scale width of lines so they are not wholey overwritten by other lines 
        default_width = 1
        scalar = 0.3

        custom_width = default_width + (scalar * (numFigs - (i+1)))
        # print("Figure " + str(i + 1))
        # print(custom_width)
        # print("-----------")

        
        # plotting PDF and CDF
        # plt.plot(bins_count[1:], pdf, color="red", label="PDF")
        curSubplot.plot(bins_count[1:], cdf, label=curPlotName, color=colors[i], linewidth=custom_width)

        np.insert(cdf, 1, 0.0)

        # lines at head and tail
        curSubplot.hlines(y=0, xmin = -1000, xmax = bins_count[1], color = colors[i], linewidth=custom_width)
        curSubplot.vlines(x=bins_count[1], ymin = 0, ymax = min(cdf), color = colors[i], linewidth=custom_width)

        curSubplot.hlines(y=1, xmin = bins_count[len(bins_count) - 1], xmax = max(data) + 1000, color = colors[i], linewidth=custom_width)

        if i == 0 and "server" in filename:
            plt.text(max(data), 1, "{:.2f}".format(max(data)) + " " + scale, rotation=-45, va="top")
        else:
            plt.text(max(data), 1, "{:.2f}".format(max(data)) + " " + scale, rotation=45)

        plt.text(bins_count[1], 0, "{:.2f}".format(min(data)) + " " + scale, rotation=45)
        

        # Add circles to points of interest
        plt.plot([bins_count[1]], [0], 'o', color=colors[i])
        plt.plot([max(data)], [1], 'o', color=colors[i])

        curSubplot.grid(True)
        # curSubplot.title.set_text(curPlotName)
        curSubplot.xlabel("Time (" + scale + ")")
        # curSubplot.ylabel('Likelihood of occurrence')

    
    locs, labels = plt.yticks()
    locs = locs[1:]
    locs = locs[:-1]
    # print(locs)
    labels = list(map(lambda x:str( int(float(x) * 100) ) + "%", locs))
    plt.yticks(locs, labels)

       
    # plt.margins(0, 0)


    plt.legend(loc="lower right")
    plt.gcf().set_size_inches(6.4, 4.8)
    plt.rcParams.update({'font.size': 12})
    plt.savefig(figurePath + figurename + ".pdf", bbox_inches='tight', pad_inches = 0)



# ----------------- Figure generation ----------------------

# administrative observation window
minObsRequests = 1
maxObsRequests = 100000000
# maxObsRequests = 7000


# Change this path to plot different results
resultPath = "results/single-client-2/"
# resultPath = "results/single-client/"


figurePath = resultPath.replace("results/", "figures/")

print("reading results from " + resultPath)
print("Writing figures to " + figurePath)

if not os.path.exists(figurePath):
    os.makedirs(figurePath)

clientKE = resultPath + 'client_nts_ke'
clientNTP = resultPath + 'client_nts_ntp'
serverKE = resultPath + 'server_ke_create'
serverNTP = resultPath + 'server_ntp_alone'
serverNTS = resultPath + 'server_nts_auth'

if "single-client" in resultPath:

    # plotCDFs([clientKE, clientNTP], ["Client KE CDF", "Client NTS CDF"], "Client CDFs", "ms")
    plotCDFs([clientNTP, clientKE], ["$d_{CNTS}$", "$d_{CKE}$"], "Client CDFs", "ms")
    # plotCDFs([clientNTP], ["Client NTP CDF"], "Client NTP CDF", "ms")
    # plotCDFs([serverNTP, serverNTS, serverKE], ["Server NTP CDF", "Server NTS CDF", "Server KE CDF"], "Server CDFs", "us")
    plotCDFs([serverNTP, serverKE, serverNTS], ["$d_{SNTP}$", "$d_{SKE}$", "$d_{SNTS}$"], "Server CDFs", r"$\mu$s")
    # plotPseudoCDF(1, clientKE, "Client KE Pseudo CDF", "ms")
    

    # plotPseudoCDF(1, clientNTP, "Client NTS Pseudo CDF", "ms")
    # plotCDF(clientNTP, "Client NTS CDF", "ms")


    # plotCDF(serverNTP, "Server NTP CDF", "us")
    # plotCDF(serverNTS, "Server NTS CDF", "us")
    # plotCDF(serverKE, "Server KE CDF", "us")
    exit(0)


plot(clientKE, "Client NTS KE Total Time", "ms")
plot(clientNTP, "Client NTS NTP Total Time", "ms")

print("Client plots complete")

addRequestNums(serverKE)
addRequestNums(serverNTP)
addRequestNums(serverNTS)

print("Client numbers added to server files complete")

plot(serverKE, "Server NTS Key Creation", r"$\mu$s")
plot(serverNTP, "Server NTP Header Creation", r"$\mu$s")
plot(serverNTS, "Server NTS Packet Creation", r"$\mu$s")

# print("Server plots complete")

numReq = 200
# plotPseudoCDF(numReq, serverNTP, "Request " + str(numReq) + " Server NTP CDF", "us")

# plotPseudoCDF(500, serverKE, "500 Pseudo CDF", r"$\mu$s")
# plotPseudoCDF(2000, serverKE, "2k Pseudo CDF", r"$\mu$s")
# plotPseudoCDF(400, clientNTP, "Request 400 NTP CDF", "ms")

print("\"CDF\" plots complete")
