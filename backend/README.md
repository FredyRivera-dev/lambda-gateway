# lambda-gateway: Back-End

## Prerequisites
- Python (with pip installed)
- Docker installed and running

## Installation

1. **Navigate to the backend folder**
   
   Open a terminal and go to the `lambda-gateway/backend` directory

2. **Install Python dependencies**
   
   ```bash
   pip install -r requirements.txt
   ```

## Docker Configuration

3. **Add your user to the Docker group**
   
   This step allows you to run Docker commands without using `sudo`:
   
   ```bash
   sudo usermod -aG docker $USER
   ```
   
   **Note:** After running this command, you'll need to log out and log back in (or restart) for the changes to take effect.

## Running the Backend

4. **Start the backend server**
   
   ```bash
   python backend.py
   ```
   
   The backend will be available at:
   - **Host:** `0.0.0.0` or `localhost`
   - **Port:** `5500`
   - **URL:** `http://localhost:5500`
