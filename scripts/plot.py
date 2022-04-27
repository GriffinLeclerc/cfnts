import statistics as stats
import matplotlib.pyplot as plt
import os

plotClientNums = []
clientKELineNums = []
clientNTPLineNums = []

minObsClients = 0
maxObsClients = 200

def mapInt(num):
    return int(num)

def cullOutliers(data):
    avg = stats.mean(data)
    newData = []

    for point in data:
        if point < avg * 1000:
            newData.append(point)

    return newData

def relevantClientNums(filename):
    if "ke" in filename:
        return clientKELineNums
    else:
        return clientNTPLineNums

# determines if the file in question has client number delimiters
def hasClientNums(filename):
    with open(filename, 'r') as file:
        if "client" in file.read():
            return True
    return False

# The server side measurements do not know how many clients there are
# add that info to their results at known offsets based on the client measurements
def addClientNums(filename):
    # don't add them if they're already there
    if hasClientNums(filename):
        return

    lines = []
    with open(filename, 'r') as file:
        lines = file.readlines()

    with open(filename, 'w') as file:
        # ignore some warmup server measurements to measure steady state
        warmupRuns = 10;

        index = 0

        # for curLineNum, line in enumerate(lines):
        curLineNum = 0
        for line in list(lines):
            # print("evaluate line " + str(curLineNum) + line, end='')

            if warmupRuns > 0:
                warmupRuns -= 1
                continue;
            
            if curLineNum in relevantClientNums(filename):
                delimeter = str(plotClientNums[index]) + " client(s)\n"
                file.write(delimeter)
                curLineNum += 1
                index += 1

            file.write(line)
            curLineNum += 1

# Scale measurements 
def adjustMeasurements(lists, scale):
    scalar = 1.0
    if scale == "ms":
        scalar = 1000000.0
    elif scale == "us":
        scalar = 1000.0

    for l in lists:
        for i, val in enumerate(l):
            l[i] = val / scalar
            # print(str(l[i]) + scale)

# determine if the desired number of clients is relevant to the plot being made
def inPlotWindow(num):
    return num <= minObsClients or num > maxObsClients

def addClientNum(num, lineNum, plotClientNums, relevantClientNums, filename):
    plotClientNums.append(num)
    relevantClientNums(filename).append(lineNum)


def addDataPoint(numClients, measurements, meanMeasurements, minMeasurements, maxMeasurements):
    meanMeasurements.append(stats.mean(measurements))
    minMeasurements.append(min(measurements))
    maxMeasurements.append(max(measurements))


# Plot the data
def plot(filename, plotname, scale):
    file1 = open(filename, 'r')
    data = file1.readlines()

    numClients = 0
    measurements = []

    meanMeasurements = []
    minMeasurements = []
    maxMeasurements = []
    plotClientNums.clear()

    plt.figure()
    plt.gcf().set_size_inches(20, 10)


    for lineNum, line in enumerate(data):
        # print("line = " + line, end='')
        # print("line number = " + str(lineNum))

        # print(numClients)
        
        if line.strip() == "":
            continue

        if "Waiting" in line:
            # plot a green vertical line at numClients
            plt.axvline(numClients, color='g')
            continue

        if "client(s)" in line:
            if numClients == 0:
                # no number of clients seen, set it and move on
                numClients = int(line.replace(" client(s)\n", ""))
                addClientNum(numClients, lineNum, plotClientNums, relevantClientNums, filename)
                continue

            # this line contatins the number of clients for the following measurements 
            if numClients != len(measurements):
                print("! " + filename + ": Clients: " + str(numClients) + " | numMeasS: " + str(len(measurements)) + " !")

            numClients = int(line.replace(" client(s)\n", ""))
            addClientNum(numClients, lineNum, plotClientNums, relevantClientNums, filename)

            addDataPoint(numClients, measurements, meanMeasurements, minMeasurements, maxMeasurements)

            # clear the measurements
            measurements = []

        else:
            measurements.append(int(line))


    # if the server failed, add 0 RTTs to cause alarm
    if len(measurements) == 0:
        measurements.append(0)
    
    # add the last set of measurements
    addDataPoint(numClients, measurements, meanMeasurements, minMeasurements, maxMeasurements)

    adjustMeasurements([meanMeasurements, minMeasurements, maxMeasurements], scale)

    plt.plot(plotClientNums, meanMeasurements, 'm', label="Mean")
    plt.plot(plotClientNums, minMeasurements, 'b', label="Min")
    plt.plot(plotClientNums, maxMeasurements, 'r', label="Max")

    plt.xlabel("Number of Concurrent Clients")
    plt.ylabel("Total Operational Time (" + scale + ")")
    plt.legend(loc="upper left")

    plt.savefig(figurePath + plotname + ".pdf")

# Figure gen
resultPath = "results/"
figurePath = resultPath.replace("results/", "figures/")

if not os.path.exists(figurePath):
    os.makedirs(figurePath)

plot(resultPath + 'client_nts_ntp', "Client NTS NTP Total Time", "ms")
plot(resultPath + 'client_nts_ke', "Client NTS KE Total Time", "ms")

addClientNums(resultPath + 'server_ntp_enc')
addClientNums(resultPath + 'server_ke_create')

plot(resultPath + 'server_ntp_enc', "Server NTP Encryption", "us")
plot(resultPath + 'server_ke_create', "Server NTP Cookie Creation", "us")