# All lines written by Andrew Rivers in fulfillment of the CSIS 484: Information Technology Capstone Individual Assignment requirements
#
# Version: 1.0.0
#
# Created: 05-02-2021
# Updated: 05-02-2021
#
# Performance Monitor monitors system CPU and RAM usage and logs scenarios in which either surpasses 75%
# Logs are not created for each second that CPU or RAM usage is over 75%, but only the initial recorded measurement over 75%
# and any subsequent measurements that surpass the previously highest measured percent usage, reset upon usage dropping below 75%

# Import required libraries
import PySimpleGUI as gui
import psutil as monitor
import pypyodbc as sql
import os

# Initialize connection to AWS instance
def initAWSConnection():

    # Attempt instance connection
    try:
        print('Connecting to AWS instance')
        connection = sql.connect('Driver={SQL Server};server=capstonedatabase.c7dqnlpgchhn.us-east-2.rds.amazonaws.com;Database=capstonedatabase;uid=capstoneuser;pwd=capstonepass')

    # On connection fail
    except:
        print('Error connecting to AWS instance. Please check your Internet connection and try again.\Exiting')
        quit()

    print('Connected')

    # Return connection
    return connection

# Get all processes running on the local machine
def getAllProcesses():

    # Initialize variables
    processList = []

    # Get all running processes
    for process in monitor.process_iter():

        # Attempt to append process
        try:
            processData = process.as_dict(attrs=['pid', 'cpu_percent', 'name'])
            processList.append(processData);

        # On append fail
        except (monitor.NoSuchProcess, monitor.AccessDenied, monitor.ZombieProcess):
            pass

    # Sort list by CPU usage
    processList = sorted(processList, key=lambda procObj: procObj['cpu_percent'], reverse=True)

    # Return list of processes
    return processList

# Get top 20 processes from list of all processes
def getTop20Processes(processes):

    # Initialize variables
    processList = []
    index = 0

    # Run for 20 iterations or until length of processes has been reached
    while index <= 20 and index < len(processes):

        # Sort out System Idle Process (runs at 100% CPU usage minus amount being used by current processes)
        pid = processes[index]['pid']
        if pid != 0:

            # Initialize variables
            lpid = len(str(pid))
            cpu = processes[index]['cpu_percent'] / monitor.cpu_count()
            lcpu = len(str(int(cpu)))
            name = processes[index]['name']

            # Append to list in string format for PySimpleGUI Listbox
            processList.append(' '*(5-lpid) + str(pid) + ' |' + ' '*(4-lcpu) + str(round(cpu, 1)) + ' | ' + name)

        # Move to next index of array
        index = index + 1

    # Return list of top 20 processes
    return processList

# Calulate CPU usage based on processes (using psutil.cpu_percent() does not return accurate numbers)
def getCPUUsage(processes):

    # Initialize variables
    percent = 0.0
    index = 0

    # Use only top 20 processes for efficiency as percentages past 20 processes are negligible
    while index <= 20 and index < len(processes):
        # Sort out System Idle Process (runs at 100% CPU usage minus amount being used by current processes)
        pid = processes[index]['pid']
        if pid != 0:

            # Add process CPU usage to total CPU usage
            cpu_percent = processes[index]['cpu_percent'] / monitor.cpu_count()
            percent = percent + cpu_percent

        # Move to next index of array
        index = index + 1

    # Cap maximum CPU usage at 100% (can, on occasion, reach 101% due to low number of significant figures when adding individual process percentages)
    if percent > 100:
        percent = 100

    # Return CPU percentage as a float
    return percent

# Build application GUI
def buildGui(connection):

    # Initialize variables
    cpuhighestrecorded = 0
    ramhighestrecorded = 0
    devicename = os.environ['COMPUTERNAME']

    # Initialize SQL cursor
    cursor = connection.cursor()

    # Set GUI theme
    gui.theme('LightGrey1')

    # Initialize GUI layout
    layout = [
        [gui.Text('CPU', font='Arial 12', size=(20,1)), gui.Text('RAM', font='Arial 12', size=(20,1))],
        [gui.Text('', font='Arial 12', size=(20,2), key='CPUPercent'), gui.Text('', font='Arial 12', size=(20,2), key='RAMPercent')],
        [gui.Text('', font='Arial 10', size=(23,1), key='PhysicalCores'), gui.Text('', font='Arial 10', size=(20,1), key='TotalMemory')],
        [gui.Text('', font='Arial 10', size=(23,1), key='LogicalCores'), gui.Text('', font='Arial 10', size=(20,1), key='UsedMemory')],
        [gui.Text('', font='Arial 10', size=(23,2)), gui.Text('', font='Arial 10', size=(20,2), key='AvailableMemory')],
        [gui.Text('PID', font='Arial 10', size=(5,1)), gui.Text('CPU %', font='Arial 10', size=(7,1)), gui.Text('Program Name', font='Arial 10', size=(12,1))],
        [gui.Listbox(values=[], font='Courier 8', size=(50,20), key='Top20Processes')],
        [gui.Button('Export Monitor Results to Console'), gui.Button('Close')]
    ]

    # Set window title and load layout
    window = gui.Window('Performance Monitor', layout)

    # Application loop
    while True:

        # Update window values
        event, values = window.read(1)

        # Check for application close events
        if event == gui.WIN_CLOSED or event == 'Close':
            break

        # On 'Export Monitor Results to Console' button pressed
        if event == 'Export Monitor Results to Console':

            # Get all data from HardwareCode table
            query = '''SELECT * FROM HardwareCode'''
            cursor.execute(query)

            # Print table info
            print('\nHardwareCode Table\n')
            print('\n== Beginning of Hardware Codes ==\n')

            # Print column names
            print('  Id | Name')

            # For each row in results
            while True:

                # Get row data
                row = cursor.fetchone()

                # On end of rows reached
                if not row:
                    print('\n===== End of Hardware Codes =====\n')
                    break

                # Print row data
                print('   ' + str(row['id']) + ' | ' + str(row['name']))


            # Print table info
            print('\n\nPerformanceLogs Table (entries for all scenarios in which CPU or RAM usage exceeded 75%)\n')
            print('\n=============================================================== Beginning of Performance Logs ==============================================================\n')

            # Print column names
            print('  Id | HardwareId | UsagePercent | PhysicalCores | LogicalCores | TotalMemory | AvailableMemory | UsedMemory |            Time             |    DeviceName')

            # Get all data from PerformanceLogs table
            query = '''SELECT * FROM PerformanceLogs'''
            cursor.execute(query)

            # For each row
            while True:

                # Get row data
                row = cursor.fetchone()

                # On end of rows reached
                if not row:
                    print('\n================================================================== End of Performance Logs =================================================================\n')
                    break

                # Print row data
                print(' '*(4-len(str(row['id']))) + str(row['id']) + ' |      ' + str(row['hardwareid']) + '     |    ' + ' '*(5-len(str(round(row['usagepercent'], 1)))) + str(round(row['usagepercent'], 1)) + '%    |      ' + ' '*(2-len(str(row['physicalcores']))) + str(row['physicalcores'])  + '       |      ' + ' '*(3-len(str(row['logicalcores']))) + str(row['logicalcores']) + '     |    ' + ' '*(3-len(str(row['totalmemory']))) + str(row['totalmemory']) + 'GB    |      ' + ' '*(3-len(str(row['availablememory']))) + str(row['availablememory']) + 'GB      |    ' + ' '*(3-len(str(row['usedmemory']))) + str(row['usedmemory']) + 'GB   | ' + str(row['time'] + ' | ' + str(row['devicename'])))

        # CPU data
        processes = getAllProcesses()
        top20Processes = getTop20Processes(processes)
        cpupercent = getCPUUsage(processes)
        physicalcores = monitor.cpu_count(False)
        logicalcores = monitor.cpu_count(True)

        # RAM data
        ram = monitor.virtual_memory()
        rampercent = ram.percent
        ramtotal = ram.total >> 30
        ramused = ram.used >> 30
        ramavailable = ram.available >> 30

        # Update CPU data in window
        window['CPUPercent'].Update(str(round(cpupercent, 0)) + '%')
        window['PhysicalCores'].Update('Physical Cores: ' + str(physicalcores))
        window['LogicalCores'].Update('Logical Cores: ' + str(physicalcores))

        # If CPU usage is less than 75%
        if cpupercent < 75:

            #Resent highest recorded CPU usage
            cpuhighestrecorded = 0

            # Set font color to green
            window['CPUPercent'].Update(text_color='#058700')

        # If CPU usage is more than 75%
        else:

            # If CPU usage is higher than the previously highest recorded CPU usage (only log scenarios to database where CPU usage is higher than previously logged CPU usage, instead of creating a record for each second, until usage drops below 75% and is reset)
            if cpupercent > cpuhighestrecorded:

                # Set new highest recorded CPU usage for period over 75%
                cpuhighestrecorded = cpupercent

                # Add log to database
                query = '''INSERT INTO PerformanceLogs (HardwareId, UsagePercent, PhysicalCores, LogicalCores, TotalMemory, UsedMemory, AvailableMemory, DeviceName) VALUES (?,?,?,?,?,?,?,?)'''
                values = [1,cpupercent,physicalcores,logicalcores,ramtotal,ramused,ramavailable, devicename]
                cursor.execute(query, values)
                connection.commit()

            # Set font color to red
            window['CPUPercent'].Update(text_color='#870000')

        # Update RAM data in window
        window['RAMPercent'].Update(str(round(rampercent, 1)) + '%')
        window['TotalMemory'].Update('Total Memory: ' + str(ramtotal))
        window['UsedMemory'].Update('Used Memory: ' + str(ramused) + 'GB')
        window['AvailableMemory'].Update('Available Memory: ' + str(ramavailable) + 'GB')

        # If RAM usage is less than 75%
        if rampercent < 75:

            #Resent highest recorded RAM usage
            ramhighestrecorded = 0

            # Set font color to green
            window['RAMPercent'].Update(text_color='#058700')

        # If RAM usage is more than 75%
        else:

            # If RAM usage is higher than the previously highest recorded RAM usage (only log scenarios to database where RAM usage is higher than previously logged RAM usage, instead of creating a record for each second, until usage drops below 75% and is reset)
            if cpupercent > cpuhighestrecorded:

                # Set new highest recorded RAM usage for period over 75%
                cpuhighestrecorded = cpupercent

                # Add log to database
                query = '''INSERT INTO PerformanceLogs (HardwareId, UsagePercent, PhysicalCores, LogicalCores, TotalMemory, UsedMemory, AvailableMemory, DeviceName) VALUES (?,?,?,?,?,?,?,?)'''
                values = [2,rampercent,physicalcores,logicalcores,ramtotal,ramused,ramavailable, devicename]
                cursor.execute(query, values)
                connection.commit()

            # Set font color to red
            window['RAMPercent'].Update(text_color='#870000')

        # Update list if top 20 processes in window
        window['Top20Processes'].Update(values=top20Processes)

# Main
if __name__ == "__main__":

    # On program start
    print('Starting Performance Monitor')

    # Create connection to AWS instance
    connection = initAWSConnection()

    # Build GUI
    buildGui(connection)

    # On program exit
    print('\nExiting Performance Monitor')
    connection.cursor().close()
    connection.close()
