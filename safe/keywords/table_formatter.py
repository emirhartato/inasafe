# -*- coding: utf-8 -*-
"""**Handle JSON keywords file.**

Classes to handle the creation and ingestion of keywords data in JASON format.
"""
__author__ = 'cchristelis@gmail.com'
__version__ = '0.1'
__date__ = '10/11/2013'
__copyright__ = ('Copyright 2012, Australia Indonesia Facility for '
                 'Disaster Reduction')

from safe.impact_functions.core import get_question
from safe.common.tables import Table, TableRow
from safe.common.utilities import ugettext as tr, format_int


class TableFormatter(object):
    """Format a keywords object into a table.

    :param keywords: A keywords instance.
    """

    def __init__(self, keywords):
        self.keywords = keywords

    def __call__(self, table_type='Analysis Result'):
        """Call the Table Formatter as a function.

        :param table_type: The type of table we wish to obtain. (
            Currently only the default 'Analysis Result' is used)
        :type table_type: str

        :return: A table of teh desired type based on the initialized keywords.
        :rtype: Table
        """
        if table_type == 'Analysis Result':
            return self.analysis_table()

    @staticmethod
    def _get_reduced_totals(buildings_affected, min_group_count=25):
        buildings_reduced = {}
        for building_type in buildings_affected:
            building_type_data = buildings_affected[building_type]
            if building_type_data["affected"] < min_group_count:
                if 'other' not in buildings_reduced:
                    buildings_reduced['other'] = {
                        'total': building_type_data['total'],
                        'affected': building_type_data['affected']}
                else:
                    buildings_reduced['other'][
                        'total'] += building_type_data['total']
                    buildings_reduced['other'][
                        'affected'] += building_type_data['affected']
            else:
                buildings_reduced[building_type] = buildings_affected[
                    building_type]

        return buildings_reduced

    def analysis_table(self):
        """Build a table describing the analysis results.

        :return: The analysis table
        :rtype: Table
        """
        keywords = self.keywords
        primary_layer = keywords.primary_layer
        function_id = primary_layer.function_details['impact_function_id']
        version = keywords.version
        question = get_question(
            keywords.provenance['impact_layer']['name'],
            keywords.provenance['exposure_layer']['name'],
            primary_layer.function_details['title'])
        table_body = [question]
        if function_id == 'FB1' and version == 1:
            header = [tr('Building type'), tr('Number flooded'), tr('Total')]
            TableRow(header, header=True)
            buildings_affected_original = primary_layer.buildings_breakdown
            total = primary_layer.impact_assessment['total_buildings']
            total_affected = primary_layer.impact_assessment[
                'affected_buildings']
            buildings_affected = self._get_reduced_totals(
                buildings_affected_original)
            table_body.append(TableRow([tr('All'), total_affected, total]))
            table_body.append(TableRow(
                tr('Breakdown by building type'), header=True))
            building_types = buildings_affected.keys()
            building_types.sort()
            for building_type in building_types:
                if building_type == 'other':
                    continue
                table_body.append(TableRow([
                    building_type,
                    buildings_affected[building_type]['affected'],
                    buildings_affected[building_type]['total']]))
            if 'other' in building_types:
                table_body.append(TableRow([
                    'other',
                    buildings_affected['other']['affected'],
                    buildings_affected['other']['total']]))
            table_body.append(TableRow(tr('Action Checklist:'), header=True))
            table_body.append(TableRow(
                tr('Are the critical facilities still open?')))
            table_body.append(TableRow(tr(
                'Which structures have warning capacity (eg. sirens, speakers, '
                'etc.)?')))
            table_body.append(TableRow(
                tr('Which buildings will be evacuation centres?')))
            table_body.append(TableRow(
                tr('Where will we locate the operations centre?')))
            table_body.append(TableRow(tr(
                'Where will we locate warehouse and/or distribution centres?')))
            if buildings_affected_original.get('school', {}).get('affected', 0):
                table_body.append(TableRow(tr(
                    'Where will the students from the %s closed schools go to '
                    'study?') % format_int(
                        buildings_affected['school']['affected'])))
            if buildings_affected_original.get('hospital', {}).get(
                    'affected', 0):
                table_body.append(TableRow(tr(
                    'Where will the patients from the %s closed hospitals go '
                    'for treatment and how will we transport them?') % (
                        format_int(buildings_affected['school']['affected']))))
            table_body.append(TableRow(tr('Notes'), header=True))
            assumption = tr('Buildings are said to be flooded when ')
            if keywords['impact_layer'].provenance['type'] == 'raster':
                threshold = primary_layer.function_details['parameters'][
                    'threshold [m]']
                assumption += tr('flood levels exceed %.1f m') % threshold
            else:
                assumption += tr('in regions marked as affected')
            table_body.append(assumption)
        if function_id == 'FP1' and version == 1:
            thresholds = primary_layer.function_details['parameters'][
                'thresholds [m]']
            evacuated =  primary_layer.impact_assessment[
                'evacuated_population']
            table_body.append(TableRow([
                (tr('People in %.1f m of water') % (thresholds[-1])),
                '%s%s' % (format_int(evacuated),
                ('*' if evacuated >= 1000 else ''))], header=True))
            table_body.append(TableRow(
                tr('* Number is rounded to the nearest 1000')))
            table_body.append(TableRow(tr(
                'Map shows population density needing evacuation')))
            table_body.append(TableRow(tr(
                'Table below shows the weekly minium needs for all '
                'evacuated people')))
            table_body.append(TableRow(
                [tr('Needs per week'), tr('Total')], header=True))
            tot_needs = primary_layer.minimum_needs
            food = tot_needs['food']
            drinking_water = tot_needs['drinking_water']
            clean_water = tot_needs['clean_water']
            hygine_pack = tot_needs['hygine_pack']
            toilet = tot_needs['toilet']
            for resource in [
                    food, drinking_water, clean_water]:
                table_body.append(
                    [tr('%s [%s]' % (
                        resource['type'], resource['unit_abbreviation'])),
                     format_int(resource['quantity'])])
            for resource in [hygine_pack, toilet]:
                table_body.append([
                    tr('%s' % resource['type']),
                    format_int(resource['quantity'])])

            table_body.append(TableRow(tr('Action Checklist:'), header=True))
            table_body.append(TableRow(
                tr('How will warnings be disseminated?')))
            table_body.append(TableRow(
                tr('How will we reach stranded people?')))
            table_body.append(TableRow(tr('Do we have enough relief items?')))
            table_body.append(TableRow(tr(
                'If yes, where are they located and how will we distribute '
                'them?')))
            table_body.append(TableRow(tr(
                'If no, where can we obtain additional relief items from and '
                'how will we transport them to here?')))

            # Extend impact report for on-screen display
            total_population = primary_layer.impact_assessment[
                'total_population']
            table_body.extend([
                TableRow(tr('Notes'), header=True),
                tr('Total population: %s') % format_int(total_population),
                tr('People need evacuation if flood levels exceed '
                   '%(eps).1f m') % {'eps': thresholds[-1]},
                tr('Minimum needs are defined in BNPB regulation 7/2008'),
                tr('All values are rounded up to the nearest integer in order '
                    'to avoid representing human lives as fractionals.')])

            if len(thresholds) > 1:
                table_body.append(TableRow(
                    tr('Detailed breakdown'), header=True))

                for i, val in enumerate(thresholds[:-1]):
                    s = (tr(
                        'People in %(lo).1f m to %(hi).1f m of water: '
                        '%(val)i') % {
                            'lo': val,
                            'hi': thresholds[i + 1],
                            'val': primary_layer.impact_assessment[val]})
                    table_body.append(TableRow(s))

        return Table(table_body)
