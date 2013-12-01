# coding=utf-8
"""
InaSAFE Disaster risk assessment tool by AusAid **GUI Keywords Creation Wizard Dialog.**

Contact : ole.moller.nielsen@gmail.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

.. todo:: Check raster is single band

"""

__author__ = 'qgis@borysjurgiel.pl'
__revision__ = '$Format:%H$'
__date__ = '21/02/2011'
__copyright__ = ('Copyright 2012, Australia Indonesia Facility for '
                 'Disaster Reduction')

import logging
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignature

from third_party.odict import OrderedDict

from safe_qgis.safe_interface import InaSAFEError, get_version
from safe_qgis.ui.keywords_wizard_base import Ui_KeywordsWizardBase
from safe_qgis.utilities.defaults import breakdown_defaults
from safe_qgis.utilities.keyword_io import KeywordIO
from safe_qgis.utilities.help import show_context_help
from safe_qgis.utilities.utilities import (
    get_error_message,
    is_polygon_layer,
    layer_attribute_names)

from safe_qgis.exceptions import (
    InvalidParameterError, HashNotFoundError, NoKeywordsFoundError)

LOGGER = logging.getLogger('InaSAFE')


class KeywordsWizard(QtGui.QDialog, Ui_KeywordsWizardBase):
    """Dialog implementation class for the InaSAFE keywords wizard."""

    def __init__(self, parent, iface, dock=None, layer=None):
        """Constructor for the dialog.

        .. note:: In QtDesigner the advanced editor's predefined keywords
           list should be shown in english always, so when adding entries to
           cboKeyword, be sure to choose :safe_qgis:`Properties<<` and untick
           the :safe_qgis:`translatable` property.

        :param parent: Parent widget of this dialog.
        :type parent: QWidget

        :param iface: Quantum GIS QGisAppInterface instance.
        :type iface: QGisAppInterface

        :param dock: Dock widget instance that we can notify of changes to
            the keywords. Optional.
        :type dock: Dock
        """

        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle('InaSAFE')
        self.keywordIO = KeywordIO()
        # note the keys should remain untranslated as we need to write
        # english to the keywords file. The keys will be written as user data
        # in the combo entries.
        # .. seealso:: http://www.voidspace.org.uk/python/odict.html
        self.standardExposureList = OrderedDict(
            [('population', self.tr('population')),
             ('structure', self.tr('structure')),
             ('Not Set', self.tr('Not Set'))])
        self.standardHazardList = OrderedDict(
            [('earthquake [MMI]', self.tr('earthquake [MMI]')),
             ('tsunami [m]', self.tr('tsunami [m]')),
             ('tsunami [wet/dry]', self.tr('tsunami [wet/dry]')),
             ('tsunami [feet]', self.tr('tsunami [feet]')),
             ('flood [m]', self.tr('flood [m]')),
             ('flood [wet/dry]', self.tr('flood [wet/dry]')),
             ('flood [feet]', self.tr('flood [feet]')),
             ('tephra [kg2/m2]', self.tr('tephra [kg2/m2]')),
             ('volcano', self.tr('volcano')),
             ('Not Set', self.tr('Not Set'))])

        self.standard_categories = [
            ('hazard', self.tr('hazard'), self.tr('A <b>hazard</b> layer represents something that will impact the people or infrastructure in area. For example a flood, earth quake, tsunami inundation are all different kinds of hazards.')),
            ('exposure', self.tr('exposure'), self.tr('An <b>exposure</b> layer represents people, property or infrastructure that may be affected in the event of a flood, earthquake, volcano etc.')),
            ('aggregation', self.tr('aggregation'), self.tr('An <b>aggregation</b> layer represents regions you can use to summarize the results by. For example, we might summarise the affected people after a flood according to city districts.'))]

        self.standard_subcategories = {
            0: [
             ('flood', self.tr('flood'), self.tr('description of subcategory: flood')),
             ('tsunami', self.tr('tsunami'), self.tr('description of subcategory: tsunami')),
             ('earthquake', self.tr('earthquake'), self.tr('description of subcategory: earthquake')),
             ('tephra', self.tr('tephra'), self.tr('description of subcategory: tephra')),
             ('volcano', self.tr('volcano'), self.tr('description of subcategory: volcano')),
             ('Not Set', self.tr('Not Set'), self.tr('description of subcategory: empty'))
            ],
            1: [
            ('population', self.tr('population'), self.tr('description of subcategory: pupulation')),
            ('buildings', self.tr('buildings'), self.tr('description of subcategory: buildings')),
            ('roads', self.tr('roads'), self.tr('description of subcategory: roads'))
            ],
            2: []
        }

        self.standard_subcategories_descriptions = {
            0: self.tr('What kind of hazard does this '
                'layer represent? The choice you make here will determine '
                'which impact functions this hazard layer can be used with. '
                'For example, if you have choose <i>flood</i> you will be '
                'able to use this hazard layer with impact functions such as '
                '<i>flood impact on population</i>.'),
            1: self.tr('What kind of exposure does this '
                'layer represent? The choice you make here will determine '
                'which impact fundtions this exposure layer can be used with. '
                'For example, if you have choose <i>population</i> you will be '
                'able to use this exposure layer with impact functions such as '
                '<i>flood impact on population</i>.'),
            2: ""
        }

        self.standard_units = {
            0: [
             ('meters', self.tr('meters'), self.tr('description of subcategory: meters')),
             ('feet', self.tr('feet'), self.tr('description of subcategory: feet')),
             ('wet/dry', self.tr('wet/dry'), self.tr('description of subcategory: wet/dry'))
            ],
            1: [
             ('meters', self.tr('meters'), self.tr('description of subcategory: meters')),
             ('feet', self.tr('feet'), self.tr('description of subcategory: feet')),
             ('wet/dry', self.tr('wet/dry'), self.tr('description of subcategory: wet/dry'))
            ],
            2: [
             ('MMI', self.tr('MMI'), self.tr('description of subcategory: MMI')),
             ('Not Set', self.tr('Not Set'), self.tr('description of subcategory: Not Set')),
            ],
            3: [
             ('kg/m2', self.tr('kg/m2'), self.tr('description of subcategory: kg/m<sup2</sup>')),
             ('Not Set', self.tr('Not Set'), self.tr('description of subcategory: Not Set')),
            ],
            4: [],
            5: []
        }


        # Save reference to the QGIS interface and parent
        self.iface = iface
        self.parent = parent
        self.dock = dock

        self.pbnBack.setEnabled(False)
        self.pbnNext.setEnabled(False)

        for i in self.standard_categories:
            self.lstCategories.addItem(i[1])

        #clear the label initially
        self.lblDescribeCategory.setText('')

        self.pbnCancel.released.connect(self.reject)

        self.go_to_step(1)



    # prevents actions being handled twice
    @pyqtSignature('')
    def on_lstCategories_itemSelectionChanged(self):
        """Automatic slot executed when category change. Set description label
           and subcategory widgets according to the selected category
        """

        # exit if no selection
        if not len(self.lstCategories.selectedIndexes()): return

        # set description label
        index = self.lstCategories.selectedIndexes()[0].row()
        self.lblDescribeCategory.setText(self.standard_categories[index][2])

        # set subcategory widgets
        self.lblSelectSubcategory.setText(self.standard_subcategories_descriptions[index])

        self.lstSubcategories.clear()
        for i in self.standard_subcategories[index]:
            self.lstSubcategories.addItem(i[1])

        #clear the label initially
        self.lblDescribeSubcategory.setText('')

        # enable the next button
        self.pbnNext.setEnabled(True)



    def on_lstSubcategories_itemSelectionChanged(self):
        """Automatic slot executed when subcategory change. Set description label
           and unit widgets according to the selected category
        """

        # exit if no selection
        if not len(self.lstCategories.selectedIndexes()): return
        if not len(self.lstSubcategories.selectedIndexes()): return

        category = self.lstCategories.selectedIndexes()[0].row()
        index = self.lstSubcategories.selectedIndexes()[0].row()

        self.lblDescribeSubcategory.setText(self.standard_subcategories[category][index][2])

        self.lblSelectUnit.setText(self.tr('You have selected <b>%s</b> '
                'for this <b>%s</b> layer type. We need to know what units the '
                'data are in. For example in a raster layer, each cell might '
                'represent depth in meters or depth in feet. If the dataset '
                'is a vector layer, each polygon might represent an inundated '
                'area, while ares with no polygon coverage would be assumed '
                'to be dry.') % (self.standard_subcategories[category][index][1],self.standard_categories[category][1]))

        self.lstUnits.clear()
        for i in self.standard_units[index]:
            self.lstUnits.addItem(i[1])

        #clear the label initially
        self.lblDescribeUnit.setText('')

        # enable the next button
        self.pbnNext.setEnabled(True)



    def on_lstUnits_itemSelectionChanged(self):
        """Automatic slot executed when unit change. Set description label
           and field widgets according to the selected category
        """
        # exit if no selection
        if not len(self.lstCategories.selectedIndexes()): return
        if not len(self.lstUnits.selectedIndexes()): return

        category = self.lstCategories.selectedIndexes()[0].row()
        index = self.lstUnits.selectedIndexes()[0].row()

        self.lblDescribeUnit.setText(self.standard_units[category][index][2])

        hazard = self.standard_categories[category][1]
        unit = self.standard_units[category][index][1]

        self.lblSelectField.setText(self.tr('You have selected <b>%s</b> '
            'measured in <b>%s</b>, and the selected layer is vector layer. '
            'Please choose the attiribute that contains the selected value.')
            % (hazard, unit))

        # populate the fields list
        layer = self.iface.mapCanvas().currentLayer()
        if layer and layer.type() == layer.VectorLayer:
            for field in layer.dataProvider().fields():
                self.lstFields.addItem(field.name())

        # enable the next button
        self.pbnNext.setEnabled(True)



    def on_lstFields_itemSelectionChanged(self):
        """Automatic slot executed when field change.
           Unlocks the Next button.
        """
        # enable the next button
        self.pbnNext.setEnabled(True)



    def on_leSource_textChanged(self):
        """Automatic slot executed when the source change.
           Unlocks the Next button.
        """
        # enable the next button
        self.pbnNext.setEnabled(bool(self.leSource.text()))



    def on_leTitle_textChanged(self):
        """Automatic slot executed when the title change.
           Unlocks the Next button.
        """
        # enable the next button
        self.pbnNext.setEnabled(bool(self.leTitle.text()))



    def go_to_step(self, step):
        """Set the stacked widget to the given step

        :param step: The step number to be moved to
        :type step: int
        """
        self.stackedWidget.setCurrentIndex(step-1)
        self.lblStep.setText(self.tr("step %d of %d") % (step, 6))
        self.pbnBack.setEnabled(step>1)
        self.pbnNext.setVisible(step < self.stackedWidget.count())
        self.pbnFinish.setVisible(step == self.stackedWidget.count())



    # prevents actions being handled twice
    @pyqtSignature('')
    def on_pbnNext_released(self):
        """Automatic slot executed when the pbnNext button is released."""
        new_step = self.stackedWidget.currentIndex()+2
        self.go_to_step(new_step)
        #disable the Next button until new data entered
        self.pbnNext.setEnabled(self.is_ready_to_next_step(new_step))



    # prevents actions being handled twice
    @pyqtSignature('')
    def on_pbnBack_released(self):
        """Automatic slot executed when the pbnBack button is released."""
        new_step = self.stackedWidget.currentIndex()
        self.pbnNext.setEnabled(True)
        self.go_to_step(new_step)



    def is_ready_to_next_step(self, step):
        """Check if widgets are filled an new step can be enabled

        :param step: The present step number
        :type step: int

        :returns: True if new step may be enabled
        :rtype: bool
        """

        if step == 1 and len(self.lstCategories.selectedIndexes()): return True
        if step == 2 and (len(self.lstSubcategories.selectedIndexes()) or not self.lstSubcategories.count()): return True
        if step == 3 and (len(self.lstUnits.selectedIndexes()) or not self.lstUnits.count()): return True
        if step == 4 and (len(self.lstFields.selectedIndexes()) or not self.lstFields.count()): return True
        if step == 5 and self.leSource.text(): return True
        if step == 6 and self.leTitle.text(): return True

        return False
