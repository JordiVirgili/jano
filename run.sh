#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Display header
echo -e "${BOLD}${BLUE}"
echo "==============================================================="
echo "     ██╗ █████╗ ███╗   ██╗ ██████╗"
echo "     ██║██╔══██╗████╗  ██║██╔═══██╗"
echo "     ██║███████║██╔██╗ ██║██║   ██║"
echo "██   ██║██╔══██║██║╚██╗██║██║   ██║"
echo "╚█████╔╝██║  ██║██║ ╚████║╚██████╔╝"
echo " ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝"
echo ""
echo "     Unified Security Configuration & Testing System"
echo "==============================================================="
echo -e "${NC}"
echo -e "This script will set up virtual environments and launch all Jano components."


# Function to print status messages
print_status() {
    echo -e "${YELLOW}[*] $1${NC}"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}[+] $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}[-] $1${NC}"
    exit 1
}

# Check required dependencies
check_dependencies() {
    print_status "Checking required dependencies..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install it before continuing."
    fi

    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed. Please install it before continuing."
    fi

    # Check virtualenv
    if ! python3 -c "import venv" &> /dev/null; then
        print_status "The venv module is not available. Trying to install it..."
        pip3 install virtualenv
        if [ $? -ne 0 ]; then
            print_error "Could not install virtualenv. Please install it manually."
        fi
    fi

    print_success "All dependencies are satisfied."
}

# Set up virtual environment and dependencies for Argos
setup_argos() {
    print_status "Setting up the Argos environment..."

    # Create virtual environment for Argos
    if [ ! -d "./argos_venv" ]; then
        python3 -m venv ./argos_venv
        if [ $? -ne 0 ]; then
            print_error "Could not create virtual environment for Argos."
        fi
        print_success "Argos virtual environment created."
    else
        print_status "Argos virtual environment already exists. Using existing one."
    fi

    # Activate virtual environment
    source ./argos_venv/bin/activate

    # Install dependencies
    print_status "Installing Argos dependencies..."
    pip install -r argos/requirements.txt
    if [ $? -ne 0 ]; then
        deactivate
        print_error "Error installing Argos dependencies."
    fi

    # Configure .env file if it doesn't exist
    if [ ! -f "./argos/.env" ]; then
        print_status "Configuring Argos .env file..."
        cp ./argos/.env.example ./argos/.env

        # Generate random API password
        API_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)

        # Replace the password in the .env file
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/secure_password_here/$API_PASSWORD/g" ./argos/.env
        else
            # Linux
            sed -i "s/secure_password_here/$API_PASSWORD/g" ./argos/.env
        fi

        print_success "Argos .env file configured."
        print_status "Generated API password: $API_PASSWORD (save this to configure other components)"
    else
        print_status "Argos .env file already exists. Using existing configuration."
        # Extract the current password to use in other components
        API_PASSWORD=$(grep "JANO_API_PASSWORD" ./argos/.env | cut -d '=' -f2)
    fi

    deactivate
}

# Set up virtual environment and dependencies for Eris
setup_eris() {
    print_status "Setting up the Eris environment..."

    # Create virtual environment for Eris
    if [ ! -d "./eris_venv" ]; then
        python3 -m venv ./eris_venv
        if [ $? -ne 0 ]; then
            print_error "Could not create virtual environment for Eris."
        fi
        print_success "Eris virtual environment created."
    else
        print_status "Eris virtual environment already exists. Using existing one."
    fi

    # Activate virtual environment
    source ./eris_venv/bin/activate

    # Install dependencies
    print_status "Installing Eris dependencies..."
    pip install -r eris/requirements.txt
    if [ $? -ne 0 ]; then
        deactivate
        print_error "Error installing Eris dependencies."
    fi

    # Configure .env file if it doesn't exist
    if [ ! -f "./eris/.env" ]; then
        print_status "Configuring Eris .env file..."
        cp ./eris/.env.example ./eris/.env

        # Update the .env file with the API password
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/secure_password_here/$API_PASSWORD/g" ./eris/.env
        else
            # Linux
            sed -i "s/secure_password_here/$API_PASSWORD/g" ./eris/.env
        fi

        print_success "Eris .env file configured."
    else
        print_status "Eris .env file already exists. Using existing configuration."
    fi

    deactivate
}

# Set up virtual environment and dependencies for the frontend
setup_frontend() {
    print_status "Setting up the frontend environment..."

    # Create virtual environment for the frontend
    if [ ! -d "./frontend_venv" ]; then
        python3 -m venv ./frontend_venv
        if [ $? -ne 0 ]; then
            print_error "Could not create virtual environment for the frontend."
        fi
        print_success "Frontend virtual environment created."
    else
        print_status "Frontend virtual environment already exists. Using existing one."
    fi

    # Activate virtual environment
    source ./frontend_venv/bin/activate

    # Install dependencies
    print_status "Installing frontend dependencies..."
    pip install -r frontend/requirements.txt
    if [ $? -ne 0 ]; then
        deactivate
        print_error "Error installing frontend dependencies."
    fi

    # Configure .env file if it doesn't exist
    if [ ! -f "./frontend/.env" ]; then
        print_status "Configuring frontend .env file..."
        cp ./frontend/.env.example ./frontend/.env

        # Update the .env file with the API password
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/secure_password_here/$API_PASSWORD/g" ./frontend/.env
        else
            # Linux
            sed -i "s/secure_password_here/$API_PASSWORD/g" ./frontend/.env
        fi

        print_success "Frontend .env file configured."
    else
        print_status "Frontend .env file already exists. Using existing configuration."
    fi

    deactivate
}

# Function to start Argos
start_argos() {
    print_status "Starting Argos..."
    source ./argos_venv/bin/activate
    cd argos
    python -m argos &
    ARGOS_PID=$!
    cd ..
    print_success "Argos started with PID: $ARGOS_PID"
    deactivate
}

# Function to start Eris
start_eris() {
    print_status "Starting Eris..."
    source ./eris_venv/bin/activate
    cd eris
    python -m eris &
    ERIS_PID=$!
    cd ..
    print_success "Eris started with PID: $ERIS_PID"
    deactivate
}

# Function to start the frontend
start_frontend() {
    print_status "Starting the frontend..."
    source ./frontend_venv/bin/activate
    cd frontend
    streamlit run app.py &
    FRONTEND_PID=$!
    cd ..
    print_success "Frontend started with PID: $FRONTEND_PID"
    deactivate
}

# Function to terminate processes when exiting
cleanup() {
    print_status "Stopping services..."
    if [ ! -z "$ARGOS_PID" ]; then
        kill $ARGOS_PID
        print_success "Argos stopped."
    fi
    if [ ! -z "$ERIS_PID" ]; then
        kill $ERIS_PID
        print_success "Eris stopped."
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID
        print_success "Frontend stopped."
    fi
    exit 0
}

# Register the cleanup function to run on exit
trap cleanup SIGINT SIGTERM

# Run the main functions
check_dependencies
setup_argos
setup_eris
setup_frontend
start_argos
start_eris
start_frontend

print_success "Jano is now running!"
print_status "Argos: http://localhost:8005"
print_status "Eris: http://localhost:8006"
print_status "Frontend: http://localhost:8501"
print_status "Press Ctrl+C to stop all services."

# Keep the script running
wait