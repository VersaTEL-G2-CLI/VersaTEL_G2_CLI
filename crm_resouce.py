#coding=utf-8
import re
import subprocess
import time

"""
@author: Zane
@note: VersaTEL-iSCSI获取crm信息
@time: 2020/03/11
@uptime: 2020/04/07
"""
class crm():
	"""docstring for crm_data"""
	def __init__(self):
		
		self.iscsistatu = r'''primitive apple iSCSILogicalUnit \
			params target_iqn="iqn.2019-09.feixitek.com:1" implementation=lio-t lun=5 path="/dev/drbd1000" allowed_initiators="iqn.1993-08.org.debian:01:bc429d5fc3b iqn.1991-05.com.microsoft:win7tian" \
			        meta target-role=Started
			primitive ben iSCSILogicalUnit \
			        params target_iqn="iqn.2019-09.feixitek.com:1" implementation=lio-t lun=2 path="/dev/drbd1005" allowed_initiators="iqn.1993-08.org.debian:01:1cc967493b4 iqn.1993-08.org.debian:01:181885d4e7d7" \
			        meta target-role=Started
			primitive fred iSCSILogicalUnit \
			        params target_iqn="iqn.2019-09.feixitek.com:1" implementation=lio-t lun=4 path="/dev/drbd1003" allowed_initiators="iqn.1993-08.org.debian:01:bc429d5fc3b iqn.1991-05.com.microsoft:win7tian" \
			        meta target-role=Started
			primitive iscsi_target_test iSCSITarget \
			        params iqn="iqn.2019-09.feixitek.com:1" implementation=lio-t portals="10.203.1.33:3260" \
			        op start timeout=20 interval=0 \
			        op stop timeout=20 interval=0 \
			        op monitor interval=20 timeout=40
			primitive p_drbd_linstordb ocf:linbit:drbd \
			        params drbd_resource=linstordb \
			        op monitor interval=29 role=Master \
			        op monitor interval=30 role=Slave \
			        op start interval=0 timeout=240s \
			        op stop interval=0 timeout=100s
			primitive p_fs_linstordb Filesystem \
			        params device="/dev/drbd/by-res/linstordb/0" directory="/var/lib/linstor" fstype=xfs \
			        op start interval=0 timeout=60s \
			        op stop interval=0 timeout=100s \
			        op monitor interval=20s timeout=40s
			primitive p_iscsi_portblock_off_drbd0 portblock \
			        params ip=10.203.1.33 portno=3260 protocol=tcp action=unblock \
			        op start timeout=20 interval=0 \
			        op stop timeout=20 interval=0 \
			        op monitor timeout=20 interval=20
			primitive p_iscsi_portblock_on_drbd0 portblock \
			        params ip=10.203.1.33 portno=3260 protocol=tcp action=block \
			        op start timeout=20 interval=0 \
			        op stop timeout=20 interval=0 \
			        op monitor timeout=20 interval=20
			primitive p_linstor-controller systemd:linstor-controller \
			        op start interval=0 timeout=100s \
			        op stop interval=0 timeout=100s \
			        op monitor interval=30s timeout=100s \
			        meta is-managed=true
			primitive seven iSCSILogicalUnit \
			        params target_iqn="iqn.2019-09.feixitek.com:1" implementation=lio-t lun=1 path="/dev/drbd1006" allowed_initiators="iqn.1993-08.org.debian:01:e3589b7c9ce iqn.1991-05.com.microsoft:win7mark" \
			        op monitor interval=10s \
			        meta target-role=Started
			primitive test iSCSILogicalUnit \
			        params target_iqn="iqn.2019-09.feixitek.com:1" implementation=lio-t lun=3 path="/dev/drbd1004" allowed_initiators="iqn.1993-08.org.debian:01:1cc967493b4 iqn.1993-08.org.debian:01:181885d4e7d7" \
			        meta target-role=Started
			primitive vip IPaddr2 \
			        params ip=10.203.1.33 cidr_netmask=24 \
			        op monitor interval=10 timeout=20
			group g_linstor p_iscsi_portblock_on_drbd0 p_fs_linstordb p_linstor-controller vip iscsi_target_test seven ben test fred apple p_iscsi_portblock_off_drbd0
			ms ms_drbd_linstordb p_drbd_linstordb \
			        meta master-max=1 master-node-max=1 clone-max=2 clone-node-max=1 notify=true
			colocation c_linstor_with_drbd inf: g_linstor ms_drbd_linstordb:Master
			order o_drbd_before_linstor inf: ms_drbd_linstordb:promote g_linstor:start
			property cib-bootstrap-options: \
			        have-watchdog=false \
			        dc-version=1.1.14-70404b0 \
			        cluster-infrastructure=corosync \
			        cluster-name=debian \
			        stonith-enabled=false \
			        no-quorum-policy=ignore '''

		self.resstatu = '''+---------------------------------------------------------------------------------------------------------------+
| Node  | Resource  | StoragePool          | VolumeNr | MinorNr | DeviceName    | Allocated | InUse  |    State |
|===============================================================================================================|
| klay1 | apple     | pool_hdd             | 0        | 1000    | /dev/drbd1000 | 12 MiB    | InUse  | UpToDate |
| klay2 | apple     | DfltDisklessStorPool | 0        | 1000    | /dev/drbd1000 |           | Unused | Diskless |
| klay1 | banana    | pool_hdd             | 0        | 1001    | /dev/drbd1001 | 12 MiB    | InUse  | UpToDate |
| klay2 | banana    | pool_hdd             | 0        | 1001    | /dev/drbd1001 | 12 MiB    | Unused | UpToDate |
| klay1 | ben       | pool_hdd             | 0        | 1005    | /dev/drbd1005 | 12 MiB    | InUse  | UpToDate |
| klay2 | ben       | pool_hdd             | 0        | 1005    | /dev/drbd1005 | 12 MiB    | Unused | UpToDate |
| klay1 | fred      | pool_hdd             | 0        | 1003    | /dev/drbd1003 | 12 MiB    | InUse  | UpToDate |
| klay2 | fred      | pool_hdd             | 0        | 1003    | /dev/drbd1003 | 12 MiB    | Unused | UpToDate |
| klay1 | fst       | pool_hdd             | 0        | 1011    | /dev/drbd1011 | 1.00 GiB  | Unused | UpToDate |
| klay2 | fst       | pool_hdd             | 0        | 1011    | /dev/drbd1011 | 1.00 GiB  | Unused | UpToDate |
| klay1 | linstordb | pool_hdd             | 0        | 1002    | /dev/drbd1002 | 252 MiB   | InUse  | UpToDate |
| klay2 | linstordb | pool_hdd             | 0        | 1002    | /dev/drbd1002 | 252 MiB   | Unused | UpToDate |
| klay2 | pllo      | pllo                 | 0        | 1012    | None          |           | Unused |  Unknown |
| klay1 | seven     | pool_hdd             | 0        | 1006    | /dev/drbd1006 | 12 MiB    | InUse  | UpToDate |
| klay2 | seven     | pool_hdd             | 0        | 1006    | /dev/drbd1006 | 12 MiB    | Unused | UpToDate |
| klay1 | ssss      | pool_hdd             | 0        | 1009    | /dev/drbd1009 | 12 MiB    | Unused | UpToDate |
| klay1 | test      | pool_hdd             | 0        | 1004    | /dev/drbd1004 | 10.00 GiB | InUse  | UpToDate |
| klay2 | test      | pool_hdd             | 0        | 1004    | /dev/drbd1004 | 10.00 GiB | Unused | UpToDate |
| klay2 | xx2       | pool_hdd             | 0        | 1010    | /dev/drbd1010 | 12 MiB    | Unused | UpToDate |
+---------------------------------------------------------------------------------------------------------------+'''

	def re_data(self):
		crmdata = str(self.get_data_crm())
		plogical = re.compile(r'primitive\s(\w*)\s\w*\s\\\s*\w*\starget_iqn="([a-zA-Z0-9.:-]*)"\s[a-z=-]*\slun=(\d*)\spath="([a-zA-Z0-9/]*)"\sallowed_initiators="([a-zA-Z0-9.: -]+)"(?:.*\s*){2}meta target-role=(\w*)')
		pvip = re.compile(r'primitive\s(\w*)\sIPaddr2\s\\\s*\w*\sip=([0-9.]*)\s\w*=(\d*)\s')
		ptarget = re.compile(r'primitive\s(\w*)\s\w*\s\\\s*params\siqn="([a-zA-Z0-9.:-]*)"\s[a-z=-]*\sportals="([0-9.]*):\d*"\s\\')
		redata = [plogical.findall(crmdata), pvip.findall(crmdata), ptarget.findall(crmdata)]
		print("get crm config data")
		# print(redata)
		return redata

	def lsdata(self):
		linstordata = self.resstatu
		return linstordata

	def get_data_crm(self):
		crmconfig = subprocess.getoutput('crm configure show')
		print("do crm configure show")
		return crmconfig

	def get_data_linstor(self):	
		linstorres = subprocess.getoutput('linstor --no-color --no-utf8 r lv')
		print("do linstor r lv")
		return linstorres

	def createres(self,res,hostiqn,targetiqn):
		# print(res)
		# print(hostiqn)
		# print(targetiqn)
		# resname = "addi"
		# target_iqn = "\"iqn.2019-09.feixitek.com:aaa\""
		# lunid = "2"
		# path = "\"/dev/drbd1003\""
		# allowed_initiators = "\"iqn.1993-08.org.debian:01:78ddb2d6247e iqn.1991-05.com.microsoft:win7mark\""
		initiator = " ".join(hostiqn)
		lunid = str(int(res[1][1:]))
		op = " op start timeout=40 interval=0" \
		   " op stop timeout=40 interval=0" \
		   " op monitor timeout=40 interval=15"
		meta = " meta target-role=Stopped"
		mstr = "crm conf primitive " + res[0] \
		    + " iSCSILogicalUnit params target_iqn=\"" + targetiqn \
		    + "\" implementation=lio-t lun=" + lunid \
		    + " path=\"" + res[2] \
		    + "\" allowed_initiators=\"" + initiator +"\"" \
		    + op + meta
		print(mstr)
		createcrm = subprocess.call(mstr,shell=True)
		print ("call",mstr)
		if createcrm == 0:
			print("create iSCSILogicalUnit success")
			return True
		else:
			return False


	def delres(self, res):
		# crm res stop <LUN_NAME>
		stopsub = subprocess.call("crm res stop " + res,shell=True)
		if stopsub == 0:
			print("crm res stop " + res)
			n = 0
			while n < 10:
				n += 1
				if self.resstate(res):
					print(res + " is Started, Wait a moment...")
					time.sleep(1)
				else:
					print(res + " is Stopped")
					break
			else:
				print("Stop ressource " + res + " fail, Please try again.")
				return False
			
			time.sleep(3)
			# crm conf del <LUN_NAME>
			delsub = subprocess.call("crm conf del " + res,shell=True)
			if delsub == 0:
				print("crm conf del " + res)
				return True
			else:
				print("crm delete fail")
				return False
		else:
			print("crm res stop fail")
			return False


	def createco(self, res, target):
		# crm conf colocation <COLOCATION_NAME> inf: <LUN_NAME> <TARGET_NAME> 
		print("crm conf colocation co_" + res + " inf: " + res + " " + target)
		coclocation = subprocess.call("crm conf colocation co_" + res + " inf: " + res + " " + target, shell=True)
		if coclocation == 0:
			print("set coclocation")
			return True
		else:
			return False


	def createor(self, res, target):
		# crm conf order <ORDER_NAME1> <TARGET_NAME> <LUN_NAME>
		print("crm conf order or_" + res + " " + target + " " + res)
		order = subprocess.call("crm conf order or_" + res + " " + target + " " + res, shell=True)
		if order == 0:
			print("set order")
			return True
		else:
			return False


	def resstart(self, res):
		# crm res start <LUN_NAME>
		print("crm res start " + res)
		start = subprocess.call("crm res start " + res,shell=True)
		if start == 0:
			return True
		else:
			return False


	def resstate(self, res):
		crm_config_statu = self.re_data()
		for s in crm_config_statu[0]:
			if s[0] == res:
				if s[-1] == 'Stopped':
					return False
				else:
					return True



