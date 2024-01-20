# Start from MiniZinc base image
FROM minizinc/minizinc

# Install required packages
RUN apt-get update
RUN apt-get install -y python3 python3-pip git

# Set working dir in the container
WORKDIR /root

# Clone repo
RUN git clone https://github.com/diaconuccalin/CDMO_project.git
RUN git switch calin

# cd to project root
RUN cd CDMO_project/

# Install python dependencies
RUN pip3 install -r requirements.txt
