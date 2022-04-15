import statistics as stats
import matplotlib.pyplot as plt
import matplotlib.ticker as tick

def mapInt(num):
    return int(num)

def cullOutliers(data):
    avg = stats.mean(data) * 10
    newData = []
    
    for point in data:
        if point < avg * 10:
            newData.append(point)

    return newData

def plot(filename, plotname):
    file1 = open(filename, 'r')
    data = list(map(mapInt, file1.readlines()))

    data = cullOutliers(data)

    plt.figure()

    plt.xlabel = "Measurement Number"
    plt.ylabel = "Total Operational Time"

    plt.gcf().set_size_inches(10, 5)

    # plt.gca().yaxis.set_major_formatter(tick.FormatStrFormatter('ns'))

    measNums = list(range(0, len(data)))

    plt.plot(measNums, data)

    plt.savefig("figures/" + plotname + ".pdf")

plot('results/server_ntp_enc', "Server NTP Encryption")
plot('results/server_ke_create', "Server NTP Cookie Creation")

plot('results/client_nts_ke', "Client NTS NTP Total Time")
plot('results/client_nts_ke', "Client NTS KE Total Time")