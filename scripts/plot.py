import statistics as stats
import matplotlib.pyplot as plt

plotClientNums = []
clientKELineNums = []
clientNTPLineNums = []

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


    for lineNum, line in enumerate(data):
        # print("line = " + line, end='')
        # print("line number = " + str(lineNum))
        
        if line.strip() == "":
            continue

        if "client(s)" in line:
            if numClients == 0:
                # no number of clients seen, set it and move on
                numClients = int(line.replace(" client(s)\n", ""))
                plotClientNums.append(numClients)
                relevantClientNums(filename).append(lineNum)
                continue

            # this line contatins the number of clients for the following measurements 
            if numClients != len(measurements):
                print("! " + filename + ": Clients: " + str(numClients) + " | numMeasS: " + str(len(measurements)) + " !")

            numClients = int(line.replace(" client(s)\n", ""))
            plotClientNums.append(numClients)
            relevantClientNums(filename).append(lineNum)

            meanMeasurements.append(stats.mean(measurements))
            minMeasurements.append(min(measurements))
            maxMeasurements.append(max(measurements))

            # clear the measurements
            measurements = []

        else:
            measurements.append(int(line))

    # add the last set of measurements
    meanMeasurements.append(stats.mean(measurements))
    minMeasurements.append(min(measurements))
    maxMeasurements.append(max(measurements))

    adjustMeasurements([meanMeasurements, minMeasurements, maxMeasurements], scale)

    plt.figure()

    plt.gcf().set_size_inches(10, 5)

    plt.plot(plotClientNums, meanMeasurements, 'm', label="Mean")
    plt.plot(plotClientNums, minMeasurements, 'b', label="Min")
    plt.plot(plotClientNums, maxMeasurements, 'r', label="Max")

    plt.xlabel("Number of Concurrent Clients")
    plt.ylabel("Total Operational Time (" + scale + ")")
    plt.legend(loc="upper left")

    plt.savefig("figures/" + plotname + ".pdf")

# Figure gen
resultPath = "results/"

plot(resultPath + 'client_nts_ntp', "Client NTS NTP Total Time", "ms")
plot(resultPath + 'client_nts_ke', "Client NTS KE Total Time", "ms")

addClientNums(resultPath + 'server_ntp_enc')
addClientNums(resultPath + 'server_ke_create')

plot(resultPath + 'server_ntp_enc', "Server NTP Encryption", "us")
plot(resultPath + 'server_ke_create', "Server NTP Cookie Creation", "us")