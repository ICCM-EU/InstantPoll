VENV := . .venv/bin/activate &&

all:
	@echo "help:"
	@echo "  make quickstart"

quickstart: create_venv pip_packages create_db create_superuser
	@echo 
	@echo =====================================================================================
	@echo Installation has finished successfully

create_superuser:
	${VENV} echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(is_superuser=True).exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | python manage.py shell

pip_packages:
	${VENV} pip install --upgrade pip
	${VENV} pip install -r requirements.txt

create_venv:
	python3 -m venv .venv

create_db:
	if [ ! -f instantpoll/settings_local.py ]; then cp instantpoll/settings_local.py.example instantpoll/settings_local.py; fi
	${VENV} python manage.py migrate
	${VENV} python manage.py compilemessages

start_redis:
	sudo podman run -p 6379:6379 -d docker.io/library/redis:5

collectstatic:
	${VENV} (echo "yes" | python manage.py collectstatic)

runserver: collectstatic
	${VENV} python manage.py runserver localhost:8000

