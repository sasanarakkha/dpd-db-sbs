#!/bin/bash

# This script runs a command and logs its output to a file.
# It also provides a timestamped log file with the command output and
# handles log rotation for the specified log files.
# It requires the user to provide a log base name and the command to run.
# The script captures the start and end time of the command execution,
# along with the exit status of the command.
# It also checks for the number of log files and deletes older logs if
# the number exceeds a specified limit.

# Exit immediately if a command exits with a non-zero status.
# Treat unset variables as an error when substituting.
# Cause a pipeline to return the exit status of the last command
# that exited with a non-zero status, or zero if all commands in the
# pipeline exit successfully.
set -euo pipefail

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <log_base_name> <command_to_run_with_args...>"
    echo "Example: $0 my_script_log uv run bash ./my_script.sh --arg1 value1"
    exit 1
fi

LOG_BASE_NAME="$1"
shift # Remove log_base_name from arguments, the rest is the command

COMMAND_TO_RUN=("$@") # Store the rest of the arguments as the command to run

# --- Initial Setup ---
PROJECT_ROOT="$HOME/Documents/dpd-db"
cd "${PROJECT_ROOT}" || { echo "FATAL: Failed to cd to ${PROJECT_ROOT}" >&2; exit 1; }

LOG_DIR="logs"
mkdir -p "${LOG_DIR}"

# --- Timing & Log File Naming ---
START_TIME_EPOCH=$(date +%s)
START_TIME_HUMAN=$(date +"%Y-%m-%d %H:%M:%S %Z")
LOG_FILE_TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S") # Timestamp for the log filename
LOG_FILE="${LOG_DIR}/${LOG_BASE_NAME}_${LOG_FILE_TIMESTAMP}.log"

# --- Log Header Information (to file) ---
echo "==================================================" >> "${LOG_FILE}"
echo "Command:          ${COMMAND_TO_RUN[*]}" >> "${LOG_FILE}"
echo "Log File:         ${LOG_FILE}" >> "${LOG_FILE}"
echo "Process Started:  ${START_TIME_HUMAN}" >> "${LOG_FILE}"
echo "==================================================" >> "${LOG_FILE}"
echo "" >> "${LOG_FILE}" # Blank line for readability

# --- Terminal Header Information ---
echo "=================================================="
echo "Command:          ${COMMAND_TO_RUN[*]}"
echo "Log File:         ${LOG_FILE}"
echo "Process Started:  ${START_TIME_HUMAN}"
echo "=================================================="
echo # Blank line
echo "Please provide any required input in the terminal."
echo "Output from command follows:"
echo "--------------------------------------------------"

# --- Execute the Command ---
# tee -a appends to the log file, preserving the header we just wrote.
"${COMMAND_TO_RUN[@]}" 2>&1 | tee -a "${LOG_FILE}"
EXIT_STATUS=${PIPESTATUS[0]} # Capture exit status of the first command in pipeline (COMMAND_TO_RUN)

# --- Timing End & Duration Calculation ---
END_TIME_EPOCH=$(date +%s)
END_TIME_HUMAN=$(date +"%Y-%m-%d %H:%M:%S %Z")
DURATION_SECONDS=$((END_TIME_EPOCH - START_TIME_EPOCH))

if [ ${DURATION_SECONDS} -lt 60 ]; then
    DURATION_FORMATTED="${DURATION_SECONDS}s"
else
    DURATION_MINUTES=$((DURATION_SECONDS / 60))
    DURATION_REMAINING_SECONDS=$((DURATION_SECONDS % 60))
    DURATION_FORMATTED="${DURATION_MINUTES}m ${DURATION_REMAINING_SECONDS}s"
fi

# --- Log Footer Information (to file) ---
echo "" >> "${LOG_FILE}" # Blank line
echo "==================================================" >> "${LOG_FILE}"
echo "Process Ended:    ${END_TIME_HUMAN}" >> "${LOG_FILE}"
echo "Total Duration:   ${DURATION_FORMATTED} (${DURATION_SECONDS}s)" >> "${LOG_FILE}"
echo "Exit Status:      ${EXIT_STATUS}" >> "${LOG_FILE}"
echo "==================================================" >> "${LOG_FILE}"

# --- Terminal Footer Information ---
echo "--------------------------------------------------"
echo "Command output ended."
echo "=================================================="
echo "Process Ended:    ${END_TIME_HUMAN}"
echo "Total Duration:   ${DURATION_FORMATTED} (${DURATION_SECONDS}s)"
echo "Exit Status:      ${EXIT_STATUS}"
echo "=================================================="

# --- Log Rotation ---
MAX_LOGS=10
LOG_PATTERN="${LOG_BASE_NAME}_*.log"

log_files_to_consider=()
while IFS= read -r line; do
    log_files_to_consider+=("${line}")
done < <(ls -1t "${LOG_DIR}/${LOG_PATTERN}" 2>/dev/null || true)

num_log_files=${#log_files_to_consider[@]}

if [ "$num_log_files" -gt "$MAX_LOGS" ]; then
    echo "Rotating logs for '${LOG_BASE_NAME}'. Keeping the newest ${MAX_LOGS} log files."
    for (( i=MAX_LOGS; i<num_log_files; i++ )); do
        file_to_delete="${log_files_to_consider[$i]}"
        if [ -f "$file_to_delete" ]; then
            rm -- "$file_to_delete"
            echo "Deleted old log: $file_to_delete"
        fi
    done
fi

# --- Final Status & Exit ---
if [ ${EXIT_STATUS} -eq 0 ]; then
  echo "Successfully completed."
else
  echo "Execution failed. Please check the terminal output and the log."
fi
echo "Full log available at: ${LOG_FILE}"
echo "--------------------------------------------------"

exit ${EXIT_STATUS}
