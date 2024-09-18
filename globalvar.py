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
            with open('settings/page.json', 'r') as file:
                json_data = json.load(file)
                size_w = json_data["size"]["width"]
                size_h = json_data["size"]["height"]
                padding_t = json_data["padding"]["t"]
                padding_b = json_data["padding"]["b"]
                padding_l = json_data["padding"]["l"]
                padding_r = json_data["padding"]["r"]
                position_part_x = json_data["position"]["part"]["x"]
                position_part_y = json_data["position"]["part"]["y"]
                position_date_x = json_data["position"]["date"]["x"]
                position_date_y = json_data["position"]["date"]["y"]
                position_qty_x = json_data["position"]["qty"]["x"]
                position_qty_y = json_data["position"]["qty"]["y"]

                dt = datetime.now()
                filename = f"{part['name']}-{dt.strftime('%Y%m%d')}-{dt.strftime('%H%M%S')}.pdf"
                file_path = os.path.join('label', filename)

                # font_name = "custom_font"
                # font_path = "fonts/THSarabunNew.ttf"

                # Register the custom font
                # pdfmetrics.registerFont(TTFont(font_name, font_path))

                # Create a canvas object with the specified paper size
                paper_size = (size_w * mm, size_h * mm)
                c = canvas.Canvas(file_path, pagesize=paper_size)

                # Set the font and size
                c.setFontSize(14)

                # Draw the text on the canvas
                # width, height = GlobalConfig.paper_size
                c.drawString((padding_l + position_part_x) * mm, size_h - ((padding_t + position_part_y) * mm), part['name'])
                c.drawString((padding_l + position_date_x) * mm, size_h - ((padding_t + position_date_y) * mm), f"{dt.strftime('%Y-%m-%d')}")
                c.drawString((padding_l + position_qty_x) * mm, size_h - ((padding_t + position_qty_y) * mm), f"{qty}")

                # Save the PDF file
                c.save()

                conn = cups.Connection()
                printer_name = conn.getDefault()
                print_job_id = conn.printFile(printer_name, file_path, "Print Job", {})

                job_attributes = conn.getJobAttributes(print_job_id)
                job_state = job_attributes['job-state']
                GlobalConfig.log_data(part, qty, print_job_id, job_state)

                while True:
                    job_attributes = conn.getJobAttributes(print_job_id)
                    job_state = job_attributes['job-state']
                    # Check if the job is completed or canceled
                    if job_state in [cups.IPP_JOB_COMPLETED, cups.IPP_JOB_CANCELED, cups.IPP_JOB_ABORTED]:
                        # print(job_state)
                        GlobalConfig.update_job_state(print_job_id, job_state)
                        break
                    elif job_state in [cups.IPP_JOB_PROCESSING, cups.IPP_JOB_HELD, cups.IPP_JOB_PENDING, cups.IPP_JOB_STOPPED]:
                        # print(job_state)
                        GlobalConfig.update_job_state(print_job_id, job_state)

                    # Wait for a short period before checking again
                    time.sleep(1)
        except Exception as e:
            print(f"An error occurred during printing: {e}")

        return True

    def reprint_job(job_id):
        try:
            # Connect to the CUPS server
            conn = cups.Connection()

            # Get the job attributes
            job_attributes = conn.getJobAttributes(job_id)
            if not job_attributes:
                print(f"Job ID {job_id} not found.")
                return False

            conn.restartJob(job_id)
            job_attributes = conn.getJobAttributes(job_id)
            job_state = job_attributes['job-state']
            GlobalConfig.update_job_state(job_id, job_state)

            while True:
                job_attributes = conn.getJobAttributes(job_id)
                job_state = job_attributes['job-state']
                # Check if the job is completed or canceled
                if job_state in [cups.IPP_JOB_COMPLETED, cups.IPP_JOB_CANCELED, cups.IPP_JOB_ABORTED]:
                    # print(job_state)
                    GlobalConfig.update_job_state(job_id, job_state)
                    break
                elif job_state in [cups.IPP_JOB_PROCESSING, cups.IPP_JOB_HELD, cups.IPP_JOB_PENDING, cups.IPP_JOB_STOPPED]:
                    # print(job_state)
                    GlobalConfig.update_job_state(job_id, job_state)

                # Wait for a short period before checking again
                time.sleep(1)
        except Exception as e:
            print(f"An error occurred during reprinting: {e}")

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

    def update_job_state(job_id, new_job_state):
        # Get the current date in the format yyyy-mm-dd
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_filename = f"logs/print-job-{current_date}.json"

        # Check if the log file exists
        if not os.path.isfile(log_filename):
            print(f"Log file {log_filename} does not exist.")
            return False

        # Read the log file
        with open(log_filename, 'r') as log_file:
            data = json.load(log_file)

        # Find the entry with the specified job_id and update its job_state
        job_found = False
        for entry in data:
            if entry['jobid'] == job_id:
                entry['state'] = new_job_state
                job_found = True
                break

        if not job_found:
            print(f"Job ID {job_id} not found in log file.")
            return False

        # Write the updated data back to the log file
        with open(log_filename, 'w') as log_file:
            json.dump(data, log_file, indent=4)

        # print(f"Job ID {job_id} updated to state {new_job_state}.")
        return True