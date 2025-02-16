#!/usr/bin/env bash

set -euxo pipefail

#  IMPORTANT: for any test using the dss command:
#
# - Clear PYTHON shell vars to prevent conflicts between dss
#   and checkbox python environments
# - Run from ${HOME} as dss writes logs to its working directory,
#   and as a snap does not have permissions to write to the default
#   working directory for checkbox tests
export -n PYTHONHOME PYTHONPATH PYTHONUSERBASE

check_dss_can_be_initialized() {
    # TODO: we actually seem to initialize dss here; maybe split it out
    cd "${HOME}"
    dss initialize --kubeconfig="$(sudo microk8s config)"
    echo "Test success: dss initialized."
}

check_dss_namespace_is_deployed() {
    if microk8s.kubectl get ns | grep -q dss; then
        echo "Test success: 'dss' namespace is deployed!"
    else
        >&2 echo "Test failure: no namespace named 'dss' deployed."
        exit 1
    fi
}

check_mlflow_status_is_ready() {
    cd "${HOME}"
    result=$(dss status) # save result to shell var to avoid broken pipe error
    if echo "${result}" | grep -q "MLflow deployment: Ready"; then
        echo "Test success: 'dss status' shows ready status for mlflow."
    else
        >&2 echo "Test failure: 'dss status' does not show ready status for mlflow."
        exit 1
    fi
}

check_mlflow_is_deployed_as_first_service() {
    # TODO: enable mlflow to be a service in any position
    result=$(microk8s.kubectl get service -n dss -o jsonpath='{.items[0].metadata.name}')
    if [ "${result}" = "mlflow" ]; then
        echo "Test success: 'mlflow' service is deployed!"
    else
        >&2 echo "Test failure: expected service name 'mlflow' but got ${result}"
        exit 1
    fi
}

check_dss_has_intel_gpu_acceleration_enabled() {
    cd "${HOME}"
    result=$(dss status) # save result to shell var to avoid broken pipe error
    if echo "${result}" | grep -q "Intel GPU acceleration: Enabled"; then
        echo "Test success: 'dss status' correctly reports Intel GPU status."
    else
        >&2 echo "Test failure: 'dss status' does not report that Intel GPU acceleration is enabled."
        exit 1
    fi
}

check_dss_can_create_itex_215_notebook() {
    cd "${HOME}"
    if dss create itex-215-notebook --image=intel/intel-extension-for-tensorflow:2.15.0-xpu-idp-jupyter; then
        echo "Test success: successfully created an ITEX 2.15 notebook."
    else
        >&2 echo "Test failure: failed to create an ITEX 2.15 notebook."
        exit 1
    fi
}

check_dss_can_create_ipex_2120_notebook() {
    cd "${HOME}"
    if dss create ipex-2120-notebook --image=intel/intel-extension-for-pytorch:2.1.20-xpu-idp-jupyter; then
        echo "Test success: successfully created an IPEX 2.1.20 notebook."
    else
        >&2 echo "Test failure: failed to create an IPEX 2.1.20 notebook."
        exit 1
    fi
}

help_function() {
    echo "This script is used for generic tests related to DSS"
    echo "Usage: check_dss.sh <test_case>"
    echo
    echo "Test cases currently implemented:"
    echo -e "\t<dss_can_be_initialized>: check_dss_can_be_initialized"
    echo -e "\t<dss_namespace_is_deployed>: check_dss_namespace_is_deployed"
    echo -e "\t<mlflow_status_is_ready>: check_mlflow_status_is_ready"
    echo -e "\t<mlflow_is_deployed_as_first_service>: check_mlflow_is_deployed_as_first_service"
    echo -e "\t<intel_gpu_acceleration_is_enabled>: check_dss_has_intel_gpu_acceleration_enabled"
    echo -e "\t<can_create_itex_215_notebook>: check_dss_can_create_itex_215_notebook"
    echo -e "\t<can_create_ipex_2120_notebook>: check_dss_can_create_ipex_2120_notebook"
}

main() {
    case ${1} in
    dss_can_be_initialized) check_dss_can_be_initialized ;;
    dss_namespace_is_deployed) check_dss_namespace_is_deployed ;;
    mlflow_status_is_ready) check_mlflow_status_is_ready ;;
    mlflow_is_deployed_as_first_service) check_mlflow_is_deployed_as_first_service ;;
    intel_gpu_acceleration_is_enabled) check_dss_has_intel_gpu_acceleration_enabled ;;
    can_create_itex_215_notebook) check_dss_can_create_itex_215_notebook ;;
    can_create_ipex_2120_notebook) check_dss_can_create_ipex_2120_notebook ;;
    *) help_function ;;
    esac
}

main "$@"
