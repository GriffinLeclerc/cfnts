from smtplib import LMTP
import statistics as stats
import matplotlib.pyplot as plt
import matplotlib.ticker as tick

plotClientNums = []
clientLineNums = []

def mapInt(num):
    return int(num)

def cullOutliers(data):
    avg = stats.mean(data)
    newData = []

    for point in data:
        if point < avg * 1000:
            newData.append(point)

    return newData

# The server side measurements do not know how many clients there are
# add that info to their results at known offsets based on the client measurements
def addClientNums(filename):
    lines = []

    with open(filename, 'r') as file:
        lines = file.readlines()

    with open(filename, 'w') as file:
        index = 0

        # for curLineNum, line in enumerate(lines):
        curLineNum = 0
        for line in list(lines):
            # print("evaluate line " + str(curLineNum) + line, end='')
            
            if curLineNum in clientLineNums:
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
    clientLineNums.clear()


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
                clientLineNums.append(lineNum)
                continue

            # this line contatins the number of clients for the following measurements 
            
            numClients = int(line.replace(" client(s)\n", ""))
            plotClientNums.append(numClients)
            clientLineNums.append(lineNum)

            plotMeasurements.append(stats.median(measurements))

        else:
            measurements.append(int(line))

    # add the last set of measurements
    plotMeasurements.append(stats.median(measurements))

    
    plt.figure()

    plt.gcf().set_size_inches(10, 5)

    plt.set_xlabel = "Number of Clients"
    plt.set_ylabel = "Total Operational Time"

    plt.plot(plotClientNums, plotMeasurements)
    plt.savefig("figures/" + plotname + ".pdf")

plot('results/client_nts_ntp', "Client NTS NTP Total Time")
plot('results/client_nts_ke', "Client NTS KE Total Time")

addClientNums('results/server_ntp_enc')
addClientNums('results/server_ke_create')

plot('results/server_ntp_enc', "Server NTP Encryption")
plot('results/server_ke_create', "Server NTP Cookie Creation")