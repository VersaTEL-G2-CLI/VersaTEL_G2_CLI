# #coding:utf-8
# # import prettytable as pt
# # import colorama as ca
# from linstordb import DataProcess as DP
#
# #上色装饰器
#
# class ViewShow():
#     table = pt.PrettyTable()
#
#     def __init__(self):
#         ca.init(autoreset=True)
#         self.pd = DP()
#
#
#     def node_all(self):
#         # node_all_tb = pt.PrettyTable()
#         self.table.field_names = ["node", "node type", "res num", "stp num", "addr", "status"]
#         for i in self.pd.process_data_node_all():
#             self.table.add_row(i)
#         print(self.table)
#
#     def node_one(self,node):
#         node_one_tb = pt.PrettyTable()
#         node_one_tb.field_names = ['res_name','stp_name','size','device_name','used','status']
#         for i in self.pd.process_data_node_specific(node):
#             node_one_tb.add_row(i)
#
#         stp_all_tb = pt.PrettyTable()
#         stp_all_tb.field_names = ['stp_name','node_name','res_num','driver','pool_name','free_size','total_size','snapshots','status']
#         for i in self.pd.process_data_stp_all_of_node(node):
#             stp_all_tb.add_row(i)
#
#         try:
#             print("node:%s\nnodetype:%s\nresource num:%s\nstoragepool num:%s\naddr:%s\nstatus:%s"%self.pd.process_data_node_one(node))
#             print(node_one_tb)
#             print(stp_all_tb)
#         except TypeError:
#             print('Node %s does not exist.'%node)
#
#
#
#     def resource_all(self):
#         resource_all_tb = pt.PrettyTable()
#         resource_all_tb.field_names = ["resource","mirror_way","size","device_name","used"]
#         for i in self.pd.process_data_resource_all():
#             resource_all_tb.add_row(i)
#         print(resource_all_tb)
#
#     def resource_one(self,resource):
#         resource_one_tb = pt.PrettyTable()
#         resource_one_tb.field_names = ['node_name','stp_name','drbd_role','status']
#         for i in self.pd.process_data_resource_specific(resource):
#             resource_one_tb.add_row(i)
#         try:
#             print("resource:%s\nmirror_way:%s\nsize:%s\ndevice_name:%s\nused:%s"%self.pd.process_data_resource_one(resource))
#             print(resource_one_tb)
#         except TypeError:
#             print ('Resource %s does not exist.' % resource)
#
#     def storagepool_all(self):
#         stp_all_tb = pt.PrettyTable()
#         stp_all_tb.field_names = ['stp_name','node_name','res_num','driver','pool_name','free_size','total_size','snapshots','status']
#         for i in self.pd.process_data_stp_all():
#             stp_all_tb.add_row(i)
#         print(stp_all_tb)
#
#     def storagepool_one(self,stp):
#         stp_specific = pt.PrettyTable()
#         stp_specific.field_names = ['res_name','size','device_name','used','status']
#         for i in self.pd.process_data_stp_specific(stp):
#             stp_specific.add_row(i)
#         node_num = self.pd._node_num_of_storagepool(stp)
#         node_name = self.pd._node_name_of_storagepool(stp)
#         if node_num == 0:
#             print('The storagepool does not exist')
#         elif node_num == 1:
#             print('Only one node (%s) exists in the storage pool named %s'%(node_name,stp))
#             print(stp_specific)
#         else:
#             node_name = ' and '.join(node_name)
#             print('The storagepool name for %s nodes is %s,they are %s.'%(node_num,stp,node_name))
#             print(stp_specific)
#
#
