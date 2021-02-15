"""

    SATELLITE'S TELEMETRY ANALYSIS
    Description: The code here implemented is my personal work
    trying to analyse a satellite's telemetry file.

    This small script tries to find out all the telemetry data
    which is contained in a binary file, parse it, extract some of the
    info and then create a new file to be exported to STK.

    Date: 22 of January 2021
    Author: Jose María Herrera Sampablo

"""

import struct

block_size = 2068  # Every block of info (record) is made up of 2068 bytes

"""
    According to .csv structure:
        - Time in TAI seconds from J2000 is uint32 datatype so they are 
        4 bytes in length starting from byte 65 in data
        - Orbit Position ECI are int32 data types so they are 4 bytes in 
        length starting from byte 112 position in data
        - Attitude quaternions are int32 data types so they are 4 bytes in length 
        starting from byte 206 position in data
"""

time_begin, time_end = 65, 69
pos_begin, pos_end = 112, 124  # Position
att_begin, att_end = 206, 222  # Attitude


# Begin and end shows the byte in which the information we are looking for
# begins and ends respectively inside a given block of information.
# Each block of information (record) will correspond to a different
# epoch


def parse_data(data, offset=0):
    """Parse the data for the variables Time, Position and Attitude"""
    # offset will allow us to move between the different records
    time = struct.unpack('@I', data[offset + time_begin:offset + time_end])
    position_ECI = struct.unpack('@iii', data[offset + pos_begin:offset + pos_end])
    quaternions = struct.unpack('@iiii', data[offset + att_begin:offset + att_end])

    return time, position_ECI, quaternions


# Careful with big-endians and little-endians


def num_blocks(data):
    """Function to find how many blocks of info (epochs) we have"""

    return int(len(data) / block_size)


def get_offset(block_number):
    """Compute the offset between blocks of info"""

    return block_number * block_size


"""

    HERE IS THE MAIN PROGRAM
        Here we will open the file, load the data, decode 
        it and finally parse the desired information
        
"""

file = open('telemetry.bin', 'rb')
tlm = file.read()
file.close()

time = []
position = []
attitude = []

for record in range(num_blocks(tlm)):
    off = get_offset(record)
    t, p, q = parse_data(tlm, off)
    time.append(t[0])
    position.append(p)
    attitude.append(q)

# Once we have got the data for every block of info, we can write
# it in a file to be imported in STK. I have chosen an attitude
# file .a which describes the attitude quaternions.


att_conversion = 5 * 10 ** (-10)
pos_conversion = 2.00 * 10 ** (-5)

# Conversion according .csv file for Attitude and Time.
# TAI time does not take into account leap seconds as UTC does.
# STK tend to use UTC time, so I will apply the .csv conversion
# to TAI time in telemetry and then apply the difference between
# both time measurement systems.
# I have done some rough conversions. For time may be better to
# use some libraries like datetime to perform this using
# datetime.deltatime to account for the real date from J2000

with open('Attitude.a', 'w') as file:
    file.write('stk.v.11.7' + '\n')
    file.write('BEGIN Attitude' + '\n')
    file.write('NumberOfAttitudePoints {}'.format(len(time)) + '\n')
    file.write('ScenarioEpoch           1 Jan 2000 00:00:00.000000000' + '\n')
    file.write('InterpolationMethod     Lagrange' + '\n')
    file.write('CentralBody             Earth' + '\n')
    file.write('CoordinateAxes        J2000' + '\n')
    file.write('AttitudeTimeQuaternions' + '\n')
    for data_block in range(len(time)):
        file.write('{} {} {} {} {}'.format((time[data_block]*0.2 - 37),
                                           attitude[data_block][0] * att_conversion,
                                           attitude[data_block][1] * att_conversion,
                                           attitude[data_block][2] * att_conversion,
                                           attitude[data_block][3] * att_conversion)
                   + '\n')
    file.write('END Attitude')

# There is another file we can create related to the ephemeris of the satellite.
# In this case I have choose to write a 'EphemerisTimePosFormat'. Here we just
# need to introduce Time and Position, and STK just compute the velocity by
# interpolation of position and function and analytical derivation.

with open('Ephemeris.e', 'w') as file:
    file.write('stk.v.11.7' + '\n')
    file.write('BEGIN Ephemeris' + '\n')
    file.write('NumberOfEphemerisPoints {}'.format(len(time)) + '\n')
    file.write('ScenarioEpoch           1 Jan 2000 00:00:00.000000000' + '\n')
    file.write('InterpolationMethod     Lagrange' + '\n')
    file.write('DistanceUnit           Kilometers' + '\n')
    file.write('CentralBody             Earth' + '\n')
    file.write('CoordinateSystem        J2000' + '\n')
    file.write('EphemerisTimePos' + '\n')
    for data_block in range(len(time)):
        file.write('{} {} {} {}'.format((time[data_block] * 0.2 - 37),
                                        position[data_block][0] * pos_conversion,
                                        position[data_block][1] * pos_conversion,
                                        position[data_block][2] * pos_conversion)
                   + '\n')
    file.write('END Ephemeris')
