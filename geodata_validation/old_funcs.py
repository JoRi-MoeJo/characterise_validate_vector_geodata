# collection of utils to characterize and validate vector data

from qgis.core import QgsVectorLayer, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.core import QgsProject, QgsRectangle
from qgis.core import QgsPointXY, QgsGeometry, QgsFeature, QgsField
from qgis import processing 
from qgis.core import QgsWkbTypes
from qgis.PyQt.QtCore import QVariant

import json

class Infotext():
    def __init__(self, text: str="") -> None:
        self.content = self._set_content(text)
    
    def _set_content(self, text):
        if len(text.strip()) < 2 or text.strip()[-2:] != "\n":
            return text
        else:
            return text + "\n"
            
    def newline(self):
        self.content += "\n"

    def append(self, text: str|None):
        if not text:
            pass
        self.content += f"{text} \n"

    def add_info(self, text: str):
        self.content += f"INFO: {text} \n"

    def add_warning(self, text: str):
        self.content += f"WARNING: {text} \n"

    def add_error(self, text: str):
        self.content += f"ERROR: {text} \n"

    def clear(self):
        self.content = ""



class Result():
    def __init__(self, category: str, analysis: str, geodata_layer: dict=None, info_output: dict=None):
        self.category = category
        self.analysis = analysis
        self.geodata_layer = geodata_layer # dict of keys (names) and values (geodata_layer)
        self.info_output = info_output # dict of keys (names) and values (info)

    def append_geodata(self, name: str, geodata):
        if name not in self.geodata_layer:
            self.geodata_layer[name] = geodata
        else:
            raise ValueError(f"Key name already exists in this dictionary - {self.geodata_layer}")

    def append_info(self, name: str, info):
        if name not in self.info_output:
            self.info_output[name] = info
        else:
            raise ValueError(f"Key name already exists in this dictionary - {self.info_output}")



class DataStructureChecks():
    category_name = "Data Structure Checks"
    
    @staticmethod
    def null_vals(self, vectorlayer: type[QgsVectorLayer]) -> tuple[Result or None, Infotext or None]:
        method_info = Infotext("Checking for NULL values in the data structure:")
        result = Result(category=self.category_name, analysis="NULL check")

        fields = [(a.name(), a.typeName()) for a in vectorlayer.fields()]
        data = [o.attributes() for o in vectorlayer.getFeatures()]
        data_transposed = list(zip(*data))

        null_objs = [obj for obj in data if obj.count(None) >= 0.9*len(fields)]
        if len(null_objs) > 0:
            method_info.add_info(f"Found {len(null_objs)} objects with over 90% Null values")
            method_info.append("Null objects: ", ', '.join(null_objs))

            result.append_info("null objects", null_objs)

        null_attrs = [attr for attr in data_transposed if attr.count(None) >= 0.9*len(data)]
        if len(null_attrs) > 0:
            method_info.add_info(f"Found {len(null_attrs)} attributes in the data that have over 90% null values")
            method_info.append("Null attributes: ", ', '.join(null_attrs))

            result.append_info("null attributes", null_attrs)

        return (result if result.geodata_layer or result.info_output else None, 
                method_info or None)

    @staticmethod
    def oid(self) -> tuple[Result or None, Infotext or None]:
        pass

    @staticmethod
    def duplicates(self) -> tuple[Result or None, Infotext or None]:
        pass


class GeometryChecks():

    category_name = "Geometry Checks"

    @staticmethod
    def empty_geomtries(self, vectorlayer: type[QgsVectorLayer]) -> tuple[Result or None, Infotext or None]:
        info = Infotext("Analysis for empty geometries:")
        result = Result(category= self.category_name, analysis="Check for empty geometries")

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
    
    @staticmethod
    def _holes_in_polygon(self, polygon_layer: type[QgsVectorLayer], out_layer_name: str) -> tuple[QgsVectorLayer|None, int]:
        
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
        

    @staticmethod
    def holes(self, vectorlayer: type[QgsVectorLayer]) -> tuple[Result or None, Infotext or None]:
        info = Infotext()
        result = Result(category=self._category_name, analysis="Check for holes in geometries")

        if vectorlayer.geometryType() != QgsWkbTypes.PolygonGeometry:
            info.add_error("can't investigate geometries for holes that are not polygons.")
            return (None, info)

        (holes_in_geometries, counter_in_geometries) = self._holes_in_polygon(vectorlayer, "Holes inside geometries")
            
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
        
        (holes_in_layer, counter_layer) = self._holes_in_polygon(out['OUTPUT'], "Holes between geometries")
        
        if counter_layer > 0:
            info.add_warning(f"Found {counter_layer} holes between Geometries of the layer.")
            result.append_geodata("Holes_between_geoms", holes_in_layer)
            result.append_info("Holes between geometries", f"Found {counter_layer} holes between geometries/features of the layer.")
        else:
            info.add_info(f"No holes between geometries of the layer found")
        

        return (result if result.geodata_layer or result.info_output else None, info)


    @staticmethod
    def overlaps(self) -> tuple[Result or None, Infotext or None]:
        pass



class CrsChecks():

    category_name = "Crs Checks"

    @staticmethod
    def crs_characteristics(self, vectorlayer: type[QgsVectorLayer]) -> tuple[Result or None, Infotext or None]:
        crs = vectorlayer.crs()
        crs_type = crs.type()

        geographic = crs.isGeographic()

        auth_id = crs.authid()
        valid = crs.isValid()
        deprecated = crs.isDeprecated()
        postgissrid = crs.postgisSrid()

        if crs.hasVerticalAxis():
            vertical_crs = crs.verticalCrs()
            vertical_axis = crs.verticalAxis()
        else:
            vertical_crs = None
            vertical_axis = None
        
        is_3D = None
        if vectorlayer.hasFeatures():
            for i in range(vectorlayer.feaureCount()-1):
                geo = vectorlayer.getGeometry(i)
                if geo:
                    abstrgeo = geo.constGet()
                    is_3D = abstrgeo.is3D()
                    break
        

    @staticmethod
    def crs_code(self, vectorlayer: type[QgsVectorLayer]) -> tuple[Result or None, Infotext or None]:
        pass

    @staticmethod
    def crs_compare(self, vectorlayer: type[QgsVectorLayer], compare_crs: type[QgsCoordinateReferenceSystem]) -> tuple[Result or None, Infotext or None]:
        pass

    @staticmethod
    def check_crs_bounds(self, vectorlayer: type[QgsVectorLayer]) -> tuple[Result or None, Infotext or None]:
        info = Infotext()
        result = Result(category=self.category_name, analysis="Check Geometries for Crs bounds")
        
        crs = vectorlayer.crs()
        crs_bounds = crs.bounds()

        if 'EPSG' in crs.authid():
            epsg_code = int(crs.authid().split(':')[1])
            dest_crs = QgsCoordinateReferenceSystem(epsg_code)
        else:
            dest_crs = QgsCoordinateReferenceSystem().createFromWkt(crs.asWkt())
        
        source_crs = QgsCoordinateReferenceSystem(4326)

        crs_transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())

        bound_polygon = QgsGeometry.fromWkt(crs_bounds.asWktPolygon())
        bound_polygon.transorm(crs_transform)

        xmin, xmax = bound_polygon.boundingBox().xMinimum(), bound_polygon.boundingBox().xMaximum()
        ymin, ymax = bound_polygon.boundingBox().yMinimum(), bound_polygon.boundingBox().yMaximum()

        # crit_factor = 5 # adding the reciproce of this to the bounds for the check

        # crit_xmin, crit_xmax = xmin - (xmax-xmin)/crit_factor, xmax + (xmax-xmin)/crit_factor
        # crit_ymin, crit_ymax = ymin - (ymax-ymin)/crit_factor, ymax + (ymax-ymin)/crit_factor

        #crit_rectangle = QgsRectangle(crit_xmin, crit_ymin, crit_xmax, crit_ymax)
        crit_rectangle = QgsRectangle(xmin, ymin, xmax, ymax)

        feats_out_of_bounds = []
        for feat in vectorlayer.getFeatures():
            geom = feat.geometry()
            if not crit_rectangle.intersects(geom.boundingBox()):
                feats_out_of_bounds.append(tuple(feat.attributes(), geom))
        
        if len(feats_out_of_bounds) > 0:
            info.add_warning(f"{len(feats_out_of_bounds)} features/geometries lie out of bounds of the crs of the layer")
            result.append_info("Geometies out of bounds", f"{len(feats_out_of_bounds)} features are out of bounds of the crs of the layer")
        else:
            info.add_info(f"All geometries are inside the bounds of the crs.")
        


