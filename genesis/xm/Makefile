XM_PATH=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# XiVO paths
ASTERISK_PATH=$(XIVO_PATH)/asterisk11
AGENT_PATH=$(XIVO_PATH)/xivo-agentd
AGI_PATH=$(XIVO_PATH)/xivo-agid
BACKUP_PATH=$(XIVO_PATH)/xivo-backup
BUS_PATH=$(XIVO_PATH)/xivo-bus
CALL_LOGS_PATH=$(XIVO_PATH)/xivo-call-logs
CONFGEN_PATH=$(XIVO_PATH)/xivo-confgend
CONFD_CLIENT_PATH=$(XIVO_PATH)/xivo-confd-client
CONFIG_PATH=$(XIVO_PATH)/xivo-config
CONSUL_PATH=$(XIVO_PATH)/xivo-consul-packaging
CTI_PATH=$(XIVO_PATH)/xivo-ctid
CTID_NG_CLIENT_PATH=$(XIVO_PATH)/xivo-ctid-ng-client
CTIDNG_PATH=$(XIVO_PATH)/xivo-ctid-ng
DAO_PATH=$(XIVO_PATH)/xivo-dao
DIRD_PATH=$(XIVO_PATH)/xivo-dird
DIRD_CLIENT_PATH=$(XIVO_PATH)/xivo-dird-client
DOC_PATH=$(XIVO_PATH)/xivo-doc
FETCHFW_PATH=$(XIVO_PATH)/xivo-fetchfw
LIB_PYTHON_PATH=$(XIVO_PATH)/xivo-lib-python
CONFD_PATH=$(XIVO_PATH)/xivo-confd
SCCP_PATH=$(XIVO_PATH)/xivo-libsccp
SYSCONF_PATH=$(XIVO_PATH)/xivo-sysconfd
WEBI_PATH=$(XIVO_PATH)/xivo-web-interface
LIB_REST_CLIENT_PATH=$(XIVO_PATH)/xivo-lib-rest-client

# PYTHONPATHS
LIB_PYTHON_PP=$(LIB_PYTHON_PATH)
BUS_PP=$(BUS_PATH)
XIVO_DAO_PYTHONPATH=$(XIVO_PATH)/xivo-dao
XIVO_DIRD_PYTHONPATH=$(XIVO_PATH)/xivo-dird
XIVO_AGENT_PYTHONPATH=$(XIVO_PATH)/xivo-agent
XIVO_PROVD_PYTHONPATH=$(XIVO_PATH)/xivo-provisioning
CTI_PP=$(CTI_PATH)

XIVO_PYTHONPATH=$(LIB_PYTHON_PP):$(XIVO_DAO_PYTHONPATH):$(XIVO_DIRD_PYTHONPATH):$(XIVO_AGENT_PYTHONPATH):$(XIVO_PROVD_PYTHONPATH):$(CTI_PP):$(BUS_PP)
TMP_PYTHONPATH=/root/build/lib/python2.7/site-packages
REMOTE_PYTHONPATH=/usr/lib/python2.7/dist-packages
REMOTE_PYTHON3PATH=/usr/lib/python3/dist-packages

# Local paths
AGENT_LOCAL_PATH=$(AGENT_PATH)/xivo_agent
AGI_LOCAL_PATH=$(AGI_PATH)/xivo_agid
ALEMBIC_LOCAL_PATH=$(XIVO_PATH)/xivo-manage-db/alembic/versions
AMID_LOCAL_PATH=$(XIVO_PATH)/xivo-amid/xivo_ami
ASTERISK_LOCAL_PATH=$(shell /usr/bin/dirname $(shell /usr/bin/find $(ASTERISK_PATH) -name 'BUGS'))
BUS_LOCAL_PATH=$(BUS_PATH)/xivo_bus
CALL_LOGS_LOCAL_PATH=$(CALL_LOGS_PATH)/xivo_call_logs
CONFGEN_LOCAL_PATH=$(CONFGEN_PATH)/xivo_confgen
CTI_LOCAL_PATH=$(CTI_PATH)/xivo_cti
CONFD_CLIENT_LOCAL_PATH=$(CONFD_CLIENT_PATH)/xivo_confd_client
DAO_LOCAL_PATH=$(DAO_PATH)/xivo_dao
DIALPLAN_LOCAL_PATH=$(CONFIG_PATH)/dialplan/asterisk
DIRD_LOCAL_PATH=$(DIRD_PATH)/xivo_dird
DIRD_CLIENT_LOCAL_PATH=$(DIRD_CLIENT_PATH)/xivo_dird_client
FETCHFW_LOCAL_PATH=$(FETCHFW_PATH)/xivo_fetchfw
LIB_PYTHON_LOCAL_PATH=$(LIB_PYTHON_PATH)/xivo
XIVO_DAO_LOCAL_PATH=$(XIVO_DAO_PYTHONPATH)/xivo_dao
SCCP_LOCAL_PATH=$(XIVO_PATH)/xivo-libsccp
STAT_LOCAL_PATH=$(XIVO_PATH)/xivo-stat
SYSCONF_LOCAL_PATH=$(SYSCONF_PATH)/xivo_sysconf
UPGRADE_LOCAL_PATH=$(XIVO_PATH)/xivo-upgrade
CONFD_LOCAL_PATH=$(CONFD_PATH)/xivo_confd
FETCHFW_DATA_LOCAL=$(FETCHFW_PATH)/xivo-fetchfw/resources/data/
WEBI_LOCAL_PATH=$(WEBI_PATH)/src
LIB_REST_CLIENT_LOCAL_PATH=$(LIB_REST_CLIENT_PATH)/xivo_lib_rest_client

# Remote paths
ALEMBIC_REMOTE_PATH=/usr/share/xivo-manage-db/alembic/versions
PYTHON_PACKAGES=/usr/lib/python2.7/dist-packages/
WEBI_REMOTE_PATH=/usr/share/xivo-web-interface
FETCHFW_DATA_PATH=/var/lib/xivo-fetchfw/installable
DIALPLAN_REMOTE_PATH=/usr/share/xivo-config/dialplan/asterisk

# Tags
AGI_TAGS=$(AGI_PATH)/TAGS
ASTERISK_TAGS=$(ASTERISK_PATH)/TAGS
BUS_TAGS=$(BUS_PATH)/TAGS
CONFD_TAGS=$(CONFD_PATH)/TAGS
CTI_TAGS=$(CTI_PATH)/TAGS
DAO_TAGS=$(DAO_PATH)/TAGS
DIRD_TAGS=$(DIRD_PATH)/TAGS
SCCP_TAGS=$(SCCP_PATH)/TAGS
WEBI_TAGS=$(WEBI_PATH)/TAGS

ASTERISK_CSCOPE_FILES=$(ASTERISK_PATH)/cscope.files
SCCP_CSCOPE_FILES=$(SCCP_PATH)/cscope.files

# Commands
SYNC=rsync -vrtlp --filter '- *.pyc' --filter '- *.git' --filter '- *~'
XIVO_LIBSCCP_BUILDH=./buildh
XIVO_LIBSCCP_DEP_COMMAND='apt-get update && apt-get install build-essential autoconf automake libtool asterisk-dev'

# shared targets
.PHONY : sync.bootstrap xivo.umount xivo.mount
sync.bootstrap:
	ssh -q $(XIVO_HOSTNAME) "mkdir -p ~/dev ${TMP_PYTHONPATH}"
	$(SYNC) $(XM_PATH)/bin/00-pre-upgrade.sh $(XIVO_HOSTNAME):"/usr/share/xivo-upgrade/post-stop.d/"

xivo.umount: auth.umount dao.umound dird.umount confgen.umount cti.umount dialplan.umount ctid-ng.umount confd.umount plugind.umount bus.umount plugind-cli.umount webhookd.umount admin-ui-market.umount
	ssh -q $(XIVO_HOSTNAME) "mount | grep -q \"on /var/dev/xivo type\" && umount /var/dev/xivo"

xivo.mount:
	ssh -q $(XIVO_HOSTNAME) "mount | grep -q \"on /var/dev/xivo type\" || mount 10.37.0.1:${XIVO_PATH} /var/dev/xivo"

################################################################################
# wazo-auth
################################################################################
.PHONY : auth.sync auth.mount auth.orig auth.restart auth.umount auth.db-upgrade auth.db_downgrade
auth.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/wazo_auth type\" || mount --bind /var/dev/xivo/wazo-auth/wazo_auth ${REMOTE_PYTHONPATH}/wazo_auth"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on /usr/share/wazo-auth/alembic type\" || mount --bind /var/dev/xivo/wazo-auth/alembic /usr/share/wazo-auth/alembic"

auth.sync: auth.mount
	ssh $(XIVO_HOSTNAME) 'cd /var/dev/xivo/wazo-auth && python setup.py develop'

auth.umount:
	ssh $(XIVO_HOSTNAME) "umount ${REMOTE_PYTHONPATH}/wazo_auth || true"
	ssh $(XIVO_HOSTNAME) "umount /usr/share/wazo-auth/alembic || true"

auth.orig:
	ssh $(XIVO_HOSTNAME) "cd /var/dev/xivo/wazo-auth && python setup.py develop --uninstall"
	ssh $(XIVO_HOSTNAME) "rm -f /usr/local/bin/wazo-auth"

auth.restart:
	ssh $(XIVO_HOSTNAME) 'systemctl restart wazo-auth'

auth.db-upgrade:
	ssh -q $(XIVO_HOSTNAME) 'cd /usr/share/wazo-auth && alembic -c alembic.ini upgrade head'

auth.db-downgrade:
	ssh -q $(XIVO_HOSTNAME) 'cd /usr/share/wazo-auth && alembic -c alembic.ini downgrade -1'

################################################################################
# xivo-web-interface
################################################################################
.PHONY : webi.mount webi.ctags
webi.ctags:
	rm -f $(WEBI_TAGS)
	ctags -o $(WEBI_TAGS) -R -e --langmap=php:.php.inc $(WEBI_LOCAL_PATH)

webi.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q "${WEBI_REMOTE_PATH}" || mount --bind /var/dev/xivo/xivo-web-interface/src ${WEBI_REMOTE_PATH}"

# xivo-fetchfw
.PHONY : fetchfw.sync
fetchfw.sync:
	$(SYNC) $(FETCHFW_LOCAL_PATH) $(XIVO_HOSTNAME):$(PYTHON_PACKAGES)
	$(SYNC) $(FETCHFW_DATA_LOCAL) $(XIVO_HOSTNAME):$(FETCHFW_DATA_PATH)

################################################################################
# xivo-agentd
################################################################################
.PHONY : agentd.mount agentd-restart agentd.umuont
agentd.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/xivo_agent type\" || mount --bind /var/dev/xivo/xivo-agentd/xivo_agent ${REMOTE_PYTHONPATH}/xivo_agent"

agentd.umount:
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/xivo_agent type\" && umount ${REMOTE_PYTHONPATH}/xivo_agent || true"

agentd.restart:
	ssh $(XIVO_HOSTNAME) 'systemctl restart xivo-agentd'

################################################################################
# xivo-agentd-client
################################################################################
.PHONY : agentd-client.sync
agentd-client.sync:
	$(SYNC) --delete $(XIVO_PATH)/xivo-agentd-client $(XIVO_HOSTNAME):/tmp
	ssh $(XIVO_HOSTNAME) 'cd /tmp/xivo-agentd-client && python setup.py develop'

################################################################################
# xivo-agentd-cli
################################################################################
.PHONY : agentd-cli.sync
agentd-cli.sync:
	$(SYNC) $(XIVO_PATH)/xivo-agentd-cli/xivo_agentd_cli $(XIVO_HOSTNAME):$(PYTHON_PACKAGES)

# xivo-agid
.PHONY : agi.sync agi.ctags
agi.sync:
	$(SYNC) $(AGI_LOCAL_PATH) $(XIVO_HOSTNAME):$(PYTHON_PACKAGES)
	ssh $(XIVO_HOSTNAME) '/etc/init.d/xivo-agid restart'

agi.ctags:
	rm -f $(AGI_TAGS)
	ctags -o $(AGI_TAGS) -R -e $(AGI_LOCAL_PATH)

# xivo-amid
.PHONY : amid.sync
amid.sync:
	$(SYNC) $(AMID_LOCAL_PATH) $(XIVO_HOSTNAME):$(PYTHON_PACKAGES)

# xivo-backup
.PHONE : backup.sync
backup.sync:
	$(SYNC) $(BACKUP_PATH)/bin/ $(XIVO_HOSTNAME):/usr/sbin

################################################################################
# xivo-bus
################################################################################

.PHONY : bus.mount bus.umount bus.clean bus.tags
bus.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/xivo_bus type\" || mount --bind /var/dev/xivo/xivo-bus/xivo_bus ${REMOTE_PYTHONPATH}/xivo_bus"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/xivo_bus type\" || mount --bind /var/dev/xivo/xivo-bus/xivo_bus ${REMOTE_PYTHON3PATH}/xivo_bus"

bus.umount:
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/xivo_bus type\" && umount ${REMOTE_PYTHONPATH}/xivo_bus || true"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/xivo_bus type\" && umount ${REMOTE_PYTHON3PATH}/xivo_bus || true"

bus.tags: bus.clean
	ctags -o $(BUS_TAGS) -R -e $(BUS_LOCAL_PATH)

bus.clean:
	rm -rf $(BUS_PATH)/.tox
	find $(BUS_PATH) -name '*.pyc' -delete
	rm -f $(BUS_TAGS)

################################################################################
# wazo-call-logd
################################################################################

.PHONY : call-logs.mount call-logs.umount
call-logs.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/wazo_call_logd type\" || mount --bind /var/dev/xivo/wazo-call-logd/wazo_call_logd ${REMOTE_PYTHON3PATH}/wazo_call_logd"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on /etc/wazo-call-logd/config.yml type\" || mount --bind /var/dev/xivo/wazo-call-logs/etc/wazo-call-logd/config.yml /etc/wazo-call-logd/config.yml"

call-logs.umount:
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/wazo_call_logd type\" && umount ${REMOTE_PYTHON3PATH}/wazo_call_logd || true"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on /etc/wazo-call-logd/config.yml type\" && umount /etc/wazo-call-logd/config.yml || true"


################################################################################
# xivo-confgen
################################################################################
.PHONY : confgen.sync confgen.umount
confgend.sync: sync.bootstrap confgend.umount
	rsync -av --delete --exclude "*.git" --exclude "*.tox" $(CONFGEN_PATH)/ $(XIVO_HOSTNAME):~/dev/xivo-confgend
	ssh -q $(XIVO_HOSTNAME) "cd ~/dev/xivo-confgend && PYTHONPATH=${TMP_PYTHONPATH} python setup.py install --prefix=~/build"
	ssh -q $(XIVO_HOSTNAME) "mount --bind ~/dev/xivo-confgend/build/lib.linux-*-2.7/xivo_confgen ${REMOTE_PYTHONPATH}/xivo_confgen"

confgend.umount:
	ssh -q $(XIVO_HOSTNAME) 'umount ${REMOTE_PYTHONPATH}/xivo_confgen || true'
	ssh -q $(XIVO_HOSTNAME) 'umount ${REMOTE_PYTHONPATH}/xivo_confgen-*.egg-info || true'

################################################################################
# xivo-ctid
################################################################################

.PHONY : cti.mount cti.ctags cti.clean cti.umount cti.restart
cti.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/xivo_cti type\" || mount --bind /var/dev/xivo/xivo-ctid/xivo_cti ${REMOTE_PYTHONPATH}/xivo_cti"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on /etc/xivo-ctid/config.yml type\" || mount --bind /var/dev/xivo/xivo-ctid/etc/xivo-ctid/config.yml /etc/xivo-ctid/config.yml"

cti.umount:
	ssh -q $(XIVO_HOSTNAME) 'umount ${REMOTE_PYTHONPATH}/xivo_cti || true'
	ssh -q $(XIVO_HOSTNAME) 'umount /etc/xivo-ctid/config.yml || true'

cti.ctags: cti.clean
	ctags -o $(CTI_TAGS) -R -e $(CTI_LOCAL_PATH)
	ctags -o $(CTI_TAGS) -R -e -a $(XIVO_DAO_LOCAL_PATH)
	ctags -o $(CTI_TAGS) -R -e -a $(LIB_PYTHON_LOCAL_PATH)

cti.clean:
	rm -rf $(CTI_PATH)/.tox
	find $(CTI_PATH) -name '*.pyc' -delete
	rm -f $(CTI_TAGS)

cti.restart:
	ssh -q $(XIVO_HOSTNAME) 'systemctl restart xivo-ctid.service'

################################################################################
# xivo-ctid-ng
################################################################################

.PHONY: ctid-ng.mount ctid-ng.umount
ctid-ng.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/xivo_ctid_ng type\" || mount --bind /var/dev/xivo/xivo-ctid-ng/xivo_ctid_ng ${REMOTE_PYTHONPATH}/xivo_ctid_ng"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on /etc/xivo-ctid-ng/config.yml type\" || mount --bind /var/dev/xivo/xivo-ctid-ng/etc/xivo-ctid-ng/config.yml /etc/xivo-ctid-ng/config.yml"

ctid-ng.umount:
	ssh $(XIVO_HOSTNAME) 'umount /etc/xivo-ctid-ng/config.yml || true'
	ssh $(XIVO_HOSTNAME) "umount ${REMOTE_PYTHONPATH}/xivo_ctid_ng || true"

################################################################################
# xivo-dao
################################################################################
.PHONY : dao.mount dao.umount dao.sync dao.ctags
dao.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/xivo_dao type\" || mount --bind /var/dev/xivo/xivo-dao/xivo_dao ${REMOTE_PYTHONPATH}/xivo_dao"

dao.umount:
	ssh $(XIVO_HOSTNAME) "umount ${REMOTE_PYTHONPATH}/xivo_dao || true"

dao.sync:
	$(SYNC) $(DAO_LOCAL_PATH) $(XIVO_HOSTNAME):$(PYTHON_PACKAGES)

dao.ctags:
	rm -f $(DAO_TAGS)
	ctags -o $(DAO_TAGS) -R -e $(DAO_LOCAL_PATH)


################################################################################
# xivo-manage-db
################################################################################
.PHONY : db.sync db.upgrade db.downgrade
db.sync:
	$(SYNC) $(ALEMBIC_LOCAL_PATH)/* $(XIVO_HOSTNAME):$(ALEMBIC_REMOTE_PATH)/

db.upgrade:
	ssh -q $(XIVO_HOSTNAME) 'cd /usr/share/xivo-manage-db && alembic upgrade +1'

db.downgrade:
	ssh -q $(XIVO_HOSTNAME) 'cd /usr/share/xivo-manage-db && alembic downgrade -1'

################################################################################
# consul
################################################################################

.PHONY : consul.sync consul.restart
consul.sync:
	rsync -av $(CONSUL_PATH)/debian/init $(XIVO_HOSTNAME):/etc/init.d/consul
	ssh -q $(XIVO_HOSTNAME) 'chmod +x /etc/init.d/consul'

consul.restart:
	ssh -q $(XIVO_HOSTNAME) 'service consul restart'


# xivo-dird
.PHONY : dird.sync dird.umount dird.ctags dird.clean dird.restart dird.db-upgrade dird.db-downgrade
dird.sync: dird.umount sync.bootstrap
	rsync -av --delete --exclude "*.git" --exclude "*.tox" $(DIRD_PATH)/ $(XIVO_HOSTNAME):~/dev/xivo-dird
	ssh -q $(XIVO_HOSTNAME) "cd ~/dev/xivo-dird && PYTHONPATH=${TMP_PYTHONPATH} python setup.py install --prefix=~/build"
	ssh -q $(XIVO_HOSTNAME) "mount --bind ${TMP_PYTHONPATH}/xivo_dird-*-py2.7.egg/xivo_dird ${REMOTE_PYTHONPATH}/xivo_dird"
	ssh -q $(XIVO_HOSTNAME) "mount --bind ${TMP_PYTHONPATH}/xivo_dird-*-py2.7.egg/EGG-INFO ${REMOTE_PYTHONPATH}/xivo_dird-$(shell $(DIRD_PATH)/setup.py --version).egg-info"
	ssh -q $(XIVO_HOSTNAME) "mount --bind ~/dev/xivo-dird/alembic /usr/share/xivo-dird/alembic"

dird.umount:
	ssh -q $(XIVO_HOSTNAME) "umount ${REMOTE_PYTHONPATH}/xivo_dird || true"
	ssh -q $(XIVO_HOSTNAME) "umount ${REMOTE_PYTHONPATH}/xivo_dird-*.egg-info || true"
	ssh -q $(XIVO_HOSTNAME) "umount /usr/share/xivo-dird/alembic || true"

dird.ctags: dird.clean
	ctags -o $(DIRD_TAGS) -R -e $(DIRD_PATH)/xivo_dird
	ctags -o $(DIRD_TAGS) -R -e -a $(LIB_PYTHON_LOCAL_PATH)
	ctags -o $(DIRD_TAGS) -R -e -a $(XIVO_PATH)/xivo-auth-client/xivo_auth_client
	ctags -o $(DIRD_TAGS) -R -e -a $(XIVO_PATH)/xivo-lib-rest-client/xivo_lib_rest_client
	ctags -o $(DIRD_TAGS) -R -e -a $(XIVO_PATH)/xivo-confd-client/xivo_confd_client

dird.clean:
	rm -rf $(DIRD_PATH)/.tox
	find $(DIRD_PATH) -name '*.pyc' -delete
	rm -f $(DIRD_TAGS)

dird.restart:
	ssh -q $(XIVO_HOSTNAME) 'service xivo-dird restart'

dird.db-upgrade:
	ssh -q $(XIVO_HOSTNAME) 'cd /usr/share/xivo-dird && alembic -c alembic.ini upgrade head'

dird.db-downgrade:
	ssh -q $(XIVO_HOSTNAME) 'cd /usr/share/xivo-dird && alembic -c alembic.ini downgrade -1'


# xivo-doc
.PHONY : doc.build
doc.build:
	cd $(DOC_PATH) && make html

.PHONY : doc.clean
doc.clean:
	cd $(DOC_PATH) && make clean

.PHONY : doc.rebuild
doc.rebuild: doc.clean doc.build

################################################################################
# xivo-lib-python
################################################################################
.PHONY : lib-python.mount lib-python.umount
lib-python.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/xivo type\" || mount --bind /var/dev/xivo/xivo-lib-python/xivo ${REMOTE_PYTHONPATH}/xivo"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/xivo type\" || mount --bind /var/dev/xivo/xivo-lib-python/xivo ${REMOTE_PYTHON3PATH}/xivo"

lib-python.umount:
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/xivo type\" && umount ${REMOTE_PYTHONPATH}/xivo || true"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/xivo type\" && umount ${REMOTE_PYTHON3PATH}/xivo || true"

################################################################################
# xivo-libsccp
################################################################################
.PHONY : sccp.sync
sccp.sync:
	cd $(SCCP_LOCAL_PATH)/xivo-libsccp && $(XIVO_LIBSCCP_BUILDH) makei

.PHONY : sccp.dep
sccp.dep:
	ssh $(XIVO_HOSTNAME) $(XIVO_LIBSCCP_DEP_COMMAND)

.PHONY : sccp.setup
sccp.setup:
	cd $(SCCP_LOCAL_PATH)/xivo-libsccp && $(XIVO_LIBSCCP_BUILDH) init

.PHONY : sccp.ctags
sccp.ctags:
	rm -f $(SCCP_TAGS)
	ctags -o $(SCCP_TAGS) -R -e $(SCCP_LOCAL_PATH)
	ctags -o $(SCCP_TAGS) -R -e -a $(ASTERISK_LOCAL_PATH)

.PHONY : sccp.cscope
sccp.cscope:
	rm -f $(SCCP_CSCOPE_FILES)
	find $(SCCP_LOCAL_PATH) -name "*.c" -o -name "*.h" > $(SCCP_CSCOPE_FILES)
	find $(ASTERISK_LOCAL_PATH) -name "*.c" -o -name "*.h" >> $(SCCP_CSCOPE_FILES)

# xivo-provd
.PHONY : provd.sync
provd.sync:
	$(SYNC) $(XIVO_PROVD_PYTHONPATH)/provd $(XIVO_HOSTNAME):$(PYTHON_PACKAGES)
	$(SYNC) $(XIVO_PROVD_PYTHONPATH)/debian/xivo-provd.service $(XIVO_HOSTNAME):/lib/systemd/system/xivo-provd.service


################################################################################
# xivo-provd-cli
################################################################################

.PHONY : provd-cli.sync
provd-cli.sync:
	$(SYNC) $(XIVO_PATH)/xivo-provd-cli/xivo_provd_cli $(XIVO_HOSTNAME):$(PYTHON_PACKAGES)

################################################################################
# xivo-upgrade
################################################################################

.PHONY : upgrade.sync
upgrade.sync:
	$(SYNC) $(UPGRADE_LOCAL_PATH)/bin/ $(XIVO_HOSTNAME):/usr/bin/

################################################################################
# xivo-confd
################################################################################

.PHONY : confd.mount confd.umount confd.ctags confd.clean confd.restart

confd.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/xivo_confd type\" || mount --bind /var/dev/xivo/xivo-confd/xivo_confd ${REMOTE_PYTHONPATH}/xivo_confd"

confd.umount:
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/xivo_confd type\" && umount ${REMOTE_PYTHONPATH}/xivo_confd || true"

confd.clean:
	rm -rf $(CONFD_PATH)/.tox
	find $(CONFD_PATH) -name '*.pyc' -delete
	rm -f $(CONFD_TAGS)

confd.ctags: confd.clean
	ctags -o $(CONFD_TAGS) -R -e $(CONFD_PATH)/xivo_confd
	ctags -o $(CONFD_TAGS) -R -e -a $(LIB_PYTHON_LOCAL_PATH)
	ctags -o $(CONFD_TAGS) -R -e -a $(XIVO_PATH)/xivo-auth-client/xivo_auth_client
	ctags -o $(CONFD_TAGS) -R -e -a $(XIVO_PATH)/xivo-lib-rest-client/xivo_lib_rest_client
	ctags -o $(CONFD_TAGS) -R -e -a $(XIVO_PATH)/xivo-dao/xivo_dao

confd.restart:
	ssh -q $(XIVO_HOSTNAME) 'service xivo-confd restart'


################################################################################
# xivo-sysconf
################################################################################

.PHONY : sysconf.sync
sysconf.sync:
	$(SYNC) $(SYSCONF_LOCAL_PATH) $(XIVO_HOSTNAME):$(PYTHON_PACKAGES)

# xivo-stat
.PHONY : stat.sync
stat.sync:
	$(SYNC) $(STAT_LOCAL_PATH) $(XIVO_HOSTNAME):$(PYTHON_PACKAGES)

# asterisk
.PHONY : asterisk.clean asterisk.generate asterisk.refresh asterisk.ctags asterisk.cscope
asterisk.clean:
	rm -fr $(ASTERISK_PATH)/asterisk/tmp/

asterisk.ctags:
	rm -f $(ASTERISK_TAGS)
	ctags -o $(ASTERISK_TAGS) -R -e -a $(ASTERISK_LOCAL_PATH)

asterisk.cscope:
	rm -f $(ASTERISK_CSCOPE_FILES)
	find $(ASTERISK_LOCAL_PATH) -name "*.c" -o -name "*.h" >> $(ASTERISK_CSCOPE_FILES)

asterisk.generate:
	$(ASTERISK_PATH)/asterisk/prepare_test_sources.sh

asterisk.refresh: asterisk.clean asterisk.generate sccp.ctags sccp.cscope

################################################################################
# dialplan
################################################################################

.PHONY : dialplan.sync dialplan.reload dialplan.reload dialplan.umount
dialplan.reload:
	ssh -q $(XIVO_HOSTNAME) 'asterisk -rx "dialplan reload"'

dialplan.sync: dialplan.umount sync.bootstrap
	rsync -av --delete --exclude "*.git" --exclude "*.tox" $(DIALPLAN_LOCAL_PATH)/ $(XIVO_HOSTNAME):~/dev/dialplan
	ssh -q $(XIVO_HOSTNAME) 'mount --bind ~/dev/dialplan/ $(DIALPLAN_REMOTE_PATH)'

dialplan.umount:
	ssh -q $(XIVO_HOSTNAME) 'umount $(DIALPLAN_REMOTE_PATH) || true'


################################################################################
# lib-rest-client
################################################################################

.PHONY : lib-rest-client.mount
lib-rest-client.mount:
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/xivo_lib_rest_client type\" || mount --bind /var/dev/xivo/xivo-lib-rest-client/xivo_lib_rest_client ${REMOTE_PYTHON3PATH}/xivo_lib_rest_client"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/xivo_lib_rest_client type\" || mount --bind /var/dev/xivo/xivo-lib-rest-client/xivo_lib_rest_client ${REMOTE_PYTHONPATH}/xivo_lib_rest_client"

lib-rest-client.umount:
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/xivo_lib_rest_client type\" && umount ${REMOTE_PYTHON3PATH}/xivo_lib_rest_client || true"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/xivo_lib_rest_client type\" && umount ${REMOTE_PYTHONPATH}/xivo_lib_rest_client || true"


.PHONY : dird-client.sync
dird-client.sync:
	$(SYNC) --delete $(XIVO_PATH)/xivo-dird-client $(XIVO_HOSTNAME):/tmp
	ssh $(XIVO_HOSTNAME) 'cd /tmp/xivo-dird-client && python setup.py develop'


################################################################################
# confd-client
################################################################################

.PHONY : confd-client.sync confd-client.umount confd-client.clean

confd-client.sync: confd-client.umount confd-client.clean sync.bootstrap
	rsync -av --delete --exclude "*.git" --exclude "*.tox" $(CONFD_CLIENT_PATH)/ $(XIVO_HOSTNAME):~/dev/xivo-confd-client
	ssh -q $(XIVO_HOSTNAME) "cd ~/dev/xivo-confd-client && PYTHONPATH=${TMP_PYTHONPATH} python setup.py install --prefix=~/build"
	ssh -q $(XIVO_HOSTNAME) 'mount --bind ~/dev/xivo-confd-client/xivo_confd_client ${REMOTE_PYTHONPATH}/xivo_confd_client'
	ssh -q $(XIVO_HOSTNAME) "mount --bind ~/dev/xivo-confd-client/xivo_confd_client.egg-info ${REMOTE_PYTHONPATH}/xivo_confd_client-1.1.2.egg-info"

confd-client.umount:
	ssh -q $(XIVO_HOSTNAME) 'umount ${REMOTE_PYTHONPATH}/xivo_confd_client || true'
	ssh -q $(XIVO_HOSTNAME) 'umount ${REMOTE_PYTHONPATH}/xivo_confd_client-*.egg-info || true'

confd-client.clean:
	rm -rf $(CONFD_CLIENT_PATH)/.tox
	find $(CONFD_CLIENT_PATH) -name '*.pyc' -delete

################################################################################
# auth-client
################################################################################

.PHONY : auth-client.sync
auth-client.sync:
	$(SYNC) --delete $(XIVO_PATH)/xivo-auth-client $(XIVO_HOSTNAME):/tmp
	ssh $(XIVO_HOSTNAME) 'cd /tmp/xivo-auth-client && python setup.py develop'

################################################################################
# monitoring
################################################################################

.PHONY : monitoring.mount monitoring.umount
monitoring.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "cat /proc/mounts | awk '{ print $2 }' | grep -q /usr/share/xivo-monitoring/checks || mount --bind /var/dev/xivo/xivo-monitoring/checks /usr/share/xivo-monitoring/checks"

monitoring.umount:
	ssh $(XIVO_HOSTNAME) "cat /proc/mounts | awk '{ print $2 }' | grep -q /usr/share/xivo-monitoring/checks && umount /usr/share/xivo-monitoring/checks || true"


################################################################################
# ctid-ng-client
################################################################################

.PHONY: ctid-ng-client.sync ctid-ng-client.umount ctid-ng-client.clean
ctid-ng-client.sync: ctid-ng-client.umount ctid-ng-client.clean sync.bootstrap
	rsync -av --delete --exclude "*.git" --exclude "*.tox" $(CTID_NG_CLIENT_PATH)/ $(XIVO_HOSTNAME):~/dev/xivo-ctid-ng-client
	ssh -q $(XIVO_HOSTNAME) "cd ~/dev/xivo-ctid-ng-client && PYTHONPATH=${TMP_PYTHONPATH} python setup.py install --prefix=~/build"
	ssh -q $(XIVO_HOSTNAME) 'mount --bind ~/dev/xivo-ctid-ng-client/xivo_ctid_ng_client ${REMOTE_PYTHONPATH}/xivo_ctid_ng_client'
	ssh -q $(XIVO_HOSTNAME) "mount --bind ~/dev/xivo-ctid-ng-client/xivo_ctid_ng_client.egg-info ${REMOTE_PYTHONPATH}/xivo_ctid_ng_client-0.1.egg-info"

ctid-ng-client.umount:
	ssh -q $(XIVO_HOSTNAME) 'umount ${REMOTE_PYTHONPATH}/xivo_ctid_ng_client || true'
	ssh -q $(XIVO_HOSTNAME) 'umount ${REMOTE_PYTHONPATH}/xivo_ctid_ng_client-*.egg-info || true'

ctid-ng-client.clean:
	rm -rf $(CTID_NG_CLIENT_PATH)/.tox
	find $(CTID_NG_CLIENT_PATH) -name '*.pyc' -delete

################################################################################
# wazo-plugind
################################################################################
.PHONY : plugind.mount plugind.umount
plugind.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/wazo_plugind type\" || mount --bind /var/dev/xivo/wazo-plugind/wazo_plugind ${REMOTE_PYTHON3PATH}/wazo_plugind"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on /usr/lib/wazo-plugind/templates type\" || mount --bind /var/dev/xivo/wazo-plugind/templates /usr/lib/wazo-plugind/templates"

plugind.umount:
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on /usr/lib/wazo-plugind/templates type\" && umount /usr/lib/wazo-plugind/templates || true"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/wazo_plugind type\" && umount ${REMOTE_PYTHON3PATH}/wazo_plugind || true"

################################################################################
# wazo-webhookd
################################################################################
.PHONY : webhookd.mount webhookd.umount webhookd.sync webhookd.db-upgrade webhookd.db-downgrade
webhookd.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/wazo_webhookd type\" || mount --bind /var/dev/xivo/wazo-webhookd/wazo_webhookd ${REMOTE_PYTHON3PATH}/wazo_webhookd"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on /usr/share/wazo-webhookd/alembic type\" || mount --bind /var/dev/xivo/wazo-webhookd/alembic /usr/share/wazo-webhookd/alembic"

webhookd.umount:
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/wazo_webhookd type\" && umount ${REMOTE_PYTHON3PATH}/wazo_webhookd || true"
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on /usr/share/wazo-webhookd/alembic type\" && umount /usr/share/wazo-webhookd/alembic || true"

webhookd.sync: webhookd.mount
	ssh $(XIVO_HOSTNAME) 'cd /var/dev/xivo/wazo-webhookd && python3 setup.py develop'

webhookd.db-upgrade:
	ssh -q $(XIVO_HOSTNAME) 'cd /usr/share/wazo-webhookd && alembic -c alembic.ini upgrade head'

webhookd.db-downgrade:
	ssh -q $(XIVO_HOSTNAME) 'cd /usr/share/wazo-webhookd && alembic -c alembic.ini downgrade -1'

################################################################################
# wazo-plugind-cli
################################################################################
.PHONY : plugind-cli.mount plugind-cli.umount
plugind-cli.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/wazo_plugind_cli type\" || mount --bind /var/dev/xivo/wazo-plugind-cli/wazo_plugind_cli ${REMOTE_PYTHON3PATH}/wazo_plugind_cli"

plugind-cli.umount:
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/wazo_plugind_cli type\" && umount ${REMOTE_PYTHON3PATH}/wazo_plugind_cli || true"


################################################################################
# xivo-websocketd
################################################################################
.PHONY: websocketd.mount websocketd.umount
websocketd.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHON3PATH}/xivo_websocketd type\" || mount --bind /var/dev/xivo/xivo-websocketd/xivo_websocketd ${REMOTE_PYTHON3PATH}/xivo_websocketd"

websocketd.umount:
	ssh $(XIVO_HOSTNAME) "umount ${REMOTE_PYTHON3PATH}/xivo_websocketd || true"

.PHONY: token.admin token.user
token.admin:
	@read -p "Username: " username; \
	curl -ksX POST --header 'Content-Type: application/json' --header 'Accept: application/json' -u $$username  -d '{"backend": "xivo_service", "expiration": 36000}' "https://${XIVO_HOSTNAME}:9497/0.1/token" | jq -r '.[] | .token'

token.user:
	@read -p "Username: " username; \
	curl -ksX POST --header 'Content-Type: application/json' --header 'Accept: application/json' -u $$username  -d '{"backend": "xivo_user", "expiration": 36000}' "https://${XIVO_HOSTNAME}:9497/0.1/token" | jq -r '.[] | .token'

################################################################################
# admin-ui-plugins
################################################################################
.PHONY: admin-ui-market.mount admin-ui-market.umount
admin-ui-market.mount: xivo.mount
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/wazo_admin_ui_market type\" || mount --bind /var/dev/xivo/wazo-admin-ui-market/wazo_admin_ui_market ${REMOTE_PYTHONPATH}/wazo_admin_ui_market"

admin-ui-market.umount:
	ssh $(XIVO_HOSTNAME) "mount | grep -q \"on ${REMOTE_PYTHONPATH}/wazo_admin_ui_market type\" && umount ${REMOTE_PYTHONPATH}/wazo_admin_ui_market || true"
