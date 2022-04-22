#!/usr/bin/env python
# coding: utf-8

import copy
from uuid import uuid4
from django.db.models.query import QuerySet
from django.utils.safestring import mark_safe
from collections import OrderedDict
from table.columns import Column, BoundColumn, SequenceColumn
from table.widgets import SearchBox, InfoLabel, Pagination, LengthMenu, ExtButton
from table.tables import ( 
	TableOptions as BaseTableOptions,
	TableWidgets as BaseTableWidgets,
)
from itertools import chain

class TableData(object):
	def __init__(self, data, table):
		model = getattr(table.opts, "model", None)
		extra_model = getattr(table.opts, "extra_model", None)

		if (data is not None and not hasattr(data, "__iter__") or
			data is None and model is None and extra_model is None):
			raise ValueError("Model option or QuerySet-like object data"
							 "is required.")
		if data is None:
			self.list = chain(model.objects.all(), extra_model.objects.all())
		else:
			self.list = list(data)

	@property
	def data(self):
		return self.list

	def __len__(self):
		return len(self.list)

	def __iter__(self):
		return iter(self.data)

	def __getitem__(self, key):
		return self.data[key]

class TableWidgets(BaseTableWidgets):
	pass


class BaseTable(object):

	def __init__(self, data=None):
		self.data = TableData(data, self)

		# Make a copy so that modifying this will not touch the class definition.
		self.columns = copy.deepcopy(self.base_columns)
		# Build table add-ons
		self.addons = TableWidgets(self)

	@property
	def rows(self):
		rows = []
		for obj in self.data:
			# Binding object to each column of each row, so that
			# data structure for each row is organized like this:
			# { boundcol0: td, boundcol1: td, boundcol2: td }
			row = OrderedDict()
			columns = [BoundColumn(obj, col) for col in self.columns if col.space]
			for col in columns:
				row[col] = col.html
			rows.append(row)
		return rows

	@property
	def header_rows(self):
		"""
		[ [header1], [header3, header4] ]
		"""
		# TO BE FIX: refactor
		header_rows = []
		headers = [col.header for col in self.columns]
		for header in headers:
			if len(header_rows) <= header.row_order:
				header_rows.append([])
			header_rows[header.row_order].append(header)
		return header_rows


class TableOptions(BaseTableOptions):
	def __init__(self, options=None):
		super(TableOptions, self).__init__(options=options)
		self.extra_model = getattr(options, 'extra_model', None)

class TableDataMap(object):
	"""
	A data map that represents relationship between Table instance and
	Model.
	"""
	map = {}

	@classmethod
	def register(cls, token, model, extra_model, columns):
		if token not in TableDataMap.map:
			TableDataMap.map[token] = (model, extra_model, columns)

	@classmethod
	def get_model(cls, token):
		return TableDataMap.map.get(token)[0]

	@classmethod
	def get_extra_model(cls, token):
		return TableDataMap.map.get(token)[1]

	@classmethod
	def get_columns(cls, token):
		return TableDataMap.map.get(token)[2]


class TableMetaClass(type):
	""" Meta class for create Table class instance.
	"""

	def __new__(cls, name, bases, attrs):
		opts = TableOptions(attrs.get('Meta', None))
		# take class name in lower case as table's id
		if opts.id is None:
			opts.id = name.lower()
		attrs['opts'] = opts

		# extract declared columns
		columns = []
		for attr_name, attr in attrs.items():
			if isinstance(attr, SequenceColumn):
				columns.extend(attr)
			elif isinstance(attr, Column):
				columns.append(attr)
		columns.sort(key=lambda x: x.instance_order)

		# If this class is subclassing other tables, add their fields as
		# well. Note that we loop over the bases in reverse - this is
		# necessary to preserve the correct order of columns.
		parent_columns = []
		for base in bases[::-1]:
			if hasattr(base, "base_columns"):
				parent_columns = base.base_columns + parent_columns
		base_columns = parent_columns + columns

		# For ajax data source, store columns into global hash map with
		# unique token key. So that, columns can be get to construct data
		# on views layer.
		token = uuid4().hex
		if opts.ajax:
			TableDataMap.register(token, opts.model, opts.extra_model, copy.deepcopy(base_columns))

		attrs['token'] = token
		attrs['base_columns'] = base_columns

		return super(TableMetaClass, cls).__new__(cls, name, bases, attrs)

Table = TableMetaClass('Table', (BaseTable,), {})