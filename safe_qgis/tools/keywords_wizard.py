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
        # Save reference to the QGIS interface and parent
        self.iface = iface
        self.parent = parent
        self.dock = dock

        self.pbnBack.setEnabled(False)
        self.pbnNext.setEnabled(False)

        self.radHazardLayer.toggled.connect(self.on_category_change)
        self.radExposureLayer.toggled.connect(self.on_category_change)
        self.radAggregationLayer.toggled.connect(self.on_category_change)
        self.radHazardFlood.toggled.connect(self.on_subcategory_change)
        self.radHazardTsunami.toggled.connect(self.on_subcategory_change)
        self.radHazardEarthquake.toggled.connect(self.on_subcategory_change)
        self.radHazardTephra.toggled.connect(self.on_subcategory_change)
        self.radHazardVolcano.toggled.connect(self.on_subcategory_change)

        self.radUnitM.toggled.connect(self.on_unit_change)
        self.radUnitF.toggled.connect(self.on_unit_change)
        self.radUnitWetDry.toggled.connect(self.on_unit_change)
        self.radUnitMMI.toggled.connect(self.on_unit_change)
        self.radUnitKgpsm.toggled.connect(self.on_unit_change)
        self.radUnitNo.toggled.connect(self.on_unit_change)
        self.radUnitNo2.toggled.connect(self.on_unit_change)

        self.pbnCancel.released.connect(self.reject)

        self.go_to_step(1)




    def on_category_change(self):
        """Slot called after category change. Set subcategory widgets according to the selected category"""
        # show/hide radiobuttons for various hazards/exposures
        self.radHazardFlood.setVisible(self.radHazardLayer.isChecked())
        self.radHazardTsunami.setVisible(self.radHazardLayer.isChecked())
        self.radHazardEarthquake.setVisible(self.radHazardLayer.isChecked())
        self.radHazardTephra.setVisible(self.radHazardLayer.isChecked())
        self.radHazardVolcano.setVisible(self.radHazardLayer.isChecked())
        self.radExposurePopulation.setVisible(self.radExposureLayer.isChecked())
        self.radExposureRoads.setVisible(self.radExposureLayer.isChecked())
        self.radExposureBuildingFootprints.setVisible(self.radExposureLayer.isChecked())

        if self.radHazardLayer.isChecked():
            self.lblSelectSubcategory.setText(self.tr('What kind of hazard does this '
                'layer represent? The choice you make here will determine '
                'which impact functions this hazard layer can be used with. '
                'For example, if you have choose <i>flood</i> you will be '
                'able to use this hazard layer with impact functions such as '
                '<i>flood impact on population</i>.'))
        else:
            self.lblSelectSubcategory.setText(self.tr('What kind of exposure does this '
                'layer represent? The choice you make here will determine '
                'which impact fundtions this exposure layer can be used with. '
                'For example, if you have choose <i>population</i> you will be '
                'able to use this exposure layer with impact functions such as '
                '<i>flood impact on population</i>.'))

        # enable the next button
        self.pbnNext.setEnabled(True)


    def on_subcategory_change(self):
        """Slot called after subcategory change. Set unit widgets according to the selected subcategory"""
        # show/hide radiobuttons for various hazards/exposures
        self.radUnitM.setVisible(self.radHazardFlood.isChecked() or self.radHazardTsunami.isChecked())
        self.radUnitF.setVisible(self.radHazardFlood.isChecked() or self.radHazardTsunami.isChecked())
        self.radUnitWetDry.setVisible(self.radHazardFlood.isChecked() or self.radHazardTsunami.isChecked())
        self.radUnitMMI.setVisible(self.radHazardEarthquake.isChecked())
        self.radUnitNo.setVisible(self.radHazardEarthquake.isChecked())
        self.radUnitKgpsm.setVisible(self.radHazardTephra.isChecked())
        self.radUnitNo2.setVisible(self.radHazardTephra.isChecked())

        if self.radHazardFlood.isChecked():
            self.lblSelectUnit.setText('You have selected <b>Flood</b> '
                'for this hazard layer type. We need to know what units the '
                'data are in. For example in a raster layer, each cell might '
                'represent depth in meters or depth in feet. If the dataset '
                'is a vector layer, each polygon might represent an inundated '
                'area, while ares with no polygon coverage would be assumed '
                'to be dry.')
        elif self.radHazardTsunami.isChecked():
            self.lblSelectUnit.setText('You have selected <b>Tsunami</b> '
                'for this hazard layer type. We need to know what units the '
                'data are in. For example in a raster layer, each cell might '
                'represent depth in meters or depth in feet. If the dataset '
                'is a vector layer, each polygon might represent an inundated '
                'area, while ares with no polygon coverage would be assumed '
                'to be dry.')
        elif self.radHazardEarthquake.isChecked():
            self.lblSelectUnit.setText('You have selected <b>Earthquake</b> '
                'for this hazard layer type. We need your confirmation the '
                'unit of the data is MMI. Otherwise please select <i>unknown '
                'unit</i>.')
        elif self.radHazardTephra.isChecked():
            self.lblSelectUnit.setText('You have selected <b>Tephra</b> '
                'for this hazard layer type. We need your confirmation the '
                'unit of the data is kg/m<sup>2</sup>. Otherwise please '
                'select <i>unknown unit</i>.')

        # enable the next button
        self.pbnNext.setEnabled(True)


    def on_unit_change(self):
        """Slot called after unit change. Set field widgets according to the selected unit"""
        # show/hide radiobuttons for various hazards/exposures


        if self.radHazardFlood.isChecked():
            hazard = self.tr('Flood')
        elif self.radHazardTsunami.isChecked():
            hazard = self.tr('Tsunami')
        elif self.radHazardEarthquake.isChecked():
            hazard = self.tr('Earthquake')
        elif self.radHazardTephra.isChecked():
            hazard = self.tr('Tephra')

        if self.radUnitM.isChecked():
            unit = self.tr('meters')
        elif self.radUnitF.isChecked():
            unit = self.tr('feet')
        elif self.radUnitWetDry.isChecked():
            unit = self.tr('wet/dry')
        elif self.radUnitMMI.isChecked():
            unit = self.tr('MMI')
        elif self.radUnitKgpsm.isChecked():
            unit = self.tr('kg/m<sup>2</sup>')
        elif self.radUnitNo.isChecked():
            unit = self.tr('no units')
        elif self.radUnitNo2.isChecked():
            unit = self.tr('no units')

        self.lblSelectField.setText(self.tr('You have selected <b>%s</b> '
            'measured in <b>%s</b>, and the selected layer is vector layer. '
            'Please choose the attiribute that contains the selected value.')
            % (hazard, unit))



        # populate the Field combo
        layer = self.iface.mapCanvas().currentLayer()
        if layer and layer.type() == layer.VectorLayer:
            for field in layer.dataProvider().fields():
                self.cmbField.addItem(field.name())

        # enable the next button
        self.pbnNext.setEnabled(True)






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
#        # disable the Next button until new data entered
#        #self.pbnNext.setEnabled(False)


    # prevents actions being handled twice
    @pyqtSignature('')
    def on_pbnBack_released(self):
        """Automatic slot executed when the pbnBack button is released."""
        new_step = self.stackedWidget.currentIndex()
        self.go_to_step(new_step)


