all: build

GOLANGCI_LINT_VERSION="v2.2.1"

# Setup test packages
TEST_PACKAGES = ./internal/...

test:
	go test -count=1 -race $(TEST_PACKAGES)

lint:
	@if [ ! -f ./bin/golangci-lint ]; then \
		curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s $(GOLANGCI_LINT_VERSION); \
	fi;
	@echo "golangci-lint checking..."
	@./bin/golangci-lint -v run $(TEST_PACKAGES)
