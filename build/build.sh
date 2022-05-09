source setting.env
if [ -z "${FLEXRAN_DIR}" ] || [ -z "${DIR_WIRELESS_SDK}" ] || [ -z "${RTE_SDK}" ] \
   || [ -z "${ICC_DIR}" ] || [ -z "${DIR_WIRELESS_TEST_5G}" ] ; then
   echo "Not all required variables are set. Please set all of the variables"
   exit 1
fi

# Create empty staging directory
rm -rf staging || true

mkdir -p staging/auto

/bin/cp -f Dockerfile staging/
/bin/cp -f driver.sh staging/auto/
/bin/cp -f env.src staging/auto/
 
# Copy l1app and testmac binaries
/bin/cp -rf "${FLEXRAN_DIR}"/bin staging/

# Copy Wireless SDK
mkdir -p staging/sdk
/bin/cp -rf "${DIR_WIRELESS_SDK}" staging/sdk/

# Copy DPDK
/bin/cp -rf "${RTE_SDK}" staging/dpdk

# Copy ICC libs
mkdir -p staging/icc_libs
/bin/cp -f "${ICC_DIR}"/compilers_and_libraries_*/linux/compiler/lib/intel64/* staging/icc_libs/
/bin/cp -f "${ICC_DIR}"/compilers_and_libraries/linux/ipp/lib/intel64/* staging/icc_libs/
/bin/cp -f "${ICC_DIR}"/compilers_and_libraries/linux/mkl/lib/intel64/* staging/icc_libs/

# Copy FlexRAN libs
mkdir -p staging/libs
/bin/cp -rf "${FLEXRAN_DIR}"/libs/cpa staging/libs/
/bin/cp -rf "${FLEXRAN_DIR}"/libs/cpa/sub6 staging/libs/cpa_sub6

# Copy FD 5G tests
mkdir -p staging/tests/nr5g
/bin/cp -rf "${DIR_WIRELESS_TEST_5G}"/fd staging/tests/nr5g/

# Copy WLS Module
/bin/cp -rf "${FLEXRAN_DIR}"/wls_mod staging/ 

cd staging && podman build . -t flexran5g:${FLEXRAN_VERSION}

