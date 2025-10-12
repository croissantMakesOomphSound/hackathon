import json
import os
class jsonHANDLER:
    def __init__(self,imagelink):
        self.imagelink=imagelink
        self.annotations=[]
        print("jsonhandler constructor called")
   
        
    def createannoatation(self,name,shape,desc,xmin,ymin,xmax,ymax):
        print("create annotation called")
        annotation = {
            "name": name,
            "shape": shape,
            "desc": desc,
            "xmin": xmin,
            "xmax": xmax,
            "ymin": ymin,
            "ymax": ymax
        }
        
        self.annotations.append(annotation)
        
    def createjson(self):
        data={ 
            "image_link":self.imagelink,
            "annotations":self.annotations
                              
                    
            }
        try:
            # ✅ Extract filename without extension from imagelink
            image_base = os.path.splitext(os.path.basename(self.imagelink))[0]

            # ✅ Use project-level 'json' folder
            project_root = os.path.dirname(os.path.abspath(__file__))
            json_dir = os.path.join(project_root, "json")
            os.makedirs(json_dir, exist_ok=True)

            # ✅ Save file as project/json/<image_base>.json
            json_path = os.path.join(json_dir, f"{image_base}.json")

            with open(json_path, "w") as json_file:
                json.dump(data, json_file, indent=4)
                print(f"JSON success → {json_path}")
                print("JSON Output:")
                print(json.dumps(data, indent=4))
                return json.dumps(data, indent=4)
                
        except Exception:
            print("FAILED")
            return
                  
