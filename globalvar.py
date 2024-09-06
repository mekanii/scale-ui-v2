import time
import serial
import serial.tools.list_ports
import json
import cups
import os
from datetime import datetime
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

class GlobalConfig:
    com_port = ""
    baud_rate = 19200
    select_com_options = []
    serial_connection = None

    paper_size = (100 * mm, 150 * mm)

    def get_available_com_ports():
        ports = serial.tools.list_ports.comports()
        return [f'    {port.device}' for port in ports if 'USB' in port.description or 'Arduino' in port.description]
    
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

    def print_label(part, qty):
        try:
            d = datetime.now().strftime('%Y%m%d')
            t = datetime.now().strftime('%H%M%S')
            filename = f'{part['name']}-{d}-{t}.pdf'
            file_path = os.path.join('label', filename)
            
            # font_name = "custom_font"
            # font_path = "fonts/THSarabunNew.ttf"

            # Register the custom font
            # pdfmetrics.registerFont(TTFont(font_name, font_path))

            # Create a canvas object with the specified paper size
            c = canvas.Canvas(file_path, pagesize=GlobalConfig.paper_size)

            # Set the font and size
            c.setFontSize(14)

            # Draw the text on the canvas
            width, height = GlobalConfig.paper_size
            c.drawString(5 * mm, height - (6 * mm), f'{d} {t}')
            c.drawString(5 * mm, height - (12 * mm), part['name'])
            c.drawString(5 * mm, height - (18 * mm), f'{qty} pack')

            # Save the PDF file
            c.save()

            conn = cups.Connection()
            printer_name = conn.getDefault()
            print_job_id = conn.printFile(printer_name, file_path, "Print Job", {})

            while True:
                job_attributes = conn.getJobAttributes(print_job_id)
                job_state = job_attributes['job-state']

                # Check if the job is completed or canceled
                if job_state in [cups.IPP_JOB_COMPLETED, cups.IPP_JOB_CANCELED, cups.IPP_JOB_ABORTED]:
                    GlobalConfig.log_data(part, qty, print_job_id, job_state)
                    break

                # Wait for a short period before checking again
                time.sleep(1)
        except Exception as e:
            print(f"An error occurred during printing: {e}")
        
        return True

    def log_data(part, qty, job_id, job_state):
        # Get the current date in the format yyyy-mm-dd
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        log_filename = f"logs/print-job-{current_date}.json"

        # Check if the logs directory exists, if not, create it
        if not os.path.exists("logs"):
            os.makedirs("logs")

        # Check if the log file exists
        if not os.path.isfile(log_filename):
            # Create the log file with an empty list if it doesn't exist
            with open(log_filename, 'w') as log_file:
                json.dump([], log_file)

        # Prepare the log entry
        log_entry = {
            "date": current_date,
            "time": current_time,
            "part": part['name'],
            "std": part['std'],
            "unit": part['unit'],
            "hysteresis": part['hysteresis'],
            "jobid": job_id,
            "qty": qty,
            "state": job_state
        }

        # Append the log entry to the existing log file
        with open(log_filename, 'r+') as log_file:
            # Load existing data
            data = json.load(log_file)
            # Append the new entry
            data.append(log_entry)
            # Move the cursor to the beginning of the file
            log_file.seek(0)
            # Write the updated data back to the file
            json.dump(data, log_file, indent=4)