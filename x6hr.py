#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        x6hr.py
# Purpose:     log reader of SUUNTO H6HR
# Author:      tomoya kamata (iware pref. japan)
# Created:     15 Mar 2010
# Copyright:   GPL. please read COPYING file
# mailto:      lycopersin@gmail.com)
# web:         http://lycopersin.blogspot.com
#-------------------------------------------------------------------------------

import serial

## my investigation (2010.3.17 T.Kamata)
## comments are my hypothesis, pls keep in mind that they might be wrong.
## ********************************************************************************
##  05 00 04 | 5A 00 | (01) 05 5E                        
## ********************************************************************************
##  general setting
##  05 00 0E | 64 00 | (0B) 00 01 02 01 00 01 02 01 01 01 6B 04                                          
## ********************************************************************************
## = 0D48 (l 12): Retrieve watch history.
##    Format as follows:
##      Max alt: YY MM DD ALT_L ALT_H
##      Ascent :  ASC_L  .. .. .. (supposedly on 4 bytes as 2 are not enough)
##      Descent:  DESC_L .. .. .. (supposedly on 4 bytes as 2 are not enough)
##      ??: .. ..
##      Last reset date: YY MM DD 
##  05 00 15 | 48 0D | (12) 08 05 17 E5 00 00 00 00 00 00 00 00 00 04 00 FF FF FF 53               
## ********************************************************************************
##  hiking index table
##  05 00 17 | B4 0F | (14) 01 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 AC            
## ********************************************************************************
##  hiking log index 1
##  05 00 33 | C8 0F | (30) 00 0A 03 11 0E 10 0A 01 00 00 00 00 00 00 00 03 31 00 00 00 00 00 00 D8 03 11 0E 10 00 D8 03 11 0E 10 4B 61 58 E6 1E 00 00 00 11 00 00 FF FF FF AC                              
## ********************************************************************************
##  hiking log index 2
##  05 00 33 | 48 10 | (30) 00 0A 03 11 0E 1F 0A 01 00 00 00 00 00 00 00 05 14 00 00 00 00 00 00 D8 03 11 0E 1F 00 D8 03 11 0E 1F 4A 53 4E E6 1E 00 00 00 20 00 00 FF FF FF 0B                           
## ********************************************************************************
##  chrono index table
##  05 00 21 | C9 19 | (1E) 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 CF                                 
## ********************************************************************************
##  chrono log index 1
##  05 00 35 | FA 19 | (32) 09 0A 03 11 0E 1C 0A 01 00 00 00 00 00 01 00 03 0D 05 00 00 00 00 00 D8 03 11 0E 1C 00 D8 03 11 0E 1C 4A 60 54 E6 1E 00 00 00 11 00 00 FF FF FF FF FF BB                        
## ********************************************************************************
##  product or protocol number?
##  05 00 04 | 5A 00 | (01) 05 5E                        
## ********************************************************************************
##  serial number
##  05 00 07 | 5D 00 | (04) 3D 1E 20 60 3A               

class x6hr:
    def __init__(self):
        self.x6hr = None

    def open(self, serial_port = "COM1"):
        """
        open serial communication port

        serial_port : port name
        return : becomes None when Fail to open.
        """
        if self.x6hr == None:
            self.x6hr = serial.Serial(port=serial_port, timeout=3)
        return self.x6hr

    def write_raw(self, bin):
        """
        write raw binaly data
        bin : sequence of write data to suunto
        """
        cmd = "".join(map(chr, bin))
        self.x6hr.write(cmd)

    def write_cmd(self, bin):
        """
        write data. before write data this function make packet format.
        bin : sequence of write data to suunto
        """
        cmd2 = [0x05, 0x00, len(bin)] + bin
        c = 0
        for i in cmd2[3:]: c = c ^ i
        cmd3 = cmd2 + [c]
        self.write_raw(cmd3)

    def read_raw(self, length):
        """
        read raw data.
        this function will return raw packet binaly data.
        """
        return map(ord, list(self.x6hr.read(length)))

    def read_register(self, addr, length):
        self.write_cmd([addr & 0xff, (addr >> 8) & 0xff, length])
        data = self.read_raw(length + 7)
        ret = data[6:-1]
        return ret

    def read_units(self):
        data = self.read_register(0x64, 0x0b)
        # light night  [1, 0, 2, 1, 0, 1, 2, 1, 1, 1, 107]
        # light off    [1, 0, 1, 1, 0, 1, 2, 1, 1, 1, 107]
        # light normal [1, 0, 0, 1, 0, 1, 2, 1, 1, 1, 107]
        # tone on      [1, 0, 1, 1, 0, 1, 2, 1, 1, 1, 107]
        # tone off     [0, 0, 1, 1, 0, 1, 2, 1, 1, 1, 107]
        # time 24h     [1, 0, 1, 1, 0, 1, 2, 1, 1, 1, 107]
        # time 12g     [1, 0, 1, 0, 0, 1, 2, 1, 1, 1, 107]
        # icon on      [1, 1, 2, 1, 0, 1, 2, 1, 1, 1, 107]
        # icon on      [1, 0, 2, 1, 0, 1, 2, 1, 1, 1, 107]
        # I investigated above. (T.Kamata)
        #
        # 12: altitude ft(00) / m(01)
        # 13: ascentional speed m/s(00) / m/mn(01) / m/h(02) / ft/s(03) / ft/mn(04) / ft/h(05)
        # 14: pression inHg(00) / hPa(01)
        # 15: temperature F(00) / C (01)
        # Referenced from http://wiki.terre-adelie.org/SuuntoX6HR
        units = {}
        units['tone'] = data[0] == 1 
        units['icon'] = data[1] == 1
        units['light'] = ['Night', 'OFF', 'Normal'][data[2]]
        units['time'] = ['12h', '24h'][data[3]]
        units['date'] = ['MM.DD', 'DD.MM', 'Day'][data[4]]
        units['altitude'] = ['ft', 'm'][data[5]]
        units['ascsp'] = ['m/s', 'm/mn', 'm/h', 'ft/s', 'ft/mn', 'ft/h'][data[6]]
        units['pressure'] = ['inHg', 'hPa'][data[7]]
        units['temperature'] = ['F', 'C'][data[8]]
        return units

    def read_serial_number(self):
        #read serial number
        data = self.read_register(0x005d, 4)
        return (data[0] * 1000000) + (data[1] * 10000) + (data[2] * 100) + data[3]

    # Get list of "hiking" (logbook) logs
    def read_hiking_index(self):
        data = self.read_register(0x0fb4, 0x14)
        lut = []
        for i in data:
            if i != 0:
                lut.append(i)
        return lut

    def read_hiking_log(self, index):
        p = self.read_register(0x0fc8 + (index - 1) * 128, 0x30)
        log = {}
        log['start'] = "20%02d/%d/%d %02d:%02d" % (p[1],p[2],p[3],p[4],p[5])
        log['interval'] = p[6]
        log['hrdata'] = p[7] == 1
        log['total ascent'] = p[8] * 256 + p[9]
        log['total descent'] = p[10] * 256 + p[11]
        log['laps'] = p[13]        
        log['duration'] = "%02d:%02d:%02d.%d" % (p[14], p[15], p[16], p[17])
        log['highest time'] = "%d/%d %02d:%02d" % (p[0x18],p[0x19],p[0x1a],p[0x1b])
        log['highest point altitude'] = p[0x16] * 256 + p[0x17]
        log['lowest time']  = "%d/%d %02d:%02d" % (p[0x1e],p[0x1f],p[0x20],p[0x21])
        log['lowest altitude']  = p[0x1c] * 256 + p[0x1d]
        log['HR min'] = p[34]
        log['HR max'] = p[35]
        log['HR average'] = p[36]
        log['HR limit high'] = p[37]
        log['HR limit low'] = p[38]
        log['HR over limit'] = p[39] * 256 + p[40]
        log['HR in limit'] = p[41] * 256 + p[42]
        log['HR under limit'] = p[43] * 256 + p[44]
        return log
        # idx   0,  1,  2,  3,  4,  5,  6,  7,  8,  9,  A,  B,  C,  D,  E,  F,
        # hex  00, 0A, 03, 11, 0E, 10, 0A, 01, 00, 00, 00, 00, 00, 00, 00, 03,
        # dec   0, 10,  3, 17, 14, 16, 10,  1,  0,  0,  0,  0,  0,  0,  0,  3,
        
        # idx  10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 1A, 1B, 1C, 1D, 1E, 1F,
        # hex  31, 00, 00, 00, 00, 00, 00, D8, 03, 11, 0E, 10, 00, D8, 03, 11,
        # dec  49,  0,  0,  0,  0,  0,  0,216,  3, 17, 14, 16,  0,216,  3, 17,
        
        # idx  20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 2A, 2B, 2C, 2D, 2E, 2F,
        # hex  0E, 10, 4B, 61, 58, E6, 1E, 00, 00, 00, 11, 00, 00, FF, FF, FF
        # dec  14, 16, 75, 97, 88,230, 30,  0,  0,  0, 17,  0,  0,255,255,255
        
        ## Suunto X6HR. log data  (captured by SAM which is SUUNTO production.)
        ## 	General 										
        ## Wristop model: 	X6HR.									
        ## Wristop serial: 	61303296									
        ## Log name: 		心拍数のハイキング･ログ:									
        ## Log type: 		HR Hiking									
        ## Start :		2010/3/17 14:16									
        ## End :		2010/3/17 14:19									
        ## Duration: 		00:03.5									
        ## Sample interval: 	10	s								
        ## Notes: 											
        ## 	Altitude										
        ## High point: 		216	m								
        ## Time: 		2010/3/17 14:16									
        ## Low point: 		216	m								
        ## Time: 		2010/3/17 14:16									
        ## Total ascent		0	m								
        ## Ascent time: 	00:00.0									
        ## Average ascent: 	0	m/min								
        ## Total descent	0	m								
        ## Descent time: 	00:00.0									
        ## Average descent: 	0	m/min								
        ## 	Heart rate										
        ## HR min: 		75									
        ## HR max: 		97									
        ## HR average: 		88									
        ## HR limit high: 	230									
        ## HR limit low: 	30									
        ## Over high: 		00:00.0									
        ## In limits: 		00:02.5									
        ## Below low: 		00:00.0									
        ## 	Samples										
        ## Calendar time	Log time		Heart rate		Altitude (m)		Lap		Note	
        ## 2010/3/17 14:16	00:00.0		0		216		00:00.0			

    def read_chrono_index(self):
        data = self.read_register(0x19c9, 0x1e)
        lut = []
        for i in data:
            if i != 0:
                lut.append(i)
        return lut

    def read_chrono_log(self, index):
        p = self.read_register(0x19fa + (index - 1) * 0x32, 0x32)
        log = {}
        firstchunk = p[0]
        log['date'] = "%0.2d/%0.2d/%0.2d %0.2d:%0.2d"  % (p[1], p[2], p[3], p[4], p[5])
        log['interval'] = p[6]
        log['total ascent'] = p[8] * 256 + p[9]
        log['total descent'] = p[10] * 256 + p[11]
        log['laps'] = p[13]
        log['duration'] = "%0.2dh %0.2dm %0.2d.%ds" % (p[14], p[15], p[16], p[17])
        log['inter up'] = p[18] * 256 + p[19]
        log['inter down'] = p[20] * 256 + p[21]
        log['highest altitude'] = p[22] * 256 + p[23]
        log['highest time'] = "%02d/%02d %02d:%02d" % (p[31], p[30], p[32], p[33])
        log['HR exist'] = p[7] == 1
        log['HR min'] = p[34]
        log['HR max'] = p[35]
        log['HR avg'] = p[36]
        log['HR limit high'] = p[37]
        log['HR limit low'] = p[38]
        log['HR over_limit'] = p[39] * 256 + p[40]
        log['HR in_limit'] = p[41] * 256 + p[42]
        log['HR under limit'] = p[43] * 256 + p[44]
        log['data'] = self.read_chrono_data(firstchunk)
        return log
            
    def read_chrono_data(self, index):
        d, next_index = [], index
        while next_index != 0:
            addr = 0x2000 + (next_index - 1) * 128
            d0 = self.read_register(addr, 0x32) + self.read_register(addr + 0x32, 0x32) + self.read_register(addr + 0x32 * 2, 0x1c)
            next_index = d0[-1]
            d = d + d0[1:-1]
            
        data, i = [], 0
        while i < len(d):
            if d[i] == 130:
                i += 11
            elif d[i] == 128:
                break
            else:
                data.append((d[i] * 256 + d[i+1], d[i+2]))
                i += 3
        return data

    def read_weather_log(self):
        """
        read weather log from suunto
        return : temperature , pressure
        
        """
        log0 = []
        for i, addr in enumerate(range(0x0d70, 0x0d70 + 580, 0x32)):
            if i < 11: length = 50
            else: length = 30
            log0 = log0 + self.read_register(addr, length)

        
        head, log = log0[0], log0[1:]

        press0, temp0 = [], []
        for h, i in enumerate(range(0, len(log), 3)):
            press0.append(log[i] * 256 + log[i + 1])
            temp0.append(log[i + 2])
        press = press0[head:] + press0[0:head]
        temp = temp0[head:] + temp0[0:head]
        return zip(temp, press)

    def close(self):
        if self.x6hr != None:
            self.x6hr.close()
            self.x6hr == None

if __name__ == '__main__':
    import Gnuplot
    import optparse
    import sys

    parser = optparse.OptionParser(usage="%prog [Options]", version="%prog-0.1")
    parser.add_option('-l', '--list-logs', action="store_true", dest = 'list_logs', default=False, help='List available logs')
    parser.add_option('-k', '--fetch-hiking-log', dest = 'hiking_index', type='int', default=-1, help='Fetch hiking log')
    parser.add_option('-c', '--fetch-chrono-log', dest = 'chrono_index', type='int', default=-1, help='Fetch chrono log')
    parser.add_option('-w', '--fetch-weather-log',dest = 'weather_log', action='store_true', default=True, help='Fetch weather log')
    parser.add_option('-u', '--units', dest = 'units', action='store_true', default=False, help='Show units setting')
    parser.add_option('-A', '--fetch-all-indexes', dest = 'fetch_all_indexes', action='store_true', default=False, help = 'Fetch all indexes')
    parser.add_option('-d', '--device', dest = 'serial_port', metavar="FILE", default="COM1", help='Serial port device')
    parser.add_option('-C', '--chrono-log-filename', dest = 'chrono_log_filename', metavar="FILE", default="chrono.csv")
    parser.add_option('-W', '--weather-log-filename', dest = 'weather_log_filename', metavar="FILE", default="weather.csv")
    parser.add_option('-g', '--gnuplot', action="store_true", dest="show_gnuplot", default=False)    

    (opts, args) = parser.parse_args()

    fetch_all_indexes = opts.fetch_all_indexes
    if opts.show_gnuplot == True:
        fetch_all_indexes = True

    x6 = x6hr();
    x6.open(serial_port = opts.serial_port)
    serial_number = x6.read_serial_number()
    units = x6.read_units()
    hiking_logs ,chrono_logs, weather_log = [], [], None
    hiking_indexes = x6.read_hiking_index()
    if opts.hiking_index > 0:
        for i in hiking_indexes:
            if opts.fetch_all_indexes or i == opts.hiking_index:
                hiking_logs.append(x6.read_hiking_log(i))


    chrono_indexes = x6.read_chrono_index()
    if opts.chrono_index > 0:
        for i in chrono_indexes:
            if opts.fetch_all_indexes or i == opts.chrono_index:
                chrono_logs.append(x6.read_chrono_log(i))

    if opts.weather_log == True:
        weather_log = x6.read_weather_log()
        f = open(opts.weather_log_filename, 'w')
        for i, j in enumerate(weather_log):
            f.write("%02d:%02d %d %d\n" % (i / 4, (i % 4) * 15, j[0], j[1]))
        f.close()
    x6.close()

    print "serial number = ", serial_number

    for n, i in enumerate(hiking_logs):
        print "* Hiking", n + 1
        for j in i.keys():
            print j, i[j]

    #chrono log
    for n, i in enumerate(chrono_logs):
        print "* Chrono", n + 1
        for j in i.keys():
            if j != 'data':
                print j, i[j]
        if opts.show_gnuplot == True:
            interval = i['interval']
            f = open(opts.chrono_log_filename, 'w')
            for n, j in enumerate(i['data']):
                sec = n * interval
                f.write("%02d:%02d %d %d\n" % (sec / 60, sec % 60, j[0], j[1]))
            f.close()
            g_chrono = Gnuplot.Gnuplot()
            g_chrono("set title 'Chrono Log'")
            g_chrono("set style data lines")
            g_chrono("set xlabel 'Time'")
            g_chrono("set ylabel 'Altitude[%s]'" % units['altitude'])
            g_chrono("set y2tics nomirror")
            g_chrono("set y2label 'Hart Rate'")
            g_chrono("set xdata time")
            g_chrono('set timefmt "%M:%S"')
            g_chrono('set format x "%M:%S"')
            #g_chrono('set xrange ["00:00":"48:00"]')
            g_chrono.plot(Gnuplot.File(opts.chrono_log_filename, using='1:2', with_='line', title='Altitude', axes='x1y1'),
                   Gnuplot.File(opts.chrono_log_filename, using='1:3', with_='line', title='HR', axes='x1y2'))

    if opts.list_logs == True:
        print "List of Log"
        print " Hiking Log ", hiking_indexes
        print " Chrono Log ", chrono_indexes

    if opts.show_gnuplot == True:
        if weather_log != None:
            g_weather = Gnuplot.Gnuplot()
            g_weather("set title 'Weather Log'")
            g_weather("set style data lines")
            g_weather("set xlabel 'Time'")
            g_weather("set ylabel 'Temperature[%s]'" % units['temperature'])
            g_weather("set y2tics nomirror")
            g_weather("set y2label 'Pressure[%s]'" % units['pressure'])
            g_weather("set xdata time")
            g_weather('set timefmt "%M:%S"')
            g_weather('set format x "%M:%S"')
            g_weather('set xrange ["00:00":"48:00"]')
            g_weather.plot(Gnuplot.File(opts.weather_log_filename, using='1:2', with_='line', title='Temperature', axes='x1y1'),
                   Gnuplot.File(opts.weather_log_filename, using='1:3', with_='line', title='Pressure', axes='x1y2'))
        raw_input("hit any key")

    #if opts.show_log == True:
    #    for i in zip(temp, p):
    #        print i[0], i[1]
        



