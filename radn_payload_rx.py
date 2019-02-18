#!/usr/bin/env python
#   Edited version of sec_payload_rx_example.py by Mark Jessop, 2018 
#   This version is for SHSSP radiation sensing payload, Bill, 2019
#   Run this script while the wenet rx is running, radn data saved to file


import json
import socket
import struct
import datetime
import traceback
from WenetPackets import *

import time 

current_altitude =0; 

RADFILE = 'radval.txt';

def store_radn_values(rad_str):
    """ Take text from radn sensor and append to file radval.txt
    """
    ctime = int(round(time.time()))
    global  current_altitude
    
    f=open(RADFILE, 'a')
    # Store string from payload + timestamp + altitude
    st2 =  rad_str[:-1]+'; '+str(ctime)+','+str(current_altitude)+'\n'
    print(st2)
    f.write(st2)
    f.close()

    

def process_sec_text_message(payload):
    """ Convert a text message payload into a string for display.

    Keyword Arguments:
    payload (str): The packet payload as a string, or a list.
    """
    # Convert the payload into a string if it isn't already.
    payload = str(bytearray(payload))

    # Attempt to decode the text message from the payload.
    try:
        _len = struct.unpack("B",payload[1])[0]
        _count = struct.unpack(">H",payload[2:4])[0]
        _text = payload[4:4+_len]
        store_radn_values(_text)
        
    except:
        traceback.print_exc()
        return "Error: Could not decode text message."

    # Return the message as a string.
    return "Text Message %s: %s" % (_count, _text)


def process_sec_floats(payload):
    """ Convert a list-of-floats payload into a string for display

    Keyword Arguments:
    payload (str): The packet payload as a string, or a list.
    """
    # Convert the payload into a string if it isn't already.
    payload = str(bytearray(payload))

    output = []

    try:
        # Second byte in the packet is the number of floats present.
        _len = struct.unpack("B", payload[1])[0]

        for _i in range(_len):
            _float = struct.unpack(">f", payload[2+_i*4: 6+_i*4])[0]
            output.append(_float)
    except:
        traceback.print_exc()
        return []

    return output




def process_sec_payload(id, payload):
    """ Process data from a secondary payload and print it as a string. 

    Keyword Arguments:
    id (int): The secondary payload id.
    payload (str): The packet's payload.
    """

    # First byte of the payload is a packet type.
    _packet_type = list(bytearray(payload))[0]

    if id==3:
      if _packet_type == 0x00:
        # We have a text message packet.
        # Pass this onto process_sec_text_message() to extract the message.

        _payload_str = process_sec_text_message(payload)


      elif _packet_type == 0x10:
        # This is a list of floating point numbers.
        _floats = process_sec_floats(payload)
        _payload_str = "Floats:" + str(_floats)


    #print("Sub-Payload #%d - %s" % (id, _payload_str))




def process_udp(udp_packet):
    """ Process received UDP packets. """

    # Parse JSON
    packet_dict = json.loads(udp_packet)

    # There may be other UDP traffic on this port, so we filter for just 'WENET'
    # telemetry packets.
    if packet_dict['type'] == 'WENET':
        # Extract the actual packet contents from the JSON blob.
        packet = packet_dict['packet']

        # Check for a 'secondary payload' packet
        if decode_packet_type(packet) == WENET_PACKET_TYPES.SEC_PAYLOAD_TELEMETRY:
            # If we have one, extract the secondary payload ID, and the packet contents.
            sec_payload = sec_payload_decode(packet)
            # Send it off to be processed.
            process_sec_payload(id=sec_payload['id'], payload=sec_payload['payload'])
        
        elif decode_packet_type(packet) == WENET_PACKET_TYPES.GPS_TELEMETRY:
            gps_data = gps_telemetry_decoder(packet)

            #print(gps_data)
            global current_altitude
            current_altitude =int(gps_data['altitude'])



def udp_rx_thread():
    """ Listen on a port for UDP broadcast packets, and pass them onto process_udp()"""
    global udp_listener_running
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.settimeout(1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except:
        pass

    s.bind(('',WENET_TELEMETRY_UDP_PORT))
    print("Started UDP Listener")
    while True:
        try:
            m = s.recvfrom(2048)
        except socket.timeout:
            m = None
        
        if m != None:
            try:
                process_udp(m[0])
            except:
                traceback.print_exc()
                pass
    
    print("Closing UDP Listener")
    s.close()


if __name__ == "__main__":
    f=open(RADFILE, 'a')
    f.write('Restart radn collection at '+str(time.gmtime())+'\n' )
    f.close()
    print("Write radn values to file "+RADFILE)
    
    try:
        # Start listening for UDP packets
        udp_rx_thread()

    # Keep on going until we get Ctrl-C'd
    except KeyboardInterrupt:
        # Stop the UDP listener.
        udp_listener_running = False
