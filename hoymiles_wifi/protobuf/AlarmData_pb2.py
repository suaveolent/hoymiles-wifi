# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: AlarmData.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0f\x41larmData.proto\"u\n\x07WInfoMO\x12\r\n\x05pv_sn\x18\x01 \x01(\x03\x12\r\n\x05WCode\x18\x02 \x01(\x05\x12\x0c\n\x04WNum\x18\x03 \x01(\x05\x12\x0e\n\x06WTime1\x18\x04 \x01(\x05\x12\x0e\n\x06WTime2\x18\x05 \x01(\x05\x12\x0e\n\x06WData1\x18\x06 \x01(\x05\x12\x0e\n\x06WData2\x18\x07 \x01(\x05\"E\n\x0bWInfoReqDTO\x12\x0e\n\x06\x64tu_sn\x18\x01 \x01(\t\x12\x0c\n\x04time\x18\x02 \x01(\x05\x12\x18\n\x06mWInfo\x18\x03 \x03(\x0b\x32\x08.WInfoMO\"U\n\x0bWInfoResDTO\x12\x14\n\x0ctime_ymd_hms\x18\x01 \x01(\t\x12\x12\n\nerror_code\x18\x02 \x01(\x05\x12\x0e\n\x06offset\x18\x03 \x01(\x05\x12\x0c\n\x04time\x18\x04 \x01(\x05\"\xc3\x01\n\rWWVDataReqDTO\x12\x0e\n\x06\x64tu_sn\x18\x01 \x01(\t\x12\x0c\n\x04time\x18\x02 \x01(\x05\x12\x13\n\x0bpackage_nub\x18\x03 \x01(\x05\x12\x13\n\x0bpackage_now\x18\x04 \x01(\x05\x12\r\n\x05pv_sn\x18\x05 \x01(\x03\x12\r\n\x05WCode\x18\x06 \x01(\x05\x12\x0c\n\x04WNum\x18\x07 \x01(\x05\x12\x0e\n\x06WTime1\x18\x08 \x01(\x05\x12\x0f\n\x07WVDataL\x18\t \x01(\x05\x12\x0c\n\x04WPos\x18\n \x01(\x05\x12\x0f\n\x07mWVData\x18\x0b \x01(\t\"l\n\rWWVDataResDTO\x12\x14\n\x0ctime_ymd_hms\x18\x01 \x01(\t\x12\x13\n\x0bpackage_now\x18\x02 \x01(\x05\x12\x12\n\nerror_code\x18\x03 \x01(\x05\x12\x0e\n\x06offset\x18\x04 \x01(\x05\x12\x0c\n\x04time\x18\x05 \x01(\x05\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'AlarmData_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_WINFOMO']._serialized_start=19
  _globals['_WINFOMO']._serialized_end=136
  _globals['_WINFOREQDTO']._serialized_start=138
  _globals['_WINFOREQDTO']._serialized_end=207
  _globals['_WINFORESDTO']._serialized_start=209
  _globals['_WINFORESDTO']._serialized_end=294
  _globals['_WWVDATAREQDTO']._serialized_start=297
  _globals['_WWVDATAREQDTO']._serialized_end=492
  _globals['_WWVDATARESDTO']._serialized_start=494
  _globals['_WWVDATARESDTO']._serialized_end=602
# @@protoc_insertion_point(module_scope)
