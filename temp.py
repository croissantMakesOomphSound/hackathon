import sys
import cv2
import numpy as np
import torch
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton,QFileDialog, QVBoxLayout,QHBoxLayout,QFormLayout, QWidget, QMessageBox,QLineEdit,QScrollArea,QTextEdit
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QPoint
from untitled1 import jsonHANDLER
from untitled2 import aichecker


class ShapeAnnotator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.drawing = False
        self.start_point = None
        self.shape = 'circle'
        self.shapes = []  # List to store drawn shapes
        self.setGeometry(100, 100, 700, 2200)
        
        # Create a central widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Layouts
        self.layout = QHBoxLayout(self.central_widget)
        self.layout1 = QVBoxLayout()
        
        # Create a scroll area for the image
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        # Create a label to display images
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.image_label)

        # Add scroll area to the layout
        self.layout1.addWidget(self.scroll_area)

        # Create buttons
        self.open_button = QPushButton("Open Image", self)
        self.open_button.clicked.connect(self.open_image)
        self.layout1.addWidget(self.open_button)

        # Shape buttons
        self.circle_button = QPushButton("Circle", self)
        self.circle_button.clicked.connect(lambda: self.change_shape('circle'))

        self.rectangle_button = QPushButton("Rectangle", self)
        self.rectangle_button.clicked.connect(lambda: self.change_shape('rectangle'))

        self.oval_button = QPushButton("Oval", self)
        self.oval_button.clicked.connect(lambda: self.change_shape('oval'))

        self.quit_button = QPushButton("Quit", self)
        self.quit_button.clicked.connect(self.close)

        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.submit_shape)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.circle_button)
        button_layout.addWidget(self.rectangle_button)
        button_layout.addWidget(self.oval_button)
        button_layout.addWidget(self.quit_button)
        button_layout.addWidget(self.submit_button)

        # Add button layout to the main layout
        self.layout1.addLayout(button_layout)

        # Input fields
        self.name = QLineEdit()
        self.name1 = QLineEdit()
        self.name2 = QLineEdit()
        self.name3 = QLineEdit()
        self.name4 = QLineEdit()
        self.name5 = QLineEdit()
        self.name6 = QTextEdit()

        # Form layout for annotations
        form_layout = QFormLayout()
        form_layout.addRow(QLabel("Name:"), self.name)
        form_layout.addRow(QLabel("Shape:"), self.name5)
        form_layout.addRow(QLabel("Description:"), self.name6)
        form_layout.addRow(QLabel("Xmin:"), self.name1)
        form_layout.addRow(QLabel("Ymin:"), self.name2)
        form_layout.addRow(QLabel("Xmax:"), self.name3)
        form_layout.addRow(QLabel("Ymax:"), self.name4)

        # Add form layout to the main layout
        self.layout1.addLayout(form_layout)

        # Add everything to the main layout
        self.layout.addLayout(self.layout1)

        self.img = None  # Store the loaded image

    def open_image(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image File", "",
                                                     "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)", options=options)
        if file_name:
            self.load_image(file_name)
            self.imagefile = r"{}".format(file_name)
            self.orgimg = cv2.imread(self.imagefile)
            self.img = cv2.resize(self.orgimg, (600, 600))
            
            # Model inference
            model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
            results = model(self.img)  # Use self.img here
            
            # Process results
            self.process_results(results)
            self.update_image()
    def process_results(self, results):
    # Get predictions
        predictions_tensor = results.xyxy[0]  # img1 predictions (tensor)
    
    # Clear previous shapes
        self.shapes.clear()

    # Draw boxes on the image and store shapes
        img_with_boxes = self.img.copy()  # Copy the original image for drawing
        for pred in predictions_tensor:
            xmin, ymin, xmax, ymax, conf, cls = pred.tolist()  # Convert tensor to list
            class_name = results.names[int(cls)]  # Get class name from the model

            # Create a shape for the bounding box
            self.shapes.append((class_name, (xmin, ymin), (xmax, ymax)))

            # Draw bounding box on the image
            cv2.rectangle(img_with_boxes, (int(xmin), int(ymin)), (int(xmax), int(ymax)), (0, 255, 0), 2)

            # Update the input fields with predictions
            self.name.setText(class_name)
            self.name1.setText(str(int(xmin)))
            self.name2.setText(str(int(ymin)))
            self.name3.setText(str(int(xmax)))
            self.name4.setText(str(int(ymax)))
            self.name5.setText("rectangle")  # Assuming bounding boxes are rectangles
            self.name6.setPlainText("Detected object")  # Example description

        # Set the processed image with bounding boxes
        self.img = img_with_boxes


    def load_image(self, file_name):
        pixmap = QPixmap(file_name)
        self.image_label.setPixmap(pixmap)
        self.image_label.adjustSize()  # Adjust size to fit the scroll area

    def update_image(self):
        """Redraw all shapes on the image and update the QLabel."""
        if self.img is None:
            return
        img_copy = self.img.copy()
        for shape_info in self.shapes:
            shape_type, start, end = shape_info
            if shape_type == 'circle':
                radius = int(np.linalg.norm(np.array(start) - np.array(end)))
                cv2.circle(img_copy, start, radius, (0, 0, 255), thickness=2)
            elif shape_type == 'rectangle':
                cv2.rectangle(img_copy, start, end, (0, 255, 0), thickness=2)
            elif shape_type == 'oval':
                center = ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2)
                axes = (abs(start[0] - end[0]) // 2, abs(start[1] - end[1]) // 2)
                cv2.ellipse(img_copy, center, axes, 0, 0, 360, (255, 0, 0), thickness=2)

        height, width, channel = img_copy.shape
        bytes_per_line = 3 * width
        q_img = QImage(img_copy.data, width, height, bytes_per_line, QImage.Format_BGR888)
        self.image_label.setPixmap(QPixmap.fromImage(q_img))
        self.image_label.adjustSize()  # Adjust size to fit the scroll area

    def change_shape(self, new_shape):
        self.shape = new_shape
        self.name5.setText(new_shape)  # Update the shape name field

    def mousePressEvent(self, event):
        if self.img is not None and event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = QPoint(event.pos().x() - self.image_label.x(), event.pos().y() - self.image_label.y())

    def mouseMoveEvent(self, event):
        if self.drawing:
            end_point = QPoint(event.pos().x() - self.image_label.x(), event.pos().y() - self.image_label.y())
            self.update_temp_shape(end_point)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
            end_point = QPoint(event.pos().x() - self.image_label.x(), event.pos().y() - self.image_label.y())
            self.shapes.append((self.shape, (self.start_point.x(), self.start_point.y()), (end_point.x(), end_point.y())))
            self.update_image()

    def update_temp_shape(self, end_point):
        if self.img is None:
            return

        img_copy = self.img.copy()

        start_x, start_y = self.start_point.x(), self.start_point.y()
        end_x, end_y = end_point.x(), end_point.y()

        xmin = min(start_x, end_x)
        ymin = min(start_y, end_y)
        xmax = max(start_x, end_x)
        ymax = max(start_y, end_y)

        if self.shape == 'circle':
            radius = int(np.linalg.norm(np.array((start_x, start_y)) - np.array((end_x, end_y))))
            cv2.circle(img_copy, (start_x, start_y), radius, (0, 0, 255), thickness=2)
        elif self.shape == 'rectangle':
            cv2.rectangle(img_copy, (start_x, start_y), (end_x, end_y), (0, 255, 0), thickness=2)
        elif self.shape == 'oval':
            center = ((start_x + end_x) // 2, (start_y + end_y) // 2)
            axes = (abs(start_x - end_x) // 2, abs(start_y - end_y) // 2)
            cv2.ellipse(img_copy, center, axes, 0, 0, 360, (255, 0, 0), thickness=2)


        self.name1.setText(str(xmin))
        self.name2.setText(str(ymin))
        self.name3.setText(str(xmax))
        self.name4.setText(str(ymax))

        height, width, channel = img_copy.shape
        bytes_per_line = 3 * width
        q_img = QImage(img_copy.data, width, height, bytes_per_line, QImage.Format_BGR888)
        self.image_label.setPixmap(QPixmap.fromImage(q_img))
        self.image_label.adjustSize()  # Adjust size to fit the scroll area

    def submit_shape(self):
        print("submit pressed")
        if self.shapes:
            last_shape = self.shapes[-1]
            shape_type, start, end = last_shape
        
        name=self.name.text()
        xmin=self.name1.text()
        ymin=self.name2.text()
        xmax=self.name3.text()
        ymax=self.name4.text()
        shape=self.name5.text()
        desc=self.name6.toPlainText() 
        imagefile=self.imagefile
        
        newImageAnnotatation=jsonHANDLER(name,imagefile)
        newImageAnnotatation.createannoatation(name,shape,desc,xmin,ymin,xmax,ymax)
        newImageAnnotatation.createjson()
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ShapeAnnotator()
    window.show()
    sys.exit(app.exec_())

