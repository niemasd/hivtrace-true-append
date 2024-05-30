# Docker image for an hivtrace-true-append development environment (Red Hat Universal Base Image 8.10)
FROM redhat/ubi8:8.10

# Set up environment and install dependencies
RUN yum -y update && \
    yum install -y cmake gcc-c++ gcc-toolset-12 git python3.11 && \
    echo 'source /opt/rh/gcc-toolset-12/enable' > ~/.bashrc && \
    source ~/.bashrc && \

    # install tn93
    git clone https://github.com/veg/tn93.git && \
    cd tn93 && \
    cmake . && \
    make install && \
    cd .. && \
    rm -rf tn93
