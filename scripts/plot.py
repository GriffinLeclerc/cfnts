import statistics as stats
import matplotlib.pyplot as plt
import matplotlib.ticker as tick

def mapInt(num):
    return int(num)

def cullOutliers(data):
    avg = stats.mean(data)
    newData = []

    for point in data:
        if point < avg * 1000:
            newData.append(point)

    return newData

def plot(filename, plotname):
    file1 = open(filename, 'r')
    data = list(file1.readlines())

    numClients = 0
    measurements = []

    plotClientNums = []
    plotMeasurements = []

    for line in data:
        if line.strip() == "":
            continue

        if "client(s)" in line:
            if numClients != 0:
                # store this point
                plotClientNums.append(numClients)
                plotMeasurements.append(stats.median(measurements))
            
            # remember the next number of clients
            numClients = int(line.replace(" client(s)\n", ""))
        else:
            measurements.append(int(line))

    # print(plotClientNums)
    # print(plotMeasurements)
    
    plt.figure()

    plt.gcf().set_size_inches(10, 5)

    plt.set_xlabel = "Number of Clients"
    plt.set_ylabel = "Total Operational Time"

    plt.plot(plotClientNums, plotMeasurements)
    plt.savefig("figures/" + plotname + ".pdf")

plot('results/server_ntp_enc', "Server NTP Encryption")
plot('results/server_ke_create', "Server NTP Cookie Creation")

plot('results/client_nts_ntp', "Client NTS NTP Total Time")
plot('results/client_nts_ke', "Client NTS KE Total Time")