#!/usr/bin/env python
# Radiation sensor data collection and transmission thr WENET HAB downlink.   
# Code is based on wenet/tx/examples/sec_payload_tx_example.py plus standard RPI 
# interrupt handlers triggered by digital transitions on GPIO pins 
# 
# Function: read counts from the two radiation sensors on the PI0
#           and send via UDP packet in WENET text packet format 
#           In addition, regularly store the edge counts locally in the PI0 

# Bill Cowley 11/2018 for SHSSP19 
#

import RPi.GPIO as GPIO
import time, socket, struct, json

GPIO.setmode(GPIO.BCM)

# following will control rate of TM data production:   one packet each ...  seconds 
INT_TIME = 10 

# setup port number 
R_PORT = 55674

GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)   #  RD2014 sensor 
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)   #  GM tube sensor 
# GPIO 17 is pin 11;    GPIO 27 is pin 13
# GPIO may be tested via gpio utility 

count = 0
count2 = 0

def my_callback(channel):
    now = time.ctime()
    print str(now) + " GM edge"
    global   count 
    count = count + 1 

def my_callback2(channel):
    now = time.ctime()
    print str(now) + " SS edge"
    global   count2
    count2 = count2 + 1


GPIO.add_event_detect(17, GPIO.RISING, callback=my_callback, bouncetime=1)
GPIO.add_event_detect(27, GPIO.RISING, callback=my_callback2, bouncetime=1) 
stime = time.time()    # time in seconds since epoch 

print "Test the GM and RD2014: print edge trigger times and progressive count totals"
print "Integration time is "+str(INT_TIME)+ ' secs'

def emit_secondary_packet(id=0, packet="", repeats = 1, hostname='<broadcast>', port=R_PORT):
    """ Send a Secondary Payload data packet into the network, to (hopefully) be
        transmitted by a Wenet transmitter.
        Keyword Arguments:
        id (int): Payload ID number, 0 - 255
        packet (): Packet data, packed as a byte array. Maximum of 254 bytes in size.
        repeats (int): Number of times to re-transmit this packet. Defaults to 1.
        hostname (str): Hostname of the Wenet transmitter. Defaults to using UDP broadcast.
        port (int): UDP port of the Wenet transmitter. Defaults to 55674.
    """

    telemetry_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    # Set up the telemetry socket so it can be re-used.
    telemetry_socket.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
    telemetry_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    """ # We need the following if running on OSX.
    try:
        telemetry_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except:
        pass
    """

    # Place data into dictionary.
    data = {'type': 'WENET_TX_SEC_PAYLOAD', 'id': int(id), 'repeats': int(repeats), 'packet': list(bytearray(packet))}

    # Send to target hostname. If this fails just send to localhost.
    try:
        telemetry_socket.sendto(json.dumps(data), (hostname, port))
    except socket.error:
        telemetry_socket.sendto(json.dumps(data), ('127.0.0.1', port))

    telemetry_socket.close()

# Global text message counter.
text_message_counter = 0

def create_text_message(message):
    """ Create a text message packet, for transmission within a 'secondary payload' message.
    This is in the same format as a standard wenet text message, however the maximum message
    length is shortened by 2 bytes to 250 bytes, due to the extra header overhead.
    Keyword Arguments:
    message(str): A text message as a string, up to 250 characters in length.
    """

    global text_message_counter

    text_message_counter = (text_message_counter+1)%65536
    # Clip message if required.
    if len(message) > 250:
        message = message[:250]

    # We will use the Wenet standard text message format, which has a packet type of 0x00,
    # and consists of a length field, a message count, and then the message itself.
    _PACKET_TYPE = 0x00
    _PACKET_LEN = len(message)
    _PACKET_COUNTER = text_message_counter

    # Assemble the packet.
    _packet = struct.pack(">BBH", _PACKET_TYPE, _PACKET_LEN, _PACKET_COUNTER) + message

    return _packet

if __name__ == "__main__":

    # Define ourselves to be 'sub-payload' number 3.
    PAYLOAD_ID = 3

    try:
        while True:

            time.sleep(INT_TIME)
            # Create and transmit a text message packet
            now = time.ctime()
            ress = "At "+str(now)+" rad counts are "+str(count)+" "+str(count2)+"\n"

            _txt_packet = create_text_message(ress)
            emit_secondary_packet(id=PAYLOAD_ID, packet=_txt_packet)  #, hostname = 'hereford2.local')
            
            print("Sent ")
            print(ress)

            # simple storage in local memory
            f = open('rad.txt', 'a')
            f.write(ress)
            f.close() 


    # Keep going unless we get a Ctrl + C event
    except KeyboardInterrupt:
        print("Closing")


    GPIO.cleanup()
