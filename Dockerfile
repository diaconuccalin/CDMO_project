# Start from MiniZinc base image
FROM minizinc/minizinc

# Install required packages
RUN apt-get update
RUN apt-get install -y python3 python3-pip git

# Set working dir in the container
WORKDIR /home

# Clone repo
RUN git clone https://github.com/diaconuccalin/CDMO_project.git

# cd to project root
WORKDIR /home/CDMO_project
RUN git switch calin

# Install python dependencies
RUN pip3 install -r requirements.txt

RUN mkdir reports
