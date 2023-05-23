import logging
from datetime import datetime

from django.core.management.base import BaseCommand

from core.models import System, Branch, TimeTracker

logger = logging.getLogger('django')


class Command(BaseCommand):
    help = 'Clone repositores'
    

    def add_arguments(self, parser):
        # Optional argument for systems
        parser.add_argument('--system', help='name of system whose repositories to clone')
        # Optional argument for branchs
        parser.add_argument('--branch', help='The branch version of repository to clone')
      
    def handle(self, *args, **options):

       # variables for conditionals
        is_system_specified = True if options['system'] else False
        is_branch_specified = True if options['branch'] else False
        should_be_executed = None

        if is_branch_specified:
            if not is_system_specified:
                logger.info("Invalid Command, please enter the name of system whose branch is to be processed.")
                should_be_executed = False
            else:
                should_be_executed = True
        else:
            should_be_executed = True

        if (should_be_executed):
            time_initial = datetime.now()
            # check for system argument
            if is_system_specified:
                system = System.objects.get(name=options['system'])
                # system.clone_repositories()
                # check for branch argument
                if is_branch_specified:

                    branch = Branch.objects.filter(system=system).get(name=options['branch'])
                    logger.info(f"Running for branch {branch} of system {system}")
                    time_initial_branch = datetime.now()
                    branch.clone_repositories()
                    branch.save_time('Clone Repositories', time_initial_branch)
                
                else:
                    branchs = Branch.objects.filter(system=system).order_by('version', 'version2', 'version3').all()
                    logger.info(f"Cloning all the repositories for {system}")
                    for branch in branchs:
                        self.stdout.write(f'Branch: {branch.name}')
                        time_initial_branch = datetime.now()
                        branch.clone_repositories()
                        branch.save_time('Clone Repositories', time_initial_branch)
                        
            # cloning all repositories 
            else:
                systems = System.objects.all()
                logger.info("Cloning every branch from every system.")

                for system in systems:
                    # system.clone_repositories()
                    self.stdout.write(f'System: {system.name}')
                    branchs = Branch.objects.filter(system=system).order_by('version', 'version2', 'version3').all()
                    for branch in branchs:
                        self.stdout.write(f'Branch: {branch.name}')
                        time_initial_branch = datetime.now()
                        branch.clone_repositories()
                        branch.save_time('Clone Repositories', time_initial_branch)

            TimeTracker.save_time('Clone Repositories', time_initial)
