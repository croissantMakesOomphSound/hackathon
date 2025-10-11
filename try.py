# annotated_app.py
import sys, os, copy
import cv2
import numpy as np
import torch
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, QFileDialog,
                             QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QFormLayout,
                             QLineEdit, QTextEdit)
from PyQt5.QtGui import QPixmap, QImage, QPalette, QBrush
from PyQt5.QtCore import Qt, QPoint

# Replace with your jsonHANDLER import
from untitled1 import jsonHANDLER


class ShapeAnnotator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Annotator")
        self.setGeometry(100, 100, 1100, 800)

        # Image state
        self.imagefile = None
        self.orig_bgr = None       # original cv2 BGR image as loaded
        self.canvas_bgr = None     # base image used for drawing annotations (kept same size as orig_bgr)
        self.scale_factor = 1.0    # display scaling applied to pixmap shown in QLabel

        # Annotations: list of dicts { 'type':..., 'start':(x,y), 'end':(x,y), 'label':..., 'source': 'AI'|'manual' }
        self.shapes = []

        # Selection / interaction
        self.selected_index = None
        self.drawing = False
        self.start_pt = None
        self.dragging = False
        self.resizing = False
        self.handle_radius = 8

        # Undo/Redo stacks (store deep copies of shapes)
        self.undo_stack = []
        self.redo_stack = []

        self.setup_ui()

    def setup_ui(self):
        # central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Left: controls + image area
        vleft = QVBoxLayout()

        # Zoom controls
        zrow = QHBoxLayout()
        btn_open = QPushButton("Open Image")
        btn_open.clicked.connect(self.open_image)
        zrow.addWidget(btn_open)
        btn_zoom_in = QPushButton("Zoom In")
        btn_zoom_in.clicked.connect(lambda: self.scale_image(1.25))
        btn_zoom_out = QPushButton("Zoom Out")
        btn_zoom_out.clicked.connect(lambda: self.scale_image(0.8))
        zrow.addWidget(btn_zoom_in); zrow.addWidget(btn_zoom_out)
        vleft.addLayout(zrow)

        # Graphics area using QLabel inside QScrollArea
        self.image_label = QLabel(alignment=Qt.AlignCenter)
        self.image_label.setBackgroundRole(QPalette.Base)
        self.image_label.setMouseTracking(True)
        self.image_label.installEventFilter(self)  # capture mouse events centrally
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.image_label)
        vleft.addWidget(self.scroll)

        # Shape controls (simple)
        shape_row = QHBoxLayout()
        self.shape_field = QLineEdit("rectangle")
        shape_row.addWidget(self.shape_field)
        btn_submit = QPushButton("Submit")
        btn_submit.clicked.connect(self.submit_shape)
        shape_row.addWidget(btn_submit)
        vleft.addLayout(shape_row)

        # Right: form panel to show details and last json
        right = QVBoxLayout()
        form = QFormLayout()
        self.name = QLineEdit()
        self.xmin = QLineEdit(); self.ymin = QLineEdit(); self.xmax = QLineEdit(); self.ymax = QLineEdit()
        form.addRow("Label:", self.name)
        form.addRow("Xmin:", self.xmin); form.addRow("Ymin:", self.ymin)
        form.addRow("Xmax:", self.xmax); form.addRow("Ymax:", self.ymax)
        right.addLayout(form)
        self.json_out = QTextEdit(); right.addWidget(self.json_out)

        # main layout
        main = QHBoxLayout(central)
        left_widget = QWidget(); left_widget.setLayout(vleft)
        right_widget = QWidget(); right_widget.setLayout(right)
        main.addWidget(left_widget, 4)
        main.addWidget(right_widget, 1)

    #
    # ----------------------- Image loading & YOLO inference -----------------------
    #
    def open_image(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not fname:
            return
        self.imagefile = fname
        bgr = cv2.imread(fname)
        if bgr is None:
            return
        self.orig_bgr = bgr.copy()
        self.canvas_bgr = self.orig_bgr.copy()
        self.scale_factor = 1.0
        self.shapes.clear()
        self.undo_stack.clear(); self.redo_stack.clear()

        # Run YOLO (small) on a resized copy for speed but convert back to original coords
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        # run on a copy resized to (640, 640) to avoid OOM on big images
        h, w = self.orig_bgr.shape[:2]
        shorter = 640
        scale = shorter / max(h, w)
        infer_img = cv2.resize(self.orig_bgr, (int(w*scale), int(h*scale)))
        results = model(infer_img[..., ::-1])  # model expects RGB
        preds = results.xyxy[0].cpu().numpy()  # x1,y1,x2,y2,conf,cls

        # convert predicted boxes back to original image coordinates
        for p in preds:
            x1, y1, x2, y2, conf, cls = p
            x1 /= scale; y1 /= scale; x2 /= scale; y2 /= scale
            lbl = results.names[int(cls)]
            ann = {'type': 'rectangle', 'start': (int(x1), int(y1)), 'end': (int(x2), int(y2)),
                   'label': lbl, 'source': 'AI'}
            self.shapes.append(ann)

        self.save_state()  # initial state for undo
        self.update_image()

    #
    # ----------------------- Undo / Redo helpers -----------------------
    #
    def save_state(self):
        # push deep copy of shapes to undo and clear redo
        self.undo_stack.append(copy.deepcopy(self.shapes))
        # cap stack length if needed
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append(copy.deepcopy(self.shapes))
        self.shapes = self.undo_stack.pop()
        self.selected_index = None
        self.update_image()

    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(copy.deepcopy(self.shapes))
        self.shapes = self.redo_stack.pop()
        self.selected_index = None
        self.update_image()

    #
    # ----------------------- Rendering -----------------------
    #
    def update_image(self):
        """Re-render the canvas image with annotations and put scaled pixmap in QLabel."""
        if self.orig_bgr is None:
            return
        # start from original image
        canvas = self.orig_bgr.copy()

        # draw all shapes onto canvas (image coords)
        for idx, ann in enumerate(self.shapes):
            st = tuple(map(int, ann['start'])); ed = tuple(map(int, ann['end']))
            if ann['type'] == 'rectangle':
                color = (0, 255, 0) if ann['source'] == 'AI' else (0, 128, 255)
                cv2.rectangle(canvas, st, ed, color, 2)
                # label
                cv2.putText(canvas, ann.get('label', ''), (st[0], max(st[1]-6, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            elif ann['type'] == 'circle':
                r = int(np.hypot(ed[0]-st[0], ed[1]-st[1]))
                cv2.circle(canvas, st, r, (0, 0, 255), 2)
            # draw selection handle for selected shape
            if idx == self.selected_index:
                # show small handle at end
                xh, yh = ed
                cv2.circle(canvas, (xh, yh), self.handle_radius, (255, 0, 0), -1)

        self.canvas_bgr = canvas

        # convert to QImage and scale by scale_factor for display
        h, w = canvas.shape[:2]
        bytes_per_line = 3 * w
        qimg = QImage(canvas.data, w, h, bytes_per_line, QImage.Format_BGR888)
        pix = QPixmap.fromImage(qimg)
        if self.scale_factor != 1.0:
            pix = pix.scaled(pix.width() * self.scale_factor, pix.height() * self.scale_factor, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(pix)
        self.image_label.adjustSize()

    #
    # ----------------------- Coordinate conversion helpers -----------------------
    #
    def widget_to_image(self, wpt):
        """Convert a QPoint in widget coordinates (mouse event pos relative to image_label)
           to image coordinates (in pixels of orig_bgr), taking scale_factor into account."""
        if self.canvas_bgr is None:
            return None
        # image_label might have margins if scaled with KeepAspectRatio; compute top-left offset
        pix = self.image_label.pixmap()
        if pix is None:
            return None
        pix_w = pix.width(); pix_h = pix.height()
        lbl_w = self.image_label.width(); lbl_h = self.image_label.height()
        # compute offset of pixmap inside label (centered)
        offset_x = max((lbl_w - pix_w) // 2, 0)
        offset_y = max((lbl_h - pix_h) // 2, 0)
        ix = (wpt.x() - offset_x) / self.scale_factor
        iy = (wpt.y() - offset_y) / self.scale_factor
        return (int(ix), int(iy))

    def image_to_widget(self, img_pt):
        if self.canvas_bgr is None:
            return None
        x, y = img_pt
        return QPoint(int(x * self.scale_factor), int(y * self.scale_factor))

    def point_in_rect(self, pt, start, end):
        x, y = pt
        x0, y0 = start; x1, y1 = end
        xmin, xmax = min(x0, x1), max(x0, x1)
        ymin, ymax = min(y0, y1), max(y0, y1)
        return (xmin <= x <= xmax) and (ymin <= y <= ymax)

    #
    # ----------------------- Mouse handling (via eventFilter) -----------------------
    #
    def eventFilter(self, source, event):
        # We installed on image_label, so map all relevant mouse events here.
        if source is self.image_label:
            if event.type() == event.MouseButtonDblClick and event.button() == Qt.LeftButton:
                wpos = event.pos()
                imgpt = self.widget_to_image(wpos)
                # select the first shape that contains the point
                self.selected_index = None
                for i, ann in enumerate(self.shapes):
                    if ann['type'] == 'rectangle' and self.point_in_rect(imgpt, ann['start'], ann['end']):
                        self.selected_index = i
                        # populate form fields
                        s, e = ann['start'], ann['end']
                        self.name.setText(ann.get('label', ''))
                        self.xmin.setText(str(int(min(s[0], e[0])))); self.ymin.setText(str(int(min(s[1], e[1]))))
                        self.xmax.setText(str(int(max(s[0], e[0])))); self.ymax.setText(str(int(max(s[1], e[1]))))
                        self.update_image()
                        break
                return True

            if event.type() == event.MouseButtonPress and event.button() == Qt.LeftButton:
                wpos = event.pos()
                imgpt = self.widget_to_image(wpos)
                # If clicked on selected handle -> start resizing
                if self.selected_index is not None:
                    ann = self.shapes[self.selected_index]
                    end = ann['end']
                    # compute handle in widget coords
                    handle_w = QPoint(int(end[0]*self.scale_factor), int(end[1]*self.scale_factor))
                    if (QPoint(wpos) - handle_w).manhattanLength() <= self.handle_radius + 4:
                        self.resizing = True
                        self.save_state()
                        return True
                    # else if clicked inside shape -> start dragging
                    if self.point_in_rect(imgpt, ann['start'], ann['end']):
                        self.dragging = True
                        self.drag_start = imgpt
                        self.save_state()
                        return True
                # else start drawing a new shape
                self.drawing = True
                self.start_pt = imgpt
                self.save_state()
                return True

            if event.type() == event.MouseMove:
                wpos = event.pos()
                imgpt = self.widget_to_image(wpos)
                if self.drawing and imgpt:
                    # temporary drawing: show current shape in bounding box
                    tmp_ann = {'type': self.shape_field.text(), 'start': self.start_pt, 'end': imgpt, 'label': self.name.text(), 'source': 'manual'}
                    # show preview by adding to list temporarily
                    # But avoid mutating actual shapes: render preview manually
                    self.update_image()
                    # draw preview overlay
                    canvas = self.canvas_bgr.copy()
                    st, ed = tmp_ann['start'], tmp_ann['end']
                    cv2.rectangle(canvas, st, ed, (0, 128, 255), 2)
                    h, w = canvas.shape[:2]
                    qimg = QImage(canvas.data, w, h, 3*w, QImage.Format_BGR888)
                    pix = QPixmap.fromImage(qimg)
                    if self.scale_factor != 1.0:
                        pix = pix.scaled(pix.width() * self.scale_factor, pix.height() * self.scale_factor, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_label.setPixmap(pix)
                    return True
                if self.dragging and imgpt is not None:
                    dx = imgpt[0] - self.drag_start[0]
                    dy = imgpt[1] - self.drag_start[1]
                    ann = self.shapes[self.selected_index]
                    s = ann['start']; e = ann['end']
                    ann['start'] = (int(s[0] + dx), int(s[1] + dy))
                    ann['end'] = (int(e[0] + dx), int(e[1] + dy))
                    self.drag_start = imgpt
                    self.update_image()
                    return True
                if self.resizing and imgpt is not None:
                    ann = self.shapes[self.selected_index]
                    ann['end'] = (int(imgpt[0]), int(imgpt[1]))
                    self.update_image()
                    return True

            if event.type() == event.MouseButtonRelease and event.button() == Qt.LeftButton:
                if self.drawing:
                    end_pt = self.widget_to_image(event.pos())
                    if end_pt and self.start_pt:
                        ann = {'type': self.shape_field.text(), 'start': self.start_pt, 'end': end_pt, 'label': self.name.text(), 'source': 'manual'}
                        self.shapes.append(ann)
                        self.selected_index = len(self.shapes)-1
                        self.update_image()
                    self.drawing = False
                    return True
                if self.dragging:
                    self.dragging = False
                    return True
                if self.resizing:
                    self.resizing = False
                    return True

        return super().eventFilter(source, event)

    #
    # ----------------------- Zoom helpers -----------------------
    #
    def scale_image(self, factor):
        # update scale_factor and re-render (we do not actually rescale underlying orig image)
        self.scale_factor *= factor
        # clamp scale
        self.scale_factor = max(0.1, min(self.scale_factor, 8.0))
        self.update_image()

    #
    # ----------------------- Submit / JSON -----------------------
    #
    def submit_shape(self):
        # use jsonHANDLER to create annotation for selected or last shape
        if not self.imagefile:
            return
        if self.selected_index is None and not self.shapes:
            return
        idx = self.selected_index if self.selected_index is not None else len(self.shapes)-1
        ann = self.shapes[idx]
        name = self.name.text() or ann.get('label','')
        xmin = str(int(min(ann['start'][0], ann['end'][0])))
        ymin = str(int(min(ann['start'][1], ann['end'][1])))
        xmax = str(int(max(ann['start'][0], ann['end'][0])))
        ymax = str(int(max(ann['start'][1], ann['end'][1])))
        shape = ann['type']
        desc = self.json_out.toPlainText() or "Detected/Annotated"
        h = jsonHANDLER(name, self.imagefile)
        h.createannoatation(name, shape, desc, xmin, ymin, xmax, ymax)
        self.json_out.setText(h.createjson())

    #
    # ----------------------- Utility keyboard shortcuts -----------------------
    #
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Z and (event.modifiers() & Qt.ControlModifier):
            self.undo()
        elif event.key() == Qt.Key_Y and (event.modifiers() & Qt.ControlModifier):
            self.redo()
        elif event.key() == Qt.Key_Delete:
            if self.selected_index is not None:
                self.save_state()
                self.shapes.pop(self.selected_index)
                self.selected_index = None
                self.update_image()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ShapeAnnotator()
    w.show()
    sys.exit(app.exec_())
