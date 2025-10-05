# lambda-gateway: Front-End

## Prerequisites
- Node.js installed (with npm)
- lambda-gateway backend running

## Installation

1. **Navigate to the frontend folder**
   
   Open a terminal and go to the `lambda-gateway/frontend` directory

2. **Install Node.js dependencies**
   
   ```bash
   npm install .
   ```

## Configuration

3. **Create the `.env.local` configuration file**
   
   In the root of the frontend directory, create a file named `.env.local` with the following content:
   
   ```env
   NEXT_PUBLIC_BACKEND_URL="http://127.0.0.1:5500"
   ```
   
   **Note:** If your backend is running at a different address, adjust the URL accordingly.

## Running the Frontend

4. **Start the development server**
   
   Make sure the backend is already running before executing this command:
   
   ```bash
   npm run dev -- -H 0.0.0.0
   ```
   
   The frontend will be available at the address shown in the terminal (typically `http://0.0.0.0:3000`).