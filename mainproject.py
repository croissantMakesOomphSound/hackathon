import sys
import cv2
import os
import numpy as np
import torch
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, 
                             QVBoxLayout, QHBoxLayout, QFormLayout, QWidget, QMessageBox, 
                             QLineEdit, QScrollArea, QTextEdit)
from PyQt5.QtGui import QPixmap, QImage, QIcon, QPalette, QBrush
from PyQt5.QtCore import Qt, QPoint
from untitled1 import jsonHANDLER



class ShapeAnnotator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.drawing = False
        self.clicked = False
        self.start_point = None
        self.shape = 'circle'
        self.shapes = []  # List to store drawn shapes
        self.setGeometry(100, 100, 700, 700)
        self.scale_factor = 1.0  # Initialize scale factor
        
        self.selected_shape = None
        self.selected_shape_index = -1
        self.dragging = False
        self.resizing = False
        self.handle_radius = 5  # For resizing handle
        
        self.setup_background()
        
        # Create a central widget
        self.central_widget = QWidget(self)
        self.central_widget.setStyleSheet("background-color: rgba(255, 255, 255, 180);")  # Semi-transparent white
        self.setCentralWidget(self.central_widget)
        
        # Create a scroll area for the image
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        
        # Create a label to display images
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.image_label)
        
        # Create buttons
        self.open_button = QPushButton("Open Image", self)
        self.open_button.clicked.connect(self.open_image)
    
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

        # Zoom buttons
        self.zoom_in_button = QPushButton("Zoom In", self)
        self.zoom_in_button.clicked.connect(self.zoom_in)

        self.zoom_out_button = QPushButton("Zoom Out", self)
        self.zoom_out_button.clicked.connect(self.zoom_out)
    
        # Create layout1 for zoom buttons
        layout1 = QHBoxLayout()
        layout1.addWidget(self.zoom_in_button)
        layout1.addWidget(self.zoom_out_button)

        # Create layout2 for the scroll area and open button
        layout2 = QVBoxLayout()
        layout2.addWidget(self.scroll_area)
        layout2.addWidget(self.open_button)

        # Create layout3 for shape buttons
        layout3 = QHBoxLayout()
        layout3.addWidget(self.circle_button)
        layout3.addWidget(self.rectangle_button)
        layout3.addWidget(self.oval_button)
        layout3.addWidget(self.quit_button)
        
        # Create container1 and set its layout
        container1 = QWidget()
        container1_layout = QVBoxLayout(container1)  # Create a vertical layout for container1
        container1_layout.addLayout(layout1)
        container1_layout.addLayout(layout2)
        container1_layout.addLayout(layout3)
        
        # Input fields
        self.name = QLineEdit()
        self.name1 = QLineEdit()
        self.name2 = QLineEdit()
        self.name3 = QLineEdit()
        self.name4 = QLineEdit()
        self.name5 = QLineEdit()
        self.name6 = QTextEdit()
        
        # Create layout4 for form inputs and submit button
        form_layout = QFormLayout()
        form_layout.addRow(QLabel("Name:"), self.name)
        form_layout.addRow(QLabel("Shape:"), self.name5)
        form_layout.addRow(QLabel("Description:"), self.name6)
        form_layout.addRow(QLabel("Xmin:"), self.name1)
        form_layout.addRow(QLabel("Ymin:"), self.name2)
        form_layout.addRow(QLabel("Xmax:"), self.name3)
        form_layout.addRow(QLabel("Ymax:"), self.name4)
            
        layout4 = QVBoxLayout()
        layout4.addLayout(form_layout)
        layout4.addWidget(self.submit_button)

        # Create container2 and set its layout
        container2 = QWidget()
        container2.setLayout(layout4)  # Set layout4 to container2

        self.name8=QTextEdit()
        layout5=QVBoxLayout()
        layout5.addWidget(self.name8)
        
        container3 = QWidget()
        container3.setLayout(layout5)
        container3.setFixedSize(400, 800)
        
        # Main layout to hold both containers
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.addWidget(container1)  # Add container1 to the main layout
        main_layout.addWidget(container2)  # Add container2 to the main layout
        main_layout.addWidget(container3)  # Add container3 to the main layout

        # Set the main layout to the central widget
        self.central_widget.setLayout(main_layout)
        
        self.img = None  # Store the loaded image
        self.original_pixmap = None  # Store the original pixmap

    
    def setup_background(self):
        background_path = r"C:\Users\TMpub\OneDrive\Desktop\londonbridge.jpg"
        if not os.path.exists(background_path):
            print(f"Error: Background image not found at {background_path}")
            return

        # Load the background image
        background = QImage(background_path)
        if background.isNull():
            print(f"Error: Failed to load background image from {background_path}")
            return

        # Scale the background image to the size of the window
        scaled_background = background.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        # Create a palette and set it as the window's background
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(scaled_background))
        self.setPalette(palette)

    def resizeEvent(self, event):
        # Resize the background image when the window is resized
        super().resizeEvent(event)
        self.setup_background()

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

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and self.img is not None:
            click_position = QPoint(event.pos().x() - self.image_label.x(), event.pos().y() - self.image_label.y())
        
            for index, shape_info in enumerate(self.shapes):
                shape_type, start, end = shape_info
                
                if self.is_point_within_shape(click_position, start, end):
                    self.selected_shape = shape_info
                    self.selected_shape_index = index
                    print(f"Selected annotation: {shape_type} at {start} to {end}")
                    break  # Stop checking after the first match

    def load_image(self, file_name):
        pixmap = QPixmap(file_name)
        self.original_pixmap = pixmap  
        self.image_label.setPixmap(pixmap)
        self.image_label.adjustSize()  # Adjust size to fit the scroll area
        self.scale_factor = 1.0
    
    def zoom_in(self):
        self.scale_image(1.25)

    def zoom_out(self):
        self.scale_image(0.8)

    def scale_image(self, factor):
        if self.original_pixmap:
            self.scale_factor *= factor
            new_size = self.original_pixmap.size() * self.scale_factor
            scaled_pixmap = self.original_pixmap.scaled(new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.adjustSize()
    
    def update_image(self):
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

        # Draw handles for resizing
        if self.selected_shape:
            shape_type, start, end = self.selected_shape
            handle_pos = (end[0] + 5, end[1] + 5)  # Position for resizing handle
            cv2.circle(img_copy, handle_pos, self.handle_radius, (255, 0, 0), -1)  # Draw handle
        
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
        if self.selected_shape and event.button() == Qt.LeftButton:
            # Check if the mouse is over the resizing handle
            handle_pos = (self.shapes[self.selected_shape_index][2][0] + 5, self.shapes[self.selected_shape_index][2][1] + 5)
            if (QPoint(event.pos().x(), event.pos().y()) - QPoint(*handle_pos)).manhattanLength() <= self.handle_radius:
                self.resizing = True  # Start resizing
            else:
                self.dragging = True
                self.drag_start_point = QPoint(event.pos().x() - self.image_label.x(), event.pos().y() - self.image_label.y())

    def mouseMoveEvent(self, event):
        if self.drawing:
            end_point = QPoint(event.pos().x() - self.image_label.x(), event.pos().y() - self.image_label.y())
            self.update_temp_shape(end_point)
        if self.dragging and self.selected_shape:
            current_point = QPoint(event.pos().x() - self.image_label.x(), event.pos().y() - self.image_label.y())
            delta = current_point - self.drag_start_point
            start, end = self.selected_shape[1], self.selected_shape[2]
            new_start = (start[0] + delta.x(), start[1] + delta.y())
            new_end = (end[0] + delta.x(), end[1] + delta.y())
            self.shapes[self.selected_shape_index] = (self.selected_shape[0], new_start, new_end)
            self.drag_start_point = current_point
            self.update_image()
        if self.resizing and self.selected_shape:
            current_point = QPoint(event.pos().x() - self.image_label.x(), event.pos().y() - self.image_label.y())
            end = self.selected_shape[2]
            new_end = (current_point.x(), current_point.y())
            self.shapes[self.selected_shape_index] = (self.selected_shape[0], self.selected_shape[1], new_end)
            self.update_image()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.drawing:
                self.drawing = False
                end_point = QPoint(event.pos().x() - self.image_label.x(), event.pos().y() - self.image_label.y())
                self.shapes.append((self.shape, (self.start_point.x(), self.start_point.y()), (end_point.x(), end_point.y())))
                self.update_image()
            elif self.dragging:
                self.dragging = False
            elif self.resizing:
                self.resizing = False  # End resizing

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
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(QPixmap.fromImage(q_img))
        self.image_label.adjustSize()  # Adjust size to fit the scroll area

    def submit_shape(self):
        print("submit pressed")
        if self.shapes:
            last_shape = self.shapes[-1]
            shape_type, start, end = last_shape
        
        name = self.name.text()
        xmin = self.name1.text()
        ymin = self.name2.text()
        xmax = self.name3.text()
        ymax = self.name4.text()
        shape = self.name5.text()
        desc = self.name6.toPlainText() 
        imagefile = self.imagefile
        
        newImageAnnotatation = jsonHANDLER(name, imagefile)
        newImageAnnotatation.createannoatation(name, shape, desc, xmin, ymin, xmax, ymax)
        self.name8.setText(newImageAnnotatation.createjson())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ShapeAnnotator()
    window.show()
    sys.exit(app.exec_())

