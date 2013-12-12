# coding=utf-8
"""A Fabric file for carrying out various administrative tasks with InaSAFE.

Usage for localhost commands::

    fab -H localhost [command]
    fab -H 188.40.123.80:8697 show_environment

To run on a vagrant vhost do::

    fab vagrant [command]

e.g. ::

    fab vagrant show_environment

.. note:: Vagrant tasks will only run if they @task decorator is used on
    the function. See show_environment function below.

Tim Sutton, Jan 2013
"""

import os
from datetime import datetime

from fabric.api import fastprint, env, run, hide, sudo, cd, task, get, put
from fabric.colors import blue, red, green
from fabric.contrib.files import contains, exists, append, sed

import fabtools
from fabtools import require

# Don't remove even though its unused
# noinspection PyUnresolvedReferences
from fabtools.vagrant import vagrant
from fabgis.system import harden
from fabgis.qgis import install_qgis_master
# Global options
env.env_set = False


def _all():
    """Things to do regardless of whether command is local or remote."""
    if env.env_set:
        fastprint(green('Environment already set!\n'))
        return

    fastprint('Setting environment!\n')
    # Key is hostname as it resolves by running hostname directly on the server
    # value is desired web site url to publish the repo as.
    doc_site_names = {
        'waterfall': 'inasafe-docs.localhost',
        'spur': 'inasafe-docs.localhost',
        'maps.linfiniti.com': 'inasafe-docs.linfiniti.com',
        'linfiniti3': 'inasafe-docs.linfiniti.com',
        'linfiniti': 'inasafe-docs.linfiniti.com',
        #vagrant instance
        'inasafe': 'inasafe-docs.vagrant.localhost',
        'shiva': 'docs.inasafe.org'}
    repo_site_names = {
        'waterfall': 'inasafe-test.localhost',
        'spur': 'inasafe-test.localhost',
        'maps.linfiniti.com': 'inasafe-test.linfiniti.com',
        'linfiniti': 'inasafe-crisis.linfiniti.com',
        'linfiniti3': 'experimental.inasafe.org',
        #vagrant instance
        'inasafe': 'experimental.vagrant.localhost',
        'shiva': 'experimental.inasafe.org'}

    with hide('output'):
        env.user = run('whoami')
        env.hostname = run('hostname')
        if env.hostname not in repo_site_names:
            print 'Error: %s not in: \n%s' % (env.hostname, repo_site_names)
            exit()
        elif env.hostname not in doc_site_names:
            print 'Error: %s not in: \n%s' % (env.hostname, repo_site_names)
            exit()
        else:
            env.repo_site_name = repo_site_names[env.hostname]
            env.doc_site_name = doc_site_names[env.hostname]
            env.plugin_repo_path = '/home/web/inasafe-test'
            env.inasafe_docs_path = '/home/web/inasafe-docs'
            env.home = os.path.join('/home/', env.user)
            env.repo_path = os.path.join(env.home,
                                         'dev',
                                         'python')
            env.git_url = 'git://github.com/AIFDR/inasafe.git'
            env.repo_alias = 'inasafe-test'
            env.code_path = os.path.join(env.repo_path, env.repo_alias)

    env.env_set = True
    fastprint(blue('env.env_set = %s\n' % env.env_set))

###############################################################################
# Next section contains helper methods tasks
###############################################################################


def initialise_qgis_plugin_repo():
    """Initialise a QGIS plugin repo where we host test builds."""
    _all()
    sudo('apt-get update')
    fabtools.require.deb.package('libapache2-mod-wsgi')
    code_path = os.path.join(env.repo_path, env.repo_alias)
    local_path = '%s/scripts/test-build-repo' % code_path

    if not exists(env.plugin_repo_path):
        sudo('mkdir -p %s' % env.plugin_repo_path)
        sudo('chown %s.%s %s' % (env.user, env.user, env.plugin_repo_path))

    run('cp %s/plugin* %s' % (local_path, env.plugin_repo_path))
    run('cp %s/icon* %s' % (code_path, env.plugin_repo_path))
    run('cp %(local_path)s/inasafe-test.conf.templ '
        '%(local_path)s/inasafe-test.conf' % {'local_path': local_path})

    sed('%s/inasafe-test.conf' % local_path,
        'inasafe-test.linfiniti.com',
        env.repo_site_name)

    with cd('/etc/apache2/sites-available/'):
        if exists('inasafe-test.conf'):
            sudo('a2dissite inasafe-test.conf')
            fastprint('Removing old apache2 conf')
            sudo('rm inasafe-test.conf')

        sudo('ln -s %s/inasafe-test.conf .' % local_path)

    # Add a hosts entry for local testing - only really useful for localhost
    repo_hosts = '/etc/hosts'
    if not contains(repo_hosts, 'inasafe-test'):
        append(repo_hosts, '127.0.0.1 %s' % env.repo_site_name, use_sudo=True)

    sudo('a2ensite inasafe-test.conf')
    sudo('service apache2 reload')


def update_git_checkout(branch='master'):
    """Make sure there is a read only git checkout.

    :param branch: The name of the branch to build from. Defaults to 'master'.
    :type branch: str

    To run e.g.::

        fab -H 188.40.123.80:8697 remote update_git_checkout

    """
    _all()
    fabtools.require.deb.package('git')
    fastprint(green('Updating git checkout in %s\n' % env.repo_path))
    fastprint(green('Using branch: %s\n' % branch))
    if not exists(env.code_path):
        fastprint('Repo checkout does not exist, creating.')
        run('mkdir -p %s' % env.repo_path)
        with cd(env.repo_path):
            run('git clone %s %s' % (env.git_url, env.repo_alias))
    else:
        fastprint('Repo checkout does exist, updating.')
        with cd(env.code_path):
            # Get any updates first
            run('git fetch')
            # Get rid of any local changes
            run('git reset --hard')
            # Get back onto master branch
            run('git checkout master')
            # Remove any local changes in master
            run('git reset --hard')
            # Delete all local branches
            #run('git branch | grep -v \* | xargs git branch -D')

    with cd(env.code_path):
        if branch != 'master':
            run('git branch --track %s origin/%s' %
                (branch, branch))
            run('git checkout %s' % branch)
        else:
            run('git checkout master')
        run('git pull')


###############################################################################
# Next section contains actual tasks
###############################################################################


@task
def build_test_package(branch='master'):
    """Create a test package and publish it in our repo.

    :param branch: The name of the branch to build from. Defaults to 'master'.
    :type branch: str


    To run e.g.::

        fab -H 176.9.37.173:8697 build_test_package

        or to package up a specific branch (in this case minimum_needs)

        fab -H 176.9.37.173:8697 build_test_package:minimum_needs

    .. note:: Using the branch option will not work for branches older than 1.1
    """
    _all()
    show_environment()
    update_git_checkout(branch)
    initialise_qgis_plugin_repo()

    fabtools.require.deb.packages(['zip', 'make', 'gettext'])

    with cd(env.code_path):
        # Get git version and write it to a text file in case we need to cross
        # reference it for a user ticket.
        sha = run('git rev-parse HEAD > git_revision.txt')
        fastprint('Git revision: %s' % sha)

        get('metadata.txt', '/tmp/metadata.txt')
        metadata_file = file('/tmp/metadata.txt', 'rt')
        metadata_text = metadata_file.readlines()
        metadata_file.close()
        for line in metadata_text:
            line = line.rstrip()
            if 'version=' in line:
                plugin_version = line.replace('version=', '')
            if 'status=' in line:
                line.replace('status=', '')

        # noinspection PyUnboundLocalVariable
        run('scripts/release.sh %s' % plugin_version)
        package_name = '%s.%s.zip' % ('inasafe', plugin_version)
        source = '/tmp/%s' % package_name
        fastprint(blue('Source: %s\n' % source))
        run('cp %s %s' % (source, env.plugin_repo_path))

        source = os.path.join('scripts', 'test-build-repo', 'plugins.xml')
        plugins_xml = os.path.join(env.plugin_repo_path, 'plugins.xml')
        fastprint(blue('Source: %s\n' % source))
        run('cp %s %s' % (source, plugins_xml))

        sed(plugins_xml, '\[VERSION\]', plugin_version)
        sed(plugins_xml, '\[FILE_NAME\]', package_name)
        sed(plugins_xml, '\[URL\]', 'http://%s/%s' %
                                    (env.repo_site_name, package_name))
        sed(plugins_xml, '\[DATE\]', str(datetime.now()))

        fastprint('Add http://%s/plugins.xml to QGIS plugin manager to use.'
                  % env.repo_site_name)


@task
def show_environment():
    """For diagnostics - show any pertinent info about server."""
    _all()
    fastprint('\n-------------------------------------------------\n')
    fastprint('User: %s\n' % env.user)
    fastprint('Host: %s\n' % env.hostname)
    fastprint('Site Name: %s\n' % env.repo_site_name)
    fastprint('Destination Path: %s\n' % env.plugin_repo_path)
    fastprint('Home Path: %s\n' % env.home)
    fastprint('Repo Path: %s\n' % env.repo_path)
    fastprint('Git Url: %s\n' % env.git_url)
    fastprint('Repo Alias: %s\n' % env.repo_alias)
    fastprint('-------------------------------------------------\n')


@task
def setup_jenkins_jobs():
    """Setup jenkins to run Continuous Integration Tests."""
    #fabgis.fabgis.initialise_jenkins_site()
    xvfb_config = "org.jenkinsci.plugins.xvfb.XvfbBuildWrapper.xml"
    job_dir = ['InaSAFE-master-QGIS1',
               'InaSAFE-master-QGIS2',
               'InaSAFE-release-QGIS1',
               'InaSAFE-release-QGIS2']

    with cd('/var/lib/jenkins/'):
        if not exists(xvfb_config):
            local_dir = os.path.dirname(__file__)
            local_file = os.path.abspath(os.path.join(
                local_dir,
                'scripts',
                'jenkins_jobs',
                xvfb_config))
            put(local_file,
                "/var/lib/jenkins/", use_sudo=True)

    with cd('/var/lib/jenkins/jobs/'):
        for job in job_dir:
            if not exists(job):
                local_dir = os.path.dirname(__file__)
                local_job_file = os.path.abspath(os.path.join(
                    local_dir,
                    'scripts',
                    'jenkins_jobs',
                    '%s.xml' % job))
                sudo('mkdir /var/lib/jenkins/jobs/%s' % job)
                put(local_job_file,
                    "/var/lib/jenkins/jobs/%s/config.xml" % job,
                    use_sudo=True)
        sudo('chown -R jenkins:nogroup InaSAFE*')
    sudo('service jenkins restart')
