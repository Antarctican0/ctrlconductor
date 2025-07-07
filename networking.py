"""
UDP networking module for Run8 Control Conductor

Handles UDP socket communication with the Run8 train simulator.
"""

import socket
import struct
import time
from typing import Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UDPClient:
    """Handles UDP communication with Run8 simulator"""
    
    def __init__(self, ip: str = '127.0.0.1', port: int = 18888):
        """
        Initialize UDP client
        
        Args:
            ip: Target IP address
            port: Target port number
        """
        self.ip = ip
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.connected = False
        
    def connect(self) -> bool:
        """
        Establish UDP connection
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(1.0)
            self.connected = True
            logger.info(f"UDP client connected to {self.ip}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect UDP client: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Close UDP connection"""
        if self.sock:
            try:
                self.sock.close()
                logger.info("UDP client disconnected")
            except Exception as e:
                logger.error(f"Error closing UDP socket: {e}")
            finally:
                self.sock = None
                self.connected = False
    
    def _calculate_crc(self, data: bytes) -> int:
        """Calculate the CRC using XOR as per Run8 protocol spec."""
        crc = 0
        for byte in data:
            crc ^= byte
        return crc

    def send_command(self, function_id: int, value: int, audio: bool = True) -> bool:
        """
        Send a command to Run8 via UDP using the correct 5-byte format.
        
        Args:
            function_id: Run8 message type (ushort)
            value: Value to send (0-255)
            audio: Whether to include the audio flag in the header.
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.sock:
            logger.warning("UDP socket not connected")
            return False
        
        try:
            # Set header based on audio flag
            header = 224 if audio else 96
            
            # Ensure value is a single byte (0-255)
            value = max(0, min(255, int(value)))
            
            # Pack the first 4 bytes (Header, Message Type as ushort, Value)
            # Format: > (big-endian), B (uchar), H (ushort), B (uchar)
            message_type = function_id
            packet_part1 = struct.pack(">BHB", header, message_type, value)
            
            # Calculate CRC on the first 4 bytes
            crc = self._calculate_crc(packet_part1)
            
            # Create the final 5-byte packet
            final_packet = packet_part1 + struct.pack(">B", crc)
            
            # Log the packet for debugging if needed
            # logger.debug(f"Sending packet: {final_packet.hex().upper()}")

            self.sock.sendto(final_packet, (self.ip, self.port))
            return True
            
        except Exception as e:
            logger.error(f"Failed to send UDP command: {e}")
            return False
    
    def update_connection(self, ip: str, port: int) -> bool:
        """
        Update connection parameters
        
        Args:
            ip: New IP address
            port: New port number
            
        Returns:
            True if reconnection successful, False otherwise
        """
        was_connected = self.connected
        
        if was_connected:
            self.disconnect()
        
        self.ip = ip
        self.port = port
        
        if was_connected:
            return self.connect()
        
        return True
    
    def is_connected(self) -> bool:
        """Check if UDP client is connected"""
        return self.connected and self.sock is not None
    
    def get_connection_info(self) -> Tuple[str, int]:
        """Get current connection parameters"""
        return self.ip, self.port


class UDPServer:
    """Handles UDP server for Run8 simulator"""
    
    def __init__(self, ip: str = '127.0.0.1', port: int = 18888):
        """
        Initialize UDP server
        
        Args:
            ip: Listening IP address
            port: Listening port number
        """
        self.ip = ip
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.running = False
        
    def start(self) -> bool:
        """
        Start the UDP server
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.ip, self.port))
            self.sock.settimeout(1.0)
            self.running = True
            logger.info(f"UDP server started on {self.ip}:{self.port}")
            
            while self.running:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    logger.info(f"Received data from {addr}: {data.hex()}")
                    
                    # Echo the data back to the sender
                    self.sock.sendto(data, addr)
                except socket.timeout:
                    continue
            
            return True
        except Exception as e:
            logger.error(f"Failed to start UDP server: {e}")
            self.running = False
            return False
    
    def stop(self) -> None:
        """Stop the UDP server"""
        if self.sock:
            try:
                self.running = False
                self.sock.close()
                logger.info("UDP server stopped")
            except Exception as e:
                logger.error(f"Error closing UDP socket: {e}")
            finally:
                self.sock = None
    
    def is_running(self) -> bool:
        """Check if UDP server is running"""
        return self.running and self.sock is not None
    
    def get_server_info(self) -> Tuple[str, int]:
        """Get current server parameters"""
        return self.ip, self.port
