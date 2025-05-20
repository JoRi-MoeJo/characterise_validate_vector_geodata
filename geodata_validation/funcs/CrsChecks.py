
from .status import Result, Infotext
from qgis.core import QgsVectorLayer, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.core import QgsProject, QgsRectangle
from qgis.core import QgsGeometry


category_name = "Crs Checks"

def crs_characteristics(vectorlayer: type[QgsVectorLayer]) -> tuple[Result or None, Infotext or None]:
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


def crs_code(vectorlayer: type[QgsVectorLayer]) -> tuple[Result or None, Infotext or None]:
        pass

def crs_compare(vectorlayer: type[QgsVectorLayer], compare_crs: type[QgsCoordinateReferenceSystem]) -> tuple[Result or None, Infotext or None]:
        pass

def check_crs_bounds(vectorlayer: type[QgsVectorLayer]) -> tuple[Result or None, Infotext or None]:
        info = Infotext()
        result = Result(category=category_name, analysis="Check Geometries for Crs bounds")
        
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


