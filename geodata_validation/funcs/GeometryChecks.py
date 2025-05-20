from .status import Result, Infotext
from qgis.core import QgsVectorLayer
from qgis.core import QgsPointXY, QgsGeometry, QgsFeature, QgsField
from qgis import processing

from qgis.core import QgsWkbTypes
from qgis.PyQt.QtCore import QVariant

import json




category_name = "Geometry Checks"

def empty_geomtries(vectorlayer: type[QgsVectorLayer]) -> tuple[Result or None, Infotext or None]:
        info = Infotext("Analysis for empty geometries:")
        result = Result(category= category_name, analysis="Check for empty geometries")

        # problem that local namespace of function doesnt get cleared after return inside of qgis session
        result.reset_data()

        attribute_names = [field.name() for field in vectorlayer.fields()]
        empty_objects = []

        counter = 0
        for feat in vectorlayer.getFeatures():
            if feat.geometry().isEmpty():
                counter += 1
                empty_objects.append(feat.attributes())

        if counter > 0:
            info.add_warning(f"found {len(empty_objects)} objects with no geometries")
            result.append_info("empty_geometries", [attribute_names] + empty_objects)
        else:
            info.add_info("No objects with empty geometries found")
        
        return (result if result.geodata_layer or result.info_output else None, info)


def _holes_in_polygon(polygon_layer: type[QgsVectorLayer], out_layer_name: str) -> tuple[QgsVectorLayer|None, int]:
        
        holes = QgsVectorLayer("Polygon", out_layer_name, "memory")
        holes.setCrs(polygon_layer.crs())
        holes_data_provider = holes.dataProvider()

        holes.startEditing()
        holes.addAttribute(QgsField("OID", QVariant.Int))
        holes.commitChanges()

        counter = 0
        for i, feat in enumerate(polygon_layer.getFeatures()):

            geom = feat.geometry().asJson()
            data = json.loads(geom)
            coords = data["coordinates"]

            oid = 1
            
            for obj in coords:
                                
                if len(obj) == 1:
                    continue
                else:
                    counter += 1
                    for i in range(1, len(obj)):
                        pointlist = []
            
                        for p in obj[i]:
                            pointlist.append(QgsPointXY(p[0], p[1]))
                            
                        new_geom = QgsGeometry.fromPolygonXY([pointlist])
                        holes.startEditing()
                        new_feat = QgsFeature()
                        new_feat.setGeometry(new_geom)
                        new_feat["OID"] = oid
                        oid += 1
                        holes_data_provider.addFeature(new_feat)
                        holes.commitChanges()
        
        return (holes if counter > 0 else None, counter)

def holes(vectorlayer: type[QgsVectorLayer]) -> tuple[Result or None, Infotext or None]:
        info = Infotext()
        result = Result(category=category_name, analysis="Check for holes in geometries")

        # problem that local namespace of function doesnt get cleared after return inside of qgis session
        result.reset_data()

        if vectorlayer.geometryType() != QgsWkbTypes.PolygonGeometry:
            info.add_error("can't investigate geometries for holes that are not polygons.")
            return (None, info)

        (holes_in_geometries, counter_in_geometries) = _holes_in_polygon(vectorlayer, "Holes inside geometries")
            
        if counter_in_geometries > 0:
            info.add_warning(f"Found {counter_in_geometries} holes in the geometries of this layer")
            result.append_geodata("Holes_in_geometries", holes_in_geometries)
            result.append_info("Holes inside geometries", f"Found {counter_in_geometries} holes inside of geometries/features")
        else:
            info.add_info("No holes in the geometries found")


        out = processing.run("native:dissolve", {'INPUT':vectorlayer,
                                                      'FIELD':[],
                                                      'SEPARATE_DISJOINT':False,
                                                      'OUTPUT':'TEMPORARY_OUTPUT'})
        
        (gaps_layer, counter_gaps) = _holes_in_polygon(out['OUTPUT'], "gaps_in_layer")
        
        if counter_gaps > 0:
            info.add_warning(f"Found {counter_gaps} gaps between Geometries of the layer.")
            result.append_geodata("gaps_in_layer", gaps_layer)
            result.append_info("Gaps between geometries", f"Found {counter_gaps} gaps between geometries/features of the layer.")
        else:
            info.add_info(f"No gaps between geometries of the layer found")
        

        return (result if result.geodata_layer or result.info_output else None, info)

def overlaps() -> tuple[Result or None, Infotext or None]:
        # use index, then check if other features overlap with the current one, if so the actually check for an overlap
        pass
