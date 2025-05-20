from .status import Result, Infotext
from qgis.core import QgsVectorLayer



category_name = "Data Structure Checks"

def null_vals(vectorlayer: type[QgsVectorLayer]) -> tuple[Result or None, Infotext or None]:
        method_info = Infotext("Checking for NULL values in the data structure: \n")
        #print(result)
        #print(id(result))
        result = Result(category=category_name, analysis="NULL check")
        
        # Problem, dass bei nochmaligem Ablauf des Tools nach Schließen mit cancel das result objekt dieser Funktion
        # vom vorherigen Druchlauf weiterhin vorhanden ist, obwohl es meiner Meinung nach aufgrund des local namespaces 
        # der Funktion nach dem return nicht mehr vorhanden sein sollte. Das wäre generell ein großen Problem innerhalb des 
        # Toolv vielleicht
        # --> deswegen einmal prüfen, ob es wahrhaftig das selbe Objekt ist (Speicherposition prüfen) und dann auch nochtmal
        # diesbezüglich recherchieren.
        # auch müsste doch eigentlich mit dem instantiieren ein neues Objekt geschaffen werden. Warum wird das selbe verwendet?
        
        #print(id(result))
        #print(f"Result at start: {result.info_output.keys()}")

        result.reset_data()

        fields = [(a.name(), a.typeName()) for a in vectorlayer.fields()]
        data = [ [i+1] + o.attributes() for i, o in enumerate(vectorlayer.getFeatures())]
        data_transposed = list(zip(*data))

        null_objs = [obj for obj in data if obj.count(None) >= 0.9*len(fields)]
        if len(null_objs) > 0:
            method_info.add_info(f"Found {len(null_objs)} objects with over 90% Null values")
            method_info.append(f"Null objects: \n{null_objs}")

            result.append_info("null objects", null_objs)

        null_attrs = [[f"Field: {fieldname[0]}"] + list(attr) for attr, fieldname in zip(data_transposed, fields) if attr.count(None) >= 0.9*(len(data)-1)]
        if len(null_attrs) > 0:
            method_info.add_info(f"Found {len(null_attrs)} attributes in the data that have over 90% null values")
            method_info.add_info(f"Fields with mostly NULL values: {[fields[0] for fields in null_attrs]}")
            method_info.append(f"Null attributes: \n{null_attrs}")

            result.append_info("null attributes", null_attrs)

        return (result if result.geodata_layer or result.info_output else None, 
                method_info or None)

def oid(vectorlayer: type[QgsVectorLayer]) -> tuple[Result or None, Infotext or None]:
        info = Infotext()
        result = Result(category=category_name, analysis="Oid existence")

        result.reset_data()

        # start
        fields = [(a.name, a.type) for a in vectorlayer.fields()]
        attrs = list(zip(*[o.attributes() for o in vectorlayer.getFeatures()]))

        for attr, fname in zip(attrs, fields):
              if len(set(attr)) == len(attr):
                    pass
        
        pot_oids = [field for attr, field in zip(attrs, fields) if len(set(attr)) == len(attr)]

        if len(pot_oids) > 0:
              info.add_info(f"{len(pot_oids)} attributes can be user as an object identifier.")
              info.add_info(f"Potential Oids are: {pot_oids}")
              result.append_info("Potential OIDs", pot_oids)
        else:
              info.add_warning("No attribute can be used as an object identifier. Please consider creating one to be able to identify objects unambiguously.")
         
        return (result if result.geodata_layer or result.info_output else None, info or None)


def duplicates(vectorlayer: type[QgsVectorLayer]) -> tuple[Result or None, Infotext or None]:
        pass

