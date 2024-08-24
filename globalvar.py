import time
import serial
import serial.tools.list_ports
import json

class GlobalConfig:
    com_port = ""
    baud_rate = 19200
    select_com_options = []
    serial_connection = None

    def get_available_com_ports():
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports if 'USB' in port.description or 'Arduino' in port.description]
    
    def send_request(request):
        try:
            str_request = json.dumps(request) + '\n'
            GlobalConfig.serial_connection.write(str_request.encode('utf-8'))
            # print(f"Sent: {str_request.strip()}")
        except Exception as e:
            print(f"Failed to send data: {e}")
            return False
        return True

    def read_response():
        try:
            while True:
                str_response = GlobalConfig.serial_connection.readline().decode('utf-8').strip()
                if str_response:
                    break
                time.sleep(0.1)
            return str_response
        except Exception as e:
            print(f"Failed to read data: {e}")
            return None

    def parse_json(str_response):
        try:
            response = json.loads(str_response)
            # print(f"Parsed JSON: {response}")
            return response
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON: {e}")
        return None
