import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout

class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # QVBoxLayout 생성
        layout = QVBoxLayout(self)
        
        # QPushButton 생성
        self.button = QPushButton("Press Me", self)
        self.button.clicked.connect(self.on_click)
        self.button.setCheckable(True)
        # self.button.setChecked(False)
        # 레이아웃에 버튼 추가
        layout.addWidget(self.button)
        
        # 윈도우 설정
        self.setLayout(layout)
        self.setWindowTitle('QPushButton Set Down')
        self.setGeometry(300, 300, 200, 100)
    
    def on_click(self):
        # 버튼을 눌러진 상태로 설정
        self.button.setChecked(True)

def main():
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
