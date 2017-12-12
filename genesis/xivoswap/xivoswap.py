#!/usr/bin/env python

import os
import subprocess
from argparse import ArgumentParser
import stat


GIT_DIR = '/home/git'


class BadArgumentsException(Exception):
    pass


class Assembler(object):
    def __init__(self):
        parser = self._create_option_parser()

        file_swapper = FileSwapper()
        module_factory = ModuleFactory(file_swapper)
        self.xivo_swapper = XiVOSwapper(parser, module_factory)

    def _create_option_parser(self):
        parser = ArgumentParser()
        parser.add_argument('-g',
                            '--git',
                            dest='source_is_git',
                            action='store_true',
                            help='swap source to git version')
        parser.add_argument('-p',
                            '--package',
                            dest='source_is_git',
                            action='store_false',
                            help='swap source to packaged version')
        parser.add_argument('modules',
                            nargs='+',
                            help='modules from which to swap source')
        parser.set_defaults(source_is_git=False)
        return parser

    def start(self, explicit_args=None):
        self.xivo_swapper.start(explicit_args)


class XiVOSwapper(object):

    def __init__(self, parser, module_factory):
        self.parser = parser
        self.module_factory = module_factory

    def start(self, explicit_args=None):
        options = self.parser.parse_args(explicit_args)
        self._check_options(options)
        self.swap(options.source_is_git, options.modules)

    def _check_options(self, options):
        if not options.modules:
            raise BadArgumentsException()

    def swap(self, swap_to_git, module_names):
        commands = []
        for module_name in module_names:
            module = self.module_factory.create_module(module_name)
            commands.extend(module.commands(swap_to_git))

        processor = CommandSimplifierDecorator(CommandProcessor())
        processor.process(commands)


module_registry = {}


def register_module(module_name, module_class):
    if issubclass(module_class, Module):
        module_registry[module_name] = module_class
    else:
        raise TypeError('Can\'t register %s' % module_class)


class ModuleFactory(object):
    def __init__(self, file_swapper):
        self._file_swapper = file_swapper

    def create_module(self, module_name):
        return module_registry[module_name](self._file_swapper, self)


class Module(object):
    daemon = ''

    def __init__(self, file_swapper, module_factory):
        self._file_swapper = file_swapper
        self._module_factory = module_factory

    def commands(self, swap_to_git):
        raise NotImplementedError()


class CompoundModule(Module):
    components = []

    def commands(self, swap_to_git):
        component_commands = [command
                              for component in self.components
                              for command in self._module_factory.create_module(component).commands(swap_to_git)]
        if component_commands:
            for command in component_commands:
                yield command
            if self.daemon:
                yield RestartDaemonCommand(self.daemon)


class PathModule(Module):
    git = ''
    package = ''

    def commands(self, swap_to_git):
        if swap_to_git and not self._file_swapper.is_link(self.package):
            yield PrintCommand('{m.package} -> {m.git}'.format(m=self))
            yield AddLinkCommand(self.package, self.git, self._file_swapper)
        if not swap_to_git and self._file_swapper.is_link(self.package):
            yield PrintCommand('%s is the packaged version' % self.package)
            yield RemoveLinkCommand(self.package, self._file_swapper)


class Command(object):
    def execute(self):
        raise NotImplementedError()


class RestartDaemonCommand(Command):
    def __init__(self, daemon_name):
        self.daemon = daemon_name

    def execute(self):
        subprocess.call(['service', self.daemon, 'restart'])


class PrintCommand(Command):
    def __init__(self, message):
        self.message = message

    def execute(self):
        print self.message


class FileCommand(Command):
    def __init__(self, file_swapper):
        self.file_swapper = file_swapper


class AddLinkCommand(FileCommand):
    def __init__(self, link_source, link_destination, file_swapper):
        super(AddLinkCommand, self).__init__(file_swapper)
        self.link_source = link_source
        self.link_destination = link_destination

    def execute(self):
        self.file_swapper.link_to(self.link_source, self.link_destination)


class RemoveLinkCommand(FileCommand):
    def __init__(self, link_source, file_swapper):
        super(RemoveLinkCommand, self).__init__(file_swapper)
        self.link_source = link_source

    def execute(self):
        self.file_swapper.restore(self.link_source)


class CommandProcessor(object):
    def process(self, commands):
        for command in commands:
            command.execute()


class CommandSimplifierDecorator(object):
    def __init__(self, processor):
        self.processor = processor

    def process(self, commands):
        self.processor.process(self.simplify(commands))

    @staticmethod
    def simplify(commands):
        seen = set()
        for command in commands:
            if command not in seen:
                yield command
                seen.add(command)


class FileSwapper(object):

    suffix = 'orig'

    def link_to(self, source_path, dest_path):
        if not self.is_link(source_path):
            subprocess.call(['mv', source_path, '%s-%s' % (source_path, self.suffix)])
            subprocess.call(['ln', '-s', dest_path, source_path])

    def restore(self, path):
        if self.is_link(path):
            subprocess.call(['rm', path])
            subprocess.call(['mv', '%s-%s' % (path, self.suffix), path])

    def is_link(self, path):
        path_stat = os.lstat(path)
        return stat.S_ISLNK(path_stat.st_mode)

# XXX: not sure if this code works with this version of xivoswap, but this is the concept
#     def link_to(self, source_path, dest_path):
#         for line in open('/proc/mounts'):
#             if source_path == line.split()[1]:
#                 print (source_path + ' is already mounted')
#                 break
#         else:
#             subprocess.call(['mount', '-o', 'bind', dest_path, source_path])

#     def restore(self, path):
#         subprocess.call(['umount', path])


class ModuleAgent(CompoundModule):
    daemon = 'xivo-agentd'
    components = ['agent-etc', 'agent-lib']

register_module('agent', ModuleAgent)


class ModuleAgentEtc(PathModule):
    package = '/etc/xivo-agentd/config.yml'
    git = '%s/agentd/etc/xivo-agentd/config.yml' % GIT_DIR

register_module('agent-etc', ModuleAgentEtc)


class ModuleAgentLib(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_agent'
    git = '%s/agentd/xivo_agent' % GIT_DIR

register_module('agent-lib', ModuleAgentLib)


class ModuleAgentCLI(CompoundModule):
    components = ['agentd-cli-lib', 'agentd-cli-etc']

register_module('agentd-cli', ModuleAgentCLI)


class ModuleAgentdCLILib(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_agentd_cli'
    git = '%s/agentd-cli/xivo_agentd_cli' % GIT_DIR

register_module('agentd-cli-lib', ModuleAgentdCLILib)


class ModuleAgentdCLIEtc(PathModule):
    package = '/etc/xivo-agentd-cli/config.yml'
    git = '%s/agentd-cli/etc/xivo-agentd-cli/config.yml' % GIT_DIR

register_module('agentd-cli-etc', ModuleAgentdCLIEtc)


class ModuleAgentdClient(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_agentd_client'
    git = '%s/agentd-client/xivo_agentd_client' % GIT_DIR

register_module('agentd-client', ModuleAgentdClient)


class ModuleAGI(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_agid'
    git = '%s/agid/xivo_agid' % GIT_DIR

register_module('agi', ModuleAGI)


class ModuleAMI(CompoundModule):
    daemon = 'xivo-amid'
    components = ['ami-bin', 'ami-lib']

register_module('ami', ModuleAMI)


class ModuleAMIBin(PathModule):
    package = '/usr/bin/xivo-amid'
    git = '%s/amid/bin/xivo-amid' % GIT_DIR

register_module('ami-bin', ModuleAMIBin)


class ModuleAMILib(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_ami'
    git = '%s/amid/xivo_ami' % GIT_DIR

register_module('ami-lib', ModuleAMILib)


class ModuleAMIdClient(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_amid_client'
    git = '%s/amid-client/xivo_amid_client' % GIT_DIR

register_module('amid-client', ModuleAMIdClient)


class ModuleARI(PathModule):
    package = '/usr/lib/python2.7/dist-packages/ari'
    git = '%s/ari-py/ari' % GIT_DIR

register_module('ari', ModuleARI)


class ModuleAuth(CompoundModule):
    daemon = 'wazo-auth'
    components = ['auth-etc', 'auth-lib']

register_module('auth', ModuleAuth)


class ModuleAuthLib(PathModule):
    package = '/usr/lib/python2.7/dist-packages/wazo_auth'
    git = '%s/auth/wazo_auth' % GIT_DIR

register_module('auth-lib', ModuleAuthLib)


class ModuleAuthEtc(PathModule):
    package = '/etc/wazo-auth/config.yml'
    git = '%s/auth/etc/wazo-auth/config.yml' % GIT_DIR

register_module('auth-etc', ModuleAuthEtc)


class ModuleAuthClient(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_auth_client'
    git = '%s/auth-client/xivo_auth_client' % GIT_DIR

register_module('auth-client', ModuleAuthClient)


class ModuleBackup(PathModule):
    package = '/usr/sbin/xivo-backup'
    git = '%s/backup/bin/xivo-backup' % GIT_DIR

register_module('backup', ModuleBackup)


class ModuleBus(CompoundModule):
    daemon = None
    components = ['bus2', 'bus3']

register_module('bus', ModuleBus)



class ModuleBus2(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_bus'
    git = '%s/bus/xivo_bus' % GIT_DIR

register_module('bus2', ModuleBus2)


class ModuleBus3(PathModule):
    package = '/usr/lib/python3/dist-packages/xivo_bus'
    git = '%s/bus/xivo_bus' % GIT_DIR

register_module('bus3', ModuleBus3)


class ModuleCallLogd(CompoundModule):
    daemon = 'wazo-call-logd'
    components = ['call-logd-lib', 'call-logs-script', 'call-logd-daemon']

register_module('call-logd', ModuleCallLogd)


class ModuleCallLogdLib(PathModule):
    package = '/usr/lib/python3/dist-packages/wazo_call_logd'
    git = '%s/call-logd/wazo_call_logd' % GIT_DIR

register_module('call-logd-lib', ModuleCallLogdLib)


class ModuleCallLogsScript(PathModule):
    package = '/usr/bin/wazo-call-logs'
    git = '%s/call-logd/bin/wazo-call-logs' % GIT_DIR

register_module('call-logs-script', ModuleCallLogsScript)


class ModuleCallLogdDaemon(PathModule):
    package = '/usr/bin/wazo-call-logd'
    git = '%s/call-logd/bin/wazo-call-logd' % GIT_DIR

register_module('call-logd-daemon', ModuleCallLogdDaemon)


class ModuleConfd(CompoundModule):
    daemon = 'xivo-confd'
    components = ['confd-lib']

register_module('confd', ModuleConfd)


class ModuleLibConfd(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_confd'
    git = '%s/confd/xivo_confd' % GIT_DIR

register_module('confd-lib', ModuleLibConfd)


class ModuleConfdClient(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_confd_client'
    git = '%s/confd-client/xivo_confd_client' % GIT_DIR

register_module('confd-client', ModuleConfdClient)


class ModuleConfgendClient(PathModule):
    package = '/usr/bin/xivo-confgen'
    git = '%s/confgend-client/bin/xivo-confgen' % GIT_DIR

register_module('confgend-client', ModuleConfgendClient)


class ModuleConfgen(CompoundModule):
    daemon = 'xivo-confgend'
    components = ['confgen-bin', 'confgen-lib', 'confgen-etc1', 'confgen-etc2']

register_module('confgen', ModuleConfgen)


class ModuleConfgenEtc1(PathModule):
    package = '/etc/xivo-confgend'
    git = '%s/confgend/etc/xivo-confgend' % GIT_DIR

register_module('confgen-etc1', ModuleConfgenEtc1)


class ModuleConfgenEtc2(PathModule):
    package = '/etc/xivo/xivo-confgen.conf'
    git = '%s/confgend/etc/xivo-confgen.conf' % GIT_DIR

register_module('confgen-etc2', ModuleConfgenEtc2)


class ModuleConfgenBin(PathModule):
    package = '/usr/bin/xivo-confgend'
    git = '%s/confgend/bin/xivo-confgend' % GIT_DIR

register_module('confgen-bin', ModuleConfgenBin)


class ModuleConfgenLib(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_confgen'
    git = '%s/confgend/xivo_confgen' % GIT_DIR

register_module('confgen-lib', ModuleConfgenLib)


class ModuleCTI(CompoundModule):
    daemon = 'xivo-ctid'
    components = ['cti-bin', 'cti-etc', 'cti-module']

register_module('cti', ModuleCTI)


class ModuleCTIBin(PathModule):
    package = '/usr/bin/xivo-ctid'
    git = '%s/ctid/bin/xivo-ctid' % GIT_DIR

register_module('cti-bin', ModuleCTIBin)


class ModuleCTIEtc(PathModule):
    package = '/etc/xivo-ctid/config.yml'
    git = '%s/ctid/etc/xivo-ctid/config.yml' % GIT_DIR

register_module('cti-etc', ModuleCTIEtc)


class ModuleCTIModule(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_cti'
    git = '%s/ctid/xivo_cti' % GIT_DIR

register_module('cti-module', ModuleCTIModule)


class ModuleCTIdClient(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_ctid_client'
    git = '%s/ctid-client/xivo_ctid_client' % GIT_DIR

register_module('ctid-client', ModuleCTIdClient)


class ModuleCTING(CompoundModule):
    daemon = 'xivo-ctid-ng'
    components = ['ctid-ng-bin', 'ctid-ng-etc', 'ctid-ng-lib']

register_module('ctid-ng', ModuleCTING)


class ModuleCTIdNGBin(PathModule):
    package = '/usr/bin/xivo-ctid-ng'
    git = '%s/ctid-ng/bin/xivo-ctid-ng' % GIT_DIR

register_module('ctid-ng-bin', ModuleCTIdNGBin)


class ModuleCTIdNGEtc(PathModule):
    package = '/etc/xivo-ctid-ng/config.yml'
    git = '%s/ctid-ng/etc/xivo-ctid-ng/config.yml' % GIT_DIR

register_module('ctid-ng-etc', ModuleCTIdNGEtc)


class ModuleCTIdNGLib(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_ctid_ng'
    git = '%s/ctid-ng/xivo_ctid_ng' % GIT_DIR

register_module('ctid-ng-lib', ModuleCTIdNGLib)


class ModuleCTIdNGClient(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_ctid_ng_client'
    git = '%s/ctid-ng-client/xivo_ctid_ng_client' % GIT_DIR

register_module('ctid-ng-client', ModuleCTIdNGClient)


class ModuleDAO(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_dao'
    git = '%s/dao/xivo_dao' % GIT_DIR

register_module('dao', ModuleDAO)


class ModuleDialplan(PathModule):
    package = '/usr/share/xivo-config/dialplan'
    git = '%s/config/dialplan' % GIT_DIR

register_module('dialplan', ModuleDialplan)


class ModuleDird(CompoundModule):
    daemon = 'xivo-dird'
    components = ['dird-bin', 'dird-lib']

register_module('dird', ModuleDird)


class ModuleDirdBin(PathModule):
    package = '/usr/bin/xivo-dird'
    git = '%s/dird/bin/xivo-dird' % GIT_DIR

register_module('dird-bin', ModuleDirdBin)


class ModuleDirdLib(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_dird'
    git = '%s/dird/xivo_dird' % GIT_DIR

register_module('dird-lib', ModuleDirdLib)


class ModuleDirdClient(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_dird_client'
    git = '%s/dird-client/xivo_dird_client' % GIT_DIR

register_module('dird-client', ModuleDirdClient)


class ModuleDxtora(CompoundModule):
    daemon = 'xivo-dxtora'
    components = ['dxtora-bin-server', 'dxtora-bin-client']

register_module('dxtora', ModuleDxtora)


class ModuleDxtoraBinServer(PathModule):
    package = '/usr/bin/xivo-dxtora'
    git = '%s/dxtora/bin/xivo-dxtora' % GIT_DIR

register_module('dxtora-bin-server', ModuleDxtoraBinServer)


class ModuleDxtoraBinClient(PathModule):
    package = '/usr/bin/dxtorc'
    git = '%s/dxtorc/bin/dxtorc' % GIT_DIR

register_module('dxtora-bin-client', ModuleDxtoraBinClient)


class ModuleLibPython(CompoundModule):
    daemon = None
    components = ['lib-python2', 'lib-python3']

register_module('lib-python', ModuleLibPython)


class ModuleLibPython2(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo'
    git = '%s/lib-python/xivo' % GIT_DIR

register_module('lib-python2', ModuleLibPython2)


class ModuleLibPython3(PathModule):
    package = '/usr/lib/python3/dist-packages/xivo'
    git = '%s/lib-python/xivo' % GIT_DIR

register_module('lib-python3', ModuleLibPython3)


class ModuleLibRestClient(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_lib_rest_client'
    git = '%s/lib-rest-client/xivo_lib_rest_client' % GIT_DIR

register_module('lib-rest-client', ModuleLibRestClient)


class ModuleFetchfw(CompoundModule):
    daemon = None
    components = ['fetchfw-source', 'fetchfw-db']

register_module('fetchfw', ModuleFetchfw)


class ModuleFetchfwSource(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_fetchfw'
    git = '%s/fetchfw/xivo_fetchfw' % GIT_DIR

register_module('fetchfw-source', ModuleFetchfwSource)


class ModuleFetchfwDB(PathModule):
    package = '/var/lib/xivo-fetchfw/installable'
    git = '%s/fetchfw/resources/data' % GIT_DIR

register_module('fetchfw-db', ModuleFetchfwDB)


class ModuleHA(CompoundModule):
    daemon = None
    components = ['ha-services', 'ha-status', 'ha-replication', 'ha-berofos', 'ha-create-config']

register_module('ha', ModuleHA)


class ModuleHAServices(PathModule):
    package = '/usr/sbin/xivo-manage-slave-services'
    git = '%s/config/sbin/xivo-manage-slave-services' % GIT_DIR

register_module('ha-services', ModuleHAServices)


class ModuleHAStatus(PathModule):
    package = '/usr/sbin/xivo-check-master-status'
    git = '%s/config/sbin/xivo-check-master-status' % GIT_DIR

register_module('ha-status', ModuleHAStatus)


class ModuleHAReplication(PathModule):
    package = '/usr/sbin/xivo-master-slave-db-replication'
    git = '%s/config/sbin/xivo-master-slave-db-replication' % GIT_DIR

register_module('ha-replication', ModuleHAReplication)


class ModuleHABerofos(PathModule):
    package = '/usr/sbin/xivo-berofos'
    git = '%s/config/sbin/xivo-berofos' % GIT_DIR

register_module('ha-berofos', ModuleHABerofos)


class ModuleHACreateConfig(PathModule):
    package = '/usr/sbin/xivo-create-config'
    git = '%s/config/sbin/xivo-create-config' % GIT_DIR

register_module('ha-create-config', ModuleHACreateConfig)


class ModulePhoned(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_dird_phoned'
    git = '%s/phoned/xivo_dird_phoned' % GIT_DIR

register_module('phoned', ModulePhoned)


class ModulePlugind(CompoundModule):
    daemon = 'wazo-plugind'
    components = ['plugind-lib', 'plugind-cli']

register_module('plugind', ModulePlugind)


class ModulePlugindLib(PathModule):
    package = '/usr/lib/python3/dist-packages/wazo_plugind'
    git = '%s/plugind/wazo_plugind' % GIT_DIR

register_module('plugind-lib', ModulePlugindLib)


class ModulePlugindCli(PathModule):
    package = '/usr/lib/python3/dist-packages/wazo_plugind_cli'
    git = '%s/plugind-cli/wazo_plugind_cli' % GIT_DIR

register_module('plugind-cli', ModulePlugindCli)


class ModuleProvd(PathModule):
    package = '/usr/lib/python2.7/dist-packages/provd'
    git = '%s/provd/provd' % GIT_DIR

register_module('provd', ModuleProvd)


class ModuleProvdClient(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_provd_client'
    git = '%s/provd-client/xivo_provd_client' % GIT_DIR

register_module('provd-client', ModuleProvdClient)


class ModuleProvdCLI(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_provd_cli'
    git = '%s/provd-cli/xivo_provd_cli' % GIT_DIR

register_module('provd-cli', ModuleProvdCLI)


class ModuleManageDB(CompoundModule):
    daemon = None
    components = ['db-populate', 'db-lib']

register_module('db', ModuleManageDB)


class ModuleDBPopulate(PathModule):
    package = '/usr/share/xivo-manage-db/populate'
    git = '%s/db/populate' % GIT_DIR

register_module('db-populate', ModuleDBPopulate)


class ModuleDBLib(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_db'
    git = '%s/db/xivo_db' % GIT_DIR

register_module('db-lib', ModuleDBLib)


class ModuleStat(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_stat'
    git = '%s/stat/xivo_stat' % GIT_DIR

register_module('stat', ModuleStat)


class ModuleSysconfd(CompoundModule):
    daemon = 'xivo-sysconfd'
    components = ['sysconfd-module', 'sysconfd-conf1', 'sysconfd-conf2']

register_module('sysconfd', ModuleSysconfd)


class ModuleSysconfdModule(PathModule):
    package = '/usr/lib/python2.7/dist-packages/xivo_sysconf'
    git = '%s/sysconfd/xivo_sysconf' % GIT_DIR

register_module('sysconfd-module', ModuleSysconfdModule)


class ModuleSysconfdConf1(PathModule):
    package = '/etc/xivo/sysconfd'
    git = '%s/sysconfd/etc/xivo/sysconfd' % GIT_DIR

register_module('sysconfd-conf1', ModuleSysconfdConf1)


class ModuleSysconfdConf2(PathModule):
    package = '/etc/xivo/sysconfd.conf'
    git = '%s/sysconfd/etc/xivo/sysconfd.conf' % GIT_DIR

register_module('sysconfd-conf2', ModuleSysconfdConf2)


class ModuleUpgrade(CompoundModule):
    components = ['wazo-upgrade', 'real-xivo-upgrade']

register_module('upgrade', ModuleUpgrade)


class ModuleWazoUpgrade(PathModule):
    package = '/usr/bin/wazo-upgrade'
    git = '%s/upgrade/bin/wazo-upgrade' % GIT_DIR

register_module('wazo-upgrade', ModuleWazoUpgrade)


class ModuleRealXiVOUpgrade(PathModule):
    package = '/usr/bin/real-xivo-upgrade'
    git = '%s/upgrade/bin/real-xivo-upgrade' % GIT_DIR

register_module('real-xivo-upgrade', ModuleRealXiVOUpgrade)


class ModuleWebhookd(CompoundModule):
    daemon = 'wazo-webhookd'
    components = ['webhookd-lib']

register_module('webhookd', ModuleWebhookd)


class ModuleWebhookdLib(PathModule):
    package = '/usr/lib/python3/dist-packages/wazo_webhookd'
    git = '%s/webhookd/wazo_webhookd' % GIT_DIR

register_module('webhookd-lib', ModuleWebhookdLib)


class ModuleWebi(PathModule):
    package = '/usr/share/xivo-web-interface'
    git = '%s/webi/src' % GIT_DIR

register_module('webi', ModuleWebi)


class ModuleMonitoring(PathModule):
    package = '/usr/share/xivo-monitoring/checks'
    git = '%s/monitoring/checks' % GIT_DIR

register_module('monit', ModuleMonitoring)


class ModuleSwagger(CompoundModule):
    components = ['swagger-html', 'swagger-css', 'swagger-catalog']

register_module('swagger', ModuleSwagger)


class ModuleSwaggerHTML(PathModule):
    package = '/usr/share/xivo-swagger-doc/index.html'
    git = '%s/swagger/web/index.html' % GIT_DIR

register_module('swagger-html', ModuleSwaggerHTML)


class ModuleSwaggerCSS(PathModule):
    package = '/usr/share/xivo-swagger-doc/css'
    git = '%s/swagger/web/css' % GIT_DIR

register_module('swagger-css', ModuleSwaggerCSS)


class ModuleSwaggerCatalog(PathModule):
    package = '/usr/share/xivo-swagger-doc/catalog/index.json'
    git = '%s/swagger/index.json' % GIT_DIR

register_module('swagger-catalog', ModuleSwaggerCatalog)


class ModuleWebsocketd(CompoundModule):
    daemon = 'xivo-websocketd'
    components = ['websocketd-module']

register_module('websocketd', ModuleWebsocketd)


class ModuleWebsocketdModule(PathModule):
    package = '/usr/lib/python3/dist-packages/xivo_websocketd'
    git = '%s/websocketd/xivo_websocketd' % GIT_DIR

register_module('websocketd-module', ModuleWebsocketdModule)


def get_top_nodes():
    all_modules = module_registry.keys()
    compound_modules = [module for (module_name, module) in module_registry.iteritems()
                        if issubclass(module, CompoundModule)]
    for compound_module in compound_modules:
        for component_name in compound_module.components:
            all_modules.remove(component_name)
    return all_modules


class AllModules(CompoundModule):
    components = get_top_nodes()


register_module('all', AllModules)


if __name__ == '__main__':
    assembler = Assembler()
    assembler.start()
