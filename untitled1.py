import json
class jsonHANDLER:
    def __init__(self,imagename,imagelink):
        self.imagename=imagename
        self.imagelink=imagelink
        self.annotations=[]
        
    def createannoatation(self,name,shape,desc,xmin,ymin,xmax,ymax):
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
            "image_name":self.imagename,
            "image_link":self.imagelink,
            "annotations":self.annotations
                              
                    
            }
        try:
          with open(f"{self.imagename}.json", "w") as json_file:
             json.dump(data, json_file, indent=4)
             print("JSON success")
        except Exception:
            print("FAILED")
            traceback.print_exc()
                  
