#coding:utf-8

import argparse
import sys
# import view
from stor_cmds import Action as stor_action
import usage
import linstordb

import os
from crm_resouce import crm
from getlinstor import GetLinstor
from iscsi_json import JSON_OPERATION
from cli_socketclient import SocketSend

#多节点创建resource时，storapoo多于node的异常类
class NodeLessThanSPError(Exception):
    pass


class CLI():
    def __init__(self):
        self.parser_vtel()
        self.parser_stor()
        self.parser_iscsi()
        self.args = self.vtel.parse_args()
        self.judge()


    def parser_vtel(self):
        self.vtel = argparse.ArgumentParser(prog='vtel')
        sub_vtel = self.vtel.add_subparsers(dest='vtel_sub')

        # add all sub parse
        self.vtel_stor = sub_vtel.add_parser('stor',help='Management operations for LINSTOR',add_help=False,usage=usage.stor)
        self.vtel_iscsi = sub_vtel.add_parser('iscsi',help='Management operations for iSCSI',add_help=False)
        self.vtel_fc = sub_vtel.add_parser('fc',help='for fc resource management...',add_help=False)
        self.vtel_ceph = sub_vtel.add_parser('ceph',help='for ceph resource management...',add_help=False)
        self.vtel_stor.add_argument('-gui',dest='db',action='store_true',help=argparse.SUPPRESS,default=False)

    def parser_stor(self):
        ##stor
        sub_stor = self.vtel_stor.add_subparsers(dest='stor_sub')
        self.stor_node = sub_stor.add_parser('node', aliases='n', help='Management operations for node',usage=usage.node)
        self.stor_resource = sub_stor.add_parser('resource', aliases='r', help='Management operations for storagepool',usage=usage.resource)
        self.stor_storagepool = sub_stor.add_parser('storagepool', aliases=['sp'],help='Management operations for storagepool',usage=usage.storagepool)
        self.stor_snap = sub_stor.add_parser('snap', aliases=['sn'], help='Management operations for snapshot')
        # self.stor_gui = sub_stor.add_parser('gui',help='for GUI')

        ###node
        sub_node = self.stor_node.add_subparsers(dest='node_sub')
        self.node_create = sub_node.add_parser('create', aliases='c', help='Create the node',usage=usage.node_create)
        self.node_modify = sub_node.add_parser('modify', aliases='m', help='Modify the node',usage=usage.node_modify)
        self.node_delete = sub_node.add_parser('delete', aliases='d', help='Delete the node',usage=usage.node_delete)
        self.node_show = sub_node.add_parser('show', aliases='s', help='Displays the node view',usage=usage.node_show)

        ###resource
        sub_resource = self.stor_resource.add_subparsers(dest='resource_sub')
        self.resource_create = sub_resource.add_parser('create', aliases='c', help='Create the resource',usage=usage.resource_create)
        self.resource_modify = sub_resource.add_parser('modify', aliases='m',help='Modify the resource',usage=usage.resource_modify)
        self.resource_delete = sub_resource.add_parser('delete', aliases='d',help='Delete the resource',usage=usage.resource_delete)
        self.resource_show = sub_resource.add_parser('show', aliases='s', help='Displays the resource view',usage=usage.resource_show)

        ###storagepool
        sub_storagepool = self.stor_storagepool.add_subparsers(dest='storagepool_sub')
        self.storagepool_create = sub_storagepool.add_parser('create', aliases='c',help='Create the storagpool',usage=usage.storagepool_create)
        self.storagepool_modify = sub_storagepool.add_parser('modify', aliases='m',help='Modify the storagpool',usage=usage.storagepool_modify)
        self.storagepool_delete = sub_storagepool.add_parser('delete', aliases='d',help='Delete the storagpool',usage=usage.storagepool_delete)
        self.storagepool_show = sub_storagepool.add_parser('show', aliases='s',help='Displays the storagpool view',usage=usage.storagepool_show)

        ###snap
        sub_snap = self.stor_snap.add_subparsers(dest='snap_sub')
        self.snap_create = sub_snap.add_parser('create', help='Create the snapshot')
        self.snap_modify = sub_snap.add_parser('modify', help='Modify the snapshot')
        self.snap_delete = sub_snap.add_parser('delete', help='Delete the snapshot')
        self.snap_show = sub_snap.add_parser('show', help='Displays the snapshot view')

        ###stor node create
        self.node_create.add_argument('node', metavar='NODE', action='store', help='Name of the new node, must match the nodes hostname')
        self.node_create.add_argument('-ip', dest='ip', action='store', help='IP address of the new node, if not specified it will be resolved by the name.', required=True)
        self.node_create.add_argument('-nt', dest='nodetype', action='store', help='node type: {Controller,Auxiliary,Combined,Satellite}',required=True)
        self.node_create.add_argument('-gui',dest='gui',action='store_true',help=argparse.SUPPRESS,default=False)

        ###stor node modify

        ###stor node delete
        self.node_delete.add_argument('node', metavar='NODE',action='store', help=' Name of the node to remove')
        self.node_delete.add_argument('-y', dest='yes', action='store_true',help='Skip to confirm selection', default=False)
        self.node_delete.add_argument('-gui', dest='gui', action='store_true', help=argparse.SUPPRESS, default=False)

        ###stor node show
        self.node_show.add_argument('node', metavar='NODE',help='Print information about the node in LINSTOR cluster', action='store', nargs='?', default=None)
        self.node_show.add_argument('--no-color',dest='nocolor',help='Do not use colors in output.', action='store_true',default=False)
        ###stor resource create

        self.resource_create.add_argument('resource', metavar='RESOURCE',action='store',help='Name of the resource')
        self.resource_create.add_argument('-s', dest='size', action='store',help=' Size of the resource.In addition to creating diskless resource, you must enter SIZE.'
                                                                                 'Valid units: B, K, kB, KiB, M, MB,MiB, G, GB, GiB, T, TB, TiB, P, PB, PiB.')
        self.resource_create.add_argument('-gui', dest='gui', action='store_true', help=argparse.SUPPRESS, default=False)


        #自动创建在num个节点上
        group_auto = self.resource_create.add_argument_group(title='auto create')
        group_auto.add_argument('-a', dest='auto', action='store_true', default=False,help='Auto create method Automatic create')
        group_auto.add_argument('-num', dest='num', action='store', help='Number of nodes specified by auto creation method', type=int)

        #手动选择节点和存储池
        group_manual = self.resource_create.add_argument_group(title='manual create')
        group_manual.add_argument('-n', dest='node', action='store', nargs='+',help='Name of the node to deploy the resource')
        group_manual.add_argument('-sp', dest='storagepool',nargs='+', help='Storage pool name to use.')

        #创建diskless
        group_manual_diskless = self.resource_create.add_argument_group(title='diskless create')
        group_manual_diskless.add_argument('-diskless', action='store_true', default=False, dest='diskless',help='Will add a diskless resource on all non replica nodes.')

        #创建mirror way，可用于自动创建和手动创建
        group_add_mirror = self.resource_create.add_argument_group(title='add mirror way')
        group_add_mirror.add_argument('-am',action='store_true', default=False, dest='add_mirror',help='Add resource mirror on other nodes')

        ###stor resource modify
        self.resource_modify.add_argument('resource',metavar='RESOURCE',action='store', help='resources to be modified')
        self.resource_modify.add_argument('-n', dest='node', action='store', help='node to be modified')
        self.resource_modify.add_argument('-sp', dest='storagepool', action='store', help='Storagepool')

        ###stor resource delete
        self.resource_delete.add_argument('resource',metavar='RESOURCE',action='store', help='Name of the resource to delete')
        self.resource_delete.add_argument('-n', dest='node', action='store', help='Name of the node')
        self.resource_delete.add_argument('-y', dest='yes', action='store_true',help='Skip to confirm selection', default=False)
        self.resource_delete.add_argument('-gui', dest='gui', action='store_true', help=argparse.SUPPRESS, default=False)

        ###stor resource show
        self.resource_show.add_argument('resource',metavar='RESOURCE',help='Print information about the resource in LINSTOR cluster', action='store', nargs='?')
        self.resource_show.add_argument('--no-color',dest='nocolor',help='Do not use colors in output.', action='store_true',default=False)

        ###stor storagepool create
        self.storagepool_create.add_argument('storagepool', metavar='STORAGEPOOL',action='store', help='Name of the new storage pool')
        self.storagepool_create.add_argument('-n', dest='node', action='store', help='Name of the node for the new storage pool',required=True)
        self.storagepool_create.add_argument('-gui', dest='gui', action='store_true', help=argparse.SUPPRESS, default=False)
        group_type = self.storagepool_create.add_mutually_exclusive_group()
        group_type.add_argument('-lvm', dest='lvm', action='store', help='The Lvm volume group to use.')
        group_type.add_argument('-tlv', dest='tlv', action='store', help='The LvmThin volume group to use. The full name of the thin pool, namely VG/LV')

        ###stor storagepool modify

        ###stor storagepool delete
        self.storagepool_delete.add_argument('storagepool',metavar='STORAGEPOOL',help='Name of the storage pool to delete', action='store')
        self.storagepool_delete.add_argument('-n', dest='node', action='store', help='Name of the Node where the storage pool exists',required=True)
        self.storagepool_delete.add_argument('-y', dest='yes', action='store_true',help='Skip to confirm selection', default=False)
        self.storagepool_delete.add_argument('-gui', dest='gui', action='store_true', help=argparse.SUPPRESS, default=False)

        ###stor storgagepool show
        self.storagepool_show.add_argument('storagepool',metavar='STORAGEPOOL',help='Print information about the storage pool in LINSTOR cluster', action='store',nargs='?')
        self.storagepool_show.add_argument('--no-color',dest='nocolor',help='Do not use colors in output.', action='store_true',default=False)

        ###stor snap create

        ###stor snap modify

        ###stor snap delete

        ###stor snap show

    def parser_iscsi(self):
        ##iscsi
        sub_vtel_iscsi = self.vtel_iscsi.add_subparsers(dest='iscsi_next')
        self.vtel_iscsi_create = sub_vtel_iscsi.add_parser('create', help='iscsi resource create...', add_help=False)
        self.vtel_iscsi_show = sub_vtel_iscsi.add_parser('show', help='iscsi resource modify...', add_help=False)
        self.vtel_iscsi_modify = sub_vtel_iscsi.add_parser('modify', help='iscsi resource create...', add_help=False)
        self.vtel_iscsi_delete = sub_vtel_iscsi.add_parser('delete', help='iscsi resource modify...', add_help=False)





    def case_node(self):
        args = self.args
        parser_create = self.node_create
        parser_delete = self.node_delete

        def node_create():
            if args.gui:
                handle = cli_socketclient.SocketSend()
                handle.send_result(stor_action.create_node,args.node, args.ip, args.nodetype)
            elif args.node and args.nodetype and args.ip:
                stor_action.create_node(args.node, args.ip, args.nodetype)
            else:
                parser_create.print_help()

        def node_modify():
            pass

        def node_delete():
            def excute():
                if args.gui:
                    print('for gui delete node')
                else:
                    stor_action.delete_node(args.node)


            def _delete_comfirm():#命名，是否删除
                if stor_action.confirm_del():
                    excute()
                else:
                    print('Delete canceled')

            def _skip_confirm():#是否跳过确认
                if args.yes:
                    excute()
                else:
                    _delete_comfirm()

            _skip_confirm() if args.node else parser_delete.print_help()


        def node_show():
            tb = linstordb.OutputData()
            if args.nocolor:
                tb.show_node_one(args.node) if args.node else tb.node_all()
            else:
                tb.show_node_one_color(args.node) if args.node else tb.node_all_color()


        # 对输入参数的判断（node的下一个参数）
        if self.args.node_sub in ['create','c']:
            node_create()
        elif self.args.node_sub in ['modify','m']:
            node_modify()
        elif self.args.node_sub in ['delete','d']:
            node_delete()
        elif self.args.node_sub in ['show','s']:
            node_show()
        else:
            self.stor_node.print_help()

    def case_resource(self):
        args = self.args
        parser_create = self.resource_create
        parser_modify = self.resource_modify
        parser_delete = self.resource_delete
        """
        resource create 使用帮助
        自动创建：vtel stor create RESOURCE -s SIZE -a -num NUM
        手动创建：vtel stor create RESOURCE -s SIZE -n NODE -sp STORAGEPOOL
        创建diskless：vtel stor create RESOURCE -diskless NODE
        添加mirror到其他节点(手动):vtel stor create RESOURCE -am -n NODE -sp STORAGEPOOL
        添加mirror到其他节点(自动):vtel stor create RESOURCE -am -a -num NUM
        """
        def resource_create():
            # def is_args_correct():
            #     if len(args.node) >= len(args.storagepool):
            #         return True


            """
            以下注释代码为创建resource判断分支的另一种写法
            把创建resource的三种模式：正常创建（包括自动和手动），创建diskless，添加mirror分别封装
            最后再执行
            """
            #指定node和storagepool数量的规范判断，符合则继续执行
            def is_args_correct():
                if len(args.node) < len(args.storagepool):
                    raise NodeLessThanSPError('指定的storagepool数量应少于node数量')

            #特定模式必需的参数
            list_auto_required = [args.auto, args.num]
            list_manual_required = [args.node, args.storagepool]


            #正常创建resource
            def create_normal_resource():
                #正常创建resource禁止输入的参数
                list_normal_forbid = [args.diskless, args.add_mirror]
                if not args.size:
                    return
                if any(list_normal_forbid):
                    return
                if all(list_auto_required) and not any(list_manual_required):
                    #For GUI
                    if args.gui:
                        handle = cli_socketclient.SocketSend()
                        handle.send_result(stor_action.create_res_auto,args.resource, args.size, args.num)
                        return True
                    #CLI
                    else:
                        stor_action.create_res_auto(args.resource, args.size, args.num)
                        return True
                elif all(list_manual_required) and not any(list_auto_required):
                    try:
                        is_args_correct()
                    except NodeLessThanSPError:
                        print('The number of nodes and storage pools do not meet the requirements')
                        return True
                    else:
                        #For GUI
                        if args.gui:
                            handle = cli_socketclient.SocketSend()
                            handle.send_result(stor_action.create_res_manual,args.resource,args.size,args.node,args.storagepool)
                            return True
                        #CLI
                        else:
                            stor_action.create_res_manual(args.resource,args.size,args.node,args.storagepool)
                            return True

            #创建resource的diskless资源条件判断，符合则执行
            def create_diskless_resource():
                list_diskless_forbid = [args.auto, args.num, args.storagepool, args.add_mirror,args.size]
                if not args.node:
                    return
                if not any(list_diskless_forbid):
                    if args.gui:
                        handle = cli_socketclient.SocketSend()
                        handle.send_result(stor_action.create_res_diskless,args.node, args.resource)
                        return True
                    else:
                        stor_action.create_res_diskless(args.node, args.resource)
                        return True

            #添加mirror
            def add_resource_mirror():
                # 添加mirror禁止输入的参数
                list_add_mirror_forbid = [args.diskless, args.size]
                if not args.add_mirror:
                    return
                if any(list_add_mirror_forbid):
                    return
                if all(list_auto_required) and not any(list_manual_required):
                    #For GUI
                    if args.gui:
                        handle = cli_socketclient.SocketSend()
                        handle.send_result(stor_action.add_mirror_auto,args.resource,args.num)
                        return True
                    else:
                        stor_action.add_mirror_auto(args.resource,args.num)
                        return True
                elif all(list_manual_required) and not any(list_auto_required):
                    try:
                        is_args_correct()
                    except NodeLessThanSPError:
                        print('The number of nodes does not meet the requirements')
                        return True
                    else:
                        #For GUI
                        if args.gui:
                            handle = cli_socketclient.SocketSend()
                            handle.send_result(stor_action.add_mirror_manual,args.resource,args.node,args.storagepool)
                            return True
                        else:
                            stor_action.add_mirror_manual(args.resource,args.node,args.storagepool)
                            return True


            # 总执行
            if create_normal_resource():
                pass
            elif create_diskless_resource():
                pass
            elif add_resource_mirror():
                pass
            else:
                parser_create.print_help()



            # # 对应创建模式必需输入的参数和禁止输入的参数
            # list_auto_required = [args.auto, args.num]
            # list_auto_forbid = [args.node, args.storagepool, args.diskless,args.add_mirror]
            # list_manual_required = [args.node, args.storagepool]
            # list_manual_forbid = [args.auto, args.num, args.diskless,args.add_mirror]
            # list_diskless_forbid = [args.auto, args.num, args.storagepool,args.add_mirror]
            #
            #
            # if args.size:
            #     #自动创建条件判断，符合则执行
            #     if all(list_auto_required) and not any(list_auto_forbid):
            #         stor_action.create_res_auto(args.resource, args.size, args.num)
            #     #手动创建条件判断，符合则执行
            #     elif all(list_manual_required) and not any(list_manual_forbid):
            #         if is_args_correct():
            #             stor_action.create_res_manual(args.resource,args.size,args.node,args.storagepool)
            #         else:
            #             parser_create.print_help()
            #     else:
            #         parser_create.print_help()
            #
            #
            # elif args.diskless:
            #     # 创建resource的diskless资源条件判断，符合则执行
            #     if args.node and not any(list_diskless_forbid):
            #         stor_action.create_res_diskless(args.node, args.resource)
            #     else:
            #         parser_create.print_help()
            #
            # elif args.add_mirror:
            #     #手动添加mirror条件判断，符合则执行
            #     if all([args.node,args.storagepool]) and not any([args.auto, args.num]):
            #         if is_args_correct():
            #             stor_action.add_mirror_manual(args.resource,args.node,args.storagepool)
            #         else:
            #             parser_create.print_help()
            #     #自动添加mirror条件判断，符合则执行
            #     elif all([args.auto,args.num]) and not any([args.node,args.storagepool]):
            #         stor_action.add_mirror_auto(args.resource,args.num)
            #     else:
            #         parser_create.print_help()
            #
            # else:
            #     parser_create.print_help()


        # resource修改功能，未开发
        def resource_modify():
            if args.resource:
                if args.size:
                    print('调整resource的size')
                elif args.node and args.diskless:
                    print('将某节点上某个diskful的资源调整为diskless')

                elif args.node and args.storagepool:
                    print('将某节点上某个diskless的资源调整为diskful')
            else:
                parser_modify.print_help()

        # resource删除判断
        def resource_delete():
            def excute():#判断是否指定节点
                if args.node:
                    if args.gui:
                        print('for gui')
                    else:
                        stor_action.delete_resource_des(args.node, args.resource)
                elif not args.node:
                    if args.gui:
                        print('for gui')
                    else:
                        stor_action.delete_resource_all(args.resource)

            def _delete_comfirm():#命名，是否删除
                if stor_action.confirm_del():
                    excute()
                else:
                    print('Delete canceled')

            def _skip_confirm():#是否跳过确认
                if args.yes:
                    excute()
                else:
                    _delete_comfirm()

            _skip_confirm() if args.resource else parser_delete.print_help()


            # if args.resource:
            #     if args.node:
            #         if args.yes:
            #             stor_action.delete_resource_des(args.node, args.resource)
            #         else:
            #             if stor_action.confirm_del():
            #                 stor_action.delete_resource_des(args.node, args.resource)
            #     elif not args.node:
            #         if args.yes:
            #             stor_action.delete_resource_all(args.resource)
            #         else:
            #             if stor_action.confirm_del():
            #                 stor_action.delete_resource_all(args.resource)
            # else:
            #     parser_delete.print_help()

        def resource_show():
            tb = linstordb.OutputData()
            if args.nocolor:
                tb.show_res_one(args.resource) if args.resource else tb.res_all()
            else:
                tb.show_res_one_color(args.resource) if args.resource else tb.res_all_color()


        # 对输入参数的判断（resource的下一个参数）
        if args.resource_sub in ['create','c']:
            resource_create()
        elif args.resource_sub in ['modify','m']:
            resource_modify()
        elif args.resource_sub in ['delete','d']:
            resource_delete()
        elif args.resource_sub in ['show','s']:
            resource_show()
        else:
            self.stor_resource.print_help()

    def case_storagepool(self):
        args = self.args
        parser_create = self.storagepool_create
        parser_modify = self.storagepool_modify
        parser_delete = self.storagepool_delete

        def storagepool_create():
            if args.storagepool and args.node:
                if args.lvm:
                    if args.gui:
                        handle = cli_socketclient.SocketSend()
                        handle.send_result(stor_action.create_storagepool_lvm,args.node, args.storagepool, args.lvm)
                    else:
                        stor_action.create_storagepool_lvm(args.node, args.storagepool, args.lvm)
                elif args.tlv:
                    if args.gui:
                        handle = cli_socketclient.SocketSend()
                        handle.send_result(stor_action.create_storagepool_thinlv,args.node, args.storagepool, args.tlv)
                    else:
                        stor_action.create_storagepool_thinlv(args.node, args.storagepool, args.tlv)
                else:
                    parser_create.print_help()
            else:
                parser_create.print_help()


        def storagepool_modify():
            pass


        def storagepool_delete():
            def excute():
                if args.gui:
                    print('for gui')
                else:
                    stor_action.delete_storagepool(args.node, args.storagepool)

            def _delete_comfirm():#命名，是否删除
                if stor_action.confirm_del():
                    excute()
                else:
                    print('Delete canceled')

            def _skip_confirm():#是否跳过确认
                if args.yes:
                    excute()
                else:
                    _delete_comfirm()

            _skip_confirm() if args.storagepool else parser_delete.print_help()


        def storagepool_show():
            tb = linstordb.OutputData()
            if args.nocolor:
                tb.show_sp_one(args.storagepool) if args.storagepool else tb.sp_all()
            else:
                tb.show_sp_one_color(args.storagepool) if args.storagepool else tb.sp_all_color()


        if args.storagepool_sub in ['create','c']:
            storagepool_create()
        elif args.storagepool_sub in ['modify','m']:
            storagepool_modify()
        elif args.storagepool_sub in ['delete','d']:
            storagepool_delete()
        elif args.storagepool_sub in ['show','s']:
            storagepool_show()
        else:
            self.stor_storagepool.print_help()

    #pass
    def case_snap(self):
        args = self.args
        parser = self.storagepool_create

        def snap_create():
            args = self.args
            parser = self.storagepool_create

            if args.storagepool and args.node:
                if args.lvm:
                    stor_action.create_storagepool_lvm(args.node, args.storagepool, args.lvm)
                elif args.tlv:
                    stor_action.create_storagepool_thinlv(args.node, args.storagepool, args.tlv)
            else:
                parser.print_help()

        def snap_modify():
            pass

        def snap_delete():
            pass

        def snap_show():
            pass


        if args.snap_sub == 'create':
            snap_create()
        elif args.snap_sub == 'modify':
            snap_modify()
        elif args.snap_sub == 'delete':
            snap_delete()
        elif args.snap_sub == 'show':
            snap_show()
        else:
            self.stor_snap.print_help()

    #gui端 get DB
    def getdb(self):
        mes = cli_socketclient.SocketSend()
        mes.send_result(mes.sql_script)#get sql_scipt

    def judge(self):
        args = self.args
        if args.vtel_sub == 'stor':
            if self.args.stor_sub in ['node','n']:
                self.case_node()
            elif self.args.stor_sub in ['resource','r']:
                self.case_resource()
            elif self.args.stor_sub in ['storagepool','sp']:
                self.case_storagepool()
            elif self.args.stor_sub in ['snap','sn']:
                self.case_snap()

            elif self.args.db:
                self.getdb()
            else:
                self.vtel_stor.print_help()

        elif 'iscsi' in sys.argv:
            if 'show' in sys.argv:
                pass

        else:
            self.vtel.print_help()

if __name__ == '__main__':
    CLI()
