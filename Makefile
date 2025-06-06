# Variables
SOLUTION_ZIP := solution.zip
# IMPORTANT: This MUST be the name of the single folder your packing script puts inside solution.zip.
# This is the folder that will be removed from testing_env before unzipping the new one.
TESTING_ENV_DIR := testing_env
TEST_SCRIPT := run_tests.py # Assumed to be at the root of LOGIN69 when unzipped

ALL : sssp_okeanos

.PHONY: test clean_test_env local

sssp_okeanos: src/main.cpp src/parse_data.cpp
	CC -std=c++17 -O3 -Wall -Werror $^ -o sssp -lm -Wno-sign-compare

local: src/main.cpp src/parse_data.cpp
	mpic++ -std=c++17 -O3 -Wall -Werror $^ -o sssp -lm -Wno-sign-compare

unit_test: src/unit_tests.cpp src/common.hpp src/block_dist.hpp
	mpic++ -std=c++17 -g -Wall -Werror src/unit_tests.cpp -o $@ -lm -fsanitize=undefined,address -fno-omit-frame-pointer

# Primary rule to test the solution
test: $(SOLUTION_ZIP)
	@echo "--- Testing Solution ---"
	@echo "Calculating SHA256 sum of $(SOLUTION_ZIP)..."
	sha256sum $(SOLUTION_ZIP)

	@echo "Cleaning up previous solution artifacts in $(TESTING_ENV_DIR)/..."
	# Remove the old zip file from the testing environment, if it's there
	rm -f "$(TESTING_ENV_DIR)/$(SOLUTION_ZIP)"
	# Remove the old extracted solution folder from the testing environment, if it's there
	if [ -d "$(TESTING_ENV_DIR)/LOGIN69" ]; then \
		echo "Removing old solution folder: $(TESTING_ENV_DIR)/LOGIN69"; \
		rm -rf "$(TESTING_ENV_DIR)/LOGIN69"; \
	fi

	@echo "Copying $(SOLUTION_ZIP) to $(TESTING_ENV_DIR)/..."
	cp $(SOLUTION_ZIP) $(TESTING_ENV_DIR)/

	@echo "Unzipping $(SOLUTION_ZIP) in $(TESTING_ENV_DIR)/..."
	# -q quiet
	# -d $(TESTING_ENV_DIR) extracts files into this directory
	unzip -q $(TESTING_ENV_DIR)/$(SOLUTION_ZIP) -d $(TESTING_ENV_DIR)

	@echo "Removing old testing env"
	ssh okeanos "rm -rf testing_env"
	@echo "Uploading new testing env to okeanos"
	scp -rq testing_env okeanos:
	@echo "Done! Files ready to test at remote"


test-local: $(SOLUTION_ZIP)
	@echo "--- Testing Solution ---"
	@echo "Calculating SHA256 sum of $(SOLUTION_ZIP)..."
	sha256sum $(SOLUTION_ZIP)

	@echo "Cleaning up previous solution artifacts in $(TESTING_ENV_DIR)/..."
	# Remove the old zip file from the testing environment, if it's there
	rm -f "$(TESTING_ENV_DIR)/$(SOLUTION_ZIP)"
	# Remove the old extracted solution folder from the testing environment, if it's there
	if [ -d "$(TESTING_ENV_DIR)/LOGIN69" ]; then \
		echo "Removing old solution folder: $(TESTING_ENV_DIR)/LOGIN69"; \
		rm -rf "$(TESTING_ENV_DIR)/LOGIN69"; \
	fi

	@echo "Copying $(SOLUTION_ZIP) to $(TESTING_ENV_DIR)/..."
	cp $(SOLUTION_ZIP) $(TESTING_ENV_DIR)/

	@echo "Unzipping $(SOLUTION_ZIP) in $(TESTING_ENV_DIR)/..."
	# -q quiet
	# -d $(TESTING_ENV_DIR) extracts files into this directory
	unzip -q $(TESTING_ENV_DIR)/$(SOLUTION_ZIP) -d $(TESTING_ENV_DIR)

	@echo "Running tests in $(TESTING_ENV_DIR)/ ..."
	cd $(TESTING_ENV_DIR) && python3 $(TEST_SCRIPT) -l
	@echo "--- Testing Complete ---"


test-okeanos: $(SOLUTION_ZIP)
	@echo "--- Testing Solution ---"
	@echo "Calculating SHA256 sum of $(SOLUTION_ZIP)..."
	sha256sum $(SOLUTION_ZIP)

	@echo "Cleaning up previous solution artifacts in $(TESTING_ENV_DIR)/..."
	# Remove the old zip file from the testing environment, if it's there
	rm -f "$(TESTING_ENV_DIR)/$(SOLUTION_ZIP)"
	# Remove the old extracted solution folder from the testing environment, if it's there
	if [ -d "$(TESTING_ENV_DIR)/LOGIN69" ]; then \
		echo "Removing old solution folder: $(TESTING_ENV_DIR)/LOGIN69"; \
		rm -rf "$(TESTING_ENV_DIR)/LOGIN69"; \
	fi
	# Remove the old artifacts
	rm -f "$(TESTING_ENV_DIR)/LOGIN69/core";
	rm -f "$(TESTING_ENV_DIR)/LOGIN69/debug_log_*.txt";
	rm -f "$(TESTING_ENV_DIR)/outputs/*";
	rm -f "$(TESTING_ENV_DIR)/LOGIN69/output.txt";

	@echo "Copying $(SOLUTION_ZIP) to $(TESTING_ENV_DIR)/..."
	cp $(SOLUTION_ZIP) $(TESTING_ENV_DIR)/

	@echo "Unzipping $(SOLUTION_ZIP) in $(TESTING_ENV_DIR)/..."
	# -q quiet
	# -d $(TESTING_ENV_DIR) extracts files into this directory
	unzip -q $(TESTING_ENV_DIR)/$(SOLUTION_ZIP) -d $(TESTING_ENV_DIR)

	@echo "Running tests in $(TESTING_ENV_DIR)/ ..."
	cd $(TESTING_ENV_DIR) && sbatch sbatch_run_tests.sh
	@echo "--- Testing Complete ---"

solution.zip: pack.sh $(shell find src -type f) Makefile
	bash pack.sh LOGIN69

# Phony target to clean the testing environment's solution artifacts only
# This does NOT remove other scripts/files in TESTING_ENV_DIR.
clean_test_env:
	@echo "Cleaning solution artifacts from testing environment $(TESTING_ENV_DIR)..."
	rm -f $(TESTING_ENV_DIR)/$(SOLUTION_ZIP)
	if [ -d "$(TESTING_ENV_DIR)/LOGIN69" ]; then \
		echo "Removing solution folder: $(TESTING_ENV_DIR)/LOGIN69"; \
		rm -rf "$(TESTING_ENV_DIR)/LOGIN69"; \
	fi
	rm $(TESTING_ENV_DIR)/output.txt  $(TESTING_ENV_DIR)/debug_log_*.txt

	@echo "Solution artifacts cleaned from testing environment."

# Example of a more general clean rule
# clean:
#   # ... your other clean commands for build artifacts ...
#   $(MAKE) clean_test_env