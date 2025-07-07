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
    
    def send_command(self, function_id: int, value: int) -> bool:
        """
        Send a command to Run8 via UDP
        
        Args:
            function_id: Run8 function ID
            value: Value to send (0-255 or 0-65535 for special functions)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.sock:
            logger.warning("UDP socket not connected")
            return False
        
        try:
            # Ensure value is within valid range
            value = max(0, min(65535, value))
            
            # Create 6-byte packet: 4 bytes for function ID, 2 bytes for value
            packet = struct.pack("<IH", function_id, value)
            
            self.sock.sendto(packet, (self.ip, self.port))
            logger.debug(f"Sent Run8 command: function={function_id}, value={value}, data={packet.hex()}")
            return True
        except Exception as e:
            logger.error(f"Error sending UDP command: {e}")
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
