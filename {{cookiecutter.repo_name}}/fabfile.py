from datetime import datetime

from fabric.api import *


env.roledefs = {
    'production': [],
    'staging': [],
    'demo': ['dokku@demo.torchboxapps.com'],
}


@roles('production')
def deploy_production():
    # Remove this line when you're happy that this task is correct
    raise RuntimeError("Please check the fabfile before using it")

    run('git pull origin master')
    run('pip install -r requirements.txt')
    run('django-admin migrate --noinput')
    run('django-admin collectstatic --noinput')
    run('django-admin compress')
    run('django-admin update_index')

    # 'restart' should be an alias to a script that restarts the web server
    run('restart')


@roles('staging')
def deploy_staging():
    # Remove this line when you're happy that this task is correct
    raise RuntimeError("Please check the fabfile before using it")

    run('git pull origin staging')
    run('pip install -r requirements.txt')
    run('django-admin migrate --noinput')
    run('django-admin collectstatic --noinput')
    run('django-admin compress')
    run('django-admin update_index')

    # 'restart' should be an alias to a script that restarts the web server
    run('restart')


def _pull_data(env_name, remote_db_name, local_db_name, remote_dump_path, local_dump_path):
    timestamp = datetime.now().strftime('%Y%m%d-%I%M%S')

    filename = '.'.join([env_name, remote_db_name, timestamp, 'sql'])
    remote_filename = remote_dump_path + filename
    local_filename = local_dump_path + filename

    params = {
        'remote_db_name': remote_db_name,
        'remote_filename': remote_filename,
        'local_db_name': local_db_name,
        'local_filename': local_filename,
    }

    # Dump/download database from server
    run('pg_dump {remote_db_name} -xOf {remote_filename}'.format(**params))
    run('gzip {remote_filename}'.format(**params))
    get('{remote_filename}.gz'.format(**params), '{local_filename}.gz'.format(**params))
    run('rm {remote_filename}.gz'.format(**params))

    # Load database locally
    local('gunzip {local_filename}.gz'.format(**params))
    local('dropdb {local_db_name}'.format(**params))
    local('createdb {local_db_name}'.format(**params))
    local('psql {local_db_name} -f {local_filename}'.format(**params))
    local('rm {local_filename}'.format(**params))


@roles('production')
def pull_production_data():
    # Remove this line when you're happy that this task is correct
    raise RuntimeError("Please check the fabfile before using it")

    _pull_data(
        env_name='production',
        remote_db_name='{{ cookiecutter.repo_name }}',
        local_db_name='{{ cookiecutter.repo_name }}',
        remote_dump_path='/usr/local/django/{{ cookiecutter.repo_name }}/tmp/',
        local_dump_path='/tmp/',
    )


@roles('staging')
def pull_staging_data():
    # Remove this line when you're happy that this task is correct
    raise RuntimeError("Please check the fabfile before using it")

    _pull_data(
        env_name='staging',
        remote_db_name='{{ cookiecutter.repo_name }}',
        local_db_name='{{ cookiecutter.repo_name }}',
        remote_dump_path='/usr/local/django/{{ cookiecutter.repo_name }}/tmp/',
        local_dump_path='/tmp/',
    )


def dokku(command, **kwargs):
    kwargs.setdefault('shell', False)
    return run(command, **kwargs)


class DemoEnvironment(object):

    def __init__(self, app, branch):
        self.app = app
        self.branch = branch
        self.name = app + '-' + branch.replace('/', '-')

    def set_config(self, config):
        config_string = ' '.join([
            name + '=' + value
            for name, value in config.items()
        ])
        dokku('config:set %s %s' % (self.name, config_string), warn_only=True)

    def run(self, command, interactive=False):
        dokku('run %s %s' % (self.name, command))

    def django_admin(self, command, interactive=False):
        self.run('django-admin %s' % command, interactive=interactive)

    def push(self):
        local('git push %s:%s %s:master' % (env['host_string'], self.name, self.branch))

    def push_postgres_data(self, localdb):
        local('pg_dump -c --no-acl --no-owner %s | ssh %s "postgres:connect %s"' % (localdb, env['host_string'], self.name))
        self.django_admin('migrate')
        self.django_admin('update_index')

    def exists(self):
        return dokku('config %s' % self.name, quiet=True).succeeded

    def create(self):
        # Create app
        dokku('apps:create %s' % self.name)

        # Create database
        dokku('postgres:create %s' % self.name)
        dokku('postgres:link %s %s' % (self.name, self.name))

        # Create redis instance
        dokku('redis:create %s' % self.name)
        dokku('redis:link %s %s' % (self.name, self.name))

        # Link to central Elasticsearch instance
        dokku('elasticsearch:link elasticsearch %s' % self.name)

        # Create volume for media
        # dokku('volume:create %s /app/media/' % self.name)
        # dokku('volume:link %s %s' % (self.name, self.name))

        # Extra configuration
        self.set_config({
            'APP_NAME': self.name,
            'DJANGO_SETTINGS_MODULE': '{{ cookiecutter.repo_name }}.settings.production',
            'SECRET_KEY': 'demo',
            'ALLOWED_HOSTS': self.name + '.demo.torchboxapps.com'
        })

    def update(self):
        self.push()
        self.django_admin('migrate')
        self.django_admin('update_index')


@roles('demo')
def demo(subcommand='deploy'):
    branch = local('git branch | grep "^*" | cut -d" " -f2', capture=True)

    env = DemoEnvironment('{{ cookiecutter.repo_name }}', branch)

    if subcommand == 'deploy':
        # Create the environment
        if not env.exists():
            print("Creating demo environment for %s..." % branch)
            env.create()

        # Update it
        print("Updating demo environment...")
        env.update()
    elif subcommand == 'pushdb':
        # Check the environment exists
        if not env.exists():
            raise Exception("Demo environment doesn't exist yet. Please run 'fab demo' first.")

        # Push data
        env.push_postgres_data(localdb='{{ cookiecutter.repo_name }}')
    else:
        raise Exception("Unrecognised command: " + subcommand)
