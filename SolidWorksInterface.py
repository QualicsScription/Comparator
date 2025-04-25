import logging
import win32com.client

class SolidWorksInterface:
    def __init__(self):
        self.sw_app = None
        self.model_doc = None
        
    def connect(self):
        """SolidWorks uygulamasına bağlan"""
        try:
            self.sw_app = win32com.client.Dispatch("SldWorks.Application")
            self.sw_app.Visible = False
            return True
        except Exception as e:
            logging.error(f"SolidWorks bağlantı hatası: {e}")
            return False
    
    def open_document(self, file_path):
        """SolidWorks dosyasını aç"""
        try:
            self.model_doc = self.sw_app.OpenDoc6(file_path, 1, 1, "", None, None)
            return True
        except Exception as e:
            logging.error(f"Dosya açma hatası: {e}")
            return False
    
    def get_feature_tree(self):
        """Feature ağacını çıkar"""
        try:
            feature_mgr = self.model_doc.FeatureManager
            root_feature = feature_mgr.GetFeatures(True)
            return self._process_feature_tree(root_feature)
        except Exception as e:
            logging.error(f"Feature tree okuma hatası: {e}")
            return None
    
    def get_geometry_data(self):
        """Geometri verilerini çıkar"""
        try:
            body = self.model_doc.GetBodies2(1, False)
            return {
                'volume': body.GetMassProperties(1)[3],
                'surface_area': body.GetMassProperties(1)[4],
                'vertices': body.GetVertices(),
                'edges': body.GetEdges(),
                'faces': body.GetFaces()
            }
        except Exception as e:
            logging.error(f"Geometri okuma hatası: {e}")
            return None
            
    def _process_feature_tree(self, features):
        """Feature ağacını işle"""
        result = []
        for i in range(features.Count):
            feature = features.Item(i)
            feature_data = {
                'name': feature.Name,
                'type': feature.GetTypeName(),
                'id': feature.GetID(),
                'parameters': self._get_feature_parameters(feature),
                'children': []
            }
            
            # Alt özellikleri işle
            if hasattr(feature, 'GetChildren'):
                children = feature.GetChildren()
                if children and children.Count > 0:
                    feature_data['children'] = self._process_feature_tree(children)
                    
            result.append(feature_data)
        return result
        
    def _get_feature_parameters(self, feature):
        """Feature parametrelerini al"""
        params = {}
        try:
            # Parametreleri al
            if hasattr(feature, 'GetParameters'):
                parameters = feature.GetParameters()
                if parameters:
                    for i in range(parameters.Count):
                        param = parameters.Item(i)
                        params[param.Name] = param.Value
        except:
            pass
        return params
        
    def get_sketches(self):
        """Çizimleri al"""
        sketches = []
        try:
            feature_mgr = self.model_doc.FeatureManager
            features = feature_mgr.GetFeatures(False)
            
            for i in range(features.Count):
                feature = features.Item(i)
                if feature.GetTypeName() == "ProfileFeature":
                    sketch = {
                        'name': feature.Name,
                        'id': feature.GetID(),
                        'entities': self._get_sketch_entities(feature)
                    }
                    sketches.append(sketch)
        except Exception as e:
            logging.error(f"Çizim okuma hatası: {e}")
        
        return sketches
        
    def _get_sketch_entities(self, sketch_feature):
        """Çizim elemanlarını al"""
        entities = []
        try:
            sketch = sketch_feature.GetSpecificFeature2()
            sketch_entities = sketch.GetSketchEntities()
            
            for i in range(sketch_entities.Count):
                entity = sketch_entities.Item(i)
                entity_type = entity.GetType()
                
                entity_data = {
                    'type': entity_type,
                    'id': entity.GetID()
                }
                
                # Çizgi
                if entity_type == 1:  # Line
                    line = entity.GetSpecificFeature2()
                    entity_data['start'] = [line.GetStartPoint().X, line.GetStartPoint().Y, line.GetStartPoint().Z]
                    entity_data['end'] = [line.GetEndPoint().X, line.GetEndPoint().Y, line.GetEndPoint().Z]
                
                # Daire
                elif entity_type == 2:  # Circle
                    circle = entity.GetSpecificFeature2()
                    entity_data['center'] = [circle.GetCenterPoint().X, circle.GetCenterPoint().Y, circle.GetCenterPoint().Z]
                    entity_data['radius'] = circle.GetRadius()
                
                entities.append(entity_data)
        except:
            pass
            
        return entities
        
    def close(self):
        """SolidWorks bağlantısını kapat"""
        try:
            if self.model_doc:
                self.sw_app.CloseDoc(self.model_doc.GetTitle())
            if self.sw_app:
                self.sw_app.ExitApp()
            self.model_doc = None
            self.sw_app = None
        except:
            pass
