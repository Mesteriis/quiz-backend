# Quiz App Makefile - Complete Development Automation 🚀
# Compatible with UV package manager

# Colors for beautiful output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
WHITE := \033[37m
RESET := \033[0m
BOLD := \033[1m

# Emojis for fancy output
ROCKET := 🚀
GEAR := ⚙️
CHECK := ✅
CROSS := ❌
PACKAGE := 📦
TEST := 🧪
CLEAN := 🧹
DOC := 📚
SECURITY := 🔒
MONITOR := 📊

# Project settings
PROJECT_NAME := quiz-app
PYTHON_VERSION := 3.11
BACKEND_PORT := 8000
FRONTEND_PORT := 3000

# Virtual environment
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UV := uv

# Check if uv is installed
UV_CHECK := $(shell command -v uv 2> /dev/null)

.PHONY: help
help: ## Show this help message
	@echo "$(BOLD)$(BLUE)$(PROJECT_NAME) Development Commands $(ROCKET)$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BOLD)Examples:$(RESET)"
	@echo "  $(GREEN)make setup$(RESET)           - Full project initialization"
	@echo "  $(GREEN)make dev$(RESET)             - Start development server"
	@echo "  $(GREEN)make test$(RESET)            - Run all tests"
	@echo "  $(GREEN)make lint$(RESET)            - Run code quality checks"

# ================================
# 🚀 SETUP AND INITIALIZATION
# ================================

.PHONY: check-uv
check-uv: ## Check if UV is installed
ifndef UV_CHECK
	@echo "$(RED)$(CROSS) UV is not installed!$(RESET)"
	@echo "$(YELLOW)Install UV: curl -LsSf https://astral.sh/uv/install.sh | sh$(RESET)"
	@exit 1
else
	@echo "$(GREEN)$(CHECK) UV is installed$(RESET)"
endif

.PHONY: setup
setup: check-uv ## 🚀 Complete project setup
	@echo "$(BOLD)$(BLUE)$(ROCKET) Setting up Quiz App development environment...$(RESET)"
	$(UV) venv --python $(PYTHON_VERSION)
	$(UV) sync --dev
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)$(GEAR) Creating .env file from example...$(RESET)"; \
		cp env.example .env; \
	fi
	$(MAKE) install-hooks
	$(MAKE) migrate-up
	@echo "$(GREEN)$(CHECK) Setup complete! Run 'make dev' to start development$(RESET)"

.PHONY: setup-clean
setup-clean: clean check-uv ## 🧹 Clean setup (removes venv and reinstalls)
	@echo "$(BOLD)$(YELLOW)$(CLEAN) Clean setup - removing existing environment...$(RESET)"
	rm -rf $(VENV)
	$(MAKE) setup

.PHONY: install-hooks
install-hooks: ## Install pre-commit hooks
	@echo "$(BLUE)$(GEAR) Installing pre-commit hooks...$(RESET)"
	$(UV) run pre-commit install
	@echo "$(GREEN)$(CHECK) Pre-commit hooks installed$(RESET)"

# ================================
# 🏃‍♂️ DEVELOPMENT SERVERS
# ================================

.PHONY: dev
dev: ## 🚀 Start backend development server
	@echo "$(BOLD)$(GREEN)$(ROCKET) Starting Quiz App backend server...$(RESET)"
	$(UV) run uvicorn src.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

.PHONY: dev-prod
dev-prod: ## Start backend in production mode
	@echo "$(BOLD)$(GREEN)$(ROCKET) Starting Quiz App in production mode...$(RESET)"
	$(UV) run uvicorn src.main:app --host 0.0.0.0 --port $(BACKEND_PORT) --workers 4

.PHONY: dev-debug
dev-debug: ## Start backend with debug logging
	@echo "$(BOLD)$(YELLOW)$(GEAR) Starting Quiz App with debug logging...$(RESET)"
	DEBUG=true LOG_LEVEL=DEBUG $(UV) run uvicorn src.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

# ================================
# 🧪 TESTING WITH POLYFACTORY
# ================================

.PHONY: test
test: ## 🧪 Run all tests
	@echo "$(BOLD)$(BLUE)$(TEST) Running all tests...$(RESET)"
	$(UV) run pytest

.PHONY: test-with-file-db
test-with-file-db: ## 🗄️ Run tests with file database for analysis
	@echo "$(BOLD)$(BLUE)$(TEST) Running tests with file database...$(RESET)"
	TEST_USE_FILE_DB=true $(UV) run pytest -v
	@echo "$(GREEN)$(CHECK) Test database files available in tests/data/$(RESET)"

.PHONY: test-fast
test-fast: ## ⚡ Run tests with in-memory database (fast)
	@echo "$(BOLD)$(BLUE)$(TEST) Running fast tests with in-memory database...$(RESET)"
	TEST_USE_FILE_DB=false $(UV) run pytest

.PHONY: analyze-test-db
analyze-test-db: ## 🔍 Analyze the latest test database
	@echo "$(BOLD)$(CYAN)$(GEAR) Analyzing latest test database...$(RESET)"
	@latest_db=$$(ls tests/data/quiz_test_*.db 2>/dev/null | sort -n | tail -1); \
	if [ -n "$$latest_db" ]; then \
		echo "$(GREEN)$(CHECK) Opening: $$latest_db$(RESET)"; \
		sqlite3 "$$latest_db" ".schema" | head -20; \
		echo ""; \
		echo "$(YELLOW)Available tables:$(RESET)"; \
		sqlite3 "$$latest_db" ".tables"; \
		echo ""; \
		echo "$(BLUE)Recent users:$(RESET)"; \
		sqlite3 "$$latest_db" "SELECT id, username, email, is_active FROM users ORDER BY created_at DESC LIMIT 5;" 2>/dev/null || echo "No users table"; \
		echo ""; \
		echo "$(BLUE)Recent surveys:$(RESET)"; \
		sqlite3 "$$latest_db" "SELECT id, title, is_public, is_active FROM surveys ORDER BY created_at DESC LIMIT 5;" 2>/dev/null || echo "No surveys table"; \
	else \
		echo "$(RED)$(CROSS) No test database files found$(RESET)"; \
		echo "$(YELLOW)Run 'make test-with-file-db' first$(RESET)"; \
	fi

.PHONY: clean-test-dbs
clean-test-dbs: ## 🧹 Clean old test database files
	@echo "$(BOLD)$(YELLOW)$(CLEAN) Cleaning old test database files...$(RESET)"
	@if ls tests/data/quiz_test_*.db 1> /dev/null 2>&1; then \
		rm -f tests/data/quiz_test_*.db; \
		echo "$(GREEN)$(CHECK) Test database files cleaned$(RESET)"; \
	else \
		echo "$(BLUE)ℹ️  No test database files to clean$(RESET)"; \
	fi

.PHONY: install-polyfactory
install-polyfactory: ## 📦 Install or update Polyfactory
	@echo "$(BOLD)$(BLUE)$(PACKAGE) Installing/updating Polyfactory...$(RESET)"
	$(UV) add polyfactory
	@echo "$(GREEN)$(CHECK) Polyfactory installed$(RESET)"

.PHONY: test-factories
test-factories: ## 🏭 Test factory functionality
	@echo "$(BOLD)$(BLUE)$(TEST) Testing factory functionality...$(RESET)"
	$(UV) run python -c "from tests.factories.users import UserModelFactory; print('✅ User factory works:', UserModelFactory.build().username)"
	$(UV) run python -c "from tests.factories.surveys import SurveyModelFactory; print('✅ Survey factory works:', SurveyModelFactory.build(created_by=1).title)"
	@echo "$(GREEN)$(CHECK) All factories working correctly$(RESET)"

.PHONY: demo-factories
demo-factories: ## 🎭 Demonstrate factory capabilities
	@echo "$(BOLD)$(MAGENTA)$(GEAR) Polyfactory Demo...$(RESET)"
	@echo ""
	@echo "$(BOLD)$(BLUE)👥 User Factories:$(RESET)"
	$(UV) run python -c "\
from tests.factories.users import UserModelFactory, AdminUserModelFactory, TelegramUserModelFactory; \
user = UserModelFactory.build(); \
admin = AdminUserModelFactory.build(); \
tg_user = TelegramUserModelFactory.build(); \
print(f'📝 Regular User: {user.username} ({user.email})'); \
print(f'👑 Admin User: {admin.username} (admin: {admin.is_admin})'); \
print(f'📱 Telegram User: {tg_user.username} (tg_id: {tg_user.telegram_id})'); \
"
	@echo ""
	@echo "$(BOLD)$(GREEN)📊 Survey Factories:$(RESET)"
	$(UV) run python -c "\
from tests.factories.surveys import SurveyModelFactory, PublicSurveyModelFactory; \
survey = SurveyModelFactory.build(created_by=1); \
public = PublicSurveyModelFactory.build(created_by=1); \
print(f'📋 Survey: {survey.title[:50]}...'); \
print(f'🌍 Public Survey: {public.title[:50]}... (public: {public.is_public})'); \
"
	@echo ""
	@echo "$(BOLD)$(CYAN)🎯 Pydantic Factories:$(RESET)"
	$(UV) run python -c "\
from tests.factories.users import UserCreateDataFactory, ValidUserCreateDataFactory; \
create_data = UserCreateDataFactory.build(); \
valid_data = ValidUserCreateDataFactory.build(); \
print(f'📝 Create Data: {create_data.username} ({create_data.email})'); \
print(f'✅ Valid Data: {valid_data.username} ({valid_data.email})'); \
"
	@echo "$(GREEN)$(CHECK) Demo complete! Factories working perfectly$(RESET)"

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(BLUE)$(TEST) Running unit tests...$(RESET)"
	$(UV) run pytest tests/unit/ -v

.PHONY: test-integration
test-integration: ## Run integration tests only
	@echo "$(BLUE)$(TEST) Running integration tests...$(RESET)"
	$(UV) run pytest tests/integration/ -v

.PHONY: test-e2e
test-e2e: ## Run e2e tests only
	@echo "$(BLUE)$(TEST) Running E2E tests...$(RESET)"
	$(UV) run pytest tests/e2e/ -v

.PHONY: test-cov
test-cov: ## 🧪 Run tests with coverage
	@echo "$(BOLD)$(BLUE)$(TEST) Running tests with coverage...$(RESET)"
	$(UV) run pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)$(CHECK) Coverage report: htmlcov/index.html$(RESET)"

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	@echo "$(BLUE)$(TEST) Running tests in watch mode...$(RESET)"
	$(UV) run pytest-watch

.PHONY: test-parallel
test-parallel: ## Run tests in parallel
	@echo "$(BLUE)$(TEST) Running tests in parallel...$(RESET)"
	$(UV) run pytest -n auto

.PHONY: test-performance
test-performance: ## Run performance tests
	@echo "$(BLUE)$(TEST) Running performance tests...$(RESET)"
	$(UV) run locust --host=http://localhost:$(BACKEND_PORT)

.PHONY: test-quick
test-quick:
	@echo "⚡ Быстрые тесты с timeout..."
	$(UV) run pytest -xvs --timeout=15 --timeout-method=thread tests/unit/

.PHONY: test-no-hang
test-no-hang:
	@echo "🚫 Тесты без зависания (короткий timeout)..."
	$(UV) run pytest -xvs --timeout=10 --timeout-method=thread --tb=short tests/unit/

.PHONY: test-debug
test-debug:
	@echo "🔍 Отладочные тесты..."
	$(UV) run pytest -xvs --timeout=30 --timeout-method=thread --tb=long --capture=no

.PHONY: test-specific
test-specific:
	@echo "🎯 Запуск конкретного теста..."
	@read -p "Укажите путь к тесту (например: tests/unit/test_auth_router.py::TestLogin::test_login_success): " test_path; \
	$(UV) run pytest -xvs --timeout=15 --timeout-method=thread "$$test_path"

.PHONY: test-single-router
test-single-router:
	@echo "🎯 Тестирование одного роутера..."
	@read -p "Укажите имя роутера (например: auth, admin, surveys): " router_name; \
	$(UV) run pytest -xvs --timeout=10 --timeout-method=thread --tb=short tests/unit/test_$${router_name}_router.py

.PHONY: test-ultra-quick
test-ultra-quick:
	@echo "⚡ Сверхбыстрое тестирование auth роутера..."
	$(UV) run pytest -xvs --timeout=5 --timeout-method=thread --tb=short tests/unit/test_auth_router.py

.PHONY: test-one-class
test-one-class:
	@echo "🔍 Тестирование одного класса..."
	@read -p "Укажите путь к классу (например: tests/unit/test_auth_router.py::TestRegistration): " class_path; \
	$(UV) run pytest -xvs --timeout=8 --timeout-method=thread --tb=short "$$class_path"

# ================================
# 🔍 CODE QUALITY
# ================================

.PHONY: lint
lint: ## 🔍 Run all linting tools
	@echo "$(BOLD)$(BLUE)$(GEAR) Running code quality checks...$(RESET)"
	$(MAKE) format-check
	$(MAKE) ruff-check
	$(MAKE) mypy-check
	@echo "$(GREEN)$(CHECK) All linting passed!$(RESET)"

.PHONY: format
format: ## Format code with black and ruff
	@echo "$(BLUE)$(GEAR) Formatting code...$(RESET)"
	$(UV) run black .
	$(UV) run ruff --fix .
	@echo "$(GREEN)$(CHECK) Code formatted$(RESET)"

.PHONY: format-check
format-check: ## Check code formatting
	@echo "$(BLUE)$(GEAR) Checking code formatting...$(RESET)"
	$(UV) run black --check .

.PHONY: ruff-check
ruff-check: ## Run Ruff linter
	@echo "$(BLUE)$(GEAR) Running Ruff checks...$(RESET)"
	$(UV) run ruff check .

.PHONY: ruff-fix
ruff-fix: ## Fix Ruff issues
	@echo "$(BLUE)$(GEAR) Fixing Ruff issues...$(RESET)"
	$(UV) run ruff --fix .

.PHONY: mypy-check
mypy-check: ## Run MyPy type checking
	@echo "$(BLUE)$(GEAR) Running MyPy type checking...$(RESET)"
	$(UV) run mypy .

# ================================
# 🔒 SECURITY
# ================================

.PHONY: security
security: ## 🔒 Run security checks
	@echo "$(BOLD)$(RED)$(SECURITY) Running security checks...$(RESET)"
	$(MAKE) bandit-check
	$(MAKE) safety-check
	@echo "$(GREEN)$(CHECK) Security checks passed!$(RESET)"

.PHONY: bandit-check
bandit-check: ## Run Bandit security scanner
	@echo "$(RED)$(SECURITY) Running Bandit security scanner...$(RESET)"
	$(UV) run bandit -r . -f json -o bandit-report.json || echo "$(YELLOW)Bandit found some issues, check bandit-report.json$(RESET)"

.PHONY: safety-check
safety-check: ## Check dependencies for security vulnerabilities
	@echo "$(RED)$(SECURITY) Checking dependencies for vulnerabilities...$(RESET)"
	$(UV) run safety check

# ================================
# 🗄️ DATABASE OPERATIONS
# ================================

.PHONY: migrate-create
migrate-create: ## Create new database migration
	@echo "$(BLUE)$(GEAR) Creating new migration...$(RESET)"
	@read -p "Migration message: " msg; \
	$(UV) run alembic revision --autogenerate -m "$$msg"

.PHONY: migrate-up
migrate-up: ## Apply database migrations
	@echo "$(BLUE)$(GEAR) Applying database migrations...$(RESET)"
	$(UV) run alembic upgrade head
	@echo "$(GREEN)$(CHECK) Migrations applied$(RESET)"

.PHONY: migrate-down
migrate-down: ## Rollback last migration
	@echo "$(YELLOW)$(GEAR) Rolling back last migration...$(RESET)"
	$(UV) run alembic downgrade -1

.PHONY: migrate-status
migrate-status: ## Show migration status
	@echo "$(BLUE)$(GEAR) Migration status:$(RESET)"
	$(UV) run alembic current
	$(UV) run alembic history

.PHONY: migrate-reset
migrate-reset: ## Reset database (DROP ALL DATA!)
	@echo "$(RED)$(CROSS) WARNING: This will DELETE ALL DATA!$(RESET)"
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		$(UV) run alembic downgrade base; \
		$(UV) run alembic upgrade head; \
		echo "$(GREEN)$(CHECK) Database reset complete$(RESET)"; \
	else \
		echo "$(YELLOW)Operation cancelled$(RESET)"; \
	fi

# ================================
# 🐳 DOCKER OPERATIONS
# ================================

.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "$(BLUE)$(PACKAGE) Building Docker image...$(RESET)"
	docker build -t $(PROJECT_NAME):latest .
	@echo "$(GREEN)$(CHECK) Docker image built$(RESET)"

.PHONY: docker-run
docker-run: ## Run Docker container
	@echo "$(BLUE)$(ROCKET) Running Docker container...$(RESET)"
	docker run -p $(BACKEND_PORT):$(BACKEND_PORT) --env-file .env $(PROJECT_NAME):latest

.PHONY: docker-compose-up
docker-compose-up: ## Start all services with docker-compose
	@echo "$(BLUE)$(ROCKET) Starting all services...$(RESET)"
	docker-compose up -d
	@echo "$(GREEN)$(CHECK) All services started$(RESET)"

.PHONY: docker-compose-down
docker-compose-down: ## Stop all services
	@echo "$(YELLOW)$(GEAR) Stopping all services...$(RESET)"
	docker-compose down

.PHONY: docker-compose-logs
docker-compose-logs: ## Show docker-compose logs
	docker-compose logs -f

# ================================
# 📚 DOCUMENTATION
# ================================

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	@echo "$(BLUE)$(DOC) Serving documentation...$(RESET)"
	$(UV) run mkdocs serve

.PHONY: docs-build
docs-build: ## Build documentation
	@echo "$(BLUE)$(DOC) Building documentation...$(RESET)"
	$(UV) run mkdocs build

.PHONY: docs-deploy
docs-deploy: ## Deploy documentation to GitHub Pages
	@echo "$(BLUE)$(DOC) Deploying documentation...$(RESET)"
	$(UV) run mkdocs gh-deploy

# ================================
# 📊 MONITORING
# ================================

.PHONY: monitor
monitor: ## 📊 Start monitoring stack
	@echo "$(BOLD)$(MAGENTA)$(MONITOR) Starting monitoring stack...$(RESET)"
	docker-compose -f docker-compose.yml up -d prometheus grafana
	@echo "$(GREEN)$(CHECK) Monitoring available at:$(RESET)"
	@echo "  $(CYAN)Prometheus: http://localhost:9090$(RESET)"
	@echo "  $(CYAN)Grafana: http://localhost:3000$(RESET)"

.PHONY: logs
logs: ## Show application logs
	@echo "$(BLUE)$(GEAR) Showing application logs...$(RESET)"
	tail -f logs/*.log 2>/dev/null || echo "$(YELLOW)No log files found$(RESET)"

# ================================
# 🧹 CLEANUP
# ================================

.PHONY: clean
clean: ## 🧹 Clean build artifacts and cache
	@echo "$(BOLD)$(YELLOW)$(CLEAN) Cleaning build artifacts...$(RESET)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf bandit-report.json
	@echo "$(GREEN)$(CHECK) Cleanup complete$(RESET)"

.PHONY: clean-all
clean-all: clean ## 🧹 Deep clean (includes venv and node_modules)
	@echo "$(BOLD)$(RED)$(CLEAN) Deep cleaning...$(RESET)"
	rm -rf $(VENV)
	rm -rf node_modules/
	@echo "$(GREEN)$(CHECK) Deep cleanup complete$(RESET)"

# ================================
# 📦 PACKAGE MANAGEMENT
# ================================

.PHONY: deps-install
deps-install: ## Install dependencies
	@echo "$(BLUE)$(PACKAGE) Installing dependencies...$(RESET)"
	$(UV) sync

.PHONY: deps-update
deps-update: ## Update dependencies
	@echo "$(BLUE)$(PACKAGE) Updating dependencies...$(RESET)"
	$(UV) sync --upgrade

.PHONY: deps-add
deps-add: ## Add new dependency (usage: make deps-add PACKAGE=package-name)
	@echo "$(BLUE)$(PACKAGE) Adding dependency: $(PACKAGE)$(RESET)"
	$(UV) add $(PACKAGE)

.PHONY: deps-add-dev
deps-add-dev: ## Add development dependency
	@echo "$(BLUE)$(PACKAGE) Adding dev dependency: $(PACKAGE)$(RESET)"
	$(UV) add --dev $(PACKAGE)

.PHONY: deps-remove
deps-remove: ## Remove dependency
	@echo "$(BLUE)$(PACKAGE) Removing dependency: $(PACKAGE)$(RESET)"
	$(UV) remove $(PACKAGE)

.PHONY: deps-check
deps-check: ## Check dependency conflicts
	@echo "$(BLUE)$(PACKAGE) Checking dependencies...$(RESET)"
	$(UV) pip check

# ================================
# 🎯 SHORTCUTS AND UTILITIES
# ================================

.PHONY: shell
shell: ## Start interactive Python shell
	@echo "$(BLUE)$(GEAR) Starting Python shell...$(RESET)"
	$(UV) run python

.PHONY: notebook
notebook: ## Start Jupyter notebook
	@echo "$(BLUE)$(GEAR) Starting Jupyter notebook...$(RESET)"
	$(UV) run jupyter notebook

.PHONY: profile
profile: ## Profile application performance
	@echo "$(BLUE)$(GEAR) Profiling application...$(RESET)"
	$(UV) run py-spy top --pid $$(pgrep -f "uvicorn src.main:app")

.PHONY: check-ports
check-ports: ## Check if ports are available
	@echo "$(BLUE)$(GEAR) Checking ports...$(RESET)"
	@echo "Backend port $(BACKEND_PORT): $$(lsof -ti:$(BACKEND_PORT) && echo 'OCCUPIED' || echo 'FREE')"
	@echo "Frontend port $(FRONTEND_PORT): $$(lsof -ti:$(FRONTEND_PORT) && echo 'OCCUPIED' || echo 'FREE')"

.PHONY: env-info
env-info: ## Show environment information
	@echo "$(BOLD)$(CYAN)Environment Information:$(RESET)"
	@echo "  $(YELLOW)Project:$(RESET) $(PROJECT_NAME)"
	@echo "  $(YELLOW)Python:$(RESET) $$(python --version 2>/dev/null || echo 'Not found')"
	@echo "  $(YELLOW)UV:$(RESET) $$(uv --version 2>/dev/null || echo 'Not found')"
	@echo "  $(YELLOW)Backend Port:$(RESET) $(BACKEND_PORT)"
	@echo "  $(YELLOW)Virtual Env:$(RESET) $(VENV)"

# ================================
# 🎯 CI/CD HELPERS
# ================================

.PHONY: ci-install
ci-install: ## Install dependencies for CI
	$(UV) sync --dev

.PHONY: ci-test
ci-test: ## Run tests for CI
	$(UV) run pytest --cov=src --cov-report=xml --cov-report=term-missing

.PHONY: ci-lint
ci-lint: ## Run linting for CI
	$(UV) run black --check .
	$(UV) run ruff check .
	$(UV) run mypy .

.PHONY: ci-security
ci-security: ## Run security checks for CI
	$(UV) run bandit -r . -f json
	$(UV) run safety check

# ================================
# 🚀 TELEGRAM BOT
# ================================

.PHONY: bot-start
bot-start: ## Start Telegram bot in polling mode
	@echo "$(BLUE)$(ROCKET) Starting Telegram bot...$(RESET)"
	$(UV) run python src/telegram_bot_polling.py

.PHONY: bot-webhook
bot-webhook: ## Set up Telegram bot webhook
	@echo "$(BLUE)$(GEAR) Setting up Telegram webhook...$(RESET)"
	$(UV) run python -c "from services.telegram_service import setup_webhook; setup_webhook()"

# ================================
# 📝 MAINTENANCE
# ================================

.PHONY: backup-db
backup-db: ## Backup database
	@echo "$(BLUE)$(GEAR) Creating database backup...$(RESET)"
	cp quiz.db "quiz_backup_$$(date +%Y%m%d_%H%M%S).db" 2>/dev/null || echo "$(YELLOW)SQLite database not found$(RESET)"

.PHONY: restore-db
restore-db: ## Restore database from backup
	@echo "$(YELLOW)Available backups:$(RESET)"
	@ls -la quiz_backup_*.db 2>/dev/null || echo "$(YELLOW)No backups found$(RESET)"
	@read -p "Enter backup filename: " backup; \
	if [ -f "$$backup" ]; then \
		cp "$$backup" quiz.db; \
		echo "$(GREEN)$(CHECK) Database restored from $$backup$(RESET)"; \
	else \
		echo "$(RED)$(CROSS) Backup file not found$(RESET)"; \
	fi

# ================================
# 🎯 DEFAULT TARGET
# ================================

.DEFAULT_GOAL := help

# Make sure we display help if no target is specified
all: help

# 🚀 БЫСТРОЕ ТЕСТИРОВАНИЕ (без coverage)
.PHONY: test-fast test-auth-fast test-surveys-fast test-responses-fast test-all-fast

test-fast: ## Быстрые тесты без coverage
	@echo "🚀 Быстрое тестирование без coverage..."
	uv run pytest tests/unit/ -v --no-cov --tb=short

test-auth-fast: ## Быстрые тесты auth роутера
	@echo "🔐 Быстрые тесты auth роутера..."
	uv run pytest tests/unit/test_auth_router.py -v --no-cov --tb=short

test-surveys-fast: ## Быстрые тесты surveys роутера
	@echo "📋 Быстрые тесты surveys роутера..."
	uv run pytest tests/unit/test_surveys_router.py -v --no-cov --tb=short

test-responses-fast: ## Быстрые тесты responses роутера
	@echo "💬 Быстрые тесты responses роутера..."
	uv run pytest tests/unit/test_responses_router.py -v --no-cov --tb=short

test-all-fast: ## Быстрые тесты всех роутеров
	@echo "⚡ Быстрые тесты всех роутеров..."
	@echo "🔐 Auth Router:"
	@uv run pytest tests/unit/test_auth_router.py --no-cov --tb=no -q
	@echo "📋 Surveys Router:"
	@uv run pytest tests/unit/test_surveys_router.py --no-cov --tb=no -q
	@echo "💬 Responses Router:"
	@uv run pytest tests/unit/test_responses_router.py --no-cov --tb=no -q
	@echo "✅ Быстрое тестирование завершено!"
