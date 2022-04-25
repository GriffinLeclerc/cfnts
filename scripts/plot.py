import statistics as stats
import matplotlib.pyplot as plt
import matplotlib.ticker as tick

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
    lines = []

    if hasClientNums(filename):
        return

    with open(filename, 'r') as file:
        lines = file.readlines()

    with open(filename, 'w') as file:
        index = 0

        # for curLineNum, line in enumerate(lines):
        curLineNum = 0
        for line in list(lines):
            # print("evaluate line " + str(curLineNum) + line, end='')
            
            if curLineNum in relevantClientNums(filename):
                delimeter = str(plotClientNums[index]) + " client(s)\n"
                file.write(delimeter)
                curLineNum += 1
                index += 1

            file.write(line)
            curLineNum += 1

# Plot the data
def plot(filename, plotname):
    file1 = open(filename, 'r')
    data = file1.readlines()

    numClients = 0
    measurements = []

    plotMeasurements = []
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
            
            numClients = int(line.replace(" client(s)\n", ""))
            plotClientNums.append(numClients)
            relevantClientNums(filename).append(lineNum)

            plotMeasurements.append(stats.median(measurements))

        else:
            measurements.append(int(line))

    # add the last set of measurements
    plotMeasurements.append(stats.median(measurements))

    plt.figure()

    plt.gcf().set_size_inches(10, 5)

    plt.plot(plotClientNums, plotMeasurements)

    plt.xlabel("Number of Concurrent Clients")
    plt.ylabel("Total Operational Time")

    plt.savefig("figures/" + plotname + ".pdf")

# Figure gen
resultPath = "results/10001-step100/"

plot(resultPath + 'client_nts_ntp', "Client NTS NTP Total Time")
plot(resultPath + 'client_nts_ke', "Client NTS KE Total Time")

addClientNums(resultPath + 'server_ntp_enc')
addClientNums(resultPath + 'server_ke_create')

plot(resultPath + 'server_ntp_enc', "Server NTP Encryption")
plot(resultPath + 'server_ke_create', "Server NTP Cookie Creation")