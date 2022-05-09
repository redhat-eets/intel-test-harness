FROM centos:stream8
RUN yum install -y rsync kmod libhugetlbfs libhugetlbfs-devel libhugetlbfs-utils \
        numactl-devel vim python3 pciutils iproute procps-ng expect \
     && yum clean all \
     && rm -rf /var/cache/yum \
     && pip3 install pyyaml lxml dataclasses

WORKDIR /opt/flexran

COPY bin ./bin
COPY dpdk ./dpdk
COPY icc_libs ./icc_libs
COPY libs ./libs
COPY sdk ./sdk
COPY tests ./tests
COPY wls_mod ./wls_mod
COPY auto ./auto

ENV flexranPath=/opt/flexran
ENV RTE_SDK=$flexranPath/dpdk
ENV RTE_TARGET=x86_64-native-linuxapp-icc
ENV WIRELESS_SDK_TARGET_ISA=avx512
ENV RPE_DIR=${flexranPath}/libs/ferrybridge
ENV ROE_DIR=${flexranPath}/libs/roe
ENV XRAN_DIR=${flexranPath}/xran
ENV WIRELESS_SDK_TOOLCHAIN=icc
ENV DIR_WIRELESS_SDK_ROOT=${flexranPath}/sdk
ENV DIR_WIRELESS_TEST_5G=${flexranPath}/tests/nr5g
ENV SDK_BUILD=build-${WIRELESS_SDK_TARGET_ISA}-icc
ENV DIR_WIRELESS_SDK=${DIR_WIRELESS_SDK_ROOT}/${SDK_BUILD}
ENV FLEXRAN_SDK=${DIR_WIRELESS_SDK}/install
ENV DIR_WIRELESS_TABLE_5G=${flexranPath}/bin/nr5g/gnb/l1/table
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${flexranPath}/icc_libs

WORKDIR /opt/flexran/auto
