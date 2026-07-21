EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 3
Title "PI Daughter Board (Power, CPU & Switches)"
Date "2021-02-28"
Rev "0.1"
Comp "Segmentum"
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
Text GLabel 2000 4950 0    50   Input ~ 0
RS485_TXD
Text GLabel 2000 5050 0    50   Input ~ 0
RS485_RXD
Wire Wire Line
	2000 4950 2150 4950
Wire Wire Line
	2000 5050 2150 5050
$Comp
L power:+5V #PWR07
U 1 1 603B34BA
P 2750 3900
F 0 "#PWR07" H 2750 3750 50  0001 C CNN
F 1 "+5V" H 2765 4073 50  0000 C CNN
F 2 "" H 2750 3900 50  0001 C CNN
F 3 "" H 2750 3900 50  0001 C CNN
	1    2750 3900
	1    0    0    -1  
$EndComp
$Comp
L power:GND #PWR09
U 1 1 603B3CA2
P 2200 4150
F 0 "#PWR09" H 2200 3900 50  0001 C CNN
F 1 "GND" H 2205 3977 50  0000 C CNN
F 2 "" H 2200 4150 50  0001 C CNN
F 3 "" H 2200 4150 50  0001 C CNN
	1    2200 4150
	1    0    0    -1  
$EndComp
$Comp
L Device:C_Small C15
U 1 1 603B4B49
P 2000 4050
F 0 "C15" H 2250 4000 50  0000 R CNN
F 1 "0.1u" H 2250 4100 50  0000 R CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 2000 4050 50  0001 C CNN
F 3 "~" H 2000 4050 50  0001 C CNN
F 4 "C14663" H 2000 4050 50  0001 C CNN "LCSC Part #"
	1    2000 4050
	-1   0    0    1   
$EndComp
$Comp
L Device:C_Small C16
U 1 1 603B545A
P 2400 4050
F 0 "C16" H 2308 4004 50  0000 R CNN
F 1 "0.1u" H 2308 4095 50  0000 R CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 2400 4050 50  0001 C CNN
F 3 "~" H 2400 4050 50  0001 C CNN
F 4 "C14663" H 2400 4050 50  0001 C CNN "LCSC Part #"
	1    2400 4050
	-1   0    0    1   
$EndComp
$Comp
L Connector:Raspberry_Pi_2_3 J3
U 1 1 603AB82F
P 2950 5850
F 0 "J3" H 1900 7250 50  0000 C CNN
F 1 "Raspberry PI Header" H 2250 7150 50  0000 C CNN
F 2 "Segmentum:Raspberry_Pi_Header_FaceDown" H 2950 5850 50  0001 C CNN
F 3 "https://www.raspberrypi.org/documentation/hardware/raspberrypi/schematics/rpi_SCH_3bplus_1p0_reduced.pdf" H 2950 5850 50  0001 C CNN
	1    2950 5850
	1    0    0    -1  
$EndComp
Wire Wire Line
	2850 4550 2750 4550
Wire Wire Line
	2750 4550 2750 3950
Connection ~ 2750 4550
Connection ~ 2750 3950
Wire Wire Line
	2750 3950 2750 3900
$Comp
L power:+3V3 #PWR08
U 1 1 603BA6E2
P 3150 3900
F 0 "#PWR08" H 3150 3750 50  0001 C CNN
F 1 "+3V3" H 3165 4073 50  0000 C CNN
F 2 "" H 3150 3900 50  0001 C CNN
F 3 "" H 3150 3900 50  0001 C CNN
	1    3150 3900
	1    0    0    -1  
$EndComp
$Comp
L Device:C_Small C17
U 1 1 603BACA3
P 3350 4050
F 0 "C17" H 3258 4004 50  0000 R CNN
F 1 "0.1u" H 3258 4095 50  0000 R CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 3350 4050 50  0001 C CNN
F 3 "~" H 3350 4050 50  0001 C CNN
F 4 "C14663" H 3350 4050 50  0001 C CNN "LCSC Part #"
	1    3350 4050
	-1   0    0    1   
$EndComp
$Comp
L Device:C_Small C18
U 1 1 603BB403
P 3750 4050
F 0 "C18" H 3658 4004 50  0000 R CNN
F 1 "0.1u" H 3658 4095 50  0000 R CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 3750 4050 50  0001 C CNN
F 3 "~" H 3750 4050 50  0001 C CNN
F 4 "C14663" H 3750 4050 50  0001 C CNN "LCSC Part #"
	1    3750 4050
	-1   0    0    1   
$EndComp
$Comp
L power:GND #PWR010
U 1 1 603BB883
P 3550 4150
F 0 "#PWR010" H 3550 3900 50  0001 C CNN
F 1 "GND" H 3555 3977 50  0000 C CNN
F 2 "" H 3550 4150 50  0001 C CNN
F 3 "" H 3550 4150 50  0001 C CNN
	1    3550 4150
	1    0    0    -1  
$EndComp
Wire Wire Line
	3350 4150 3550 4150
Connection ~ 3550 4150
Wire Wire Line
	3550 4150 3750 4150
Wire Wire Line
	3150 3900 3150 3950
Wire Wire Line
	3150 4550 3050 4550
Connection ~ 3150 4550
Wire Wire Line
	3150 3950 3350 3950
Connection ~ 3150 3950
Wire Wire Line
	3150 3950 3150 4550
Connection ~ 3350 3950
Wire Wire Line
	3350 3950 3750 3950
Connection ~ 2400 3950
Wire Wire Line
	2400 3950 2750 3950
Wire Wire Line
	2000 3950 2400 3950
Wire Wire Line
	2000 4150 2200 4150
Connection ~ 2200 4150
Wire Wire Line
	2200 4150 2400 4150
$Comp
L power:GND #PWR017
U 1 1 603BDD94
P 2900 7300
F 0 "#PWR017" H 2900 7050 50  0001 C CNN
F 1 "GND" H 2905 7127 50  0000 C CNN
F 2 "" H 2900 7300 50  0001 C CNN
F 3 "" H 2900 7300 50  0001 C CNN
	1    2900 7300
	1    0    0    -1  
$EndComp
Wire Wire Line
	2550 7150 2650 7150
Connection ~ 2650 7150
Wire Wire Line
	2650 7150 2750 7150
Connection ~ 2750 7150
Wire Wire Line
	2750 7150 2850 7150
Connection ~ 2850 7150
Wire Wire Line
	2850 7150 2900 7150
Connection ~ 2950 7150
Wire Wire Line
	2950 7150 3050 7150
Connection ~ 3050 7150
Wire Wire Line
	3050 7150 3150 7150
Connection ~ 3150 7150
Wire Wire Line
	3150 7150 3250 7150
Wire Wire Line
	2900 7150 2900 7300
Connection ~ 2900 7150
Wire Wire Line
	2900 7150 2950 7150
Text GLabel 3900 5250 2    50   Input ~ 0
I2C_External_Data
Text GLabel 3900 5350 2    50   Input ~ 0
I2C_External_Clock
Wire Wire Line
	3750 5250 3900 5250
Wire Wire Line
	3750 5350 3900 5350
Text GLabel 3900 6550 2    50   Input ~ 0
PWM_0
Text GLabel 3900 6650 2    50   Input ~ 0
PWM_1
Wire Wire Line
	3750 6550 3900 6550
Wire Wire Line
	3750 6650 3900 6650
Text GLabel 2000 6250 0    50   Input ~ 0
RS485_TXE
Text GLabel 2000 6450 0    50   Input ~ 0
STATUS_LED_4
Wire Wire Line
	2000 6150 2150 6150
Wire Wire Line
	2000 6250 2150 6250
Wire Wire Line
	2000 6450 2150 6450
Text GLabel 3900 4950 2    50   Input ~ 0
I2C_Internal_Data
Text GLabel 3900 5050 2    50   Input ~ 0
I2C_Internal_Clock
Text GLabel 2000 5650 0    50   Input ~ 0
STATUS_LED_1
Text GLabel 2000 5750 0    50   Input ~ 0
STATUS_LED_3
Text GLabel 2000 5850 0    50   Input ~ 0
SHUTDOWN
Text GLabel 2000 5250 0    50   Input ~ 0
STATUS_LED_2
Text GLabel 2000 5450 0    50   Input ~ 0
SHIFT_NOE
Wire Wire Line
	2000 5250 2150 5250
Wire Wire Line
	2000 5450 2150 5450
Wire Wire Line
	2000 5650 2150 5650
Wire Wire Line
	2000 5750 2150 5750
Wire Wire Line
	2000 5850 2150 5850
Wire Wire Line
	3750 4950 3900 4950
Wire Wire Line
	3750 5050 3900 5050
Text GLabel 3900 6350 2    50   Input ~ 0
SHIFT_IN_Load
Text GLabel 3900 6250 2    50   Input ~ 0
SHIFT_IN_SerialData
Text GLabel 3900 6150 2    50   Input ~ 0
SHIFT_IN_Clock
Text GLabel 3900 6050 2    50   Input ~ 0
SHIFT_IN_ClockEnable
Wire Wire Line
	3900 6050 3750 6050
Wire Wire Line
	3750 6150 3900 6150
Wire Wire Line
	3900 6250 3750 6250
Wire Wire Line
	3750 6350 3900 6350
Text GLabel 3900 5650 2    50   Input ~ 0
WD_E
Text GLabel 3900 5750 2    50   Input ~ 0
WATCHDOG
Text GLabel 3900 5950 2    50   Input ~ 0
PB_1
Wire Wire Line
	3750 5650 3900 5650
Wire Wire Line
	3750 5750 3900 5750
Wire Wire Line
	3750 5950 3900 5950
Text Notes 850  3900 0    213  ~ 0
CPU
$Comp
L PiDaughterBoard-rescue:TPS54331-Converter_DCDC U1
U 1 1 603DA750
P 7950 1200
F 0 "U1" H 8000 1150 50  0000 C CNN
F 1 "TPS54331" H 8000 1050 50  0000 C CNN
F 2 "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm" H 7950 1200 50  0001 C CNN
F 3 "" H 7950 1200 50  0001 C CNN
F 4 "C9865" H 7950 1200 50  0001 C CNN "LCSC Part #"
	1    7950 1200
	1    0    0    -1  
$EndComp
$Comp
L Device:L_Small L1
U 1 1 603DD47A
P 9100 1000
F 0 "L1" V 9285 1000 50  0000 C CNN
F 1 "6.8u" V 9194 1000 50  0000 C CNN
F 2 "Inductor_SMD:L_Wuerth_HCI-1365" H 9100 1000 50  0001 C CNN
F 3 "~" H 9100 1000 50  0001 C CNN
F 4 "C149573" H 9100 1000 50  0001 C CNN "LCSC Part #"
	1    9100 1000
	0    -1   -1   0   
$EndComp
$Comp
L Device:C_Small C1
U 1 1 603DE8B8
P 7350 1250
F 0 "C1" H 7258 1204 50  0000 R CNN
F 1 "0.1u" H 7258 1295 50  0000 R CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 7350 1250 50  0001 C CNN
F 3 "~" H 7350 1250 50  0001 C CNN
F 4 "C14663" H 7350 1250 50  0001 C CNN "LCSC Part #"
	1    7350 1250
	-1   0    0    1   
$EndComp
$Comp
L power:GND #PWR02
U 1 1 603EA66A
P 9550 1650
F 0 "#PWR02" H 9550 1400 50  0001 C CNN
F 1 "GND" H 9555 1477 50  0000 C CNN
F 2 "" H 9550 1650 50  0001 C CNN
F 3 "" H 9550 1650 50  0001 C CNN
	1    9550 1650
	1    0    0    -1  
$EndComp
$Comp
L Device:D_Schottky D1
U 1 1 603EAFA7
P 8750 1350
F 0 "D1" V 8704 1430 50  0000 L CNN
F 1 "B340A" V 8795 1430 50  0000 L CNN
F 2 "Diode_SMD:D_SMA" H 8750 1350 50  0001 C CNN
F 3 "~" H 8750 1350 50  0001 C CNN
F 4 "C64982" H 8750 1350 50  0001 C CNN "LCSC Part #"
	1    8750 1350
	0    1    1    0   
$EndComp
$Comp
L Device:C_Small C2
U 1 1 603ED96A
P 9350 1250
F 0 "C2" H 9258 1204 50  0000 R CNN
F 1 "33u" H 9258 1295 50  0000 R CNN
F 2 "Capacitor_SMD:C_1210_3225Metric" H 9350 1250 50  0001 C CNN
F 3 "~" H 9350 1250 50  0001 C CNN
F 4 "C531418" H 9350 1250 50  0001 C CNN "LCSC Part #"
	1    9350 1250
	-1   0    0    1   
$EndComp
Wire Wire Line
	7350 1350 7350 1500
Wire Wire Line
	7350 1500 7600 1500
Wire Wire Line
	7350 1150 7350 1000
Wire Wire Line
	7350 1000 8500 1000
Wire Wire Line
	8350 1650 8750 1650
Connection ~ 8750 1650
Wire Wire Line
	8350 1500 8500 1500
Wire Wire Line
	8500 1500 8500 1000
Connection ~ 8500 1000
$Comp
L Device:C_Small C3
U 1 1 60400EE8
P 9800 1250
F 0 "C3" H 9708 1204 50  0000 R CNN
F 1 "33u" H 9708 1295 50  0000 R CNN
F 2 "Capacitor_SMD:C_1210_3225Metric" H 9800 1250 50  0001 C CNN
F 3 "~" H 9800 1250 50  0001 C CNN
F 4 "C531418" H 9800 1250 50  0001 C CNN "LCSC Part #"
	1    9800 1250
	-1   0    0    1   
$EndComp
Wire Wire Line
	9800 1350 9800 1650
Wire Wire Line
	8750 1650 9350 1650
Wire Wire Line
	9350 1350 9350 1650
Connection ~ 9350 1650
Wire Wire Line
	9350 1150 9350 1000
Wire Wire Line
	9350 1000 9800 1000
Wire Wire Line
	9800 1000 9800 1150
$Comp
L power:+5V #PWR01
U 1 1 60407DE4
P 10700 1000
F 0 "#PWR01" H 10700 850 50  0001 C CNN
F 1 "+5V" H 10715 1173 50  0000 C CNN
F 2 "" H 10700 1000 50  0001 C CNN
F 3 "" H 10700 1000 50  0001 C CNN
	1    10700 1000
	1    0    0    -1  
$EndComp
Wire Wire Line
	9800 1000 10400 1000
Connection ~ 9800 1000
$Comp
L Device:R_Small R1
U 1 1 6040A5A3
P 10400 1200
F 0 "R1" H 10459 1246 50  0000 L CNN
F 1 "0R" H 10459 1155 50  0000 L CNN
F 2 "Resistor_SMD:R_0805_2012Metric" H 10400 1200 50  0001 C CNN
F 3 "~" H 10400 1200 50  0001 C CNN
F 4 "C17477" H 10400 1200 50  0001 C CNN "LCSC Part #"
	1    10400 1200
	1    0    0    -1  
$EndComp
$Comp
L Device:R_Small R2
U 1 1 6040AFA5
P 10400 1500
F 0 "R2" H 10459 1546 50  0000 L CNN
F 1 "10K" H 10459 1455 50  0000 L CNN
F 2 "Resistor_SMD:R_0805_2012Metric" H 10400 1500 50  0001 C CNN
F 3 "~" H 10400 1500 50  0001 C CNN
F 4 "C17414" H 10400 1500 50  0001 C CNN "LCSC Part #"
	1    10400 1500
	1    0    0    -1  
$EndComp
$Comp
L Device:R_Small R3
U 1 1 6040B71B
P 10400 1850
F 0 "R3" H 10459 1896 50  0000 L CNN
F 1 "1.8k" H 10459 1805 50  0000 L CNN
F 2 "Resistor_SMD:R_0805_2012Metric" H 10400 1850 50  0001 C CNN
F 3 "~" H 10400 1850 50  0001 C CNN
F 4 "C17398" H 10400 1850 50  0001 C CNN "LCSC Part #"
	1    10400 1850
	1    0    0    -1  
$EndComp
Connection ~ 10400 1000
Wire Wire Line
	10400 1000 10700 1000
Wire Wire Line
	10400 1600 10400 1650
Wire Wire Line
	8350 1950 8650 1950
Connection ~ 10400 1650
Wire Wire Line
	10400 1650 10400 1750
$Comp
L Device:C_Small C10
U 1 1 604176A6
P 8950 2100
F 0 "C10" H 8858 2054 50  0000 R CNN
F 1 "4.7u" H 8858 2145 50  0000 R CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 8950 2100 50  0001 C CNN
F 3 "~" H 8950 2100 50  0001 C CNN
F 4 "C1779" H 8950 2100 50  0001 C CNN "LCSC Part #"
	1    8950 2100
	-1   0    0    1   
$EndComp
$Comp
L Device:C_Small C11
U 1 1 60417C63
P 9450 2100
F 0 "C11" H 9358 2054 50  0000 R CNN
F 1 "39p" H 9358 2145 50  0000 R CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 9450 2100 50  0001 C CNN
F 3 "~" H 9450 2100 50  0001 C CNN
F 4 "C53278" H 9450 2100 50  0001 C CNN "LCSC Part #"
	1    9450 2100
	-1   0    0    1   
$EndComp
$Comp
L Device:R_Small R6
U 1 1 60417FA1
P 8950 2350
F 0 "R6" H 9009 2396 50  0000 L CNN
F 1 "47k" H 9009 2305 50  0000 L CNN
F 2 "Resistor_SMD:R_0805_2012Metric" H 8950 2350 50  0001 C CNN
F 3 "~" H 8950 2350 50  0001 C CNN
F 4 "C17713" H 8950 2350 50  0001 C CNN "LCSC Part #"
	1    8950 2350
	1    0    0    -1  
$EndComp
Wire Wire Line
	8350 1800 8950 1800
Wire Wire Line
	8950 1800 8950 1950
Wire Wire Line
	9450 1950 8950 1950
Connection ~ 9800 1650
Wire Wire Line
	9450 2000 9450 1950
Wire Wire Line
	8500 1000 8750 1000
Wire Wire Line
	8750 1650 8750 1500
Wire Wire Line
	8750 1200 8750 1000
Connection ~ 8750 1000
Wire Wire Line
	9200 1000 9350 1000
Connection ~ 9350 1000
Wire Wire Line
	8750 1000 9000 1000
Wire Wire Line
	8950 1950 8950 2000
Connection ~ 8950 1950
$Comp
L Device:C_Small C12
U 1 1 60437BCD
P 7550 2775
F 0 "C12" H 7458 2729 50  0000 R CNN
F 1 "0.01u" H 7458 2820 50  0000 R CNN
F 2 "Capacitor_SMD:C_0402_1005Metric" H 7550 2775 50  0001 C CNN
F 3 "~" H 7550 2775 50  0001 C CNN
F 4 "C15195" H 7550 2775 50  0001 C CNN "LCSC Part #"
	1    7550 2775
	-1   0    0    1   
$EndComp
$Comp
L power:GND #PWR06
U 1 1 6043A824
P 6250 3250
F 0 "#PWR06" H 6250 3000 50  0001 C CNN
F 1 "GND" H 6255 3077 50  0000 C CNN
F 2 "" H 6250 3250 50  0001 C CNN
F 3 "" H 6250 3250 50  0001 C CNN
	1    6250 3250
	1    0    0    -1  
$EndComp
$Comp
L Device:R_Small R9
U 1 1 6043E043
P 6850 2800
F 0 "R9" H 6909 2846 50  0000 L CNN
F 1 "68K" H 6909 2755 50  0000 L CNN
F 2 "Resistor_SMD:R_0805_2012Metric" H 6850 2800 50  0001 C CNN
F 3 "~" H 6850 2800 50  0001 C CNN
F 4 "C17801" H 6850 2800 50  0001 C CNN "LCSC Part #"
	1    6850 2800
	1    0    0    -1  
$EndComp
$Comp
L Device:R_Small R4
U 1 1 6043E9CE
P 6950 1900
F 0 "R4" H 7009 1946 50  0000 L CNN
F 1 "330K" H 7009 1855 50  0000 L CNN
F 2 "Resistor_SMD:R_0805_2012Metric" H 6950 1900 50  0001 C CNN
F 3 "~" H 6950 1900 50  0001 C CNN
F 4 "C17629" H 6950 1900 50  0001 C CNN "LCSC Part #"
	1    6950 1900
	1    0    0    -1  
$EndComp
Wire Wire Line
	6950 1650 6950 1800
Connection ~ 6950 1650
Wire Wire Line
	6950 1650 7600 1650
$Comp
L Device:C_Small C8
U 1 1 60457647
P 5900 1900
F 0 "C8" H 5808 1854 50  0000 R CNN
F 1 "4.7u" H 5808 1945 50  0000 R CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 5900 1900 50  0001 C CNN
F 3 "~" H 5900 1900 50  0001 C CNN
F 4 "C1779" H 5900 1900 50  0001 C CNN "LCSC Part #"
	1    5900 1900
	-1   0    0    1   
$EndComp
$Comp
L Device:C_Small C9
U 1 1 60457A93
P 6250 1900
F 0 "C9" H 6158 1854 50  0000 R CNN
F 1 "0.01u" H 6158 1945 50  0000 R CNN
F 2 "Capacitor_SMD:C_0402_1005Metric" H 6250 1900 50  0001 C CNN
F 3 "~" H 6250 1900 50  0001 C CNN
F 4 "C15195" H 6250 1900 50  0001 C CNN "LCSC Part #"
	1    6250 1900
	-1   0    0    1   
$EndComp
$Comp
L Device:C_Small C7
U 1 1 60458559
P 5550 1900
F 0 "C7" H 5458 1854 50  0000 R CNN
F 1 "4.7u" H 5458 1945 50  0000 R CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 5550 1900 50  0001 C CNN
F 3 "~" H 5550 1900 50  0001 C CNN
F 4 "C1779" H 5550 1900 50  0001 C CNN "LCSC Part #"
	1    5550 1900
	-1   0    0    1   
$EndComp
Wire Wire Line
	10400 1000 10400 1100
Wire Wire Line
	10400 1300 10400 1400
Wire Notes Line
	500  3500 11150 3500
Text Notes 5150 900  0    213  ~ 0
+5V SUPPLY
$Comp
L power:GND #PWR05
U 1 1 604131A8
P 10400 2450
F 0 "#PWR05" H 10400 2200 50  0001 C CNN
F 1 "GND" H 10405 2277 50  0000 C CNN
F 2 "" H 10400 2450 50  0001 C CNN
F 3 "" H 10400 2450 50  0001 C CNN
	1    10400 2450
	1    0    0    -1  
$EndComp
$Comp
L Device:R_Small R5
U 1 1 6049F7B2
P 10400 2200
F 0 "R5" H 10459 2246 50  0000 L CNN
F 1 "100R" H 10459 2155 50  0000 L CNN
F 2 "Resistor_SMD:R_1206_3216Metric" H 10400 2200 50  0001 C CNN
F 3 "~" H 10400 2200 50  0001 C CNN
F 4 "C351537" H 10400 2200 50  0001 C CNN "LCSC Part #"
	1    10400 2200
	1    0    0    -1  
$EndComp
Wire Wire Line
	10400 1950 10400 2100
Wire Wire Line
	10400 2300 10400 2450
$Comp
L Device:R_Small R8
U 1 1 60503BA6
P 8950 2600
F 0 "R8" H 9009 2646 50  0000 L CNN
F 1 "2.7K" H 9009 2555 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 8950 2600 50  0001 C CNN
F 3 "~" H 8950 2600 50  0001 C CNN
F 4 "C13167" H 8950 2600 50  0001 C CNN "LCSC Part #"
	1    8950 2600
	1    0    0    -1  
$EndComp
$Comp
L Device:R_Small R10
U 1 1 60503E5E
P 8950 2850
F 0 "R10" H 8891 2804 50  0000 R CNN
F 1 "100R" H 8891 2895 50  0000 R CNN
F 2 "Resistor_SMD:R_1206_3216Metric" H 8950 2850 50  0001 C CNN
F 3 "~" H 8950 2850 50  0001 C CNN
F 4 "C351537" H 8950 2850 50  0001 C CNN "LCSC Part #"
	1    8950 2850
	-1   0    0    1   
$EndComp
Text Notes 8850 3000 1    50   ~ 0
49.9k (TOTAL)
Wire Wire Line
	5550 1650 5550 1800
Connection ~ 5550 1650
Wire Wire Line
	5550 1650 5900 1650
Wire Wire Line
	5900 1650 5900 1800
Connection ~ 5900 1650
Wire Wire Line
	5900 1650 6250 1650
Wire Wire Line
	6250 1650 6250 1800
Connection ~ 6250 1650
Wire Wire Line
	6250 1650 6950 1650
$Comp
L Device:R_Small R11
U 1 1 605359D1
P 8950 3100
F 0 "R11" H 8891 3054 50  0000 R CNN
F 1 "100R" H 8891 3145 50  0000 R CNN
F 2 "Resistor_SMD:R_1206_3216Metric" H 8950 3100 50  0001 C CNN
F 3 "~" H 8950 3100 50  0001 C CNN
F 4 "C351537" H 8950 3100 50  0001 C CNN "LCSC Part #"
	1    8950 3100
	-1   0    0    1   
$EndComp
Wire Wire Line
	8950 2200 8950 2250
Wire Wire Line
	8950 2450 8950 2500
Wire Wire Line
	8950 2700 8950 2750
Wire Wire Line
	8950 2950 8950 3000
Text Notes 10250 2300 1    50   ~ 0
1.9k (TOTAL)
Wire Wire Line
	10050 1650 10400 1650
Wire Wire Line
	8950 3200 8950 3250
Wire Wire Line
	8950 3250 9450 3250
Wire Wire Line
	8650 3400 10050 3400
Wire Wire Line
	8650 1950 8650 3400
Wire Wire Line
	10050 1650 10050 3400
Wire Wire Line
	9450 2200 9450 3250
Wire Wire Line
	9450 3250 9800 3250
Wire Wire Line
	9800 1650 9800 3250
Connection ~ 9450 3250
Wire Wire Line
	7300 1800 7600 1800
$Comp
L Device:D_Zener D3
U 1 1 60563000
P 6500 2800
F 0 "D3" V 6454 2880 50  0000 L CNN
F 1 "4v7" V 6545 2880 50  0000 L CNN
F 2 "Diode_THT:D_A-405_P2.54mm_Vertical_AnodeUp" H 6500 2800 50  0001 C CNN
F 3 "~" H 6500 2800 50  0001 C CNN
	1    6500 2800
	0    1    1    0   
$EndComp
Wire Wire Line
	6250 2000 6250 2150
Wire Wire Line
	5550 2000 5550 2150
$Comp
L power:GND #PWR04
U 1 1 60643C32
P 5900 2250
F 0 "#PWR04" H 5900 2000 50  0001 C CNN
F 1 "GND" H 5905 2077 50  0000 C CNN
F 2 "" H 5900 2250 50  0001 C CNN
F 3 "" H 5900 2250 50  0001 C CNN
	1    5900 2250
	1    0    0    -1  
$EndComp
Wire Wire Line
	5900 2000 5900 2150
Wire Wire Line
	5550 2150 5900 2150
Connection ~ 5900 2150
Wire Wire Line
	5900 2150 5900 2250
Wire Wire Line
	5900 2150 6250 2150
Wire Wire Line
	5850 3250 6250 3250
Wire Wire Line
	6500 2950 6500 3250
Connection ~ 6500 3250
Wire Wire Line
	7300 1800 7300 2500
Wire Wire Line
	6500 2650 6500 2500
Wire Wire Line
	5850 2500 6250 2500
Connection ~ 6500 2500
Wire Wire Line
	6500 2500 6850 2500
Connection ~ 6950 2500
Wire Wire Line
	6950 2500 7175 2500
Wire Wire Line
	6950 2000 6950 2500
Connection ~ 6250 3250
Wire Wire Line
	6250 3250 6500 3250
$Comp
L Device:CP C4
U 1 1 606D1865
P 2950 1700
F 0 "C4" H 3068 1746 50  0000 L CNN
F 1 "2200u" H 3068 1655 50  0000 L CNN
F 2 "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm" H 2988 1550 50  0001 C CNN
F 3 "~" H 2950 1700 50  0001 C CNN
	1    2950 1700
	1    0    0    -1  
$EndComp
$Comp
L Device:CP C5
U 1 1 606DEA9F
P 3450 1700
F 0 "C5" H 3568 1746 50  0000 L CNN
F 1 "220u" H 3568 1655 50  0000 L CNN
F 2 "Capacitor_SMD:C_Elec_6.3x5.4" H 3488 1550 50  0001 C CNN
F 3 "~" H 3450 1700 50  0001 C CNN
F 4 "C3345" H 3450 1700 50  0001 C CNN "LCSC Part #"
	1    3450 1700
	1    0    0    -1  
$EndComp
Wire Wire Line
	3450 1400 3450 1550
Connection ~ 3450 1400
Wire Wire Line
	3450 1850 3450 1950
Wire Wire Line
	2950 1400 2950 1550
Wire Wire Line
	2950 1850 2950 1950
Connection ~ 2950 1950
Text GLabel 4600 1400 2    50   Input ~ 0
VIN
$Comp
L power:PWR_FLAG #FLG03
U 1 1 6070360E
P 3900 2000
F 0 "#FLG03" H 3900 2075 50  0001 C CNN
F 1 "PWR_FLAG" H 3900 2150 50  0000 C CNN
F 2 "" H 3900 2000 50  0001 C CNN
F 3 "~" H 3900 2000 50  0001 C CNN
	1    3900 2000
	-1   0    0    1   
$EndComp
$Comp
L Switch:SW_Push SW1
U 1 1 6075D8BB
P 5150 2800
F 0 "SW1" V 5196 2752 50  0000 R CNN
F 1 "PB_MOM" V 5105 2752 50  0000 R CNN
F 2 "Button_Switch_SMD:SW_SPST_TL3342" H 5150 3000 50  0001 C CNN
F 3 "~" H 5150 3000 50  0001 C CNN
F 4 "C318884" H 5150 2800 50  0001 C CNN "LCSC Part #"
	1    5150 2800
	0    -1   -1   0   
$EndComp
$Comp
L Device:R_Small R7
U 1 1 6075F949
P 5500 2500
F 0 "R7" V 5696 2500 50  0000 C CNN
F 1 "100R" V 5605 2500 50  0000 C CNN
F 2 "Resistor_SMD:R_1206_3216Metric" H 5500 2500 50  0001 C CNN
F 3 "~" H 5500 2500 50  0001 C CNN
F 4 "C351537" H 5500 2500 50  0001 C CNN "LCSC Part #"
	1    5500 2500
	0    -1   -1   0   
$EndComp
Wire Wire Line
	5850 2500 5600 2500
Connection ~ 5850 2500
Wire Wire Line
	5400 2500 5150 2500
Wire Wire Line
	5150 2500 5150 2600
Wire Wire Line
	5150 3000 5150 3250
Wire Wire Line
	5150 3250 5850 3250
Connection ~ 5850 3250
$Comp
L Device:C_Small C13
U 1 1 60774E71
P 5850 2800
F 0 "C13" H 5758 2754 50  0000 R CNN
F 1 "4.7u" H 5758 2845 50  0000 R CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 5850 2800 50  0001 C CNN
F 3 "~" H 5850 2800 50  0001 C CNN
F 4 "C1779" H 5850 2800 50  0001 C CNN "LCSC Part #"
	1    5850 2800
	-1   0    0    1   
$EndComp
Wire Wire Line
	5850 2500 5850 2700
Wire Wire Line
	5850 2900 5850 3250
Wire Notes Line
	4950 3475 4950 525 
$Comp
L Device:C_Small C6
U 1 1 60428BBB
P 3900 1700
F 0 "C6" H 3808 1654 50  0000 R CNN
F 1 "0.1u" H 3808 1745 50  0000 R CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 3900 1700 50  0001 C CNN
F 3 "~" H 3900 1700 50  0001 C CNN
F 4 "C14663" H 3900 1700 50  0001 C CNN "LCSC Part #"
	1    3900 1700
	-1   0    0    1   
$EndComp
Wire Wire Line
	3900 1600 3900 1400
Wire Wire Line
	3450 1400 3900 1400
Connection ~ 3900 1400
Wire Wire Line
	3450 1950 3900 1950
Wire Wire Line
	3900 1950 3900 1800
Connection ~ 3450 1950
Text Notes 2600 1275 2    50   ~ 0
Bourns\nRHT-400
Wire Wire Line
	9350 1650 9550 1650
Connection ~ 9550 1650
Wire Wire Line
	9550 1650 9800 1650
$Comp
L power:PWR_FLAG #FLG02
U 1 1 6048035E
P 3900 1325
F 0 "#FLG02" H 3900 1400 50  0001 C CNN
F 1 "PWR_FLAG" H 3900 1475 50  0000 C CNN
F 2 "" H 3900 1325 50  0001 C CNN
F 3 "~" H 3900 1325 50  0001 C CNN
	1    3900 1325
	1    0    0    -1  
$EndComp
$Comp
L Switch:SW_Push SW2
U 1 1 60480FB8
P 5750 4050
F 0 "SW2" V 5796 4002 50  0000 R CNN
F 1 "PB_MOM" V 5650 4000 50  0000 R CNN
F 2 "Button_Switch_SMD:SW_SPST_TL3342" H 5750 4250 50  0001 C CNN
F 3 "~" H 5750 4250 50  0001 C CNN
F 4 "C318884" H 5750 4050 50  0001 C CNN "LCSC Part #"
	1    5750 4050
	0    -1   -1   0   
$EndComp
$Comp
L power:GND #PWR011
U 1 1 60481938
P 5750 4350
F 0 "#PWR011" H 5750 4100 50  0001 C CNN
F 1 "GND" H 5755 4177 50  0000 C CNN
F 2 "" H 5750 4350 50  0001 C CNN
F 3 "" H 5750 4350 50  0001 C CNN
	1    5750 4350
	1    0    0    -1  
$EndComp
$Comp
L Device:C_Small C19
U 1 1 60481D30
P 6350 4050
F 0 "C19" H 6258 4004 50  0000 R CNN
F 1 "4.7u" H 6258 4095 50  0000 R CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 6350 4050 50  0001 C CNN
F 3 "~" H 6350 4050 50  0001 C CNN
F 4 "C1779" H 6350 4050 50  0001 C CNN "LCSC Part #"
	1    6350 4050
	-1   0    0    1   
$EndComp
Wire Wire Line
	5750 3850 5950 3850
Wire Wire Line
	6150 3850 6350 3850
Wire Wire Line
	6350 3850 6350 3950
Wire Wire Line
	5750 4250 6350 4250
Wire Wire Line
	6350 4250 6350 4150
Connection ~ 5750 4250
Text GLabel 6600 3850 2    50   Input ~ 0
SHUTDOWN
Wire Wire Line
	6350 3850 6600 3850
Connection ~ 6350 3850
$Comp
L Device:R_Small R12
U 1 1 60482295
P 6050 3850
F 0 "R12" V 6246 3850 50  0000 C CNN
F 1 "100R" V 6155 3850 50  0000 C CNN
F 2 "Resistor_SMD:R_1206_3216Metric" H 6050 3850 50  0001 C CNN
F 3 "~" H 6050 3850 50  0001 C CNN
F 4 "C351537" H 6050 3850 50  0001 C CNN "LCSC Part #"
	1    6050 3850
	0    -1   -1   0   
$EndComp
Wire Wire Line
	5750 4250 5750 4350
$Comp
L Device:R_Small R13
U 1 1 604C011E
P 7700 3850
F 0 "R13" V 7896 3850 50  0000 C CNN
F 1 "100R" V 7805 3850 50  0000 C CNN
F 2 "Resistor_SMD:R_1206_3216Metric" H 7700 3850 50  0001 C CNN
F 3 "~" H 7700 3850 50  0001 C CNN
F 4 "C351537" H 7700 3850 50  0001 C CNN "LCSC Part #"
	1    7700 3850
	0    -1   -1   0   
$EndComp
$Comp
L Switch:SW_Push SW3
U 1 1 604C05D5
P 7350 4050
F 0 "SW3" V 7396 4002 50  0000 R CNN
F 1 "PB_MOM" V 7250 4000 50  0000 R CNN
F 2 "Button_Switch_SMD:SW_SPST_TL3342" H 7350 4250 50  0001 C CNN
F 3 "~" H 7350 4250 50  0001 C CNN
F 4 "C318884" H 7350 4050 50  0001 C CNN "LCSC Part #"
	1    7350 4050
	0    -1   -1   0   
$EndComp
$Comp
L power:GND #PWR012
U 1 1 604C0D4B
P 7350 4350
F 0 "#PWR012" H 7350 4100 50  0001 C CNN
F 1 "GND" H 7355 4177 50  0000 C CNN
F 2 "" H 7350 4350 50  0001 C CNN
F 3 "" H 7350 4350 50  0001 C CNN
	1    7350 4350
	1    0    0    -1  
$EndComp
$Comp
L Device:C_Small C20
U 1 1 604C1064
P 8050 4050
F 0 "C20" H 7958 4004 50  0000 R CNN
F 1 "4.7u" H 7958 4095 50  0000 R CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 8050 4050 50  0001 C CNN
F 3 "~" H 8050 4050 50  0001 C CNN
F 4 "C1779" H 8050 4050 50  0001 C CNN "LCSC Part #"
	1    8050 4050
	-1   0    0    1   
$EndComp
Wire Wire Line
	7350 4350 7350 4300
Wire Wire Line
	7350 3850 7600 3850
Wire Wire Line
	7800 3850 8050 3850
Wire Wire Line
	8050 3850 8050 3950
Wire Wire Line
	8050 4150 8050 4300
Wire Wire Line
	8050 4300 7350 4300
Connection ~ 7350 4300
Wire Wire Line
	7350 4300 7350 4250
Text GLabel 8350 3850 2    50   Input ~ 0
PB_1
Wire Wire Line
	8050 3850 8350 3850
Connection ~ 8050 3850
$Comp
L power:PWR_FLAG #FLG01
U 1 1 6091B1B8
P 10400 1000
F 0 "#FLG01" H 10400 1075 50  0001 C CNN
F 1 "PWR_FLAG" H 10400 1173 50  0000 C CNN
F 2 "" H 10400 1000 50  0001 C CNN
F 3 "~" H 10400 1000 50  0001 C CNN
	1    10400 1000
	1    0    0    -1  
$EndComp
$Sheet
S 5800 5600 500  650 
U 6060A527
F0 "PiDaugherBoardInputsAndComms" 50
F1 "PiDaugherBoardInputsAndComms.sch" 50
$EndSheet
$Sheet
S 7750 5550 500  650 
U 6092DD0A
F0 "PiDaughterBoardOutputsAndLEDs" 50
F1 "PiDaughterBoardOutputsAndLEDs.sch" 50
$EndSheet
Text GLabel 2000 6350 0    50   Input ~ 0
SHIFT_Conn
Text GLabel 2000 6150 0    50   Input ~ 0
RS485_RXE
Text GLabel 2000 5350 0    50   Input ~ 0
SHIFT_IN_Data
Text GLabel 2000 6550 0    50   Input ~ 0
SHIFT_Latch
Text GLabel 1975 6050 0    50   Input ~ 0
SHIFT_Clock
$Comp
L PiDaughterBoard-rescue:STWD100-Power_Management U2
U 1 1 60E58E10
P 4850 7150
F 0 "U2" H 4625 7665 50  0000 C CNN
F 1 "STWD100" H 4625 7574 50  0000 C CNN
F 2 "Package_TO_SOT_SMD:SOT-23-5" H 4850 7150 50  0001 C CNN
F 3 "" H 4850 7150 50  0001 C CNN
F 4 "C46043" H 4850 7150 50  0001 C CNN "LCSC Part #"
	1    4850 7150
	1    0    0    -1  
$EndComp
Text GLabel 3725 7225 0    50   Input ~ 0
WD_E
Text GLabel 4250 6900 0    50   Input ~ 0
WATCHDOG
$Comp
L power:GND #PWR018
U 1 1 60E6F91A
P 4600 7550
F 0 "#PWR018" H 4600 7300 50  0001 C CNN
F 1 "GND" H 4605 7377 50  0000 C CNN
F 2 "" H 4600 7550 50  0001 C CNN
F 3 "" H 4600 7550 50  0001 C CNN
	1    4600 7550
	1    0    0    -1  
$EndComp
Wire Wire Line
	4250 6900 4300 6900
Wire Wire Line
	4250 7100 4300 7100
$Comp
L power:+3V3 #PWR014
U 1 1 60E91A04
P 5050 6050
F 0 "#PWR014" H 5050 5900 50  0001 C CNN
F 1 "+3V3" H 5065 6223 50  0000 C CNN
F 2 "" H 5050 6050 50  0001 C CNN
F 3 "" H 5050 6050 50  0001 C CNN
	1    5050 6050
	1    0    0    -1  
$EndComp
Wire Wire Line
	4950 6900 5050 6900
Text GLabel 6750 6950 1    50   Input ~ 0
PWR_EN
Wire Notes Line
	5350 6500 6900 6500
Wire Notes Line
	5350 6500 5350 3500
$Comp
L Device:C_Small C21
U 1 1 60EC1663
P 4925 6250
F 0 "C21" H 5125 6250 50  0000 R CNN
F 1 "0.1u" H 5125 6150 50  0000 R CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 4925 6250 50  0001 C CNN
F 3 "~" H 4925 6250 50  0001 C CNN
F 4 "C14663" H 4925 6250 50  0001 C CNN "LCSC Part #"
	1    4925 6250
	-1   0    0    1   
$EndComp
Text GLabel 6250 2700 3    50   Input ~ 0
PWR_EN
Wire Wire Line
	6250 2700 6250 2500
Connection ~ 6250 2500
Wire Wire Line
	6250 2500 6500 2500
Wire Wire Line
	4600 7350 4600 7550
$Comp
L Device:R_Small R14
U 1 1 60EF356A
P 5250 6950
F 0 "R14" H 5309 6996 50  0000 L CNN
F 1 "10K" H 5309 6905 50  0000 L CNN
F 2 "Resistor_SMD:R_0805_2012Metric" H 5250 6950 50  0001 C CNN
F 3 "~" H 5250 6950 50  0001 C CNN
F 4 "C17414" H 5250 6950 50  0001 C CNN "LCSC Part #"
	1    5250 6950
	1    0    0    -1  
$EndComp
Wire Wire Line
	5250 7100 5250 7050
Wire Wire Line
	4950 7100 5250 7100
$Comp
L Device:D_Small D4
U 1 1 60F0CD0C
P 5600 7100
F 0 "D4" H 5600 7000 50  0000 C CNN
F 1 "IN4004" H 5700 6900 50  0000 C CNN
F 2 "Diode_SMD:D_SOD-123" V 5600 7100 50  0001 C CNN
F 3 "~" V 5600 7100 50  0001 C CNN
F 4 "C162732" H 5600 7100 50  0001 C CNN "LCSC Part #"
	1    5600 7100
	1    0    0    -1  
$EndComp
Wire Wire Line
	5250 7100 5500 7100
Connection ~ 5250 7100
$Comp
L Jumper:Jumper_2_Open JP1
U 1 1 60F273BE
P 6000 7100
F 0 "JP1" H 6000 7335 50  0000 C CNN
F 1 "Jumper_2_Open" H 6000 7244 50  0000 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_1x02_P2.54mm_Vertical" H 6000 7100 50  0001 C CNN
F 3 "~" H 6000 7100 50  0001 C CNN
	1    6000 7100
	1    0    0    -1  
$EndComp
Wire Wire Line
	5800 7100 5700 7100
Wire Wire Line
	5050 6050 5050 6150
Wire Wire Line
	4925 6150 5050 6150
Connection ~ 5050 6150
$Comp
L power:GND #PWR015
U 1 1 60F9B190
P 4925 6450
F 0 "#PWR015" H 4925 6200 50  0001 C CNN
F 1 "GND" H 4930 6277 50  0000 C CNN
F 2 "" H 4925 6450 50  0001 C CNN
F 3 "" H 4925 6450 50  0001 C CNN
	1    4925 6450
	1    0    0    -1  
$EndComp
Wire Wire Line
	4925 6350 4925 6450
$Comp
L Device:R_Small R15
U 1 1 60FA92D5
P 6500 7100
F 0 "R15" V 6600 7050 50  0000 L CNN
F 1 "100R" V 6700 7050 50  0000 L CNN
F 2 "Resistor_SMD:R_1206_3216Metric" H 6500 7100 50  0001 C CNN
F 3 "~" H 6500 7100 50  0001 C CNN
F 4 "C351537" H 6500 7100 50  0001 C CNN "LCSC Part #"
	1    6500 7100
	0    1    1    0   
$EndComp
Wire Wire Line
	6600 7100 6750 7100
Wire Wire Line
	6750 7100 6750 6950
Wire Wire Line
	6200 7100 6400 7100
Wire Wire Line
	5050 6150 5050 6900
$Comp
L power:+5V #PWR016
U 1 1 60FC4DF6
P 5250 6700
F 0 "#PWR016" H 5250 6550 50  0001 C CNN
F 1 "+5V" H 5350 6750 50  0000 C CNN
F 2 "" H 5250 6700 50  0001 C CNN
F 3 "" H 5250 6700 50  0001 C CNN
	1    5250 6700
	1    0    0    -1  
$EndComp
Wire Wire Line
	5250 6700 5250 6850
$Comp
L power:PWR_FLAG #FLG04
U 1 1 61159746
P 3350 3950
F 0 "#FLG04" H 3350 4025 50  0001 C CNN
F 1 "PWR_FLAG" H 3500 4100 50  0000 C CNN
F 2 "" H 3350 3950 50  0001 C CNN
F 3 "~" H 3350 3950 50  0001 C CNN
	1    3350 3950
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole_Pad H1
U 1 1 6120AC09
P 9600 3950
F 0 "H1" H 9700 3999 50  0000 L CNN
F 1 "RPI" H 9550 4150 50  0000 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3_Pad_Via" H 9600 3950 50  0001 C CNN
F 3 "~" H 9600 3950 50  0001 C CNN
	1    9600 3950
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole_Pad H2
U 1 1 6120B13A
P 10000 3950
F 0 "H2" H 10100 3999 50  0000 L CNN
F 1 "RPI" H 9950 4150 50  0000 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3_Pad_Via" H 10000 3950 50  0001 C CNN
F 3 "~" H 10000 3950 50  0001 C CNN
	1    10000 3950
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole_Pad H3
U 1 1 6120B2EB
P 10400 3950
F 0 "H3" H 10500 3999 50  0000 L CNN
F 1 "RPI" H 10350 4150 50  0000 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3_Pad_Via" H 10400 3950 50  0001 C CNN
F 3 "~" H 10400 3950 50  0001 C CNN
	1    10400 3950
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole_Pad H4
U 1 1 6120B48C
P 10750 3950
F 0 "H4" H 10850 3999 50  0000 L CNN
F 1 "RPI" H 10700 4150 50  0000 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3_Pad_Via" H 10750 3950 50  0001 C CNN
F 3 "~" H 10750 3950 50  0001 C CNN
	1    10750 3950
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole_Pad H5
U 1 1 6120B5E6
P 9600 4500
F 0 "H5" H 9500 4550 50  0000 R CNN
F 1 "BOARD" H 9700 4700 50  0000 R CNN
F 2 "MountingHole:MountingHole_3.2mm_M3_Pad_Via" H 9600 4500 50  0001 C CNN
F 3 "~" H 9600 4500 50  0001 C CNN
	1    9600 4500
	-1   0    0    1   
$EndComp
$Comp
L Mechanical:MountingHole_Pad H6
U 1 1 6120BDA2
P 10000 4500
F 0 "H6" H 9900 4550 50  0000 R CNN
F 1 "BOARD" H 10100 4700 50  0000 R CNN
F 2 "MountingHole:MountingHole_3.2mm_M3_Pad_Via" H 10000 4500 50  0001 C CNN
F 3 "~" H 10000 4500 50  0001 C CNN
	1    10000 4500
	-1   0    0    1   
$EndComp
$Comp
L Mechanical:MountingHole_Pad H7
U 1 1 6120C580
P 10400 4500
F 0 "H7" H 10300 4550 50  0000 R CNN
F 1 "BOARD" H 10500 4700 50  0000 R CNN
F 2 "MountingHole:MountingHole_3.2mm_M3_Pad_Via" H 10400 4500 50  0001 C CNN
F 3 "~" H 10400 4500 50  0001 C CNN
	1    10400 4500
	-1   0    0    1   
$EndComp
$Comp
L Mechanical:MountingHole_Pad H8
U 1 1 6120C848
P 10750 4500
F 0 "H8" H 10650 4550 50  0000 R CNN
F 1 "BOARD" H 10850 4700 50  0000 R CNN
F 2 "MountingHole:MountingHole_3.2mm_M3_Pad_Via" H 10750 4500 50  0001 C CNN
F 3 "~" H 10750 4500 50  0001 C CNN
	1    10750 4500
	-1   0    0    1   
$EndComp
Wire Wire Line
	10400 4050 10400 4200
Wire Wire Line
	10000 4050 10000 4200
Wire Wire Line
	9600 4050 9600 4200
$Comp
L power:GND #PWR013
U 1 1 6124097A
P 9200 4400
F 0 "#PWR013" H 9200 4150 50  0001 C CNN
F 1 "GND" H 9205 4227 50  0000 C CNN
F 2 "" H 9200 4400 50  0001 C CNN
F 3 "" H 9200 4400 50  0001 C CNN
	1    9200 4400
	1    0    0    -1  
$EndComp
Wire Wire Line
	10750 4050 10750 4200
Wire Wire Line
	10750 4200 10400 4200
Connection ~ 10750 4200
Wire Wire Line
	10750 4200 10750 4400
Connection ~ 10400 4200
Wire Wire Line
	10400 4200 10400 4400
Wire Wire Line
	10400 4200 10000 4200
Connection ~ 10000 4200
Wire Wire Line
	10000 4200 10000 4400
Wire Wire Line
	10000 4200 9600 4200
Connection ~ 9600 4200
Wire Wire Line
	9600 4200 9200 4200
Wire Wire Line
	9200 4200 9200 4400
Wire Notes Line
	5300 5200 11100 5200
Wire Notes Line
	8750 3500 8750 5200
Text Notes 5650 4950 0    213  ~ 0
PUSH BUTTONS
Text Notes 8750 5100 0    213  ~ 0
HOLES
Text Notes 650  950  0    213  ~ 0
POWER IN
$Comp
L Connector:Screw_Terminal_01x02 J?
U 1 1 6182695A
P 1325 1700
AR Path="/6092DD0A/6182695A" Ref="J?"  Part="1" 
AR Path="/6182695A" Ref="J2"  Part="1" 
F 0 "J2" H 1275 1500 50  0000 L CNN
F 1 "ST01x02" H 1125 1800 50  0000 L CNN
F 2 "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal" H 1325 1700 50  0001 C CNN
F 3 "~" H 1325 1700 50  0001 C CNN
	1    1325 1700
	-1   0    0    1   
$EndComp
Text Notes 5500 3000 2    50   ~ 0
DIS_PWR
Text Notes 6350 4350 2    50   ~ 0
PB_SHUTDOWN
Text Notes 7850 4400 2    50   ~ 0
PB_1
Text GLabel 3900 5550 2    50   Input ~ 0
SHIFT_Data
Connection ~ 2950 1400
$Comp
L power:GND #PWR03
U 1 1 6049CF99
P 2650 1950
F 0 "#PWR03" H 2650 1700 50  0001 C CNN
F 1 "GND" H 2655 1777 50  0000 C CNN
F 2 "" H 2650 1950 50  0001 C CNN
F 3 "" H 2650 1950 50  0001 C CNN
	1    2650 1950
	1    0    0    -1  
$EndComp
Wire Wire Line
	2650 1950 2950 1950
Wire Wire Line
	2550 1400 2650 1400
Wire Wire Line
	2950 1950 3450 1950
Wire Wire Line
	2950 1400 3450 1400
Wire Wire Line
	3900 1325 3900 1400
Wire Wire Line
	3900 1950 3900 2000
Connection ~ 3900 1950
Wire Wire Line
	3900 1400 4600 1400
Wire Wire Line
	5450 1650 5550 1650
Text GLabel 5450 1650 0    50   Input ~ 0
VIN
Text Notes 925  1800 0    50   ~ 0
PWR IN\n24VAC /\n24VDC
Text Notes 9950 5175 0    50   ~ 0
BOARD HOLE OFFSETS (mm): \nTL: (0, 0)\nTR: (155, 0)\nBL: (10, 100)\nBR: (155, 100)
Wire Wire Line
	6500 3250 6850 3250
Wire Wire Line
	6850 2500 6850 2700
Connection ~ 6850 2500
Wire Wire Line
	6850 2500 6950 2500
Wire Wire Line
	6850 2900 6850 3250
Connection ~ 6850 3250
$Comp
L Device:C_Small C14
U 1 1 60730B57
P 7175 2800
F 0 "C14" H 7083 2754 50  0000 R CNN
F 1 "0.1u" H 7083 2845 50  0000 R CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 7175 2800 50  0001 C CNN
F 3 "~" H 7175 2800 50  0001 C CNN
F 4 "C15195" H 7175 2800 50  0001 C CNN "LCSC Part #"
	1    7175 2800
	-1   0    0    1   
$EndComp
Wire Wire Line
	7600 1950 7550 1950
Wire Wire Line
	7550 1950 7550 2675
Wire Wire Line
	7550 3250 7550 2875
Wire Wire Line
	6850 3250 7175 3250
Wire Wire Line
	7175 2700 7175 2500
Connection ~ 7175 2500
Wire Wire Line
	7175 2500 7300 2500
Wire Wire Line
	7175 2900 7175 3250
Connection ~ 7175 3250
Wire Wire Line
	7175 3250 7550 3250
Wire Wire Line
	2000 5350 2150 5350
Wire Wire Line
	1975 6050 2150 6050
Wire Wire Line
	2000 6350 2150 6350
Wire Wire Line
	2000 6550 2150 6550
Wire Wire Line
	3750 5550 3900 5550
Wire Wire Line
	9600 4200 9600 4400
Text Notes 5225 1300 0    50   ~ 0
Vout = Vref x [R2 / (R3+R5) + 1]\n     = 0.8 x [10K / (1.8K + 0.1K) + 1]\n     = 5.01v
Text Notes 825  2475 0    50   ~ 0
VINrms = [(VPWRrms / 0.707) - (D2vdrop + D3vdrop)] / PI * 1.414\n        = [(24VAC / 0.707) - (0.7 + 0.7)] / 3.14 * 1.414\n        = 14.65v
$Comp
L Device:Fuse_Small F1
U 1 1 604689AC
P 2450 1400
F 0 "F1" H 2400 1325 50  0000 L CNN
F 1 "5A" H 2400 1475 50  0000 L CNN
F 2 "Fuse:Fuse_Bourns_MF-RHT400" H 2450 1400 50  0001 C CNN
F 3 "~" H 2450 1400 50  0001 C CNN
	1    2450 1400
	-1   0    0    1   
$EndComp
Wire Wire Line
	2275 1400 2350 1400
Connection ~ 2650 1950
Wire Wire Line
	1675 1950 2650 1950
$Comp
L Device:D_Bridge_+A-A D2
U 1 1 605159D3
P 1975 1400
F 0 "D2" H 1725 1625 50  0000 L CNN
F 1 "WO4" H 1675 1550 50  0000 L CNN
F 2 "Diode_THT:Diode_Bridge_Round_D9.0mm" H 1975 1400 50  0001 C CNN
F 3 "~" H 1975 1400 50  0001 C CNN
	1    1975 1400
	1    0    0    -1  
$EndComp
$Comp
L Device:L_Small L2
U 1 1 6051C37B
P 2750 1400
F 0 "L2" V 2935 1400 50  0000 C CNN
F 1 "6.8u" V 2844 1400 50  0000 C CNN
F 2 "Inductor_SMD:L_Wuerth_HCI-1365" H 2750 1400 50  0001 C CNN
F 3 "~" H 2750 1400 50  0001 C CNN
F 4 "C149573" H 2750 1400 50  0001 C CNN "LCSC Part #"
	1    2750 1400
	0    -1   -1   0   
$EndComp
Wire Wire Line
	2850 1400 2950 1400
Wire Wire Line
	1975 1100 1525 1100
Wire Wire Line
	1675 1400 1675 1950
Wire Wire Line
	1525 1100 1525 1600
Wire Wire Line
	1525 1700 1975 1700
Wire Wire Line
	3725 7225 4250 7225
Wire Wire Line
	4250 7225 4250 7100
Text Notes 3200 7625 0    50   ~ 0
Sec 6.2 (Alternate Functions) of \nBCM2835 shows GPIO5 defaults\nto pull up, effectively disabling \nthe WD IC\n
$Comp
L Connector:Screw_Terminal_01x02 J1
U 1 1 6047717F
P 10975 1100
F 0 "J1" H 10925 1225 50  0000 L CNN
F 1 "ST_01x02" H 10800 900 50  0000 L CNN
F 2 "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal" H 10975 1100 50  0001 C CNN
F 3 "~" H 10975 1100 50  0001 C CNN
	1    10975 1100
	1    0    0    -1  
$EndComp
Wire Wire Line
	10700 1000 10775 1000
Wire Wire Line
	10775 1000 10775 1100
Connection ~ 10700 1000
Wire Wire Line
	10775 1100 10775 1200
Connection ~ 10775 1100
$EndSCHEMATC
