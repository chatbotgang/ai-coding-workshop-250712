all: build

GIT_BRANCH=$(shell git branch | grep \* | cut -d ' ' -f2)
GIT_REV=$(shell git rev-parse HEAD | cut -c1-7)
BUILD_DATE=$(shell date +%Y-%m-%d.%H:%M:%S)
EXTRA_LD_FLAGS=-X main.AppVersion=${GIT_BRANCH}-${GIT_REV} -X main.AppBuild=${BUILD_DATE}

GOLANGCI_LINT_VERSION="v2.2.1"

# Setup test packages
TEST_PACKAGES = ./internal/...

clean:
	rm -rf bin/ cover.out

test:
	go test -count=1 -race $(TEST_PACKAGES)

test-verbose:
	go test -v -count=1 -race -cover -coverprofile cover.out $(TEST_PACKAGES)
	go tool cover -func=cover.out | tail -n 1

lint:
	@if [ ! -f ./bin/golangci-lint ]; then \
		curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s $(GOLANGCI_LINT_VERSION); \
	fi;
	@echo "golangci-lint checking..."
	@./bin/golangci-lint -v run $(TEST_PACKAGES) ./cmd/...

format:
	@if [ ! -f ./bin/golangci-lint ]; then \
		curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s $(GOLANGCI_LINT_VERSION); \
	fi;
	@echo "golangci-lint fixing..."
	@./bin/golangci-lint -v run --fix ./...

mock:
	@which mockgen > /dev/null || (echo "No mockgen installed. Try: go install github.com/golang/mock/mockgen@v1.6.0"; exit 1)
	@which gowrap > /dev/null || (echo "No gowrap installed. Try: go install github.com/hexdigest/gowrap/cmd/gowrap@v1.2.7"; exit 1)
	@echo "generating mocks..."
	@go generate ./...

build:
	go build -ldflags '${EXTRA_LD_FLAGS}' -o bin/app ./cmd/app

help: build
	./bin/app --help

run: build
	./bin/app \
	--env="staging" \
	--log_level="debug" \
	--port=8080
