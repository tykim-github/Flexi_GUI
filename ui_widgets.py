"""
UI Components and Custom Widgets
"""

from PyQt5.QtWidgets import QLabel, QLineEdit, QHBoxLayout, QWidget
from PyQt5.QtGui import QFont, QDoubleValidator
import threading


class TitleLabel(QLabel):
    """큰 제목 레이블"""
    def __init__(self, text, fontsize=15):
        super().__init__(text)
        
        font = QFont()
        font.setPointSize(fontsize)
        font.setBold(True)
        self.setFont(font)


class TextLabel(QLabel):
    """일반 텍스트 레이블"""
    def __init__(self, text, fontsize=12):
        super().__init__(text)

        font = QFont()
        font.setPointSize(fontsize)
        self.setFont(font)


class LabeledLineEdit(QWidget):
    """레이블과 입력 필드를 함께 보여주는 위젯"""
    def __init__(self, label_text, init_value=0):
        super().__init__()
        self.init_value = str(init_value)
        self.initUI(label_text)

    def initUI(self, label_text):
        # QHBoxLayout 생성
        hbox = QHBoxLayout()

        # 레이블과 QLineEdit 위젯 생성 및 추가
        self.label = TextLabel(label_text)
        self.lineEdit = QLineEdit()
        self.lineEdit.setValidator(QDoubleValidator())
        self.lineEdit.setText(self.init_value)
        hbox.addWidget(self.label)
        hbox.addWidget(self.lineEdit)

        # 현재 위젯의 레이아웃을 설정
        self.setLayout(hbox)


class TimerRepeater(object):
    """
    반복 실행되는 타이머 구현
    """

    def __init__(self, name, interval, target):
        """
        타이머를 생성합니다.

        Parameters:
            name = 스레드 이름
            interval = 대상 실행 사이의 간격(초)
            target = 매 'interval'초마다 호출되는 함수
        """
        # 스레드 및 스레드 중지 이벤트 정의
        self._name = name
        self._thread = None
        self._event = None
        # 대상 초기화
        self._target = target
        # 타이머 초기화
        self._interval = interval

    def _run(self):
        """
        타이머를 실행하는 스레드를 실행합니다.

        Returns:
            None
        """
        while not self._event.wait(self._interval):
            self._target()

    def start(self):
        """
        타이머를 시작합니다

        Returns:
            None
        """
        # 여러 번 시작하지 않도록 주의
        if self._thread == None:
            self._event = threading.Event()
            self._thread = threading.Thread(None, self._run, self._name)
            self._thread.start()

    def stop(self):
        """
        타이머를 중지합니다

        Returns:
            None
        """
        if self._thread != None:
            self._event.set()
            self._thread.join()
            self._thread = None
