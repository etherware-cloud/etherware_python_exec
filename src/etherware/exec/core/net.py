import socket
import fcntl
import struct


def get_ip_address(if_name):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(
        fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack("256s", if_name[:15].encode("ascii")),
        )[20:24]
    )
