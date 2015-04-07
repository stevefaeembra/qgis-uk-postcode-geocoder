# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeocodeUKPostcodes
                                 A QGIS plugin
 An offline geocoder for UK Postcodes
                              -------------------
        begin                : 2015-04-03
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Steven Kay
        email                : stevendkay@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant
from PyQt4.QtGui import QAction, QIcon
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from geocodeukpostcodes_dialog import GeocodeUKPostcodesDialog
import os.path
from struct import *
import re
from qgis.gui import QgsMessageBar
import time

class PostcodeFileDatabase(object):
    '''
    loads in the packed binary database and provides postcode lookups
    '''
    
    def __init__(self, widget):
        self.lookup = {}
        datasetname = ''
        if widget.dlg.rbOpenCodePoint.isChecked():
            pathh = os.path.join(os.path.dirname(__file__),"os_packed.bin")
            datasetname = 'OS Open CodePoint'
        if widget.dlg.rbONSPostcodes.isChecked():
            pathh = os.path.join(os.path.dirname(__file__),"ons_packed.bin")
            datasetname = 'ONS Postcode data'
        print pathh
        ix = 0    
        with open(pathh,"r") as fi:
            for x in self.unpackpostcodes(fi):
                #print x
                try:
                    pcode, eastings, northings = x
                    self.lookup[pcode] = (eastings, northings)
                    ix += 1
                    if (ix%100000==0):
                        widget.dlg.labProgress.setText("Unpacking data from %s..\n%d postcodes" % (datasetname,ix))
                        widget.dlg.repaint()
                except:
                    ''' valid postcode, but non-geographic'''
                    self.lookup[pcode] = (0,0)
               
        #print self.lookup
        print "Database unpacked!"

    def lookuppostcode(self, pc):
         if not pc:
             ''' most likely NULL '''
             return (-1,-1)
         pc = re.sub("\s+","", pc)
         pc = pc.upper()
         try:
             '''
             return (easting,northing)
             may be non-geographic in which case (0,0)
             '''
             return self.lookup[pc]
         except:
             ''' no match '''
             return (-1,-1)
    
    def unpackpostcodes(self, fin):
        while True:
            try:
                lenn = unpack('B',fin.read(1))
            except:
                break
            lenn = lenn[0]
            pcode = unpack('%ds' % int(lenn), fin.read(lenn))
            b1 = unpack('B',fin.read(1))
            b2 = unpack('B',fin.read(1))
            b3 = unpack('B',fin.read(1))
            eastings = (b1[0]<<16)|(b2[0]<<8)|(b3[0])
            b1 = unpack('B',fin.read(1))
            b2 = unpack('B',fin.read(1))
            b3 = unpack('B',fin.read(1))
            northings =  (b1[0]<<16)|(b2[0]<<8)|(b3[0])
            #print pcode[0]
            yield (pcode[0], eastings, northings)

class GeocodeUKPostcodes:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GeocodeUKPostcodes_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = GeocodeUKPostcodesDialog()

        # default to epsg 27700
        
        defaultproj = QgsCoordinateReferenceSystem()
        defaultproj.createFromSrid(27700)
        self.dlg.cbProjection.setCrs(defaultproj)

        # set up GUI hooks
        
        self.dlg.cbVectorLayer.layerChanged.connect(self.dlg.cbFields.setLayer)
        self.dlg.cbVectorLayer.currentIndex = 0
        self.dlg.pbGeocode.clicked.connect(self.geocode)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Geocode UK Postcodes')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'GeocodeUKPostcodes')
        self.toolbar.setObjectName(u'GeocodeUKPostcodes')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GeocodeUKPostcodes', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/GeocodeUKPostcodes/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Geocode UK Postcodes'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Geocode UK Postcodes'),
                action)
            self.iface.removeToolBarIcon(action)

    def getLayerFromName(self, layername):
        ''' get layer by name. Note, this will only get visible layers. Is there a better way than this? '''
        canvas = self.iface.mapCanvas()
        layer = None
        for x in canvas.layers():
            print x.name()
            if x.name()==layername:
                layer = x
        return layer
    
    def geocode(self, widj):
        print "Clicked GeoCode"

        dryrun = self.dlg.cbDryRun.isChecked()
        pcfildname = self.dlg.cbFields.itemText(self.dlg.cbFields.currentIndex())
        
        self.dlg.labProgress.setText("Adding new fields to schema, this can take a while..")
        self.dlg.repaint()
        
        print "pcodefieldname = [%s]" % pcfildname
        
        xxx = self.dlg.cbVectorLayer.currentLayer()
        layername = xxx.originalName()
        layer = self.getLayerFromName(layername)
        
        ixEastingsAttr = None
        ixNorthingsAttr = None
        
        # check we can edit this layer, if so add the new fields
                        
        caps = layer.dataProvider().capabilities()
        if not dryrun and (caps & QgsVectorDataProvider.AddAttributes):
            try:
                fname_E = self.dlg.leXFieldName.text()
                fname_N = self.dlg.leYFieldName.text()
                res = layer.dataProvider().addAttributes([QgsField(fname_E, QVariant.Int),QgsField(fname_N, QVariant.Int)])
                layer.updateFields()
                ixEastingsAttr = layer.dataProvider().fieldNameIndex(fname_E)
                ixNorthingsAttr = layer.dataProvider().fieldNameIndex(fname_N)
                print "index of eastings attr %d" % ixEastingsAttr
                print "index of northings attr %d" % ixNorthingsAttr
            except Exception as e:
                self.iface.messageBar().pushMessage(QCoreApplication.translate("VectorTextStatistics", e.message ), level=QgsMessageBar.CRITICAL)
                return
        elif not dryrun:
            mess = QCoreApplication.translate("VectorTextStatistics", "You cannot add fields to a layer of this type, the data provider needs to allow AddAttributes capability (e.g. Shapefile, Postgres)")
            self.iface.messageBar().pushMessage(mess, level=QgsMessageBar.CRITICAL)
            self.dlg.labProgress.setText(mess)
            return
        
        
        
        feat_iterator = layer.getFeatures()
        totalpoints = layer.featureCount()
        print "There are %d features" % totalpoints
        feat = QgsFeature()
        ix = 0
        self.dlg.labProgress.setText("Unpacking postcode database")
        self.dlg.repaint()
        print "Start unpacking..."
        pfdb = PostcodeFileDatabase(self)
        print "Finished unpacking"
        ct_all = 0
        ct_fail = 0
        ct_nongeo = 0
        ct_success = 0
        failures = []
        distinct = []
        distinctfail = []
        print "pcodefieldname = [%s]" % pcfildname
        tick = time.time()
        provider = layer.dataProvider()
        updateMap = {}
        while feat_iterator.nextFeature(feat):
            vall = feat.attribute(pcfildname)
            lookup = pfdb.lookuppostcode(vall)
            
            if (lookup==(0,0)):
                # valid postcode, but non geographic
                ct_nongeo += 1
                updateMap[feat.id()] = { ixEastingsAttr: 0, ixNorthingsAttr:0}
            elif (lookup==(-1,-1)):
                # not a known postcode
                ct_fail += 1
                failures.append(vall)
                updateMap[feat.id()] = { ixEastingsAttr: -1, ixNorthingsAttr:-1}
                if not vall in distinctfail:
                    if len(distinctfail)<1000:
                        distinctfail.append(vall)
            else:
                # success
                ct_success += 1
                e,n = lookup
                updateMap[feat.id()] = { ixEastingsAttr: e, ixNorthingsAttr:n}
                if not vall in distinct:
                    distinct.append(vall)
            ct_all += 1
            #print vall
            if (ix%100==0):
                pctg = (float(ix)/float(totalpoints))*100.0
                self.dlg.labProgress.setText("Processed %d features (%2.0f%%)" % (ix,pctg))
                print ("Processed %d features (%2.0f%%)" % (ix,pctg))
                self.dlg.repaint()
            ix += 1
        if not dryrun:
            provider.changeAttributeValues( updateMap )
        took = time.time() - tick
        successrate = (float(ct_success)/float(ct_all))*100.0
        nongeorate = (float(ct_nongeo)/float(ct_all))*100.0
        failrate = (float(ct_fail)/float(ct_all))*100.0
        if len(distinctfail)>0 :
            self.dlg.leFailures.setText("\n".join(f for f in distinctfail))
        failstext = ""
        if distinctfail and len(distinctfail)==1000:
            failstext = "Over 1000 unmatched postcodes..."
        else:
            failstext = "%d distinct failed postcodes" % len(distinctfail)  
        self.dlg.labProgress.setText("Finished processing %d features in %2.2f secs\n%d success (%2.2f%%)\n%d failures (%2.2f%%)\n%d non-geo (%2.2f%%)\n%d distinct successful postcodes\n%s" % (ix,took,ct_success,successrate,ct_fail,failrate,ct_nongeo,nongeorate,len(distinct),failstext))
        self.dlg.repaint()

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        
        
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
