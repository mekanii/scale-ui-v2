# Scale Application README

This is a scale application designed to interact with a scale device connected via a serial port. The application allows users to select a COM port, connect to the scale, and perform various operations such as taring the scale and reloading parts.

## Setting Up Python

To run this project, you need to have Python installed on your system. Follow the steps below to install Python and add it to your system PATH on Windows.

### Installing Python

1. **Download Python**:
   - Go to the [official Python website](https://www.python.org/downloads/) and download the latest version of Python.

2. **Run the Installer**:
   - Launch the downloaded installer. Make sure to check the box that says **"Add Python to PATH"** during the installation process. This will automatically add Python to your system PATH.

3. **Verify the Installation**:
   - Open a Command Prompt window and type:
     ```bash
     python --version
     ```
   - You should see the installed Python version if the installation was successful.

### Manually Adding Python to the System PATH

If you need to add Python to the PATH manually, follow these steps:

1. **Locate the Python Installation Path**:
   - By default, Python is usually installed in one of the following locations:
     - `C:\Python39` (for Python 3.9)
     - `C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python39` (for user installations)

2. **Open System Properties**:
   - Right-click on the **This PC** or **Computer** icon on the desktop or in File Explorer.
   - Select **Properties**.
   - Click on **Advanced system settings** on the left sidebar.
   - In the System Properties window, click on the **Environment Variables** button.

3. **Edit the PATH Variable**:
   - In the Environment Variables window, find the **System variables** section.
   - Scroll down and select the **Path** variable, then click on **Edit**.

4. **Add Python to PATH**:
   - In the Edit Environment Variable window, click on **New**.
   - Add the path to the Python installation directory (e.g., `C:\Python39` or `C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python39`).
   - Also, add the `Scripts` directory, which is where pip and other scripts are located (e.g., `C:\Python39\Scripts`).
   - Click **OK** to close all dialog boxes.

5. **Verify the PATH**:
   - Open a new Command Prompt window.
   - Type `python --version` or `python` and press Enter. If Python is correctly added to the PATH, you should see the Python version or the Python interpreter prompt.

### Programmatically Adding Python to the System PATH

If you want to add Python to the PATH programmatically (for example, in a batch file), you can use the following commands in a `setup.bat` file:

```batch
@echo off
SET PYTHON_PATH=C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python39
SET SCRIPTS_PATH=%PYTHON_PATH%\Scripts

REM Add Python to the PATH
setx PATH "%PATH%;%PYTHON_PATH%;%SCRIPTS_PATH%"
```

### Important Notes
- **Administrative Privileges**: Modifying system environment variables may require administrative privileges. If you encounter permission issues, run the Command Prompt as an administrator.
- **Restart Required**: After modifying the PATH, you may need to restart any open Command Prompt windows or your computer for the changes to take effect.
- **Multiple Python Versions**: If you have multiple versions of Python installed, ensure that the desired version is the first one in the PATH to avoid conflicts.

## Features

* Select and connect to a COM port for scale communication
* Tare the scale to reset the weight to zero
* Reload parts to update the list of available parts
* Display the current weight and part information

## Requirements

* Python 3.x
* ttkbootstrap 1.10.1
* pyserial 3.5
* pygame 2.6.0
* requests 2.32.3

## Installation

1. Clone the repository or download the project files.
2. Install the required packages using `pip install -r requirements.txt` in the terminal.
3. Run the application using `python main.py` in the terminal.

## Configuration

The application uses a configuration file to store settings such as the COM port and part options. The configuration file is located at `globalvar.py`.

## Usage

1. Launch the application.
2. Select a COM port from the dropdown menu.
3. Click the 'CONNECT' button to establish a connection with the scale.
4. Select a part from the dropdown menu.
5. Use the 'TARE' button to reset the scale to zero.
6. Use the 'RELOAD' button to update the list of available parts.

## Troubleshooting

* Ensure the scale device is properly connected to the computer and powered on.
* Verify that the correct COM port is selected and the scale is properly configured.
* If the application fails to connect to the scale, check the serial connection settings and ensure the scale is not already in use by another application.

## Development Environment

This project is developed using Visual Studio Code (VSCode) on Windows. To set up the development environment:

1. Install the Python extension for VSCode.
2. Open the project folder in VSCode.
3. Create a new terminal in VSCode using `Ctrl + Shift + ` (backtick).
4. Run the application using `python main.py` in the terminal.

## Contributing

Contributions are welcome. Please submit pull requests with detailed descriptions of the changes and improvements.