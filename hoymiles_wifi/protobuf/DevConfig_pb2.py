# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: DevConfig.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0f\x44\x65vConfig.proto\"\x91\x01\n\x14\x44\x65vConfigFetchResDTO\x12\x15\n\rresponse_time\x18\x01 \x01(\x05\x12\x16\n\x0etransaction_id\x18\x02 \x01(\x03\x12\x0e\n\x06\x64tu_sn\x18\x03 \x01(\t\x12\x0e\n\x06\x64\x65v_sn\x18\x04 \x01(\t\x12\x17\n\x0f\x63urrent_package\x18\x05 \x01(\x05\x12\x11\n\trule_type\x18\x06 \x01(\x05\"\xf7\x01\n\x14\x44\x65vConfigFetchReqDTO\x12\x14\n\x0crequest_time\x18\x01 \x01(\x05\x12\x16\n\x0etransaction_id\x18\x02 \x01(\x03\x12\x0f\n\x07rule_id\x18\x03 \x01(\x05\x12\x0c\n\x04\x64\x61ta\x18\x04 \x01(\t\x12\x0b\n\x03\x63rc\x18\x05 \x01(\x05\x12\x0e\n\x06\x64tu_sn\x18\x06 \x01(\t\x12\x0e\n\x06\x64\x65v_sn\x18\x07 \x01(\t\x12\x10\n\x08\x63\x66g_data\x18\x08 \x01(\t\x12\x0f\n\x07\x63\x66g_crc\x18\t \x01(\x05\x12\x16\n\x0etotal_packages\x18\n \x01(\x05\x12\x17\n\x0f\x63urrent_package\x18\x0b \x01(\x05\x12\x11\n\trule_type\x18\x0c \x01(\x05\"\x88\x02\n\x12\x44\x65vConfigPutResDTO\x12\x15\n\rresponse_time\x18\x01 \x01(\x05\x12\x16\n\x0etransaction_id\x18\x02 \x01(\x03\x12\x0f\n\x07rule_id\x18\x03 \x01(\x05\x12\x0c\n\x04\x64\x61ta\x18\x04 \x01(\t\x12\x0b\n\x03\x63rc\x18\x05 \x01(\x05\x12\x0e\n\x06\x64tu_sn\x18\x06 \x01(\t\x12\x0e\n\x06\x64\x65v_sn\x18\x07 \x01(\t\x12\x10\n\x08\x63\x66g_data\x18\x08 \x01(\t\x12\x0f\n\x07\x63\x66g_crc\x18\t \x01(\x05\x12\x16\n\x0etotal_packages\x18\n \x01(\x05\x12\x17\n\x0f\x63urrent_package\x18\x0b \x01(\x05\x12\x10\n\x08mi_to_sn\x18\x0c \x03(\x03\x12\x11\n\trule_type\x18\r \x01(\x05\"\xb0\x01\n\x12\x44\x65vConfigPutReqDTO\x12\x14\n\x0crequest_time\x18\x01 \x01(\x05\x12\x16\n\x0etransaction_id\x18\x02 \x01(\x03\x12\x0e\n\x06\x64tu_sn\x18\x03 \x01(\t\x12\x0e\n\x06\x64\x65v_sn\x18\x04 \x01(\t\x12\x0e\n\x06status\x18\x05 \x01(\x05\x12\x17\n\x0f\x63urrent_package\x18\x06 \x01(\x05\x12\x10\n\x08mi_to_sn\x18\x07 \x03(\x03\x12\x11\n\trule_type\x18\x08 \x01(\x05\"\xf8\x01\n\x15\x44\x65vConfigReportReqDTO\x12\x14\n\x0crequest_time\x18\x01 \x01(\x05\x12\x16\n\x0etransaction_id\x18\x02 \x01(\x03\x12\x0f\n\x07rule_id\x18\x03 \x01(\x05\x12\x0c\n\x04\x64\x61ta\x18\x04 \x01(\t\x12\x0b\n\x03\x63rc\x18\x05 \x01(\x05\x12\x0e\n\x06\x64tu_sn\x18\x06 \x01(\t\x12\x0e\n\x06\x64\x65v_sn\x18\x07 \x01(\t\x12\x10\n\x08\x63\x66g_data\x18\x08 \x01(\t\x12\x0f\n\x07\x63\x66g_crc\x18\t \x01(\x05\x12\x16\n\x0etotal_packages\x18\n \x01(\x05\x12\x17\n\x0f\x63urrent_package\x18\x0b \x01(\x05\x12\x11\n\trule_type\x18\x0c \x01(\x05\"\x92\x01\n\x15\x44\x65vConfigReportResDTO\x12\x15\n\rresponse_time\x18\x01 \x01(\x05\x12\x16\n\x0etransaction_id\x18\x02 \x01(\x03\x12\x0e\n\x06\x64tu_sn\x18\x03 \x01(\t\x12\x0e\n\x06\x64\x65v_sn\x18\x04 \x01(\t\x12\x17\n\x0f\x63urrent_package\x18\x05 \x01(\x05\x12\x11\n\trule_type\x18\x06 \x01(\x05\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'DevConfig_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_DEVCONFIGFETCHRESDTO']._serialized_start=20
  _globals['_DEVCONFIGFETCHRESDTO']._serialized_end=165
  _globals['_DEVCONFIGFETCHREQDTO']._serialized_start=168
  _globals['_DEVCONFIGFETCHREQDTO']._serialized_end=415
  _globals['_DEVCONFIGPUTRESDTO']._serialized_start=418
  _globals['_DEVCONFIGPUTRESDTO']._serialized_end=682
  _globals['_DEVCONFIGPUTREQDTO']._serialized_start=685
  _globals['_DEVCONFIGPUTREQDTO']._serialized_end=861
  _globals['_DEVCONFIGREPORTREQDTO']._serialized_start=864
  _globals['_DEVCONFIGREPORTREQDTO']._serialized_end=1112
  _globals['_DEVCONFIGREPORTRESDTO']._serialized_start=1115
  _globals['_DEVCONFIGREPORTRESDTO']._serialized_end=1261
# @@protoc_insertion_point(module_scope)
