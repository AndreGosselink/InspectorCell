#!/bin/bash

#######################
# Install dir
#######################
VENVDIR="$PWD/icell_venv"
PYCMD="python3.7"

#######################
# Utility functions
#######################

# Promt error message
function _emsg() {
  printf "\e[38;5;1m$1\e[0m\n" ${*:2}
}

# Promt info message
function _imsg() {
  # gray
  printf "\e[38;5;250m$1\e[0m\n" ${*:2}
}

# Promt warning message
function _wmsg() {
  # yellow
  printf "\e[38;5;11m$1\e[0m\n" ${*:2}
}

# exit with error codes
function _exit () {
  declare -A _err=( ["inval"]=22 ["ok"]=0 ["notempty"]=39 ["noent"]=2 )
  exit ${_err["$1"]}
}

# Just print usage
function usage () {
  # Fromat option $1 and helptext $2
  function _fmt () {
    printf "%5s%-18s%-20s\n" "" "$1" "$2"
  }
  printf "%-13s%s\n" "Basic usage:" "$(basename $0) -i {conda,mamba,venv}"
  printf "%-13s%s\n" "" "$(basename $0) -c VAL"
  printf "%-13s%s\n" "" "$(basename $0) -[hrv]"
  printf "Options:\n"
  _fmt "h" "This help"
  _fmt "i <variant>" "Install into '${VENVDIR}' using <env> = 'conda', 'mamba' or 'venv'"
  _fmt "r" "remove installed version, if exists"
  _fmt "c <cmd>" "Activate environment and run <cmd> "
  _fmt "v" "Print version strings and exit"
}

# Print current Python version
function version_python () {
  local verpy="$(python --version || echo unknown unknown)"
  local verpy=( $verpy )
  printf "${verpy[1]}"
}

# Print git describe of InspectorCell and Python version
function version () {
  local veric="$(git describe --always || echo unknown)"
  local verpy="$(python --version || echo unknown unknown)"

  function _fmt () {
    printf "%13s%-3s%-20s\n" "$1" ":" "$2"
  }
  _fmt "InspectorCell" "${veric}"
  _fmt "Python" "$(version_python)"
}

#########################
# Entrypoint for Install
# Orange3+InspectorCell
# Choose sub-installer 
# based on choosen venv
# variant
#########################
function install () {
  local todir="$1"
  local variant="$2"

  # check if is empty
  mkdir -p "${todir}"
  if [ "$(ls -A ${todir})" ]; then
    _emsg "Non-empty dir '%s' Please remove/uninstall first!" "${todir}"
    _exit "notempty"
  fi

  # check for variants
  # install virtual environment with _all_ dependencies
  case "$variant" in
    venv) 
      # nag if python is not there
      if ! $(hash "$PYCMD"); then
        _emsg "Install "$PYCMD" first, or/and add it into PATH"
        _exit "noent"
      fi
      # prepare venv
      make_venv "$todir" "$PYCMD" || exit $?
      ;;
    conda)
      # nag if conda is not there
      if ! $(hash conda); then
        _emsg "Install conda first, or/and add it into PATH"
        _exit "noent"
      fi
      # prepare condaenv
      make_condaenv "$todir" "conda" "${PWD}/condaenv.yml" || exit $?
     ;;
    mamba)
      # nag if mamba is not there
      if ! $(hash mamba); then
        _emsg "Install conda+mamba first, or/and add it into PATH"
        _exit "noent"
      fi
      # prepare condaenv
      make_condaenv "$todir" "mamba" "${PWD}/condaenv.yml" || exit $?
     ;;
    *)
      _emsg "Variant is '%s', but must be 'venv', 'conda' or 'mamba'" "${variant}"
      _exit "inval"
      ;;
  esac

  # activate new conda/venv environment
  activate "${VENVDIR}" || exit $?
  # install inspector cell package w/o depends
  install_inspectorcell || exit $?
}

# install inspector cell package
function install_inspectorcell () {
  _imsg "Install InpectorCell using $(type pip)"

  # python setup.py install --force
  pip install . --force-reinstall --no-deps
}

# Create condaenv with all deps
function make_condaenv () {
  local todir="$1"
  local usebin="$2"
  local envf="$3"

  _imsg "Creating conda environment in '%s'" "${todir}"
  ${usebin} env create -p "${todir}" -f "${envf}"
}

# Create a Python venv with all deps
function make_venv () {
  local todir="$1"
  local usebin="$2"
  
  _wmsg "WARNING: YOU WILL NEED TO CLOSELY LOOK FOR DEPENDENCIES" 
  _wmsg "known issues with: 'libffi7', 'bottleneck'"
  _imsg "Creating python venv in '%s'" "${todir}"
  ${usebin} -m venv "${todir}"
  activate "${VENVDIR}" || exit $?
  _imsg "Updating $(type pip)"
  "${VENVDIR}/bin/python" -m pip install --upgrade pip
  "${VENVDIR}/bin/python" -m pip install -r "${PWD}/requirements.txt"
}

# Activate whatever virtual environment is
# found in VENVDIR
function activate () {
  local indir="$1"

  if [ -f "${indir}/bin/activate" ]; then
    _imsg "Activating venv %s" "${indir}"
    source "${indir}/bin/activate"
    return 0
  fi

  if [ -d "${indir}/conda-meta" ]; then
    _imsg "Activating conda env %s" "${indir}"
    eval "$(conda shell.bash hook)"
    conda activate "${indir}"
    return 0
  fi

  _emsg "Could not find valid environment in '%s' Not installed?" "${indir}"
  _exit "noent" 
}

# Create a Python venv with all deps
function run_cmd () {
  local cmd="$1"
  
  activate "${VENVDIR}" || exit $?
  _imsg "Running ${cmd}"
  eval "${cmd}" && _exit "ok" || exit $?
}

# remove VENVDIR with all contents
function remove () {
  local todir="$1"
  
  _imsg "Removing everything in '%s'" "${todir}"
  rm -rf ${todir}
}

# Acitvate env and run Orange3
function run_orange () {
  local todir="$1"
  
  activate "${VENVDIR}" || exit $?
  python -m Orange.canvas > log.txt 2>&1 &
  disown
}

# Option parsing
while getopts ":hvri:c:" opt $@; do
  case "$opt" in
    h) usage && _exit "ok" ;;
    v) version && _exit "ok" ;;
    i) install "${VENVDIR}" "${OPTARG}" && _exit "ok" || exit $? ;;
    r) remove "${VENVDIR}" && _exit "ok" || exit $? ;;
    c) run_cmd "${OPTARG}" && _exit "ok" || exit $? ;;
    :) _emsg "Option '-${OPTARG}' needs parameter"; usage && _exit "inval" ;;
   \?) _emsg "Invalid option '-${OPTARG}'"; usage && _exit "inval" ;;
  esac
done

# default if no options are provided
run_orange || exit $?
