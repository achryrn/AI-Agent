# tools/esp32_rc_car_tool.py

import json
import aiohttp
import asyncio
from typing import Dict, Any
from .base_tool import Tool


class ESP32RCCarTool(Tool):
    """
    Tool for controlling an ESP32-based RC car through WiFi interface.
    
    This tool communicates with an ESP32 slave controller that manages an RC car
    with the following capabilities:
    - Forward/Backward movement with variable speed (PWM 0-255)
    - Left/Right steering with variable intensity
    - 4-speed gear system (1-4)
    - Handbrake functionality
    - Emergency stop (stops all movement)
    - Motion-only stop (stops forward/backward, continues steering)
    - Steering-only stop (stops left/right, continues motion)
    
    The ESP32 must be connected to WiFi and running the slave controller firmware.
    """
    
    name = "esp32_rc_car"
    description = """Control an ESP32-based RC car through WiFi. Send movement commands (forward, backward, left, right), adjust speed/power, change gears, apply handbrake, or stop the vehicle. The car supports variable speed control (0-255 PWM), 4-speed gears, and selective stopping (motion-only or steering-only). Perfect for remote vehicle control, robotics projects, or automated driving scenarios."""

    def __init__(self, timeout: int = 5):
        """
        Initialize the ESP32 RC Car controller.
        
        Args:
            timeout: HTTP request timeout in seconds (default: 5)
        """
        self.timeout = timeout
        
    async def run(self, input: dict) -> str:
        """
        Execute RC car control command.
        
        Args:
            input: Dictionary containing:
                - esp32_ip: IP address of ESP32 controller (required, e.g., "192.168.100.66")
                - action: Command type ("move", "stop", "gear", "handbrake", "status")
                - direction: Movement direction ("forward", "backward", "left", "right") [for move action]
                - speed: PWM value 0-255 (default: 128) [for move action]
                - gear: Gear number 1-4 [for gear action]
                - stop_type: Type of stop ("all", "motion", "steering") [for stop action]
        
        Returns:
            JSON string with command result and car status
        """
        try:
            # Extract ESP32 IP from input - now required for each call
            esp32_ip = input.get("esp32_ip")
            if not esp32_ip:
                return json.dumps({
                    "success": False,
                    "error": "esp32_ip is required. Provide the IP address of your ESP32 controller (e.g., '192.168.100.66')"
                })
            
            base_url = f"http://{esp32_ip}"
            action = input.get("action", "").lower()
            
            if action == "status":
                return await self._get_status(base_url)
            elif action == "move":
                return await self._send_movement_command(input, base_url)
            elif action == "stop":
                return await self._send_stop_command(input, base_url)
            elif action == "gear":
                return await self._send_gear_command(input, base_url)
            elif action == "handbrake":
                return await self._send_handbrake_command(input, base_url)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "valid_actions": ["move", "stop", "gear", "handbrake", "status"]
                })
                
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            })
    
    async def _send_movement_command(self, input: dict, base_url: str) -> str:
        """Send movement command to RC car."""
        direction = input.get("direction", "").lower()
        speed = input.get("speed", 128)
        
        # Validate inputs
        if direction not in ["forward", "backward", "left", "right"]:
            return json.dumps({
                "success": False,
                "error": "Invalid direction. Use: forward, backward, left, right"
            })
        
        # Clamp speed to valid range
        speed = max(0, min(255, int(speed)))
        
        # Map direction to command
        command_map = {
            "forward": "F",
            "backward": "B", 
            "left": "L",
            "right": "R"
        }
        
        command = command_map[direction]
        
        payload = {
            "command": command,
            "pwm": speed
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{base_url}/api/command",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    
                    return json.dumps({
                        "success": response.status == 200,
                        "action": "move",
                        "direction": direction,
                        "speed": speed,
                        "command_sent": command,
                        "esp32_response": result,
                        "status_code": response.status
                    })
                    
        except asyncio.TimeoutError:
            return json.dumps({
                "success": False,
                "error": f"Timeout connecting to ESP32 at {input.get('esp32_ip', 'unknown')}"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Communication error: {str(e)}"
            })
    
    async def _send_stop_command(self, input: dict, base_url: str) -> str:
        """Send stop command to RC car."""
        stop_type = input.get("stop_type", "all").lower()
        
        # Map stop types to commands
        command_map = {
            "all": "S",        # Stop everything (emergency stop)
            "motion": "Q",     # Stop forward/backward only
            "steering": "T"    # Stop left/right only
        }
        
        if stop_type not in command_map:
            return json.dumps({
                "success": False,
                "error": "Invalid stop_type. Use: all, motion, steering"
            })
        
        command = command_map[stop_type]
        
        # Stop commands don't need PWM
        if stop_type == "all":
            payload = {"command": command, "pwm": 0}
        else:
            payload = {"command": command, "pwm": 0}
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{base_url}/api/command",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    
                    return json.dumps({
                        "success": response.status == 200,
                        "action": "stop",
                        "stop_type": stop_type,
                        "command_sent": command,
                        "esp32_response": result,
                        "status_code": response.status
                    })
                    
        except asyncio.TimeoutError:
            return json.dumps({
                "success": False,
                "error": f"Timeout connecting to ESP32 at {input.get('esp32_ip', 'unknown')}"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Communication error: {str(e)}"
            })
    
    async def _send_gear_command(self, input: dict, base_url: str) -> str:
        """Send gear change command to RC car."""
        gear = input.get("gear", 1)
        
        # Validate gear
        if gear not in [1, 2, 3, 4]:
            return json.dumps({
                "success": False,
                "error": "Invalid gear. Use: 1, 2, 3, or 4"
            })
        
        payload = {
            "command": str(gear),
            "pwm": 0  # Gear commands don't use PWM
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{base_url}/api/command",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    
                    return json.dumps({
                        "success": response.status == 200,
                        "action": "gear",
                        "gear": gear,
                        "command_sent": str(gear),
                        "esp32_response": result,
                        "status_code": response.status
                    })
                    
        except asyncio.TimeoutError:
            return json.dumps({
                "success": False,
                "error": f"Timeout connecting to ESP32 at {input.get('esp32_ip', 'unknown')}"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Communication error: {str(e)}"
            })
    
    async def _send_handbrake_command(self, input: dict, base_url: str) -> str:
        """Send handbrake command to RC car."""
        payload = {
            "command": "Z",  # Handbrake command
            "pwm": 0
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{base_url}/api/command",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    
                    return json.dumps({
                        "success": response.status == 200,
                        "action": "handbrake",
                        "command_sent": "Z",
                        "esp32_response": result,
                        "status_code": response.status
                    })
                    
        except asyncio.TimeoutError:
            return json.dumps({
                "success": False,
                "error": f"Timeout connecting to ESP32 at {input.get('esp32_ip', 'unknown')}"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Communication error: {str(e)}"
            })
    
    async def _get_status(self, base_url: str) -> str:
        """Get current status of the ESP32 RC car controller."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"{base_url}/api/status") as response:
                    result = await response.json()
                    
                    return json.dumps({
                        "success": response.status == 200,
                        "action": "status",
                        "esp32_status": result,
                        "status_code": response.status
                    })
                    
        except asyncio.TimeoutError:
            return json.dumps({
                "success": False,
                "error": "Timeout connecting to ESP32"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Communication error: {str(e)}"
            })

    @property
    def example_usage(self) -> str:
        return """Example usage scenarios:

1. Move forward at medium speed:
{"esp32_ip": "192.168.100.66", "action": "move", "direction": "forward", "speed": 180}

2. Turn left at low speed:
{"esp32_ip": "192.168.100.66", "action": "move", "direction": "left", "speed": 100}

3. Emergency stop (stops everything):
{"esp32_ip": "192.168.100.66", "action": "stop", "stop_type": "all"}

4. Stop only forward/backward movement (keep steering):
{"esp32_ip": "192.168.100.66", "action": "stop", "stop_type": "motion"}

5. Stop only steering (keep forward/backward):
{"esp32_ip": "192.168.100.66", "action": "stop", "stop_type": "steering"}

6. Change to gear 3:
{"esp32_ip": "192.168.100.66", "action": "gear", "gear": 3}

7. Apply handbrake:
{"esp32_ip": "192.168.100.66", "action": "handbrake"}

8. Check car and connection status:
{"esp32_ip": "192.168.100.66", "action": "status"}

The esp32_ip parameter is REQUIRED for all commands. Get this from your ESP32's WiFi connection.
Speed ranges from 0 (stopped) to 255 (maximum). Default speed is 128.
Gears range from 1 (lowest) to 4 (highest).
The car supports independent control of motion and steering for advanced maneuvers."""


# Usage example for AI agent integration:
"""
# The tool can now be instantiated without parameters
esp32_car = ESP32RCCarTool()

# Example commands the AI agent can use (ESP32 IP is provided per command):
await esp32_car.run({"esp32_ip": "192.168.100.66", "action": "move", "direction": "forward", "speed": 200})
await esp32_car.run({"esp32_ip": "192.168.100.66", "action": "stop", "stop_type": "all"})
await esp32_car.run({"esp32_ip": "192.168.100.66", "action": "gear", "gear": 2})
await esp32_car.run({"esp32_ip": "192.168.100.66", "action": "status"})

# The AI agent will need to know the ESP32's IP address to control the car
# This can be discovered by checking the ESP32's serial output or router's DHCP table
"""